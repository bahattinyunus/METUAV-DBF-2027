#ifndef UCUS_KONTROL__EXTENDED_KALMAN_FILTER_HPP_
#define UCUS_KONTROL__EXTENDED_KALMAN_FILTER_HPP_

#include <array>
#include <cmath>
#include <algorithm>

namespace metuav
{
namespace navigation
{

struct NavState
{
  std::array<double, 3> pos{0.0, 0.0, 0.0};  // North, East, Down (m)
  std::array<double, 3> vel{0.0, 0.0, 0.0};  // Vn, Ve, Vd (m/s)
  std::array<double, 3> euler{0.0, 0.0, 0.0}; // Roll, Pitch, Yaw (rad)
  std::array<double, 3> accel_bias{0.0, 0.0, 0.0};
  std::array<double, 3> gyro_bias{0.0, 0.0, 0.0};
  double airspeed{0.0};
};

class ExtendedKalmanFilter
{
public:
  ExtendedKalmanFilter();

  void initialize(double init_lat, double init_lon, double init_alt);
  void reset();

  // High-rate IMU prediction step (50 Hz)
  void predict(
    double ax, double ay, double az,
    double gx, double gy, double gz,
    double dt);

  // GPS measurement update (10 Hz)
  void updateGps(double pos_n, double pos_e, double pos_d, double vel_n, double vel_e, double vel_d);

  // Pitot-static airspeed measurement update (20 Hz)
  void updateAirspeed(double measured_ias);

  // Compass / Magnetometer heading update with tilt compensation & anomaly rejection
  bool updateCompass(
    double mag_x, double mag_y, double mag_z,
    double declination_rad = 0.0,
    double expected_norm_ut = 48.5);

  NavState getState() const { return state_; }
  bool isGpsHealthy() const { return gps_healthy_; }

private:
  NavState state_;
  bool initialized_{false};
  bool gps_healthy_{true};
  double time_since_last_gps_{0.0};

  // Error covariance diagonal approximations for real-time edge embedded execution
  std::array<double, 3> p_pos_{1.0, 1.0, 2.0};
  std::array<double, 3> p_vel_{0.5, 0.5, 0.8};
  std::array<double, 3> p_att_{0.05, 0.05, 0.1};

  // Process noise Q
  double q_accel_{0.15};
  double q_gyro_{0.015};
  double q_bias_{0.001};

  // Measurement noise R
  double r_gps_pos_{1.2};
  double r_gps_vel_{0.3};
  double r_airspeed_{0.6};
  double r_compass_{0.08};
};

}  // namespace navigation
}  // namespace metuav

#endif  // UCUS_KONTROL__EXTENDED_KALMAN_FILTER_HPP_
