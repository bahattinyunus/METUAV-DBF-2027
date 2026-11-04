#include "ucus_kontrol/adaptive_pid_controller.hpp"

namespace dbf
{
namespace flight_control
{

AdaptivePIDController::AdaptivePIDController()
: AdaptivePIDController(PIDGains{1.0, 0.05, 0.1, 0.0}, -1.0, 1.0, 0.3, 0.2)
{
}

AdaptivePIDController::AdaptivePIDController(
  const PIDGains & base_gains,
  double output_min,
  double output_max,
  double integral_limit,
  double derivative_filter_alpha)
: base_gains_(base_gains),
  active_gains_(base_gains),
  output_min_(output_min),
  output_max_(output_max),
  integral_limit_(integral_limit),
  filter_alpha_(derivative_filter_alpha),
  prev_error_(0.0),
  integral_(0.0),
  filtered_derivative_(0.0),
  payload_trim_offset_(0.0),
  payload_compensation_active_(false)
{
}

void AdaptivePIDController::setBaseGains(const PIDGains & gains)
{
  base_gains_ = gains;
  active_gains_ = gains;
}

void AdaptivePIDController::setOutputLimits(double min_val, double max_val)
{
  output_min_ = min_val;
  output_max_ = max_val;
}

void AdaptivePIDController::setIntegralLimits(double limit)
{
  integral_limit_ = std::abs(limit);
}

void AdaptivePIDController::setDerivativeFilterAlpha(double alpha)
{
  filter_alpha_ = std::clamp(alpha, 0.01, 1.0);
}

void AdaptivePIDController::reset()
{
  prev_error_ = 0.0;
  integral_ = 0.0;
  filtered_derivative_ = 0.0;
  payload_trim_offset_ = 0.0;
  payload_compensation_active_ = false;
  active_gains_ = base_gains_;
}

void AdaptivePIDController::triggerPayloadReleaseCompensation(double pitch_trim_offset_deg)
{
  payload_compensation_active_ = true;
  payload_trim_offset_ = pitch_trim_offset_deg;
  
  // Instant anti-shock integral bleed: decay accumulated integral to prevent overshooting
  integral_ *= 0.25;
}

double AdaptivePIDController::compute(
  double setpoint,
  double measured,
  double dt,
  const AircraftState & state)
{
  if (dt <= 0.0001) {
    return 0.0;
  }

  // 1. Aerodynamic Dynamic Pressure Adaptation:
  // Control surface effectiveness scales quadratically with airspeed: q = 0.5 * rho * V^2.
  // Nominal speed: 22.0 m/s. At higher speed, surfaces are more effective -> reduce gains.
  // At lower speed, surfaces are sluggish -> increase gains to maintain control authority.
  const double v_nominal = 22.0;
  const double v_safe = std::max(state.airspeed, 8.0);
  const double q_ratio = std::pow(v_nominal / v_safe, 1.3);
  const double dyn_gain_factor = std::clamp(q_ratio, 0.5, 2.2);

  // 2. Mass and Inertia Adaptation:
  // When carrying heavy payload (TOGW ~25kg), aircraft has higher inertia -> requires higher Kp & Kd.
  // When payload drops (empty ~13kg), lower inertia -> lower gains needed to prevent high-frequency oscillations.
  const double mass_ratio = state.current_mass / std::max(state.nominal_mass, 10.0);
  const double mass_factor = std::clamp(std::sqrt(mass_ratio), 0.65, 1.4);

  // Scaled Gains
  active_gains_.kp = base_gains_.kp * dyn_gain_factor * mass_factor;
  active_gains_.ki = base_gains_.ki * dyn_gain_factor;
  active_gains_.kd = base_gains_.kd * dyn_gain_factor * mass_factor;
  active_gains_.ff = base_gains_.ff;

  // Error calculation
  double error = setpoint - measured;

  // Proportional Term
  double p_term = active_gains_.kp * error;

  // Integral Term with Anti-Windup Clamping
  integral_ += error * dt;
  integral_ = std::clamp(integral_, -integral_limit_, integral_limit_);
  double i_term = active_gains_.ki * integral_;

  // Derivative Term with 1st-order Low-Pass Filter
  double raw_derivative = (error - prev_error_) / dt;
  filtered_derivative_ = (1.0 - filter_alpha_) * filtered_derivative_ + filter_alpha_ * raw_derivative;
  double d_term = active_gains_.kd * filtered_derivative_;

  // Feed-forward Term
  double ff_term = active_gains_.ff * setpoint;

  // Payload drop feed-forward trim offset (applied to elevator during drop transition)
  double trim_term = 0.0;
  if (payload_compensation_active_) {
    trim_term = payload_trim_offset_;
    // Smoothly blend trim offset over time if necessary
  }

  // Combined Output
  double total_output = p_term + i_term + d_term + ff_term + trim_term;

  // Output Saturation
  double saturated_output = std::clamp(total_output, output_min_, output_max_);

  // Back-calculation anti-windup: bleed integral if saturated
  if (total_output != saturated_output && (total_output * error > 0.0)) {
    integral_ -= error * dt * 0.5;
  }

  prev_error_ = error;
  return saturated_output;
}

}  // namespace flight_control
}  // namespace dbf
