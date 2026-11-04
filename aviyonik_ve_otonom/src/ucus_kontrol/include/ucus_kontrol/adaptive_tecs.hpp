#ifndef UCUS_KONTROL__ADAPTIVE_TECS_HPP_
#define UCUS_KONTROL__ADAPTIVE_TECS_HPP_

#include <cmath>
#include <algorithm>

namespace dbf
{
namespace flight_control
{

struct TECSConfig
{
  double time_constant{1.8};        // Longitudinal tracking time constant (s)
  double v_nominal{24.5};           // Cruise airspeed (m/s)
  double v_min{17.5};               // Minimum airspeed above stall (m/s)
  double v_max{34.0};               // Never exceed speed (m/s)
  double pitch_min_deg{-15.0};      // Max nose-down pitch (deg)
  double pitch_max_deg{18.0};       // Max nose-up pitch (deg)
  double throttle_min{0.0};         // Min idle throttle (0.0 to 1.0)
  double throttle_max{1.0};         // Max throttle (1.0)
  double throttle_cruise{0.55};     // Cruise throttle
  double roll_feedforward{1.2};     // Compensation for lift loss during banking
};

struct TECSState
{
  double specific_energy_rate{0.0};         // Total energy rate (m/s)
  double specific_energy_balance_rate{0.0}; // Energy balance rate (m/s)
  double target_throttle{0.55};
  double target_pitch_deg{2.5};
  double payload_mass_factor{1.0};          // 1.0 at TOGW 55 lbs, scales down to 0.55 after drop
};

class AdaptiveTECS
{
public:
  AdaptiveTECS();
  explicit AdaptiveTECS(const TECSConfig & config);

  void reset();
  void setMassScale(double current_mass_kg, double nominal_mass_kg);

  // Computes throttle and pitch commands simultaneously
  // h_error: target_altitude - current_altitude (m)
  // v_error: target_airspeed - current_airspeed (m/s)
  // climb_rate: current vertical velocity (m/s)
  // airspeed_accel: current forward acceleration (m/s^2)
  // roll_rad: current bank angle (rad)
  void update(
    double h_error,
    double v_error,
    double climb_rate,
    double airspeed_accel,
    double roll_rad,
    double dt);

  TECSState getState() const { return state_; }
  double getThrottle() const { return state_.target_throttle; }
  double getPitchDeg() const { return state_.target_pitch_deg; }

private:
  TECSConfig config_;
  TECSState state_;
  double g_{9.80665};

  double throttle_integ_{0.0};
  double pitch_integ_{0.0};
};

}  // namespace flight_control
}  // namespace dbf

#endif  // UCUS_KONTROL__ADAPTIVE_TECS_HPP_
