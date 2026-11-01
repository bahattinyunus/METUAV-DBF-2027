from telemetri.mavlink_bridge_node import TelemetryPacketBuilder

def test_telemetry_packet_packing():
    pkt = TelemetryPacketBuilder.build_custom_dbf_telemetry(
        timestamp_ms=1000,
        voltage_v=24.5,
        current_a=20.0,
        power_w=490.0,
        lap_count=2,
        mission_id=3,
        cg_shift_mm=-38.0,
        payload_dropped=True
    )
    # Header 2 + Time 4 + Volt 2 + Amp 2 + Watt 2 + Lap 1 + Mission 1 + CG 2 + Flags 1 + Checksum 2 = 19 bytes
    assert len(pkt) == 19
    assert pkt[0] == 0x55 and pkt[1] == 0xAA  # Little endian for 0xAA55
