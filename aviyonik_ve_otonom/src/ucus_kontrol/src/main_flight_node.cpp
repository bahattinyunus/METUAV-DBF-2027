#include <memory>
#include <chrono>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/nav_sat_fix.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "std_msgs/msg/float32.hpp"
#include "std_msgs/msg/string.hpp"
#include "std_msgs/msg/bool.hpp"

#include "ucus_kontrol/adaptive_pid_controller.hpp"
#include "ucus_kontrol/mission_manager.hpp"
#include "ucus_kontrol/fast_boot_calibrator.hpp"

using namespace std::chrono_literals;

namespace dbf
{

class FlightControlNode : public rclcpp::Node
{
public:
  FlightControlNode()
  : Node("flight_control_node")
  {
    RCLCPP_INFO(this->get_logger(), "AIAA DBF 2027 Uçuş Kontrolcüsü Başlatılıyor...");

    // Declare parameters
    this->declare_parameter("roll_kp", 1.8);
    this->declare_parameter("roll_ki", 0.12);
    this->declare_parameter("roll_kd", 0.25);
    this->declare_parameter("pitch_kp", 2.2);
    this->declare_parameter("pitch_ki", 0.18);
    this->declare_parameter("pitch_kd", 0.35);
    this->declare_parameter("payload_pitch_trim_deg", -3.2);  // Nose-down trim offset when payload drops
    this->declare_parameter("nominal_mass_kg", 24.8);         // TOGW max ~25 kg
    this->declare_parameter("empty_mass_kg", 13.5);           // Post drop mass

    // Initialize PID Controllers
    flight_control::PIDGains roll_gains{
      this->get_parameter("roll_kp").as_double(),
      this->get_parameter("roll_ki").as_double(),
      this->get_parameter("roll_kd").as_double(),
      0.0
    };
    roll_controller_.setBaseGains(roll_gains);
    roll_controller_.setOutputLimits(-1.0, 1.0);

    flight_control::PIDGains pitch_gains{
      this->get_parameter("pitch_kp").as_double(),
      this->get_parameter("pitch_ki").as_double(),
      this->get_parameter("pitch_kd").as_double(),
      0.0
    };
    pitch_controller_.setBaseGains(pitch_gains);
    pitch_controller_.setOutputLimits(-1.0, 1.0);

    aircraft_state_.current_mass = this->get_parameter("nominal_mass_kg").as_double();
    aircraft_state_.nominal_mass = aircraft_state_.current_mass;

    // Publishers
    actuator_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("dbf/actuator_controls", 10);
    mission_status_pub_ = this->create_publisher<std_msgs::msg::String>("dbf/mission_state", 10);
    fast_boot_pub_ = this->create_publisher<std_msgs::msg::String>("dbf/boot_diagnostic", 10);

    // Subscribers
    imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
      "dbf/imu/data", 20,
      std::bind(&FlightControlNode::imuCallback, this, std::placeholders::_1));

    gps_sub_ = this->create_subscription<sensor_msgs::msg::NavSatFix>(
      "dbf/gps/fix", 10,
      std::bind(&FlightControlNode::gpsCallback, this, std::placeholders::_1));

    airspeed_sub_ = this->create_subscription<std_msgs::msg::Float32>(
      "dbf/airspeed", 10,
      std::bind(&FlightControlNode::airspeedCallback, this, std::placeholders::_1));

    drop_cmd_sub_ = this->create_subscription<std_msgs::msg::Bool>(
      "dbf/payload_drop_trigger", 10,
      std::bind(&FlightControlNode::dropTriggerCallback, this, std::placeholders::_1));

    // Fast 50 Hz control loop timer
    control_timer_ = this->create_wall_timer(
      20ms, std::bind(&FlightControlNode::controlLoop, this));

    // 1 Hz Mission and Diagnostics timer
    diagnostic_timer_ = this->create_wall_timer(
      1000ms, std::bind(&FlightControlNode::diagnosticLoop, this));

    RCLCPP_INFO(this->get_logger(), "Uçuş Kontrolcüsü ve Görev Yöneticisi 50 Hz döngü ile hazır!");
  }

private:
  void imuCallback(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    current_pitch_rate_ = msg->angular_velocity.y;
    current_roll_rate_ = msg->angular_velocity.x;

    if (!fast_boot_.isReady()) {
      fast_boot_.addImuSample(
        msg->angular_velocity.x, msg->angular_velocity.y, msg->angular_velocity.z,
        msg->linear_acceleration.x, msg->linear_acceleration.y, msg->linear_acceleration.z);
    }
  }

  void gpsCallback(const sensor_msgs::msg::NavSatFix::SharedPtr msg)
  {
    double hdop = std::sqrt(msg->position_covariance[0]);
    fast_boot_.updateGpsStatus(12, hdop);
    current_altitude_ = msg->altitude;
  }

  void airspeedCallback(const std_msgs::msg::Float32::SharedPtr msg)
  {
    aircraft_state_.airspeed = msg->data;
  }

  void dropTriggerCallback(const std_msgs::msg::Bool::SharedPtr msg)
  {
    if (msg->data && !aircraft_state_.payload_released) {
      RCLCPP_WARN(this->get_logger(), "GÖREV 3: FAYDALI YÜK BIRAKMA TETİKLENDİ! Adaptif CG kompanzasyonu devrede!");
      aircraft_state_.payload_released = true;
      aircraft_state_.current_mass = this->get_parameter("empty_mass_kg").as_double();
      
      double trim_offset = this->get_parameter("payload_pitch_trim_deg").as_double();
      pitch_controller_.triggerPayloadReleaseCompensation(trim_offset);
      mission_manager_.triggerPayloadDrop();
    }
  }

  void controlLoop()
  {
    const double dt = 0.02;  // 50 Hz

    if (!fast_boot_.isReady()) {
      fast_boot_.step(dt);
      return;
    }

    // Step mission manager
    mission_manager_.update(dt, battery_voltage_, current_altitude_, aircraft_state_.airspeed);

    // Compute PID control surface commands
    double roll_command = roll_controller_.compute(target_roll_rate_, current_roll_rate_, dt, aircraft_state_);
    double pitch_command = pitch_controller_.compute(target_pitch_rate_, current_pitch_rate_, dt, aircraft_state_);

    // Publish to actuators
    geometry_msgs::msg::Twist cmd;
    cmd.angular.x = roll_command;   // Ailerons
    cmd.angular.y = pitch_command;  // Elevator
    cmd.angular.z = 0.0;            // Rudder
    cmd.linear.x = 0.75;            // Throttle normalized (75% cruise)
    actuator_pub_->publish(cmd);
  }

  void diagnosticLoop()
  {
    std_msgs::msg::String diag_msg;
    diag_msg.data = fast_boot_.getReport().diagnostic_message;
    fast_boot_pub_->publish(diag_msg);

    std_msgs::msg::String mission_msg;
    mission_msg.data = "Mission: " + std::to_string(static_cast<int>(mission_manager_.getActiveMission())) +
      " | State: " + mission_manager_.getStateString() +
      " | Time: " + std::to_string(mission_manager_.getElapsedTime()) + "s";
    mission_status_pub_->publish(mission_msg);
  }

  // Member variables
  flight_control::AdaptivePIDController roll_controller_;
  flight_control::AdaptivePIDController pitch_controller_;
  flight_control::AircraftState aircraft_state_;
  mission::MissionManager mission_manager_;
  calibration::FastBootCalibrator fast_boot_;

  double current_roll_rate_{0.0};
  double current_pitch_rate_{0.0};
  double target_roll_rate_{0.0};
  double target_pitch_rate_{0.0};
  double current_altitude_{0.0};
  double battery_voltage_{24.5};

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr actuator_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr mission_status_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr fast_boot_pub_;

  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr gps_sub_;
  rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr airspeed_sub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr drop_cmd_sub_;

  rclcpp::TimerBase::SharedPtr control_timer_;
  rclcpp::TimerBase::SharedPtr diagnostic_timer_;
};

}  // namespace dbf

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<dbf::FlightControlNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
