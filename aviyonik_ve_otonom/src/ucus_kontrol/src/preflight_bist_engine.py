#!/usr/bin/env python3
"""
AIAA DBF 2027 - Pre-Flight Built-In Self-Test (BIST) Engine
Performs rapid, autonomous pre-arm verification across sensors, power rails,
actuator sweep envelopes, GPS geometry, and Mission 3 payload release locks in < 10 seconds.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class SubsystemBISTResult:
    subsystem_name: str
    passed: bool
    measured_value: float
    nominal_range: Tuple[float, float]
    unit: str
    message: str


@dataclass
class BISTCertificate:
    total_checks: int
    passed_checks: int
    failed_checks: int
    is_flight_authorized: bool
    flight_readiness_code: str
    subsystem_details: List[SubsystemBISTResult]


class PreFlightBISTEngine:
    def __init__(self):
        self.results: List[SubsystemBISTResult] = []

    def verify_imu(self, accel_z_samples: np.ndarray, gyro_norm_samples: np.ndarray) -> SubsystemBISTResult:
        mean_az = float(np.mean(accel_z_samples))
        gyro_noise_rms = float(np.sqrt(np.mean(gyro_norm_samples**2)))

        passed = (0.95 <= mean_az <= 1.05) and (gyro_noise_rms <= 0.05)
        msg = "IMU 1g gravity and low noise verified" if passed else "IMU bias or excessive noise detected"

        return SubsystemBISTResult(
            subsystem_name="IMU_6DOF_INTEGRITY",
            passed=passed,
            measured_value=mean_az,
            nominal_range=(0.95, 1.05),
            unit="g",
            message=msg
        )

    def verify_pitot_airspeed(self, static_airspeed_samples: np.ndarray) -> SubsystemBISTResult:
        zero_offset = float(np.mean(np.abs(static_airspeed_samples)))
        passed = zero_offset <= 1.20  # m/s in calm apron environment

        msg = "Pitot dynamic pressure zero offset nominal" if passed else "Pitot clogged or high offset"
        return SubsystemBISTResult(
            subsystem_name="PITOT_STATIC_AIRSPEED",
            passed=passed,
            measured_value=zero_offset,
            nominal_range=(0.0, 1.20),
            unit="m/s",
            message=msg
        )

    def verify_gps_fix(self, num_satellites: int, hdop: float) -> SubsystemBISTResult:
        passed = (num_satellites >= 10) and (hdop <= 1.20)
        msg = f"GPS 3D Fix High Precision ({num_satellites} Sats, HDOP {hdop:.2f})" if passed else "GPS Fix insufficient"

        return SubsystemBISTResult(
            subsystem_name="GPS_3D_FIX_GEOMETRY",
            passed=passed,
            measured_value=float(hdop),
            nominal_range=(0.5, 1.20),
            unit="HDOP",
            message=msg
        )

    def verify_servos_sweep(self, current_peaks_a: np.ndarray) -> SubsystemBISTResult:
        max_current = float(np.max(current_peaks_a))
        # High-performance digital servos during full sweep draw ~0.8 - 2.2A. > 3.0A indicates mechanical stall/binding
        passed = (max_current <= 2.80) and (max_current >= 0.30)
        msg = "7-channel control surfaces sweep nominal, no servo binding" if passed else "Servo stall binding detected"

        return SubsystemBISTResult(
            subsystem_name="ACTUATORS_SERVO_SWEEP",
            passed=passed,
            measured_value=max_current,
            nominal_range=(0.30, 2.80),
            unit="A",
            message=msg
        )

    def verify_battery_pack(self, voltage_v: float, cell_deviation_v: float) -> SubsystemBISTResult:
        passed = (voltage_v >= 24.0) and (cell_deviation_v <= 0.030)  # 4.0V/cell minimum, < 30mV delta
        msg = f"6S LiPo Pack Healthy ({voltage_v:.2f}V, Cell Delta {cell_deviation_v*1000:.1f}mV)" if passed else "Battery depleted or cell unbalanced"

        return SubsystemBISTResult(
            subsystem_name="POWERTRAIN_6S_BATTERY",
            passed=passed,
            measured_value=voltage_v,
            nominal_range=(24.0, 25.26),
            unit="V",
            message=msg
        )

    def verify_payload_drop_lock(self, lock_feedback_state: bool, pin_voltage_v: float) -> SubsystemBISTResult:
        passed = (lock_feedback_state is True) and (3.10 <= pin_voltage_v <= 3.45)
        msg = "Mission 3 payload release solenoid/servo mechanically locked" if passed else "Payload lock unlatched or feedback open"

        return SubsystemBISTResult(
            subsystem_name="MISSION3_PAYLOAD_LOCK",
            passed=passed,
            measured_value=pin_voltage_v,
            nominal_range=(3.10, 3.45),
            unit="V",
            message=msg
        )

    def verify_compass(self, mag_samples_ut: np.ndarray, expected_norm_ut: float = 48.5) -> SubsystemBISTResult:
        norms = np.linalg.norm(mag_samples_ut, axis=1) if mag_samples_ut.ndim > 1 else np.array([np.linalg.norm(mag_samples_ut)])
        mean_field = float(np.mean(norms))
        min_bound = 0.75 * expected_norm_ut
        max_bound = 1.25 * expected_norm_ut
        passed = (min_bound <= mean_field <= max_bound)
        msg = f"Compass magnetic field nominal ({mean_field:.1f} uT)" if passed else f"Compass anomaly/distortion detected ({mean_field:.1f} uT)"

        return SubsystemBISTResult(
            subsystem_name="MAGNETOMETER_COMPASS_HEALTH",
            passed=passed,
            measured_value=mean_field,
            nominal_range=(min_bound, max_bound),
            unit="uT",
            message=msg
        )

    def run_complete_preflight_bist(
        self,
        accel_z_samples: np.ndarray,
        gyro_norm_samples: np.ndarray,
        pitot_samples: np.ndarray,
        gps_sats: int,
        gps_hdop: float,
        servo_currents: np.ndarray,
        battery_voltage: float,
        cell_delta_v: float,
        payload_locked: bool,
        payload_pin_v: float,
        mag_samples: Optional[np.ndarray] = None
    ) -> BISTCertificate:
        self.results.clear()
        self.results.append(self.verify_imu(accel_z_samples, gyro_norm_samples))
        self.results.append(self.verify_pitot_airspeed(pitot_samples))
        self.results.append(self.verify_gps_fix(gps_sats, gps_hdop))
        self.results.append(self.verify_servos_sweep(servo_currents))
        self.results.append(self.verify_battery_pack(battery_voltage, cell_delta_v))
        self.results.append(self.verify_payload_drop_lock(payload_locked, payload_pin_v))
        if mag_samples is not None:
            self.results.append(self.verify_compass(mag_samples))

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        is_authorized = (failed == 0)
        code = "DBF-AIR-GO-2027" if is_authorized else "DBF-ABORT-BIST-FAIL"

        return BISTCertificate(
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            is_flight_authorized=is_authorized,
            flight_readiness_code=code,
            subsystem_details=self.results
        )
