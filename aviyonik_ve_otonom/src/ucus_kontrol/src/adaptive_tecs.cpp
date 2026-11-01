#include "ucus_kontrol/adaptive_tecs.hpp"

namespace metuav
{
namespace flight_control
{

AdaptiveTECS::AdaptiveTECS()
: AdaptiveTECS(TECSConfig{})
{
}

AdaptiveTECS::AdaptiveTECS(const TECSConfig & config)
: config_(config),
  throttle_integ_(0.0),
  pitch_integ_(0.0)
{
  reset();
}

void AdaptiveTECS::reset()
{
  state_ = TECSState{};
  throttle_integ_ = 0.0;
  pitch_integ_ = 0.0;
}

void AdaptiveTECS::setMassScale(double current_mass_kg, double nominal_mass_kg)
{
  if (nominal_mass_kg > 1.0) {
    state_.payload_mass_factor = std::clamp(current_mass_kg / nominal_mass_kg, 0.45, 1.25);
  }
}

void AdaptiveTECS::update(
  double h_error,
  double v_error,
  double climb_rate,
  double airspeed_accel,
  double roll_rad,
  double dt)
{
  if (dt <= 0.0001) {
    return;
  }

  double tau = std::max(config_.time_constant, 0.5);

  // 1. Demanded Specific Energy Rates (Potential + Kinetic)
  // Demanded climb rate
  double h_dot_dem = std::clamp(h_error / tau, -4.5, 5.0);
  // Demanded forward acceleration rate expressed in equivalent climb rate
  double v_dot_dem = std::clamp(v_error / tau, -3.0, 3.5);
  double v_meas = config_.v_nominal;
  double kinetic_dem = (v_meas * v_dot_dem) / g_;

  // Total Energy Rate: S_E = h_dot + kinetic
  double s_e_dem = h_dot_dem + kinetic_dem;
  // Actual Total Energy Rate
  double kinetic_act = (v_meas * airspeed_accel) / g_;
  double s_e_act = climb_rate + kinetic_act;
  double s_e_err = s_e_dem - s_e_act;

  // Energy Balance Rate: S_B = h_dot - kinetic
  double s_b_dem = h_dot_dem - kinetic_dem;
  double s_b_act = climb_rate - kinetic_act;
  double s_b_err = s_b_dem - s_b_act;

  state_.specific_energy_rate = s_e_act;
  state_.specific_energy_balance_rate = s_b_act;

  // 2. Throttle Control (Driven by Total Energy Error)
  // Gains adapt based on payload mass factor: lighter aircraft requires less thrust
  double k_thr_p = 0.12 * state_.payload_mass_factor;
  double k_thr_i = 0.04 * state_.payload_mass_factor;

  throttle_integ_ += s_e_err * dt;
  throttle_integ_ = std::clamp(throttle_integ_, -0.3, 0.4);

  double base_throttle = config_.throttle_cruise * state_.payload_mass_factor;
  double raw_throttle = base_throttle + k_thr_p * s_e_err + k_thr_i * throttle_integ_;
  state_.target_throttle = std::clamp(raw_throttle, config_.throttle_min, config_.throttle_max);

  // 3. Pitch Control (Driven by Energy Balance Error)
  // Positive balance error -> plane needs more altitude and less speed -> pitch up
  double k_pitch_p = 2.4 * state_.payload_mass_factor;
  double k_pitch_i = 0.5 * state_.payload_mass_factor;

  pitch_integ_ += s_b_err * dt;
  pitch_integ_ = std::clamp(pitch_integ_, -4.0, 4.0);

  // Roll feedforward compensation: 1 / cos(roll)
  double cos_roll = std::max(std::cos(roll_rad), 0.35);
  double roll_comp_deg = config_.roll_feedforward * ((1.0 / cos_roll) - 1.0) * (180.0 / M_PI);
  roll_comp_deg = std::clamp(roll_comp_deg, 0.0, 6.0);

  double nominal_pitch_deg = 2.2;
  double raw_pitch = nominal_pitch_deg + k_pitch_p * s_b_err + k_pitch_i * pitch_integ_ + roll_comp_deg;
  state_.target_pitch_deg = std::clamp(raw_pitch, config_.pitch_min_deg, config_.pitch_max_deg);
}

}  // namespace flight_control
}  // namespace metuav
