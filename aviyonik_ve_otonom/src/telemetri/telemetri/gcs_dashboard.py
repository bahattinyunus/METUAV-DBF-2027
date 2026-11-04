#!/usr/bin/env python3
"""
AIAA DBF 2027 - Ground Control Station (GCS) Telemetry Dashboard
Provides real-time telemetry streaming, Primary Flight Display (PFD) metrics,
battery power monitoring, and Mission 3 payload drop tracking.
Runs in Terminal UI mode or as an embedded HTTP/WebSocket JSON streaming server.
"""

import sys
import time
import math
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class TelemetryState:
    def __init__(self):
        self.lock = threading.Lock()
        self.timestamp = time.time()
        self.flight_time_sec = 0.0
        self.altitude_m = 25.0
        self.airspeed_ms = 24.5
        self.groundspeed_ms = 22.8
        self.pitch_deg = 2.4
        self.roll_deg = -1.2
        self.yaw_deg = 85.0
        self.voltage_v = 24.6
        self.current_a = 34.2
        self.power_w = self.voltage_v * self.current_a
        self.consumed_mah = 1450.0
        self.soc_pct = 90.9
        self.lap_count = 2
        self.active_mission = "MISSION_3_DELIVERY"
        self.payload_dropped = False
        self.drop_miss_distance_m = 0.42
        self.link_healthy = True

    def to_dict(self):
        with self.lock:
            return {
                "timestamp": self.timestamp,
                "flight_time_sec": round(self.flight_time_sec, 1),
                "altitude_m": round(self.altitude_m, 2),
                "airspeed_ms": round(self.airspeed_ms, 2),
                "groundspeed_ms": round(self.groundspeed_ms, 2),
                "pitch_deg": round(self.pitch_deg, 2),
                "roll_deg": round(self.roll_deg, 2),
                "yaw_deg": round(self.yaw_deg, 1),
                "voltage_v": round(self.voltage_v, 2),
                "current_a": round(self.current_a, 1),
                "power_w": round(self.power_w, 1),
                "consumed_mah": round(self.consumed_mah, 1),
                "soc_pct": round(self.soc_pct, 1),
                "lap_count": self.lap_count,
                "active_mission": self.active_mission,
                "payload_dropped": self.payload_dropped,
                "drop_miss_distance_m": round(self.drop_miss_distance_m, 2),
                "link_healthy": self.link_healthy
            }

telemetry_data = TelemetryState()

class GCSRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/telemetry':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = telemetry_data.to_dict()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AIAA DBF 2027 - Yer Istasyonu (GCS)</title>
    <meta http-equiv="refresh" content="1">
    <style>
        body {{ font-family: monospace; background: #121826; color: #00ffcc; padding: 20px; }}
        .card {{ background: #1f293d; border: 1px solid #38bdf8; padding: 15px; border-radius: 8px; margin-bottom: 15px; }}
        h1 {{ color: #facc15; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
    </style>
</head>
<body>
    <h1>🦅 AIAA DBF 2027 GCS Canli Telemetri</h1>
    <div class="grid">
        <div class="card">
            <h3>✈️ Ucus Durumu</h3>
            <p>Gorev: <b>{telemetry_data.active_mission}</b> | Tur: <b>{telemetry_data.lap_count} / 3</b></p>
            <p>Irtifa: <b>{telemetry_data.altitude_m:.1f} m</b> | Hava Hizi: <b>{telemetry_data.airspeed_ms:.1f} m/s</b></p>
            <p>Yunuslama: <b>{telemetry_data.pitch_deg:.1f}°</b> | Yuvarlanma: <b>{telemetry_data.roll_deg:.1f}°</b></p>
        </div>
        <div class="card">
            <h3>⚡ Guc ve Batarya</h3>
            <p>Gerilim: <b>{telemetry_data.voltage_v:.2f} V (6S)</b> | Akim: <b>{telemetry_data.current_a:.1f} A</b></p>
            <p>Guc: <b>{telemetry_data.power_w:.1f} W</b> | Harcanan: <b>{telemetry_data.consumed_mah:.0f} mAh (%{telemetry_data.soc_pct:.1f} SoC)</b></p>
            <p>Faydali Yuk Birakildi mi: <b>{'EVET' if telemetry_data.payload_dropped else 'HAYIR (Hazir)'}</b></p>
        </div>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress console logging for clean output


def print_terminal_dashboard():
    """Renders ANSI Terminal dashboard."""
    d = telemetry_data.to_dict()
    print("\n" + "=" * 65)
    print("  [AIAA DBF 2027] - YER ISTASYONU (GCS) CANLI TELEMETRI")
    print("=" * 65)
    print(f"  GOREV MODU     : {d['active_mission']:22s} | TUR: {d['lap_count']}/3")
    print(f"  IRTISA (AGL)   : {d['altitude_m']:6.1f} m              | HAVA HIZI  : {d['airspeed_ms']:5.1f} m/s")
    print(f"  ATTITUDE       : Pitch: {d['pitch_deg']:+5.1f}° | Roll: {d['roll_deg']:+5.1f}° | Yaw: {d['yaw_deg']:5.1f}°")
    print("-" * 65)
    print(f"  BATARYA (6S)   : {d['voltage_v']:5.2f} V               | AKIM       : {d['current_a']:5.1f} A")
    print(f"  CEKILEN GUC    : {d['power_w']:6.1f} W              | DOLULUK    : %{d['soc_pct']:5.1f}")
    print(f"  HARCANAN ENERJI: {d['consumed_mah']:6.1f} mAh")
    print("-" * 65)
    drop_str = "TETIKLENDI (BIRAKILDI)" if d['payload_dropped'] else "KILITLI (HEKDEFE YAKLASILIYOR)"
    print(f"  GOREV 3 BIRAKMA: {drop_str}")
    print(f"  HEDEF HATA PAYI: {d['drop_miss_distance_m']:5.2f} m (Tolerans: < 1.20 m)")
    print("=" * 65)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        port = 8080
        server = HTTPServer(('0.0.0.0', port), GCSRequestHandler)
        print(f"[GCS] Telemetri Web Sunucusu baslatildi: http://localhost:{port}")
        server.serve_forever()
    else:
        print_terminal_dashboard()


if __name__ == '__main__':
    main()
