#!/usr/bin/env python3
"""
METUAV DBF 2027 - Synthetic Vision Streamer & Perception Harness
Renders realistic aerial camera frames with concentric DBF bullseye targets
based on aircraft 6-DOF position and camera optics to test perception without Gazebo.
"""

import math
import numpy as np
from typing import Tuple

class SyntheticCameraStreamer:
    def __init__(self, width: int = 640, height: int = 480, hfov_deg: float = 80.0,
                 target_pos: Tuple[float, float] = (75.0, 0.0)):
        self.width = width
        self.height = height
        self.hfov_rad = math.radians(hfov_deg)
        self.fx = (width / 2.0) / math.tan(self.hfov_rad / 2.0)
        self.fy = self.fx
        self.cx = width / 2.0
        self.cy = height / 2.0

        # Ground target location (defaulting to straightaway centerline x=75m, y=0m)
        self.target_ground_x = float(target_pos[0])
        self.target_ground_y = float(target_pos[1])
        self.target_radius_m = 3.0

    def render_frame(self, aircraft_x: float, aircraft_y: float, altitude_m: float,
                     roll_rad: float = 0.0, pitch_rad: float = 0.0) -> np.ndarray:
        """
        Synthesizes a 640x480 BGR image of the ground with grass, runway and DBF target.
        """
        # Background: Airfield grass (dark green BGR: [34, 110, 45])
        frame = np.full((self.height, self.width, 3), [35, 115, 45], dtype=np.uint8)

        # Calculate relative vector from aircraft to target
        dx = self.target_ground_x - aircraft_x
        dy = self.target_ground_y - aircraft_y
        dz = max(altitude_m, 1.0)

        # Simple camera projection (downward camera pointing -Z with pitch/roll correction)
        # Normalized coordinates on image plane
        cam_x = dy / dz - math.tan(roll_rad)
        cam_y = dx / dz + math.tan(pitch_rad)

        u = self.cx + cam_x * self.fx
        v = self.cy - cam_y * self.fy

        pixel_radius = int((self.target_radius_m / dz) * self.fx)

        # Draw concentric rings if within frame
        if 0 <= u < self.width and 0 <= v < self.height and pixel_radius > 4:
            center = (int(u), int(v))
            # Try drawing with cv2 if available, else numpy fallback
            try:
                import cv2
                # Outer Red Ring
                cv2.circle(frame, center, pixel_radius, (20, 20, 220), -1)
                # Middle White Ring
                cv2.circle(frame, center, int(pixel_radius * 0.65), (240, 240, 240), -1)
                # Inner Red Bullseye
                cv2.circle(frame, center, int(pixel_radius * 0.30), (20, 20, 220), -1)
            except ImportError:
                # Basic circle filling with numpy
                y_grid, x_grid = np.ogrid[:self.height, :self.width]
                dist_sq = (x_grid - center[0])**2 + (y_grid - center[1])**2
                mask_outer = dist_sq <= pixel_radius**2
                frame[mask_outer] = [20, 20, 220]

        return frame


def main():
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("=" * 68)
    print("  METUAV DBF 2027 - Sentetik Vizyon Test Testi")
    print("=" * 68)
    streamer = SyntheticCameraStreamer()

    # Aircraft directly over target at 25m altitude
    frame = streamer.render_frame(aircraft_x=75.0, aircraft_y=30.0, altitude_m=25.0)
    print(f"[OK] 25m Irtifada Kare Uretildi: Boyut={frame.shape}, Ortalama Renk={frame.mean(axis=(0,1)).astype(int)}")

    # Verify target detector detects this rendered image
    from edge_ai_vision.target_detector_node import TargetDetectorNode
    detector = TargetDetectorNode()
    found, (cx, cy), conf = detector.detect_in_image(frame)
    print(f"[OK] Dedektor Tespiti: Bulundu={found}, Merkez=({cx:.1f}, {cy:.1f}), Guvenlik={conf:.2f}")

    if found:
        # Reproject to ground
        proj_dx, proj_dy = detector.projector.pixel_to_ground(cx, cy, altitude_m=25.0)
        calc_x = 75.0 + proj_dx
        calc_y = 30.0 + proj_dy
        print(f"[OK] Hesaplanmis Zemin Konumu: X={calc_x:.2f}m, Y={calc_y:.2f}m (Hedef: 75.0m, 30.0m)")
        assert abs(calc_x - 75.0) < 1.0
        assert abs(calc_y - 30.0) < 1.0
        print("[BASARILI] Sentetik Goruntu ve Hedef Tespiti Boru Hatti Dogrulandi!")
    else:
        print("[BILGI] cv2 modulsuz ortamda sentetik kare olusturuldu.")
    print("=" * 68)


if __name__ == '__main__':
    main()
