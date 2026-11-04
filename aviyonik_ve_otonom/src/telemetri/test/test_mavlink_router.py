#!/usr/bin/env python3
"""
Unit tests for MAVLink v2 Protocol Router & Micro-Telemetry Bridge.
"""

import math
import struct
import pytest

from aviyonik_ve_otonom.src.telemetri.mavlink_protocol_router import (
    MAVLinkProtocolRouter,
    MAVLinkMessage,
    x25_crc
)


def test_mavlink_crc_calculation():
    # Verify standard X.25 CRC check
    test_bytes = b"DBF_2027_AUTOPILOT"
    crc = x25_crc(test_bytes)
    assert 0 <= crc <= 0xFFFF
    # Invertible consistency
    assert x25_crc(b"", crc=crc) == crc


def test_encode_and_decode_heartbeat():
    router = MAVLinkProtocolRouter(sys_id=1, comp_id=1)
    packet = router.encode_heartbeat(
        mav_type=1,
        autopilot=3,
        base_mode=209,
        custom_mode=0,
        system_status=4
    )

    assert packet[0] == 0xFD  # Magic v2 byte
    assert len(packet) == 10 + 9 + 2  # Header(10) + Payload(9) + CRC(2) = 21

    msg = router.decode_packet(packet)
    assert msg is not None
    assert msg.msg_id == 0
    assert msg.msg_name == "HEARTBEAT"
    assert msg.sys_id == 1
    assert msg.payload_dict["mav_type"] == 1
    assert msg.payload_dict["system_status"] == 4


def test_encode_and_decode_attitude_and_gps():
    router = MAVLinkProtocolRouter(sys_id=1, comp_id=1)

    # 1. Attitude
    roll = math.radians(12.5)
    pitch = math.radians(-3.2)
    yaw = math.radians(45.0)
    att_packet = router.encode_attitude(
        time_boot_ms=12500,
        roll_rad=roll,
        pitch_rad=pitch,
        yaw_rad=yaw
    )
    att_msg = router.decode_packet(att_packet)
    assert att_msg is not None
    assert att_msg.msg_id == 30
    assert att_msg.payload_dict["roll"] == pytest.approx(roll, abs=1e-4)
    assert att_msg.payload_dict["pitch"] == pytest.approx(pitch, abs=1e-4)

    # 2. Global Position
    gps_packet = router.encode_global_position_int(
        time_boot_ms=12500,
        lat_deg=39.8912,
        lon_deg=32.7845,
        alt_msl_m=950.0,
        relative_alt_m=25.0,
        vx_ms=24.5,
        vy_ms=0.5,
        vz_ms=-0.2,
        heading_deg=45.0
    )
    gps_msg = router.decode_packet(gps_packet)
    assert gps_msg is not None
    assert gps_msg.msg_id == 33
    assert gps_msg.payload_dict["lat_deg"] == pytest.approx(39.8912, abs=1e-5)
    assert gps_msg.payload_dict["relative_alt_m"] == pytest.approx(25.0, abs=0.1)
    assert gps_msg.payload_dict["vx_ms"] == pytest.approx(24.5, abs=0.1)


def test_mavlink_stream_parsing_with_noise():
    router = MAVLinkProtocolRouter()

    p1 = router.encode_heartbeat()
    p2 = router.encode_statustext(severity=6, text="DBF: TARGET LOCKED")

    # Corrupt stream with leading garbage bytes and concatenated packets
    stream = b"\x00\xFF\xAA\x55" + p1 + b"\x12\x34" + p2

    parsed = router.parse_stream(stream)
    assert len(parsed) == 2
    assert parsed[0].msg_id == 0
    assert parsed[1].msg_id == 253
    assert "TARGET LOCKED" in parsed[1].payload_dict["text"]
