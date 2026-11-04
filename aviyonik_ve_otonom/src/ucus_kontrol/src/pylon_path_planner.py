#!/usr/bin/env python3
"""
AIAA DBF 2027 - Wind-Compensated Dubins Pylon Race-Track Path Planner
Generates time-optimal race circuit trajectories around DBF pylons with
dynamic bank angle limiting, G-load monitoring, and wind drift crab-angle compensation.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class Waypoint:
    x_m: float          # North (m)
    y_m: float          # East (m)
    z_m: float          # Altitude MSL (m)
    target_airspeed: float
    course_rad: float
    bank_angle_rad: float
    crab_angle_rad: float
    g_load: float


@dataclass
class CircuitPerformance:
    total_distance_m: float
    lap_time_s: float
    mean_ground_speed_ms: float
    max_bank_angle_deg: float
    max_g_load: float
    energy_consumed_wh_est: float


class PylonPathPlanner:
    def __init__(
        self,
        pylon_north_pos: Tuple[float, float] = (150.0, 0.0),
        pylon_south_pos: Tuple[float, float] = (-150.0, 0.0),
        circuit_altitude_m: float = 25.0,
        nominal_airspeed_ms: float = 24.5,
        max_bank_angle_deg: float = 55.0,
        max_g_load: float = 2.0,
        g_acc: float = 9.80665
    ):
        self.p_north = np.array(pylon_north_pos, dtype=float)
        self.p_south = np.array(pylon_south_pos, dtype=float)
        self.alt = circuit_altitude_m
        self.v_air = nominal_airspeed_ms
        self.phi_max = math.radians(max_bank_angle_deg)
        self.g_limit = max_g_load
        self.g = g_acc

    def calculate_turn_radius(self, bank_angle_rad: float) -> float:
        """
        Coordinated turn radius R = V^2 / (g * tan(phi))
        """
        tan_phi = max(math.tan(abs(bank_angle_rad)), 0.05)
        return (self.v_air ** 2) / (self.g * tan_phi)

    def calculate_wind_correction(
        self,
        desired_track_rad: float,
        wind_speed_ms: float,
        wind_dir_from_rad: float
    ) -> Tuple[float, float]:
        """
        Calculates Crab Angle (WCA) and Ground Speed using wind triangle.
        wind_dir_from_rad: direction FROM which wind is blowing (aviation standard).
        Returns: (crab_angle_rad, ground_speed_ms)
        """
        # Wind vector pointing in direction of movement
        wind_vector_to = wind_dir_from_rad + math.pi
        v_wx = wind_speed_ms * math.cos(wind_vector_to)
        v_wy = wind_speed_ms * math.sin(wind_vector_to)

        # Crosswind component perpendicular to desired track (positive when blowing from right)
        crosswind_from_right = -(v_wy * math.cos(desired_track_rad) - v_wx * math.sin(desired_track_rad))
        headwind = -(v_wx * math.cos(desired_track_rad) + v_wy * math.sin(desired_track_rad))

        ratio = crosswind_from_right / max(self.v_air, 1.0)
        ratio = np.clip(ratio, -0.95, 0.95)
        wca = math.asin(ratio)

        # Effective ground speed: Vg = Va * cos(WCA) - tailwind/headwind
        v_ground = self.v_air * math.cos(wca) - headwind
        v_ground = max(v_ground, 3.0)

        return wca, v_ground

    def generate_lap_waypoints(
        self,
        wind_speed_ms: float = 5.0,
        wind_dir_deg: float = 45.0,
        n_samples_turn: int = 16
    ) -> Tuple[List[Waypoint], CircuitPerformance]:
        """
        Generates full race-track lap:
        1. Straight east-leg (Northbound from South to North pylon)
        2. 180° turn around North Pylon
        3. Straight west-leg (Southbound from North to South pylon)
        4. 180° turn around South Pylon
        """
        wind_dir_rad = math.radians(wind_dir_deg)
        radius = self.calculate_turn_radius(self.phi_max)
        g_load = 1.0 / math.cos(self.phi_max)

        waypoints: List[Waypoint] = []
        total_dist = 0.0
        total_time = 0.0

        # Straight leg 1: South to North pylon offset by turn radius
        track_sn = 0.0  # Heading North
        wca_sn, vg_sn = self.calculate_wind_correction(track_sn, wind_speed_ms, wind_dir_rad)
        dist_sn = abs(self.p_north[0] - self.p_south[0])
        time_sn = dist_sn / vg_sn

        # Add start of straight
        waypoints.append(Waypoint(
            x_m=self.p_south[0], y_m=self.p_south[1] + radius, z_m=self.alt,
            target_airspeed=self.v_air, course_rad=track_sn, bank_angle_rad=0.0,
            crab_angle_rad=wca_sn, g_load=1.0
        ))
        waypoints.append(Waypoint(
            x_m=self.p_north[0], y_m=self.p_north[1] + radius, z_m=self.alt,
            target_airspeed=self.v_air, course_rad=track_sn, bank_angle_rad=0.0,
            crab_angle_rad=wca_sn, g_load=1.0
        ))
        total_dist += dist_sn
        total_time += time_sn

        # Turn 1: 180° turn around North Pylon (counter-clockwise)
        # Angles from 0 (East) through 90 (North) to 180 (West)
        thetas_north = np.linspace(0.0, math.pi, n_samples_turn)
        for th in thetas_north[1:]:
            x_wp = self.p_north[0] + radius * math.sin(th)
            y_wp = self.p_north[1] + radius * math.cos(th)
            track_tangent = th + math.pi / 2.0
            wca_turn, vg_turn = self.calculate_wind_correction(track_tangent, wind_speed_ms, wind_dir_rad)
            dt_segment = (radius * (thetas_north[1] - thetas_north[0])) / vg_turn
            total_dist += radius * (thetas_north[1] - thetas_north[0])
            total_time += dt_segment

            waypoints.append(Waypoint(
                x_m=x_wp, y_m=y_wp, z_m=self.alt, target_airspeed=self.v_air,
                course_rad=track_tangent, bank_angle_rad=self.phi_max,
                crab_angle_rad=wca_turn, g_load=g_load
            ))

        # Straight leg 2: North to South pylon
        track_ns = math.pi  # Heading South
        wca_ns, vg_ns = self.calculate_wind_correction(track_ns, wind_speed_ms, wind_dir_rad)
        dist_ns = dist_sn
        time_ns = dist_ns / vg_ns

        waypoints.append(Waypoint(
            x_m=self.p_south[0], y_m=self.p_south[1] - radius, z_m=self.alt,
            target_airspeed=self.v_air, course_rad=track_ns, bank_angle_rad=0.0,
            crab_angle_rad=wca_ns, g_load=1.0
        ))
        total_dist += dist_ns
        total_time += time_ns

        # Turn 2: 180° turn around South Pylon
        thetas_south = np.linspace(math.pi, 2.0 * math.pi, n_samples_turn)
        for th in thetas_south[1:]:
            x_wp = self.p_south[0] + radius * math.sin(th)
            y_wp = self.p_south[1] + radius * math.cos(th)
            track_tangent = th + math.pi / 2.0
            wca_turn, vg_turn = self.calculate_wind_correction(track_tangent, wind_speed_ms, wind_dir_rad)
            dt_segment = (radius * (thetas_south[1] - thetas_south[0])) / vg_turn
            total_dist += radius * (thetas_south[1] - thetas_south[0])
            total_time += dt_segment

            waypoints.append(Waypoint(
                x_m=x_wp, y_m=y_wp, z_m=self.alt, target_airspeed=self.v_air,
                course_rad=track_tangent, bank_angle_rad=self.phi_max,
                crab_angle_rad=wca_turn, g_load=g_load
            ))

        mean_vg = total_dist / total_time
        # Baseline ~800 W cruise consumption
        energy_wh = (800.0 * total_time) / 3600.0

        perf = CircuitPerformance(
            total_distance_m=total_dist,
            lap_time_s=total_time,
            mean_ground_speed_ms=mean_vg,
            max_bank_angle_deg=math.degrees(self.phi_max),
            max_g_load=g_load,
            energy_consumed_wh_est=energy_wh
        )

        return waypoints, perf
