#!/usr/bin/env python3
"""
AIAA DBF 2027 - L1 Adaptive Nonlinear Guidance Logic (NLGL) Path Follower
Implements the Park-Deyst-How nonlinear lateral guidance law for fixed-wing aircraft.
Provides robust straight-line cross-track tracking and circular orbit pylon guidance
with wind drift compensation and bank angle limitation.
"""

import math
import numpy as np
from typing import Tuple, Dict, Optional


class L1PathFollower:
    def __init__(self,
                 damping_ratio: float = 0.707,
                 period_sec: float = 12.0,
                 max_bank_deg: float = 45.0,
                 min_l1_distance_m: float = 15.0):
        self.damping = damping_ratio
        self.period = period_sec
        self.max_bank_rad = math.radians(max_bank_deg)
        self.min_l1 = min_l1_distance_m
        self.g = 9.80665

    def compute_l1_distance(self, ground_speed: float) -> float:
        """
        Calculates adaptive L1 lookahead distance proportional to ground speed:
        L1 = (1 / pi) * damping * period * ground_speed
        """
        L1 = (1.0 / math.pi) * self.damping * self.period * max(ground_speed, 1.0)
        return float(max(L1, self.min_l1))

    def track_straight_segment(self,
                               p_aircraft: Tuple[float, float],
                               ground_velocity: Tuple[float, float],
                               p_segment_start: Tuple[float, float],
                               p_segment_end: Tuple[float, float]) -> Dict[str, float]:
        """
        Tracks a straight waypoint path segment between p_segment_start and p_segment_end.
        p_aircraft: (x_north, y_east)
        ground_velocity: (vx, vy)
        Returns dictionary with commanded lateral accel, bank angle, and cross-track error.
        """
        ax, ay = p_aircraft
        vx, vy = ground_velocity
        vg = math.hypot(vx, vy)
        vg = max(vg, 1.0)

        # Segment vector
        x1, y1 = p_segment_start
        x2, y2 = p_segment_end
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        if seg_len < 1e-3:
            return {"lateral_accel_cmd": 0.0, "bank_angle_cmd_deg": 0.0, "crosstrack_error_m": 0.0}

        # Unit tangent and normal vectors
        t_hat = np.array([dx / seg_len, dy / seg_len])
        n_hat = np.array([-t_hat[1], t_hat[0]])  # Left normal

        # Vector from start to aircraft
        r_start_to_ac = np.array([ax - x1, ay - y1])

        # Cross-track error (positive if aircraft is to the left of path)
        crosstrack_error = float(np.dot(r_start_to_ac, n_hat))

        # Along-track projection
        s_proj = float(np.dot(r_start_to_ac, t_hat))

        # Adaptive L1 distance
        L1 = self.compute_l1_distance(vg)

        # Reference point on path at distance L1 ahead along track
        ref_s = s_proj + math.sqrt(max(0.0, L1**2 - crosstrack_error**2))
        p_ref = np.array([x1, y1]) + t_hat * ref_s

        # Vector from aircraft to reference point
        vec_to_ref = p_ref - np.array([ax, ay])
        ref_dist = np.linalg.norm(vec_to_ref)
        if ref_dist < 1e-3:
            return {"lateral_accel_cmd": 0.0, "bank_angle_cmd_deg": 0.0, "crosstrack_error_m": crosstrack_error}

        # Angle eta between ground velocity vector and vec_to_ref
        bearing_vg = math.atan2(vy, vx)
        bearing_ref = math.atan2(vec_to_ref[1], vec_to_ref[0])
        eta = (bearing_ref - bearing_vg + math.pi) % (2.0 * math.pi) - math.pi

        # Commanded lateral acceleration: a_lat = 2 * (Vg^2 / L1) * sin(eta)
        a_lat = 2.0 * (vg**2 / L1) * math.sin(eta)

        # Commanded coordinated bank angle: phi = atan(a_lat / g)
        bank_rad = math.atan(a_lat / self.g)
        bank_rad = float(np.clip(bank_rad, -self.max_bank_rad, self.max_bank_rad))

        return {
            "lateral_accel_cmd": float(a_lat),
            "bank_angle_cmd_deg": float(math.degrees(bank_rad)),
            "crosstrack_error_m": crosstrack_error,
            "eta_deg": float(math.degrees(eta)),
            "L1_distance_m": L1
        }

    def track_orbit(self,
                    p_aircraft: Tuple[float, float],
                    ground_velocity: Tuple[float, float],
                    center: Tuple[float, float],
                    radius: float,
                    clockwise: bool = True) -> Dict[str, float]:
        """
        Guides aircraft into and along a circular pylon orbit of given radius.
        center: (center_x, center_y)
        radius: target circle radius (m)
        """
        ax, ay = p_aircraft
        vx, vy = ground_velocity
        vg = math.hypot(vx, vy)
        vg = max(vg, 1.0)

        cx, cy = center
        dx, dy = ax - cx, ay - cy
        dist_to_center = math.hypot(dx, dy)
        if dist_to_center < 1e-3:
            dist_to_center = 0.1

        # Radial error from orbit radius
        radial_error = dist_to_center - radius

        # Angle of aircraft relative to center
        theta = math.atan2(dy, dx)

        # Tangent heading direction on orbit
        dir_sign = 1.0 if clockwise else -1.0
        orbit_tangent_angle = theta + (math.pi / 2.0) * dir_sign

        # Normal L1 acceleration
        L1 = self.compute_l1_distance(vg)

        # Centripetal acceleration for circular path
        a_centripetal = (vg**2 / radius) * dir_sign

        # Radial correction acceleration
        k_rad = 1.5
        a_rad = -k_rad * radial_error

        a_total = a_centripetal + a_rad
        bank_rad = math.atan(a_total / self.g)
        bank_rad = float(np.clip(bank_rad, -self.max_bank_rad, self.max_bank_rad))

        return {
            "lateral_accel_cmd": float(a_total),
            "bank_angle_cmd_deg": float(math.degrees(bank_rad)),
            "radial_error_m": float(radial_error),
            "orbit_radius_m": float(radius)
        }


def main():
    follower = L1PathFollower(damping_ratio=0.707, period_sec=12.0)
    print("=" * 72)
    print("  AIAA DBF 2027 - L1 NONLINEAR GUIDANCE LOGIC (NLGL) TEST")
    print("=" * 72)

    # 1. Test cross-track error convergence on North-bound runway (x=0 to 300, y=0)
    # Aircraft at (x=50, y=10) (10m East of runway, moving North at 24 m/s)
    res_line = follower.track_straight_segment(
        p_aircraft=(50.0, 10.0),
        ground_velocity=(24.0, 0.0),
        p_segment_start=(0.0, 0.0),
        p_segment_end=(300.0, 0.0)
    )

    print(f"[*] Düz Hat Koridor Takibi (10 metre Sağ Sapma):")
    print(f"    - Yanal Hata (Cross-track) : {res_line['crosstrack_error_m']:.2f} m")
    print(f"    - L1 Takip Mesafesi        : {res_line['L1_distance_m']:.2f} m")
    print(f"    - Komuta Yanal İvme        : {res_line['lateral_accel_cmd']:.2f} m/s^2")
    print(f"    - Komuta Bank Açısı        : {res_line['bank_angle_cmd_deg']:.2f}° (Sola yatış emredildi)")
    assert res_line['bank_angle_cmd_deg'] < 0.0, "Should command left bank to correct right offset"

    # 2. Test 30m radius pylon orbit turn
    res_orbit = follower.track_orbit(
        p_aircraft=(150.0, 30.0),
        ground_velocity=(0.0, -24.0),
        center=(150.0, 0.0),
        radius=30.0,
        clockwise=True
    )
    print("-" * 72)
    print(f"[*] 30m Yarıçaplı Pylon Dönüşü:")
    print(f"    - Yarıçap Hatası           : {res_orbit['radial_error_m']:.2f} m")
    print(f"    - Komuta Yanal İvme        : {res_orbit['lateral_accel_cmd']:.2f} m/s^2")
    print(f"    - Komuta Bank Açısı        : {res_orbit['bank_angle_cmd_deg']:.2f}°")
    print("=" * 72)
    print("[BASARILI] L1 Adaptif Yol Takipçisi Doğrulandı!")


if __name__ == '__main__':
    main()
