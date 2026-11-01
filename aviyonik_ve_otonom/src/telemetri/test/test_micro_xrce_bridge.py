#!/usr/bin/env python3
"""
Unit tests for Micro-XRCE-DDS & PX4 uORB Telemetry Bridge.
"""

import math
import struct
import time
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'telemetri')))

from micro_xrce_bridge import MicroXRCEBridge, VehicleCommand


def test_bridge_initialization():
    bridge = MicroXRCEBridge(agent_ip="127.0.0.1", port=8888)
    assert bridge.agent_ip == "127.0.0.1"
    assert bridge.port == 8888
    assert bridge.connected is True
    assert bridge.sequence_num == 0


def test_attitude_decoding():
    bridge = MicroXRCEBridge()
    # Test pitch up 15 degrees
    pitch_rad = math.radians(15.0)
    q0 = math.cos(pitch_rad / 2.0)
    q2 = math.sin(pitch_rad / 2.0)
    raw_att = struct.pack('<Q 4f 4f', int(time.time() * 1e6), q0, 0.0, q2, 0.0, 0.0, 0.0, 0.0, 0.0)

    decoded = bridge.decode_vehicle_attitude(raw_att)
    assert abs(decoded['pitch_deg'] - 15.0) < 0.05
    assert abs(decoded['roll_deg']) < 0.05
    assert abs(decoded['yaw_deg']) < 0.05


def test_vehicle_command_encoding():
    bridge = MicroXRCEBridge()
    arm_cmd = bridge.encode_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
    assert len(arm_cmd) == 42  # 8 + 7*4 + 4 + 1 + 1 = 42 bytes
    assert bridge.sequence_num == 1


def test_payload_trigger_command():
    bridge = MicroXRCEBridge()
    drop_cmd = bridge.trigger_payload_release(actuator_index=5, normalized_val=1.0)
    assert len(drop_cmd) == 42
    # Unpack to verify
    timestamp, p1, p2, p3, p4, p5, p6, p7, cmd, sys_id, comp_id = struct.unpack('<Q 7f I B B', drop_cmd)
    assert cmd == VehicleCommand.VEHICLE_CMD_DO_SET_ACTUATOR
    assert p1 == 1.0
    assert p2 == 5.0
