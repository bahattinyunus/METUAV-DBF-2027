#include "ucus_kontrol/compass_navigation_calibrator.hpp"

namespace metuav
{
namespace navigation
{

constexpr double PI_CONST = 3.14159265358979323846;

CompassNavigationCalibrator::CompassNavigationCalibrator(
  double earth_field_ref_ut,
  double declination_deg)
: earth_field_ref_(earth_field_ref_ut),
  declination_rad_(declination_deg * PI_CONST / 180.0)
{
}

void CompassNavigationCalibrator::setPrimaryCalibration(
  const std::array<double, 3>& hard_iron,
  const std::array<std::array<double, 3>, 3>& soft_iron)
{
  hard_iron_primary_ = hard_iron;
  soft_iron_primary_ = soft_iron;
}

void CompassNavigationCalibrator::setSecondaryCalibration(
  const std::array<double, 3>& hard_iron,
  const std::array<std::array<double, 3>, 3>& soft_iron)
{
  hard_iron_secondary_ = hard_iron;
  soft_iron_secondary_ = soft_iron;
}

void CompassNavigationCalibrator::setMotorInterferenceCoeffs(
  const std::array<double, 3>& k_primary,
  const std::array<double, 3>& k_secondary)
{
  k_motor_primary_ = k_primary;
  k_motor_secondary_ = k_secondary;
}

std::array<double, 3> CompassNavigationCalibrator::correctMeasurement(
  const std::array<double, 3>& raw_mag,
  double battery_current_amps,
  int compass_id) const
{
  const auto& hard = (compass_id == 1) ? hard_iron_primary_ : hard_iron_secondary_;
  const auto& soft = (compass_id == 1) ? soft_iron_primary_ : soft_iron_secondary_;
  const auto& km = (compass_id == 1) ? k_motor_primary_ : k_motor_secondary_;

  // 1. Remove hard iron
  double dx = raw_mag[0] - hard[0];
  double dy = raw_mag[1] - hard[1];
  double dz = raw_mag[2] - hard[2];

  // 2. Soft iron matrix multiplication
  double sx = soft[0][0] * dx + soft[0][1] * dy + soft[0][2] * dz;
  double sy = soft[1][0] * dx + soft[1][1] * dy + soft[1][2] * dz;
  double sz = soft[2][0] * dx + soft[2][1] * dy + soft[2][2] * dz;

  // 3. Dynamic motor current interference compensation
  sx -= km[0] * battery_current_amps;
  sy -= km[1] * battery_current_amps;
  sz -= km[2] * battery_current_amps;

  return {sx, sy, sz};
}

double CompassNavigationCalibrator::calculateTiltCompensatedHeading(
  const std::array<double, 3>& mag_corr,
  double roll_rad,
  double pitch_rad,
  bool apply_declination) const
{
  double cos_th = std::cos(pitch_rad);
  double sin_th = std::sin(pitch_rad);
  double cos_phi = std::cos(roll_rad);
  double sin_phi = std::sin(roll_rad);

  double bxh = mag_corr[0] * cos_th + mag_corr[1] * sin_phi * sin_th + mag_corr[2] * cos_phi * sin_th;
  double byh = mag_corr[1] * cos_phi - mag_corr[2] * sin_phi;

  double heading = std::atan2(-byh, bxh);
  if (apply_declination) {
    heading += declination_rad_;
  }

  while (heading > PI_CONST) heading -= 2.0 * PI_CONST;
  while (heading < -PI_CONST) heading += 2.0 * PI_CONST;

  return heading;
}

bool CompassNavigationCalibrator::isFieldHealthy(
  const std::array<double, 3>& mag_corr,
  double tolerance) const
{
  double norm = std::sqrt(
    mag_corr[0] * mag_corr[0] +
    mag_corr[1] * mag_corr[1] +
    mag_corr[2] * mag_corr[2]);

  double min_b = earth_field_ref_ * (1.0 - tolerance);
  double max_b = earth_field_ref_ * (1.0 + tolerance);

  return (norm >= min_b && norm <= max_b);
}

DualCompassHealth CompassNavigationCalibrator::processDualCompass(
  const std::array<double, 3>& raw_primary,
  const std::array<double, 3>& raw_secondary,
  double roll_rad,
  double pitch_rad,
  double battery_current_amps)
{
  auto corr1 = correctMeasurement(raw_primary, battery_current_amps, 1);
  auto corr2 = correctMeasurement(raw_secondary, battery_current_amps, 2);

  bool healthy1 = isFieldHealthy(corr1);
  bool healthy2 = isFieldHealthy(corr2);

  double h1 = calculateTiltCompensatedHeading(corr1, roll_rad, pitch_rad);
  double h2 = calculateTiltCompensatedHeading(corr2, roll_rad, pitch_rad);

  double diff_rad = std::abs(h1 - h2);
  while (diff_rad > PI_CONST) diff_rad = std::abs(diff_rad - 2.0 * PI_CONST);
  double diff_deg = diff_rad * 180.0 / PI_CONST;

  if (!healthy1 && healthy2) {
    primary_fail_count_++;
    if (primary_fail_count_ >= 5) {
      active_compass_id_ = 2;
    }
  } else if (healthy1) {
    if (primary_fail_count_ > 0) primary_fail_count_--;
    if (primary_fail_count_ == 0) active_compass_id_ = 1;
  }

  double active_h = (active_compass_id_ == 1) ? h1 : h2;
  double active_deg = active_h * 180.0 / PI_CONST;
  while (active_deg < 0.0) active_deg += 360.0;
  while (active_deg >= 360.0) active_deg -= 360.0;

  DualCompassHealth health;
  health.primary_healthy = healthy1;
  health.secondary_healthy = healthy2;
  health.active_compass_id = active_compass_id_;
  health.active_heading_deg = active_deg;
  health.divergence_deg = diff_deg;
  health.failover_active = (active_compass_id_ == 2);
  health.status_msg = health.failover_active ? "FAILOVER_SECONDARY" :
                      (diff_deg > 15.0 ? "HEADING_DIVERGENCE_WARN" : "NOMINAL");

  return health;
}

}  // namespace navigation
}  // namespace metuav
