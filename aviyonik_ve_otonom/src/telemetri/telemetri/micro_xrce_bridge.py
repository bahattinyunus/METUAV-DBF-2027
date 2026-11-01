#!/usr/bin/env python3
"""
METUAV DBF 2027 - Micro XRCE-DDS & PX4 uORB Telemetry Bridge
Maps ROS 2 DDS messages directly to PX4 Autopilot uORB middleware
for low-latency offboard control, attitude streaming, and payload drop commands.
"""

import math
import struct
import time
from typing import Dict, Tuple, Optional

class VehicleCommand:
    """PX4 Vehicle Command constants (MAV_CMD equivalent in uORB)."""
    VEHICLE_CMD_NAV_TAKEOFF = 22
    VEHICLE_CMD_NAV_LAND = 21
    VEHICLE_CMD_DO_SET_MODE = 176
    VEHICLE_CMD_COMPONENT_ARM_DISARM = 400
    VEHICLE_CMD_DO_SET_ACTUATOR = 187
    VEHICLE_CMD_DO_REPOSITION = 192

class MicroXRCEBridge:
    """Simulates/Implements bidirectional DDS bridge between ROS2 and PX4 uORB."""

    def __init__(self, agent_ip: str = "127.0.0.1", port: int = 8888):
        self.agent_ip = agent_ip
        self.port = port
        self.connected = True
        self.sequence_num = 0

    def encode_vehicle_command(self, command: int, param1: float = 0.0, param2: float = 0.0,
                               param3: float = 0.0, param4: float = 0.0, param5: float = 0.0,
                               param6: float = 0.0, param7: float = 0.0) -> bytes:
        """Encodes uORB vehicle_command message into binary DDS frame."""
        self.sequence_num += 1
        timestamp_us = int(time.time() * 1e6) & 0xFFFFFFFFFFFFFFFF
        # Format: timestamp(uint64), param1..7(float32*7), command(uint32), target_system(uint8), target_component(uint8)
        payload = struct.pack('<Q 7f I B B',
                              timestamp_us,
                              param1, param2, param3, param4, param5, param6, param7,
                              command, 1, 1)
        return payload

    def decode_vehicle_attitude(self, data: bytes) -> Dict[str, float]:
        """Decodes uORB vehicle_attitude (quaternion [w, x, y, z] to roll, pitch, yaw)."""
        if len(data) < 40:
            return {"roll_deg": 0.0, "pitch_deg": 0.0, "yaw_deg": 0.0}

        timestamp_us, q0, q1, q2, q3 = struct.unpack('<Q 4f', data[:24])
        
        # Quaternion to Euler (Z-Y-X rotation sequence)
        sinr_cosp = 2.0 * (q0 * q1 + q2 * q3)
        cosr_cosp = 1.0 - 2.0 * (q1 * q1 + q2 * q2)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (q0 * q2 - q3 * q1)
        if abs(sinp) >= 1.0:
            pitch = math.copysign(math.pi / 2.0, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2.0 * (q0 * q3 + q1 * q2)
        cosy_cosp = 1.0 - 2.0 * (q2 * q2 + q3 * q3)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return {
            "timestamp_us": timestamp_us,
            "roll_deg": math.degrees(roll),
            "pitch_deg": math.degrees(pitch),
            "yaw_deg": math.degrees(yaw)
        }

    def trigger_payload_release(self, actuator_index: int = 5, normalized_val: float = 1.0) -> bytes:
        """Sends uORB DO_SET_ACTUATOR command to trigger payload release solenoid."""
        return self.encode_vehicle_command(
            command=VehicleCommand.VEHICLE_CMD_DO_SET_ACTUATOR,
            param1=normalized_val,   # Actuator output value (-1.0 to 1.0 or 0 to 1)
            param2=float(actuator_index), # Actuator channel
        )


def main():
    bridge = MicroXRCEBridge()
    print("=" * 68)
    print("  METUAV DBF 2027 - Micro XRCE-DDS & PX4 uORB Koprusu")
    print("=" * 68)

    # Test encoding an arming command
    arm_cmd = bridge.encode_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
    print(f"[OK] Arm Komutu Kodlandi: Uzunluk={len(arm_cmd)} bayt, Hex={arm_cmd[:16].hex()}...")

    # Test payload release actuator command
    drop_cmd = bridge.trigger_payload_release(actuator_index=5, normalized_val=1.0)
    print(f"[OK] Faydali Yuk Birakma Komutu Kodlandi: Uzunluk={len(drop_cmd)} bayt")

    # Test quaternion attitude decoding: 10 deg pitch up
    pitch_rad = math.radians(10.0)
    q0 = math.cos(pitch_rad / 2.0)
    q2 = math.sin(pitch_rad / 2.0)
    raw_att = struct.pack('<Q 4f 4f', int(time.time()*1e6), q0, 0.0, q2, 0.0, 0.0, 0.0, 0.0, 0.0)
    decoded = bridge.decode_vehicle_attitude(raw_att)
    print(f"[OK] Attitude Cozucu Testi: Pitch={decoded['pitch_deg']:.2f}° (Hedef: 10.00°)")
    assert abs(decoded['pitch_deg'] - 10.0) < 0.01
    print("[BASARILI] Micro XRCE-DDS Koprusu ve uORB Paketleyicisi Hazir!")
    print("=" * 68)


if __name__ == '__main__':
    main()
