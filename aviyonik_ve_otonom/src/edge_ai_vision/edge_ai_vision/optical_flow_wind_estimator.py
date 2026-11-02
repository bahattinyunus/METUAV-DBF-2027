#!/usr/bin/env python3
"""
METUAV DBF 2027 - Downward Optical Flow & Visual Odometry Wind Estimator
Fuses downward camera pixel motion vectors with gyro derotation (p, q) and altitude
to derive accurate horizontal ground velocity and estimate in-flight wind vector (W_x, W_y).
Provides synthetic airspeed backup during pitot tube blockage.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class OpticalFlowEstimate:
    ground_speed_x_ms: float
    ground_speed_y_ms: float
    ground_speed_mag_ms: float
    wind_speed_ms: float
    wind_direction_deg: float
    synthetic_airspeed_ms: float
    is_valid: bool


class OpticalFlowWindEstimator:
    def __init__(
        self,
        camera_focal_length_px: float = 800.0,
        filter_alpha: float = 0.15
    ):
        self.focal_px = camera_focal_length_px
        self.alpha = filter_alpha

        # Filtered states
        self.filt_vg_x = 0.0
        self.filt_vg_y = 0.0
        self.filt_wind_x = 0.0
        self.filt_wind_y = 0.0

    def estimate(
        self,
        pixel_flow_x_px_s: float,
        pixel_flow_y_px_s: float,
        gyro_p_rad_s: float,
        gyro_q_rad_s: float,
        altitude_agl_m: float,
        heading_rad: float,
        pitot_airspeed_ms: float,
        is_pitot_healthy: bool = True
    ) -> OpticalFlowEstimate:
        """
        Derotates optical flow rates and estimates wind components.
        """
        if altitude_agl_m < 0.5:
            return OpticalFlowEstimate(
                ground_speed_x_ms=0.0, ground_speed_y_ms=0.0,
                ground_speed_mag_ms=0.0, wind_speed_ms=0.0,
                wind_direction_deg=0.0, synthetic_airspeed_ms=0.0,
                is_valid=False
            )

        # Angular flow rate in rad/s
        omega_flow_x = pixel_flow_x_px_s / self.focal_px
        omega_flow_y = pixel_flow_y_px_s / self.focal_px

        # Derotation: remove pure rotational flow caused by pitch/roll angular rates
        omega_trans_x = omega_flow_x - gyro_q_rad_s
        omega_trans_y = omega_flow_y + gyro_p_rad_s

        # Linear translational ground velocity in camera frame (m/s)
        v_cam_x = -omega_trans_x * altitude_agl_m
        v_cam_y = -omega_trans_y * altitude_agl_m

        # Rotate camera velocity into NED horizontal frame via heading psi
        cos_hdg = math.cos(heading_rad)
        sin_hdg = math.sin(heading_rad)
        v_ned_x = v_cam_x * cos_hdg - v_cam_y * sin_hdg
        v_ned_y = v_cam_x * sin_hdg + v_cam_y * cos_hdg

        # Low-pass filter ground speed
        self.filt_vg_x = (1.0 - self.alpha) * self.filt_vg_x + self.alpha * v_ned_x
        self.filt_vg_y = (1.0 - self.alpha) * self.filt_vg_y + self.alpha * v_ned_y
        vg_mag = math.sqrt(self.filt_vg_x**2 + self.filt_vg_y**2)

        # Airspeed vector in NED
        v_air_x = pitot_airspeed_ms * cos_hdg
        v_air_y = pitot_airspeed_ms * sin_hdg

        if is_pitot_healthy:
            # Wind = Ground_Speed - Airspeed
            raw_wind_x = self.filt_vg_x - v_air_x
            raw_wind_y = self.filt_vg_y - v_air_y
            self.filt_wind_x = (1.0 - self.alpha) * self.filt_wind_x + self.alpha * raw_wind_x
            self.filt_wind_y = (1.0 - self.alpha) * self.filt_wind_y + self.alpha * raw_wind_y

        # Wind speed & meteorological direction FROM which wind is blowing
        wind_mag = math.sqrt(self.filt_wind_x**2 + self.filt_wind_y**2)
        wind_dir_rad = math.atan2(-self.filt_wind_y, -self.filt_wind_x)
        wind_dir_deg = (math.degrees(wind_dir_rad) + 360.0) % 360.0

        # Synthetic airspeed: Va_synth = ||Vg - W||
        v_synth_x = self.filt_vg_x - self.filt_wind_x
        v_synth_y = self.filt_vg_y - self.filt_wind_y
        synth_airspeed = math.sqrt(v_synth_x**2 + v_synth_y**2)

        return OpticalFlowEstimate(
            ground_speed_x_ms=round(self.filt_vg_x, 2),
            ground_speed_y_ms=round(self.filt_vg_y, 2),
            ground_speed_mag_ms=round(vg_mag, 2),
            wind_speed_ms=round(wind_mag, 2),
            wind_direction_deg=round(wind_dir_deg, 1),
            synthetic_airspeed_ms=round(synth_airspeed, 2),
            is_valid=True
        )
