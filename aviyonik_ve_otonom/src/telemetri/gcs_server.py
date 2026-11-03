#!/usr/bin/env python3
"""
METUAV DBF 2027 - Ground Control Station (GCS) Telemetry Hub & Web Server
Serves high-rate telemetry packets, PFD cockpit status, and FDIR health
over HTTP/JSON for the mission flight-line operators.
"""

import json
import math
import os
import sys
import time
import http.server
import socketserver
import threading
from typing import Dict, Any, Optional


class GCSTelemetryPacket:
    def __init__(
        self,
        time_s: float = 0.0,
        pitch_deg: float = 0.0,
        roll_deg: float = 0.0,
        yaw_deg: float = 0.0,
        airspeed_ms: float = 24.5,
        altitude_m: float = 25.0,
        climb_rate_ms: float = 0.0,
        voltage_v: float = 24.2,
        current_a: float = 34.0,
        motor_temp_c: float = 48.5,
        battery_temp_c: float = 38.2,
        soc_pct: float = 88.5,
        pos_north_m: float = 45.0,
        pos_east_m: float = 12.0,
        mission_phase: str = "CRUISE_LAP_2",
        fdir_status: str = "ALL_SYSTEMS_NOMINAL",
        drop_armed: bool = True,
        target_dist_m: float = 65.0
    ):
        self.time_s = time_s
        self.pitch_deg = pitch_deg
        self.roll_deg = roll_deg
        self.yaw_deg = yaw_deg
        self.airspeed_ms = airspeed_ms
        self.altitude_m = altitude_m
        self.climb_rate_ms = climb_rate_ms
        self.voltage_v = voltage_v
        self.current_a = current_a
        self.motor_temp_c = motor_temp_c
        self.battery_temp_c = battery_temp_c
        self.soc_pct = soc_pct
        self.pos_north_m = pos_north_m
        self.pos_east_m = pos_east_m
        self.mission_phase = mission_phase
        self.fdir_status = fdir_status
        self.drop_armed = drop_armed
        self.target_dist_m = target_dist_m

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_s": round(self.time_s, 2),
            "pitch_deg": round(self.pitch_deg, 2),
            "roll_deg": round(self.roll_deg, 2),
            "yaw_deg": round(self.yaw_deg, 2),
            "airspeed_ms": round(self.airspeed_ms, 2),
            "airspeed_kmh": round(self.airspeed_ms * 3.6, 1),
            "altitude_m": round(self.altitude_m, 2),
            "climb_rate_ms": round(self.climb_rate_ms, 2),
            "voltage_v": round(self.voltage_v, 2),
            "current_a": round(self.current_a, 2),
            "power_w": round(self.voltage_v * self.current_a, 1),
            "motor_temp_c": round(self.motor_temp_c, 1),
            "battery_temp_c": round(self.battery_temp_c, 1),
            "soc_pct": round(self.soc_pct, 1),
            "pos_north_m": round(self.pos_north_m, 1),
            "pos_east_m": round(self.pos_east_m, 1),
            "mission_phase": self.mission_phase,
            "fdir_status": self.fdir_status,
            "drop_armed": self.drop_armed,
            "target_dist_m": round(self.target_dist_m, 1)
        }


class GCSServerHandler(http.server.SimpleHTTPRequestHandler):
    current_telemetry: GCSTelemetryPacket = GCSTelemetryPacket()

    def do_GET(self):
        if self.path == '/api/telemetry':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = json.dumps(GCSServerHandler.current_telemetry.to_dict()).encode('utf-8')
            self.wfile.write(data)
        elif self.path in ['/', '/index.html']:
            html_path = os.path.join(os.path.dirname(__file__), 'gcs_dashboard.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            super().do_GET()

    def log_message(self, format, *args):
        # Quiet logger for tests and production
        pass


class GCSServer:
    def __init__(self, port: int = 8088):
        self.port = port
        self.server: Optional[socketserver.ThreadingTCPServer] = None
        self.thread: Optional[threading.Thread] = None

    def update_telemetry(self, packet: GCSTelemetryPacket):
        GCSServerHandler.current_telemetry = packet

    def start(self):
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        self.server = socketserver.ThreadingTCPServer(("", self.port), GCSServerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


if __name__ == '__main__':
    port = 8088
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    print(f"============================================================")
    print(f"  METUAV DBF 2027 - GCS Cockpit & Telemetry Hub Web Sunucusu")
    print(f"  Yer İstasyonu: http://localhost:{port}")
    print(f"============================================================")
    gcs = GCSServer(port=port)
    gcs.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")
        gcs.stop()
