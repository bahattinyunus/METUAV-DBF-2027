#include "ucus_kontrol/fast_boot_calibrator.hpp"
#include <numeric>
#include <cmath>

namespace dbf
{
namespace calibration
{

FastBootCalibrator::FastBootCalibrator()
{
  reset();
}

void FastBootCalibrator::reset()
{
  report_ = CalibrationReport{};
  report_.status = CalibrationStatus::SAMPLING_STATIONARY;
  gx_samples_.clear();
  gy_samples_.clear();
  gz_samples_.clear();
  ax_samples_.clear();
  ay_samples_.clear();
  az_samples_.clear();
  pitot_samples_.clear();
}

void FastBootCalibrator::addImuSample(double gx, double gy, double gz, double ax, double ay, double az)
{
  if (report_.status == CalibrationStatus::SAMPLING_STATIONARY) {
    gx_samples_.push_back(gx);
    gy_samples_.push_back(gy);
    gz_samples_.push_back(gz);
    ax_samples_.push_back(ax);
    ay_samples_.push_back(ay);
    az_samples_.push_back(az);
  }
}

void FastBootCalibrator::addAirspeedSample(double differential_pressure_pa)
{
  if (report_.status == CalibrationStatus::SAMPLING_STATIONARY) {
    pitot_samples_.push_back(differential_pressure_pa);
  }
}

void FastBootCalibrator::updateGpsStatus(int satellites, double hdop)
{
  report_.gps_satellites = satellites;
  report_.gps_hdop = hdop;
}

void FastBootCalibrator::step(double dt)
{
  report_.elapsed_seconds += dt;

  if (report_.status == CalibrationStatus::SAMPLING_STATIONARY) {
    if (gx_samples_.size() >= REQUIRED_SAMPLES) {
      report_.status = CalibrationStatus::CONVERGING_BIAS;

      auto calc_mean = [](const std::vector<double> & v) {
        return std::accumulate(v.begin(), v.end(), 0.0) / static_cast<double>(v.size());
      };

      report_.gyro_bias[0] = calc_mean(gx_samples_);
      report_.gyro_bias[1] = calc_mean(gy_samples_);
      report_.gyro_bias[2] = calc_mean(gz_samples_);

      report_.accel_bias[0] = calc_mean(ax_samples_);
      report_.accel_bias[1] = calc_mean(ay_samples_);
      // Z-axis contains 1G (9.80665 m/s^2)
      report_.accel_bias[2] = calc_mean(az_samples_) - 9.80665;

      if (!pitot_samples_.empty()) {
        report_.pitot_zero_offset = calc_mean(pitot_samples_);
      }

      report_.status = CalibrationStatus::CHECKING_GPS;
    }
  }

  if (report_.status == CalibrationStatus::CHECKING_GPS) {
    // AIAA DBF Pre-flight check: Good 3D fix required
    if (report_.gps_satellites >= 8 && report_.gps_hdop <= 1.5) {
      report_.status = CalibrationStatus::SYSTEM_READY;
      report_.diagnostic_message = "Fast-Boot Calibration PASSED in " + 
        std::to_string(report_.elapsed_seconds) + " seconds (Well below 5-minute rule).";
    } else if (report_.elapsed_seconds > 180.0) {
      report_.status = CalibrationStatus::CALIBRATION_FAILED;
      report_.diagnostic_message = "GPS lock timeout exceeded 3 minutes!";
    }
  }
}

}  // namespace calibration
}  // namespace dbf
