#!/usr/bin/env python3
"""
AIAA DBF 2027 - High-Rate Flight Blackbox Recorder & Post-Flight Diagnostics
Records 50 Hz telemetric flight data packets, detects sensor clipping,
analyzes airframe vibration spectrums, and produces AIAA DBF post-flight flight readiness reports.
"""

import os
import math
import json
import struct
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class BlackboxFrame:
    timestamp_s: float
    airspeed_ms: float
    altitude_m: float
    roll_deg: float
    pitch_deg: float
    yaw_deg: float
    accel_x_g: float
    accel_y_g: float
    accel_z_g: float
    gyro_p_deg_s: float
    gyro_q_deg_s: float
    gyro_r_deg_s: float
    voltage_v: float
    current_a: float
    motor_temp_c: float
    servo_pwm_us: List[int]     # 7 actuators: [ail_lo, ail_li, ail_ri, ail_ro, elev_l, elev_r, rud]
    fdir_flags: int             # Bitmask of safety flags


@dataclass
class DiagnosticsSummary:
    total_duration_s: float
    frame_count: int
    mean_sample_rate_hz: float
    max_g_load: float
    min_g_load: float
    vibration_rms_g: float
    clipping_event_count: int
    min_voltage_v: float
    max_current_a: float
    peak_motor_temp_c: float
    control_saturation_percent: float
    is_airframe_healthy: bool


class FlightBlackboxRecorder:
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self.frames: List[BlackboxFrame] = []
        self.is_recording = False

    def start_recording(self):
        self.frames.clear()
        self.is_recording = True

    def record_frame(self, frame: BlackboxFrame):
        if self.is_recording:
            self.frames.append(frame)

    def stop_recording(self):
        self.is_recording = False
        if self.log_path and len(self.frames) > 0:
            self.save_to_json(self.log_path)

    def save_to_json(self, output_path: str):
        data = [asdict(f) for f in self.frames]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def analyze_flight_diagnostics(self) -> DiagnosticsSummary:
        if len(self.frames) < 2:
            return DiagnosticsSummary(
                total_duration_s=0.0, frame_count=len(self.frames),
                mean_sample_rate_hz=0.0, max_g_load=1.0, min_g_load=1.0,
                vibration_rms_g=0.0, clipping_event_count=0, min_voltage_v=0.0,
                max_current_a=0.0, peak_motor_temp_c=0.0,
                control_saturation_percent=0.0, is_airframe_healthy=True
            )

        duration = self.frames[-1].timestamp_s - self.frames[0].timestamp_s
        sample_rate = len(self.frames) / max(duration, 0.001)

        accel_z_arr = np.array([f.accel_z_g for f in self.frames])
        accel_x_arr = np.array([f.accel_x_g for f in self.frames])
        accel_y_arr = np.array([f.accel_y_g for f in self.frames])
        volt_arr = np.array([f.voltage_v for f in self.frames])
        curr_arr = np.array([f.current_a for f in self.frames])
        temp_arr = np.array([f.motor_temp_c for f in self.frames])

        max_g = float(np.max(accel_z_arr))
        min_g = float(np.min(accel_z_arr))

        # Vibration analysis: High-frequency deviation from mean gravity
        vibration_rms = float(np.sqrt(np.mean((accel_z_arr - np.mean(accel_z_arr))**2)))

        # IMU clipping events (Pixhawk 6X accelerometer saturation limit: > 15g)
        total_accel_mag = np.sqrt(accel_x_arr**2 + accel_y_arr**2 + accel_z_arr**2)
        clipping_events = int(np.sum(total_accel_mag > 14.0))

        # Actuator saturation: PWM clipping at 1000us or 2000us (extreme deflection)
        saturated_frames = 0
        for f in self.frames:
            if any(p <= 1050 or p >= 1950 for p in f.servo_pwm_us):
                saturated_frames += 1
        saturation_pct = (saturated_frames / len(self.frames)) * 100.0

        # Health verdict
        is_healthy = (
            vibration_rms < 1.20 and
            clipping_events == 0 and
            max_g < 3.50 and
            float(np.min(volt_arr)) > 19.8 and  # Safe cell cutoff
            float(np.max(temp_arr)) < 110.0
        )

        return DiagnosticsSummary(
            total_duration_s=round(duration, 2),
            frame_count=len(self.frames),
            mean_sample_rate_hz=round(sample_rate, 1),
            max_g_load=round(max_g, 2),
            min_g_load=round(min_g, 2),
            vibration_rms_g=round(vibration_rms, 3),
            clipping_event_count=clipping_events,
            min_voltage_v=round(float(np.min(volt_arr)), 2),
            max_current_a=round(float(np.max(curr_arr)), 2),
            peak_motor_temp_c=round(float(np.max(temp_arr)), 1),
            control_saturation_percent=round(saturation_pct, 1),
            is_airframe_healthy=is_healthy
        )
