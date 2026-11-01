#ifndef UCUS_KONTROL__ADAPTIVE_PID_CONTROLLER_HPP_
#define UCUS_KONTROL__ADAPTIVE_PID_CONTROLLER_HPP_

#include <cmath>
#include <algorithm>
#include <string>

namespace metuav
{
namespace flight_control
{

struct PIDGains
{
  double kp{1.0};
  double ki{0.0};
  double kd{0.0};
  double ff{0.0};  // Feed-forward gain
};

struct AircraftState
{
  double airspeed{22.0};        // m/s
  double air_density{1.225};     // kg/m^3
  double current_mass{24.8};     // kg (TOGW limit: ~25 kg / 55 lbs)
  double nominal_mass{24.8};     // kg
  double cg_position_x{0.32};    // m (measured from nose / wing leading edge)
  bool payload_released{false};  // True immediately after Mission 3 payload drop
};

class AdaptivePIDController
{
public:
  AdaptivePIDController();
  explicit AdaptivePIDController(
    const PIDGains & base_gains,
    double output_min,
    double output_max,
    double integral_limit,
    double derivative_filter_alpha = 0.2);

  void setBaseGains(const PIDGains & gains);
  void setOutputLimits(double min_val, double max_val);
  void setIntegralLimits(double limit);
  void setDerivativeFilterAlpha(double alpha);
  void reset();

  // Compute command output with aerodynamic dynamic pressure and mass scaling
  double compute(
    double setpoint,
    double measured,
    double dt,
    const AircraftState & state);

  // Compensation for sudden CG shift & mass reduction on payload release
  void triggerPayloadReleaseCompensation(double pitch_trim_offset_deg);

  // Getters for telemetry
  PIDGains getActiveGains() const { return active_gains_; }
  double getIntegralTerm() const { return integral_; }
  double getDerivativeTerm() const { return filtered_derivative_; }

private:
  PIDGains base_gains_;
  PIDGains active_gains_;

  double output_min_{-1.0};
  double output_max_{1.0};
  double integral_limit_{0.5};
  double filter_alpha_{0.2};  // Low-pass filter coefficient for derivative

  double prev_error_{0.0};
  double integral_{0.0};
  double filtered_derivative_{0.0};
  double payload_trim_offset_{0.0};
  bool payload_compensation_active_{false};
};

}  // namespace flight_control
}  // namespace metuav

#endif  // UCUS_KONTROL__ADAPTIVE_PID_CONTROLLER_HPP_
