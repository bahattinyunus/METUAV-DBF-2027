import json
import time
import urllib.request
import pytest
from aviyonik_ve_otonom.src.telemetri.gcs_server import GCSServer, GCSTelemetryPacket

def test_telemetry_packet_serialization():
    pkt = GCSTelemetryPacket(
        time_s=12.5,
        pitch_deg=4.2,
        roll_deg=-15.3,
        yaw_deg=180.0,
        airspeed_ms=25.0,
        altitude_m=28.5,
        voltage_v=24.1,
        current_a=35.0
    )
    d = pkt.to_dict()
    assert d["time_s"] == 12.5
    assert d["pitch_deg"] == 4.2
    assert d["airspeed_kmh"] == 90.0
    assert d["power_w"] == round(24.1 * 35.0, 1)

def test_gcs_http_server_endpoint():
    server = GCSServer(port=8999)
    try:
        server.start()
        time.sleep(0.1)

        pkt = GCSTelemetryPacket(
            time_s=45.0,
            airspeed_ms=23.8,
            voltage_v=23.5,
            mission_phase="PULL_UP_TURN"
        )
        server.update_telemetry(pkt)

        with urllib.request.urlopen('http://127.0.0.1:8999/api/telemetry') as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode('utf-8'))
            assert data["time_s"] == 45.0
            assert data["airspeed_ms"] == 23.8
            assert data["mission_phase"] == "PULL_UP_TURN"
    finally:
        server.stop()
