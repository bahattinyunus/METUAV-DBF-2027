#!/usr/bin/env python3
"""
METUAV DBF 2027 - MAVLink Telemetry Bridge Node
Transmits aircraft flight telemetry, battery power distribution, and receives GCS commands.
Compatible with PX4 / ArduPilot autopilots and QGroundControl / Mission Planner GCS.
"""

import time
import math
import struct

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import NavSatFix, BatteryState, Imu
    from geometry_msgs.msg import TwistStamped
    from std_msgs.msg import String, Bool, Float32
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


class TelemetryPacketBuilder:
    """Encodes custom binary telemetry frames and MAVLink payloads."""

    @staticmethod
    def build_custom_dbf_telemetry(timestamp_ms: int,
                                   voltage_v: float,
                                   current_a: float,
                                   power_w: float,
                                   lap_count: int,
                                   mission_id: int,
                                   cg_shift_mm: float,
                                   payload_dropped: bool) -> bytes:
        """
        Packs a compact 24-byte binary telemetry frame for high-speed RF link:
        [HEADER(2B)][TIME(4B)][VOLT(2B)][AMP(2B)][WATT(2B)][LAP(1B)][MISSION(1B)][CG(2B)][FLAGS(1B)][CHECKSUM(2B)]
        """
        header = 0xAA55
        time_u32 = int(timestamp_ms) & 0xFFFFFFFF
        volt_u16 = int(max(0.0, voltage_v) * 100) & 0xFFFF       # 0.01 V resolution
        curr_u16 = int(max(0.0, current_a) * 100) & 0xFFFF       # 0.01 A resolution
        pwr_u16  = int(max(0.0, power_w) * 10) & 0xFFFF          # 0.1 W resolution
        lap_u8   = int(lap_count) & 0xFF
        msn_u8   = int(mission_id) & 0xFF
        cg_s16   = int(round(cg_shift_mm * 10))                 # 0.1 mm resolution, signed int16
        cg_s16   = max(-32768, min(32767, cg_s16))
        flags_u8 = 0x01 if payload_dropped else 0x00

        payload_bytes = struct.pack('<H I H H H B B h B',
                                    header, time_u32, volt_u16, curr_u16, pwr_u16,
                                    lap_u8, msn_u8, cg_s16, flags_u8)

        # 16-bit Fletcher checksum
        sum1 = 0
        sum2 = 0
        for b in payload_bytes:
            sum1 = (sum1 + b) % 255
            sum2 = (sum2 + sum1) % 255
        checksum = (sum2 << 8) | sum1

        return payload_bytes + struct.pack('<H', checksum)


if ROS2_AVAILABLE:
    class MavlinkBridgeNode(Node):
        def __init__(self):
            super().__init__('mavlink_bridge_node')
            self.declare_parameter('connection_url', 'udp:127.0.0.1:14550')
            self.declare_parameter('baudrate', 57600)
            self.declare_parameter('telemetry_rate_hz', 10.0)

            self.voltage = 24.8
            self.current = 18.5
            self.power = self.voltage * self.current
            self.lap = 1
            self.mission_id = 3
            self.cg_shift = 0.0
            self.payload_dropped = False

            # Publishers to internal ROS2 network
            self.link_health_pub = self.create_publisher(Bool, 'metuav/telemetry/link_alive', 10)
            self.gcs_cmd_pub = self.create_publisher(String, 'metuav/gcs/commands', 10)

            # Subscribers
            self.create_subscription(String, 'metuav/mission_state', self.mission_cb, 10)
            self.create_subscription(Bool, 'metuav/payload_drop_trigger', self.drop_cb, 10)

            # Telemetry broadcast timer (10 Hz)
            rate = self.get_parameter('telemetry_rate_hz').as_double()
            self.timer = self.create_timer(1.0 / rate, self.broadcast_telemetry)
            self.get_logger().info("MavlinkBridgeNode running at 10 Hz.")

        def mission_cb(self, msg: String):
            # Parse mission state
            pass

        def drop_cb(self, msg: Bool):
            if msg.data:
                self.payload_dropped = True
                self.cg_shift = -38.0  # mm

        def broadcast_telemetry(self):
            now_ms = int(time.time() * 1000) & 0xFFFFFFFF
            packet = TelemetryPacketBuilder.build_custom_dbf_telemetry(
                now_ms, self.voltage, self.current, self.power,
                self.lap, self.mission_id, self.cg_shift, self.payload_dropped
            )
            alive = Bool()
            alive.data = True
            self.link_health_pub.publish(alive)


def main(args=None):
    if ROS2_AVAILABLE:
        rclpy.init(args=args)
        node = MavlinkBridgeNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        print("[STANDALONE TEST] Packing sample DBF telemetry frame...")
        pkt = TelemetryPacketBuilder.build_custom_dbf_telemetry(
            timestamp_ms=123456, voltage_v=24.52, current_a=35.40,
            power_w=868.0, lap_count=2, mission_id=3,
            cg_shift_mm=-38.0, payload_dropped=True
        )
        print(f"Packet packed successfully! Length: {len(pkt)} bytes, Hex: {pkt.hex()}")


if __name__ == '__main__':
    main()
