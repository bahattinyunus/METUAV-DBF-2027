#ifndef UCUS_KONTROL__MISSION_MANAGER_HPP_
#define UCUS_KONTROL__MISSION_MANAGER_HPP_

#include <string>
#include <chrono>
#include <cstdint>

namespace metuav
{
namespace mission
{

enum class FlightMission : uint8_t
{
  NONE = 0,
  GROUND_MISSION = 1,
  MISSION_1_STAGING = 2,
  MISSION_2_PAYLOAD = 3,
  MISSION_3_DELIVERY = 4
};

enum class MissionState : uint8_t
{
  BOOT_AND_PREFLIGHT = 0,
  ARMED_READY = 1,
  TAKEOFF_CLIMB = 2,
  CIRCUIT_NAVIGATION = 3,
  TARGET_SEARCH_AND_ALIGN = 4,
  PAYLOAD_RELEASE = 5,
  RETURN_TO_LAND = 6,
  TOUCHDOWN_DISARMED = 7,
  FAILSAFE_HOLD = 8
};

struct MissionConfig
{
  FlightMission active_mission{FlightMission::MISSION_1_STAGING};
  int total_laps_required{3};
  double max_mission_time_sec{300.0};  // 5 minutes max per DBF rule
  double cruise_altitude_m{40.0};
  double cruise_airspeed_ms{24.0};
  double drop_altitude_m{25.0};
  double min_battery_voltage{21.6};    // 6S LiPo critical cut-off (~3.6V/cell)
};

class MissionManager
{
public:
  MissionManager();
  explicit MissionManager(const MissionConfig & config);

  void configure(const MissionConfig & config);
  void startMission(FlightMission mission);
  void updateLapCount(int lap);
  void triggerPayloadDrop();
  void triggerFailsafe(const std::string & reason);

  // Periodic step
  void update(double dt, double battery_voltage, double current_altitude, double current_speed);

  // Status accessors
  FlightMission getActiveMission() const { return config_.active_mission; }
  MissionState getCurrentState() const { return current_state_; }
  int getCompletedLaps() const { return completed_laps_; }
  double getElapsedTime() const { return elapsed_time_sec_; }
  bool isPayloadReleased() const { return payload_released_; }
  bool isFailsafeActive() const { return current_state_ == MissionState::FAILSAFE_HOLD; }
  std::string getStateString() const;

private:
  MissionConfig config_;
  MissionState current_state_{MissionState::BOOT_AND_PREFLIGHT};
  int completed_laps_{0};
  double elapsed_time_sec_{0.0};
  bool payload_released_{false};
  std::string failsafe_reason_{""};
};

}  // namespace mission
}  // namespace metuav

#endif  // UCUS_KONTROL__MISSION_MANAGER_HPP_
