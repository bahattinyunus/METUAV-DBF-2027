#include "ucus_kontrol/extended_kalman_filter.hpp"

namespace metuav
{
namespace navigation
{

ExtendedKalmanFilter::ExtendedKalmanFilter()
{
  reset();
}

void ExtendedKalmanFilter::reset()
{
  state_ = NavState{};
  initialized_ = false;
  gps_healthy_ = false;
  time_since_last_gps_ = 0.0;
  p_pos_ = {5.0, 5.0, 10.0};
  p_vel_ = {1.0, 1.0, 2.0};
  p_att_ = {0.1, 0.1, 0.2};
}

void ExtendedKalmanFilter::initialize(double init_lat, double init_lon, double init_alt)
{
  (void)init_lat;
  (void)init_lon;
  state_.pos = {0.0, 0.0, -init_alt};
  state_.vel = {0.0, 0.0, 0.0};
  state_.euler = {0.0, 0.0, 0.0};
  initialized_ = true;
  gps_healthy_ = true;
  time_since_last_gps_ = 0.0;
}

void ExtendedKalmanFilter::predict(
  double ax, double ay, double az,
  double gx, double gy, double gz,
  double dt)
{
  if (!initialized_ || dt <= 0.0001) {
    return;
  }

  time_since_last_gps_ += dt;
  if (time_since_last_gps_ > 1.5) {
    gps_healthy_ = false;  // GPS timeout detection
  }

  // Bias removal
  double corr_gx = gx - state_.gyro_bias[0];
  double corr_gy = gy - state_.gyro_bias[1];
  double corr_gz = gz - state_.gyro_bias[2];

  double corr_ax = ax - state_.accel_bias[0];
  double corr_ay = ay - state_.accel_bias[1];
  double corr_az = az - state_.accel_bias[2];

  // Attitude update (Euler kinematics)
  double phi = state_.euler[0];
  double theta = state_.euler[1];
  double psi = state_.euler[2];

  double cos_th = std::cos(theta);
  double sin_th = std::sin(theta);
  double cos_phi = std::cos(phi);
  double sin_phi = std::sin(phi);

  if (std::abs(cos_th) > 0.01) {
    double d_phi = corr_gx + (corr_gy * sin_phi + corr_gz * cos_phi) * (sin_th / cos_th);
    double d_theta = corr_gy * cos_phi - corr_gz * sin_phi;
    double d_psi = (corr_gy * sin_phi + corr_gz * cos_phi) / cos_th;

    state_.euler[0] += d_phi * dt;
    state_.euler[1] += d_theta * dt;
    state_.euler[2] += d_psi * dt;
  }

  // Rotation Matrix Body to Navigation (NED)
  double r11 = std::cos(theta) * std::cos(psi);
  double r12 = sin_phi * sin_th * std::cos(psi) - cos_phi * std::sin(psi);
  double r13 = cos_phi * sin_th * std::cos(psi) + sin_phi * std::sin(psi);

  double r21 = std::cos(theta) * std::sin(psi);
  double r22 = sin_phi * sin_th * std::sin(psi) + cos_phi * std::cos(psi);
  double r23 = cos_phi * sin_th * std::sin(psi) - sin_phi * std::cos(psi);

  double r31 = -sin_th;
  double r32 = sin_phi * cos_th;
  double r33 = cos_phi * cos_th;

  // Accel in Navigation Frame (minus gravity)
  double an = r11 * corr_ax + r12 * corr_ay + r13 * corr_az;
  double ae = r21 * corr_ax + r22 * corr_ay + r23 * corr_az;
  double ad = r31 * corr_ax + r32 * corr_ay + r33 * corr_az + 9.80665;

  // Velocity update
  state_.vel[0] += an * dt;
  state_.vel[1] += ae * dt;
  state_.vel[2] += ad * dt;

  // Position update
  state_.pos[0] += state_.vel[0] * dt;
  state_.pos[1] += state_.vel[1] * dt;
  state_.pos[2] += state_.vel[2] * dt;

  // Covariance propagation (simplified diagonal tracking)
  for (int i = 0; i < 3; ++i) {
    p_pos_[i] += p_vel_[i] * dt + 0.5 * q_accel_ * dt * dt;
    p_vel_[i] += q_accel_ * dt;
    p_att_[i] += q_gyro_ * dt;
  }
}

void ExtendedKalmanFilter::updateGps(
  double pos_n, double pos_e, double pos_d,
  double vel_n, double vel_e, double vel_d)
{
  if (!initialized_) {
    initialize(0.0, 0.0, -pos_d);
    return;
  }

  time_since_last_gps_ = 0.0;
  gps_healthy_ = true;

  // Position Kalman Gain K_pos = P / (P + R)
  for (int i = 0; i < 3; ++i) {
    double z_pos = (i == 0) ? pos_n : ((i == 1) ? pos_e : pos_d);
    double k_pos = p_pos_[i] / (p_pos_[i] + r_gps_pos_);
    state_.pos[i] += k_pos * (z_pos - state_.pos[i]);
    p_pos_[i] = (1.0 - k_pos) * p_pos_[i];

    double z_vel = (i == 0) ? vel_n : ((i == 1) ? vel_e : vel_d);
    double k_vel = p_vel_[i] / (p_vel_[i] + r_gps_vel_);
    state_.vel[i] += k_vel * (z_vel - state_.vel[i]);
    p_vel_[i] = (1.0 - k_vel) * p_vel_[i];
  }
}

void ExtendedKalmanFilter::updateAirspeed(double measured_ias)
{
  if (!initialized_ || measured_ias <= 0.0) {
    return;
  }

  // Blend measured pitot airspeed with horizontal ground speed
  double v_horiz = std::sqrt(state_.vel[0] * state_.vel[0] + state_.vel[1] * state_.vel[1]);
  double k_air = 0.35;
  state_.airspeed = (1.0 - k_air) * v_horiz + k_air * measured_ias;
}

bool ExtendedKalmanFilter::updateCompass(
  double mag_x, double mag_y, double mag_z,
  double declination_rad,
  double expected_norm_ut)
{
  if (!initialized_) {
    return false;
  }

  // 1. Check magnitude sanity (magnetic anomaly rejection)
  double field_norm = std::sqrt(mag_x * mag_x + mag_y * mag_y + mag_z * mag_z);
  if (field_norm < 0.65 * expected_norm_ut || field_norm > 1.35 * expected_norm_ut) {
    return false;  // Reject distorted magnetic measurement
  }

  // 2. Tilt compensation using current attitude estimates (roll and pitch)
  double phi = state_.euler[0];
  double theta = state_.euler[1];
  double cos_th = std::cos(theta);
  double sin_th = std::sin(theta);
  double cos_phi = std::cos(phi);
  double sin_phi = std::sin(phi);

  double bxh = mag_x * cos_th + mag_y * sin_phi * sin_th + mag_z * cos_phi * sin_th;
  double byh = mag_y * cos_phi - mag_z * sin_phi;

  // 3. Azimuth in NED frame
  constexpr double PI_VAL = 3.14159265358979323846;
  double measured_psi = std::atan2(-byh, bxh) + declination_rad;

  // 4. Innovation with wrap-to-pi
  double psi_err = measured_psi - state_.euler[2];
  while (psi_err > PI_VAL) psi_err -= 2.0 * PI_VAL;
  while (psi_err < -PI_VAL) psi_err += 2.0 * PI_VAL;

  // 5. Kalman gain update on yaw
  double k_yaw = p_att_[2] / (p_att_[2] + r_compass_);
  state_.euler[2] += k_yaw * psi_err;

  // Wrap updated yaw to [-pi, pi]
  while (state_.euler[2] > PI_VAL) state_.euler[2] -= 2.0 * PI_VAL;
  while (state_.euler[2] < -PI_VAL) state_.euler[2] += 2.0 * PI_VAL;

  p_att_[2] = (1.0 - k_yaw) * p_att_[2];
  return true;
}

}  // namespace navigation
}  // namespace metuav
