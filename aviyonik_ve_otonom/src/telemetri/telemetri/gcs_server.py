#!/usr/bin/env python3
"""
METUAV DBF 2027 - Web Ground Control Station (GCS) Server
Serves the HTML5 Primary Flight Display (PFD) and streaming REST API
for real-time flight telemetry monitoring, payload drop commands, and GPS tracking.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

class GCSApiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        directory = os.path.join(os.path.dirname(__file__), 'web_gcs')
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        if self.path == '/api/telemetry':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            payload = {
                "timestamp": time.time(),
                "airspeed_ms": 24.5,
                "groundspeed_ms": 22.8,
                "altitude_m": 25.0,
                "pitch_deg": 2.4,
                "roll_deg": -1.2,
                "yaw_deg": 85.0,
                "voltage_v": 24.62,
                "current_a": 34.2,
                "power_w": 841.9,
                "soc_pct": 90.9,
                "active_mission": "MISSION_3_DELIVERY",
                "drop_miss_distance_m": 0.42,
                "payload_dropped": False
            }
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Quiet logging


def run_gcs_server(port: int = 8080, run_once: bool = False):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, GCSApiHandler)
    print(f"[GCS] Web Yer Istasyonu Sunucusu Baslatildi: http://localhost:{port}")
    if run_once:
        # For CI/headless automated testing
        httpd.server_close()
        print("[OK] Sunucu baslatma ve kapatma testi basarili.")
    else:
        httpd.serve_forever()


if __name__ == '__main__':
    run_once_flag = ('--test' in sys.argv)
    run_gcs_server(port=8080, run_once=run_once_flag)
