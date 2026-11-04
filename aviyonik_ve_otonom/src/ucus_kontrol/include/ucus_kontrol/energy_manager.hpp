#ifndef UCUS_KONTROL__ENERGY_MANAGER_HPP_
#define UCUS_KONTROL__ENERGY_MANAGER_HPP_

#include <cstdint>
#include <string>

namespace dbf
{
namespace power
{

enum class BatteryAlertLevel : uint8_t
{
  NOMINAL = 0,
  WARNING = 1,
  CRITICAL_RTL = 2,
  EMERGENCY_LAND = 3
};

struct PowerState
{
  double voltage{25.2};             // 6S full voltage (V)
  double current{0.0};              // Instantaneous current draw (A)
  double power_watts{0.0};          // Instantaneous power (W)
  double energy_consumed_mah{0.0};  // Cumulative consumed mAh
  double soc_percent{100.0};        // Estimated State of Charge (%)
  double cell_min_voltage{4.2};     // Minimum cell voltage (V)
  double max_throttle_limit{1.0};   // Throttle limit (0.0 to 1.0)
  BatteryAlertLevel alert{BatteryAlertLevel::NOMINAL};
};

class EnergyManager
{
public:
  EnergyManager();
  explicit EnergyManager(double nominal_capacity_mah, double min_cell_v = 3.55);

  void reset();
  void update(double dt, double voltage, double current, double esc_temperature_c = 40.0);

  PowerState getState() const { return state_; }
  bool isRtlTriggered() const { return state_.alert >= BatteryAlertLevel::CRITICAL_RTL; }
  std::string getAlertString() const;

private:
  double nominal_capacity_mah_{16000.0};
  double min_cell_voltage_{3.55};
  double overcurrent_time_sec_{0.0};
  PowerState state_;
};

}  // namespace power
}  // namespace dbf

#endif  // UCUS_KONTROL__ENERGY_MANAGER_HPP_
