#include "ucus_kontrol/mission_manager.hpp"

namespace metuav
{
namespace mission
{

MissionManager::MissionManager()
: MissionManager(MissionConfig{})
{
}

MissionManager::MissionManager(const MissionConfig & config)
: config_(config),
  current_state_(MissionState::BOOT_AND_PREFLIGHT),
  completed_laps_(0),
  elapsed_time_sec_(0.0),
  payload_released_(false)
{
}

void MissionManager::configure(const MissionConfig & config)
{
  config_ = config;
}

void MissionManager::startMission(FlightMission mission)
{
  config_.active_mission = mission;
  completed_laps_ = 0;
  elapsed_time_sec_ = 0.0;
  payload_released_ = false;
  failsafe_reason_.clear();
  current_state_ = MissionState::ARMED_READY;
}

void MissionManager::updateLapCount(int lap)
{
  completed_laps_ = lap;
  if (config_.active_mission == FlightMission::MISSION_1_STAGING &&
      completed_laps_ >= config_.total_laps_required)
  {
    // Mission 1 complete: 3 laps finished within 5 minutes
    current_state_ = MissionState::RETURN_TO_LAND;
  }
}

void MissionManager::triggerPayloadDrop()
{
  if (config_.active_mission == FlightMission::MISSION_3_DELIVERY) {
    current_state_ = MissionState::PAYLOAD_RELEASE;
    payload_released_ = true;
  }
}

void MissionManager::triggerFailsafe(const std::string & reason)
{
  failsafe_reason_ = reason;
  current_state_ = MissionState::FAILSAFE_HOLD;
}

void MissionManager::update(double dt, double battery_voltage, double current_altitude, double current_speed)
{
  (void)current_altitude;
  (void)current_speed;

  if (current_state_ != MissionState::BOOT_AND_PREFLIGHT &&
      current_state_ != MissionState::TOUCHDOWN_DISARMED &&
      current_state_ != MissionState::FAILSAFE_HOLD)
  {
    elapsed_time_sec_ += dt;
  }

  // Safety: Battery critical voltage check
  if (battery_voltage > 0.0 && battery_voltage < config_.min_battery_voltage) {
    triggerFailsafe("CRITICAL_BATTERY_VOLTAGE");
    return;
  }

  // 5-minute mission window limit enforcement
  if (elapsed_time_sec_ >= config_.max_mission_time_sec) {
    if (current_state_ != MissionState::RETURN_TO_LAND && current_state_ != MissionState::TOUCHDOWN_DISARMED) {
      current_state_ = MissionState::RETURN_TO_LAND;
    }
  }

  // State transitions
  switch (current_state_) {
    case MissionState::BOOT_AND_PREFLIGHT:
      break;

    case MissionState::ARMED_READY:
      // Transition to takeoff
      current_state_ = MissionState::TAKEOFF_CLIMB;
      break;

    case MissionState::TAKEOFF_CLIMB:
      if (current_altitude >= (config_.cruise_altitude_m * 0.85)) {
        if (config_.active_mission == FlightMission::MISSION_3_DELIVERY) {
          current_state_ = MissionState::TARGET_SEARCH_AND_ALIGN;
        } else {
          current_state_ = MissionState::CIRCUIT_NAVIGATION;
        }
      }
      break;

    case MissionState::CIRCUIT_NAVIGATION:
      if (completed_laps_ >= config_.total_laps_required) {
        current_state_ = MissionState::RETURN_TO_LAND;
      }
      break;

    case MissionState::TARGET_SEARCH_AND_ALIGN:
      // Awaiting payload release trigger
      break;

    case MissionState::PAYLOAD_RELEASE:
      // Once released, proceed to circuit exit and landing
      current_state_ = MissionState::RETURN_TO_LAND;
      break;

    case MissionState::RETURN_TO_LAND:
      if (current_altitude < 1.0) {
        current_state_ = MissionState::TOUCHDOWN_DISARMED;
      }
      break;

    case MissionState::TOUCHDOWN_DISARMED:
    case MissionState::FAILSAFE_HOLD:
      break;
  }
}

std::string MissionManager::getStateString() const
{
  switch (current_state_) {
    case MissionState::BOOT_AND_PREFLIGHT: return "BOOT_AND_PREFLIGHT";
    case MissionState::ARMED_READY: return "ARMED_READY";
    case MissionState::TAKEOFF_CLIMB: return "TAKEOFF_CLIMB";
    case MissionState::CIRCUIT_NAVIGATION: return "CIRCUIT_NAVIGATION";
    case MissionState::TARGET_SEARCH_AND_ALIGN: return "TARGET_SEARCH_AND_ALIGN";
    case MissionState::PAYLOAD_RELEASE: return "PAYLOAD_RELEASE";
    case MissionState::RETURN_TO_LAND: return "RETURN_TO_LAND";
    case MissionState::TOUCHDOWN_DISARMED: return "TOUCHDOWN_DISARMED";
    case MissionState::FAILSAFE_HOLD: return "FAILSAFE_HOLD (" + failsafe_reason_ + ")";
    default: return "UNKNOWN";
  }
}

}  // namespace mission
}  // namespace metuav
