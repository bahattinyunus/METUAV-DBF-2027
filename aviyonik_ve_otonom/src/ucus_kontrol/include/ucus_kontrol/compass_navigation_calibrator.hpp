#ifndef UCUS_KONTROL__COMPASS_NAVIGATION_CALIBRATOR_HPP_
#define UCUS_KONTROL__COMPASS_NAVIGATION_CALIBRATOR_HPP_

#include <array>
#include <cmath>
#include <string>
#include <vector>

namespace metuav
{
namespace navigation
{

struct CompassState
{
  bool is_healthy{true};
  double field_norm{48.5};
  double heading_rad{0.0};
  double heading_deg{0.0};
};

struct DualCompassHealth
{
  bool primary_healthy{true};
  bool secondary_healthy{true};
  int active_compass_id{1};
  double active_heading_deg{0.0};
  double divergence_deg{0.0};
  bool failover_active{false};
  std::string status_msg{"NOMINAL"};
};

class CompassNavigationCalibrator
{
public:
  CompassNavigationCalibrator(double earth_field_ref_ut = 48.5, double declination_deg = 6.2);

  // Set hard-iron offset (bx, by, bz) and 3x3 soft-iron matrix for primary compass
  void setPrimaryCalibration(
    const std::array<double, 3>& hard_iron,
    const std::array<std::array<double, 3>, 3>& soft_iron);

  // Set hard-iron offset and soft-iron matrix for secondary compass
  void setSecondaryCalibration(
    const std::array<double, 3>& hard_iron,
    const std::array<std::array<double, 3>, 3>& soft_iron);

  // Set motor-induced magnetic interference parameters (uT / Amp)
  void setMotorInterferenceCoeffs(
    const std::array<double, 3>& k_primary,
    const std::array<double, 3>& k_secondary);

  // Apply calibration and dynamic motor compensation
  std::array<double, 3> correctMeasurement(
    const std::array<double, 3>& raw_mag,
    double battery_current_amps,
    int compass_id = 1) const;

  // Calculate tilt-compensated heading (azimuth in NED, clockwise from North)
  double calculateTiltCompensatedHeading(
    const std::array<double, 3>& mag_corr,
    double roll_rad,
    double pitch_rad,
    bool apply_declination = true) const;

  // Real-time anomaly check
  bool isFieldHealthy(const std::array<double, 3>& mag_corr, double tolerance = 0.25) const;

  // Dual redundant monitor and auto-failover
  DualCompassHealth processDualCompass(
    const std::array<double, 3>& raw_primary,
    const std::array<double, 3>& raw_secondary,
    double roll_rad,
    double pitch_rad,
    double battery_current_amps = 0.0);

private:
  double earth_field_ref_{48.5};
  double declination_rad_{0.1082};

  std::array<double, 3> hard_iron_primary_{0.0, 0.0, 0.0};
  std::array<std::array<double, 3>, 3> soft_iron_primary_{{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}}};
  std::array<double, 3> k_motor_primary_{0.0, 0.0, 0.0};

  std::array<double, 3> hard_iron_secondary_{0.0, 0.0, 0.0};
  std::array<std::array<double, 3>, 3> soft_iron_secondary_{{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}}};
  std::array<double, 3> k_motor_secondary_{0.0, 0.0, 0.0};

  int active_compass_id_{1};
  int primary_fail_count_{0};
};

}  // namespace navigation
}  // namespace metuav

#endif  // UCUS_KONTROL__COMPASS_NAVIGATION_CALIBRATOR_HPP_
