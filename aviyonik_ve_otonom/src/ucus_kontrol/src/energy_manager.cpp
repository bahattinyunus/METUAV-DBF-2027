#include "ucus_kontrol/energy_manager.hpp"
#include <algorithm>

namespace dbf
{
namespace power
{

EnergyManager::EnergyManager()
: EnergyManager(16000.0, 3.55)
{
}

EnergyManager::EnergyManager(double nominal_capacity_mah, double min_cell_v)
: nominal_capacity_mah_(nominal_capacity_mah),
  min_cell_voltage_(min_cell_v),
  overcurrent_time_sec_(0.0)
{
  reset();
}

void EnergyManager::reset()
{
  state_ = PowerState{};
  overcurrent_time_sec_ = 0.0;
}

void EnergyManager::update(double dt, double voltage, double current, double esc_temperature_c)
{
  state_.voltage = std::max(0.0, voltage);
  state_.current = std::max(0.0, current);
  state_.power_watts = state_.voltage * state_.current;

  // Coulomb counting: consumed mAh = (Current * dt / 3600) * 1000
  double delta_mah = (state_.current * dt / 3.6);
  state_.energy_consumed_mah += delta_mah;

  // State of charge based on nominal capacity
  double soc = 100.0 * (1.0 - (state_.energy_consumed_mah / nominal_capacity_mah_));
  state_.soc_percent = std::clamp(soc, 0.0, 100.0);

  // Approximate 6S average cell voltage
  state_.cell_min_voltage = state_.voltage / 6.0;

  // Over-current protection (> 95A continuous threshold)
  if (state_.current > 95.0) {
    overcurrent_time_sec_ += dt;
    if (overcurrent_time_sec_ > 15.0) {
      // Throttle limit step-down to prevent ESC thermal shutdown
      state_.max_throttle_limit = 0.80;
    }
  } else {
    overcurrent_time_sec_ = std::max(0.0, overcurrent_time_sec_ - dt * 0.5);
    state_.max_throttle_limit = 1.0;
  }

  // ESC Thermal Protection
  if (esc_temperature_c > 90.0) {
    state_.max_throttle_limit = std::min(state_.max_throttle_limit, 0.65);
  }

  // Battery Alert State Machine
  if (state_.cell_min_voltage < 3.40 || state_.soc_percent < 10.0) {
    state_.alert = BatteryAlertLevel::EMERGENCY_LAND;
  } else if (state_.cell_min_voltage < min_cell_voltage_ || state_.soc_percent < 20.0) {
    state_.alert = BatteryAlertLevel::CRITICAL_RTL;
  } else if (state_.cell_min_voltage < 3.70 || state_.soc_percent < 35.0) {
    state_.alert = BatteryAlertLevel::WARNING;
  } else {
    state_.alert = BatteryAlertLevel::NOMINAL;
  }
}

std::string EnergyManager::getAlertString() const
{
  switch (state_.alert) {
    case BatteryAlertLevel::NOMINAL: return "NOMINAL";
    case BatteryAlertLevel::WARNING: return "WARNING_35PCT_BATTERY";
    case BatteryAlertLevel::CRITICAL_RTL: return "CRITICAL_RTL_BATTERY";
    case BatteryAlertLevel::EMERGENCY_LAND: return "EMERGENCY_IMMEDIATE_LAND";
    default: return "UNKNOWN";
  }
}

}  // namespace power
}  // namespace dbf
