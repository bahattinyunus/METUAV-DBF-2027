#ifndef UCUS_KONTROL__FAST_BOOT_CALIBRATOR_HPP_
#define UCUS_KONTROL__FAST_BOOT_CALIBRATOR_HPP_

#include <vector>
#include <string>
#include <array>
#include <cstdint>

namespace metuav
{
namespace calibration
{

enum class CalibrationStatus : uint8_t
{
  INITIALIZING = 0,
  SAMPLING_STATIONARY = 1,
  CONVERGING_BIAS = 2,
  CHECKING_GPS = 3,
  SYSTEM_READY = 4,
  CALIBRATION_FAILED = 5
};

struct CalibrationReport
{
  CalibrationStatus status{CalibrationStatus::INITIALIZING};
  double elapsed_seconds{0.0};
  std::array<double, 3> gyro_bias{0.0, 0.0, 0.0};
  std::array<double, 3> accel_bias{0.0, 0.0, 0.0};
  double pitot_zero_offset{0.0};
  int gps_satellites{0};
  double gps_hdop{99.9};
  std::string diagnostic_message{""};
};

class FastBootCalibrator
{
public:
  FastBootCalibrator();

  void reset();
  void addImuSample(double gx, double gy, double gz, double ax, double ay, double az);
  void addAirspeedSample(double differential_pressure_pa);
  void updateGpsStatus(int satellites, double hdop);
  void step(double dt);

  CalibrationReport getReport() const { return report_; }
  bool isReady() const { return report_.status == CalibrationStatus::SYSTEM_READY; }

private:
  static constexpr size_t REQUIRED_SAMPLES = 100;
  CalibrationReport report_;

  std::vector<double> gx_samples_;
  std::vector<double> gy_samples_;
  std::vector<double> gz_samples_;
  std::vector<double> ax_samples_;
  std::vector<double> ay_samples_;
  std::vector<double> az_samples_;
  std::vector<double> pitot_samples_;
};

}  // namespace calibration
}  // namespace metuav

#endif  // UCUS_KONTROL__FAST_BOOT_CALIBRATOR_HPP_
