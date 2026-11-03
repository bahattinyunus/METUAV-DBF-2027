#!/usr/bin/env python3
"""
METUAV DBF 2027 - Advanced Compass Navigation & Magnetometer Calibration Engine (Pusula Sistemi)
Provides 3D ellipsoid hard-iron / soft-iron calibration, ESC motor-current interference compensation,
dual-compass voting & failover, tilt-compensated heading estimation, and magnetic anomaly rejection.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np


@dataclass
class CompassCalibrationResult:
    """Stores 3D ellipsoid calibration parameters and quality metrics."""
    hard_iron_bias: np.ndarray  # [bx, by, bz] (uT)
    soft_iron_matrix: np.ndarray  # 3x3 transformation matrix
    target_field_radius: float  # uT
    rms_residual_error: float  # uT
    fitness_grade: str  # 'A+', 'A', 'B', 'C', or 'FAIL'
    is_valid: bool
    num_samples: int


@dataclass
class DualCompassStatus:
    """Status telemetry for dual redundant compass setup."""
    primary_healthy: bool
    secondary_healthy: bool
    active_compass_id: int  # 1 for primary, 2 for secondary
    heading_deg: float
    field_norm_primary: float
    field_norm_secondary: float
    angular_discrepancy_deg: float
    anomaly_detected: bool
    status_message: str


class CompassNavigationCalibrator:
    """
    Comprehensive Magnetometer / Compass Calibration and Estimation Engine.
    Handles hard/soft iron fitting, dynamic motor interference, tilt compensation,
    and redundant dual-compass monitoring.
    """

    def __init__(self, earth_field_ref_ut: float = 48.5, declination_deg: float = 6.2):
        """
        Parameters
        ----------
        earth_field_ref_ut : float
            Expected local Earth magnetic field magnitude (uT) (e.g. ~48-52 uT for DBF Tucson/Ankara).
        declination_deg : float
            Local magnetic declination angle in degrees (positive East).
        """
        self.earth_field_ref = float(earth_field_ref_ut)
        self.declination_rad = math.radians(declination_deg)

        # Primary compass calibration params
        self.hard_iron_primary = np.zeros(3, dtype=float)
        self.soft_iron_primary = np.eye(3, dtype=float)
        self.calibrated_primary = False

        # Secondary compass calibration params
        self.hard_iron_secondary = np.zeros(3, dtype=float)
        self.soft_iron_secondary = np.eye(3, dtype=float)
        self.calibrated_secondary = False

        # Motor current interference coefficients [Kx, Ky, Kz] (uT / Ampere)
        self.motor_comp_primary = np.zeros(3, dtype=float)
        self.motor_comp_secondary = np.zeros(3, dtype=float)

        # Redundancy state
        self.active_compass = 1  # 1: Primary, 2: Secondary
        self.primary_fail_count = 0
        self.failover_threshold = 5

    def fit_ellipsoid_3d(self, raw_samples: np.ndarray, target_norm_ut: Optional[float] = None) -> CompassCalibrationResult:
        """
        Fits a 3D ellipsoid to raw magnetometer samples using linear algebraic least-squares.
        Solves: v[0]*x^2 + v[1]*y^2 + v[2]*z^2 + 2*v[3]*xy + 2*v[4]*xz + 2*v[5]*yz + 2*v[6]*x + 2*v[7]*y + 2*v[8]*z = 1
        Extracts center (hard-iron bias) and eigenvector scaling (soft-iron matrix).
        """
        raw_samples = np.asarray(raw_samples, dtype=float)
        n_samples = len(raw_samples)
        target_r = target_norm_ut if target_norm_ut is not None else self.earth_field_ref

        if n_samples < 20:
            return CompassCalibrationResult(
                hard_iron_bias=np.zeros(3),
                soft_iron_matrix=np.eye(3),
                target_field_radius=target_r,
                rms_residual_error=999.0,
                fitness_grade="FAIL",
                is_valid=False,
                num_samples=n_samples
            )

        x = raw_samples[:, 0]
        y = raw_samples[:, 1]
        z = raw_samples[:, 2]

        # Design matrix D
        D = np.column_stack([
            x**2, y**2, z**2,
            2 * x * y, 2 * x * z, 2 * y * z,
            2 * x, 2 * y, 2 * z
        ])

        try:
            vec, _, rank, _ = np.linalg.lstsq(D, np.ones(n_samples), rcond=None)
            if rank < 9:
                raise np.linalg.LinAlgError("Insufficient geometric rank for 3D ellipsoid fit")

            # Quadratic matrix M and linear vector u
            M = np.array([
                [vec[0], vec[3], vec[4]],
                [vec[3], vec[1], vec[5]],
                [vec[4], vec[5], vec[2]]
            ])
            u_vec = np.array([vec[6], vec[7], vec[8]])

            # Center V = -M^{-1} * u
            center = -np.linalg.inv(M) @ u_vec

            # Scale translated quadric form
            denom = 1.0 + float(u_vec.T @ np.linalg.inv(M) @ u_vec)
            if denom <= 0:
                raise np.linalg.LinAlgError("Non-ellipsoidal algebraic quadratic surface")

            M_trans = M / denom
            evals, evecs = np.linalg.eigh(M_trans)

            if np.any(evals <= 0.0):
                raise np.linalg.LinAlgError("Quadric surface eigenvalues not positive definite")

            # Soft-iron transformation matrix W = Q * diag(R0 * sqrt(lambda)) * Q^T
            # Maps ellipsoid onto sphere of radius target_r
            W = evecs @ np.diag(target_r * np.sqrt(evals)) @ evecs.T

            # Calculate residual RMS error on calibrated sphere
            calibrated_pts = (raw_samples - center) @ W.T
            norms = np.linalg.norm(calibrated_pts, axis=1)
            residuals = norms - target_r
            rms_error = float(np.sqrt(np.mean(residuals**2)))

            # Grade the calibration quality
            if rms_error < 0.8:
                grade = "A+"
            elif rms_error < 1.8:
                grade = "A"
            elif rms_error < 3.5:
                grade = "B"
            elif rms_error < 6.0:
                grade = "C"
            else:
                grade = "POOR"

            return CompassCalibrationResult(
                hard_iron_bias=center,
                soft_iron_matrix=W,
                target_field_radius=target_r,
                rms_residual_error=rms_error,
                fitness_grade=grade,
                is_valid=(grade in ["A+", "A", "B", "C"]),
                num_samples=n_samples
            )

        except Exception:
            # Fallback to simple min-max bounding sphere
            min_bounds = np.min(raw_samples, axis=0)
            max_bounds = np.max(raw_samples, axis=0)
            center = (min_bounds + max_bounds) / 2.0
            scales = (max_bounds - min_bounds) / 2.0
            avg_scale = np.mean(scales) if np.mean(scales) > 1e-3 else 1.0
            W = np.diag(target_r / (scales + 1e-6))

            calibrated_pts = (raw_samples - center) @ W.T
            residuals = np.linalg.norm(calibrated_pts, axis=1) - target_r
            rms_error = float(np.sqrt(np.mean(residuals**2)))

            return CompassCalibrationResult(
                hard_iron_bias=center,
                soft_iron_matrix=W,
                target_field_radius=target_r,
                rms_residual_error=rms_error,
                fitness_grade="C" if rms_error < 7.0 else "FAIL",
                is_valid=(rms_error < 7.0),
                num_samples=n_samples
            )

    def set_primary_calibration(self, hard_iron: np.ndarray, soft_iron: np.ndarray):
        """Sets hard and soft iron parameters for primary compass."""
        self.hard_iron_primary = np.asarray(hard_iron, dtype=float)
        self.soft_iron_primary = np.asarray(soft_iron, dtype=float)
        self.calibrated_primary = True

    def set_secondary_calibration(self, hard_iron: np.ndarray, soft_iron: np.ndarray):
        """Sets hard and soft iron parameters for secondary compass."""
        self.hard_iron_secondary = np.asarray(hard_iron, dtype=float)
        self.soft_iron_secondary = np.asarray(soft_iron, dtype=float)
        self.calibrated_secondary = True

    def calibrate_motor_interference(
        self,
        current_samples_amps: np.ndarray,
        mag_samples_ut: np.ndarray,
        compass_id: int = 1
    ) -> np.ndarray:
        """
        Calibrates linear magnetic field bias induced by high motor current:
        delta_B = K * I_batt.
        Uses 1D least-squares fit across throttle ramp.
        """
        currents = np.asarray(current_samples_amps, dtype=float)
        mags = np.asarray(mag_samples_ut, dtype=float)

        if len(currents) < 5 or np.max(currents) - np.min(currents) < 5.0:
            return np.zeros(3)

        # Baseline zero-current magnetic field
        zero_current_mask = currents <= (np.min(currents) + 1.0)
        baseline = np.mean(mags[zero_current_mask], axis=0) if np.any(zero_current_mask) else mags[0]

        delta_m = mags - baseline
        # Solve delta_m = currents * K -> K = (I^T * I)^-1 * I^T * delta_m
        i_col = currents[:, np.newaxis]
        k_coeffs, _, _, _ = np.linalg.lstsq(i_col, delta_m, rcond=None)
        k_vec = k_coeffs.flatten()

        if compass_id == 1:
            self.motor_comp_primary = k_vec
        else:
            self.motor_comp_secondary = k_vec

        return k_vec

    def correct_measurement(
        self,
        raw_mag: np.ndarray,
        battery_current_amps: float = 0.0,
        compass_id: int = 1
    ) -> np.ndarray:
        """
        Applies hard-iron, soft-iron, and motor current corrections to raw magnetometer reading.
        """
        raw = np.asarray(raw_mag, dtype=float)
        if compass_id == 1:
            hard = self.hard_iron_primary
            soft = self.soft_iron_primary
            k_motor = self.motor_comp_primary
        else:
            hard = self.hard_iron_secondary
            soft = self.soft_iron_secondary
            k_motor = self.motor_comp_secondary

        # 1. Hard iron removal & 2. Soft iron scaling
        calibrated = soft @ (raw - hard)

        # 3. Dynamic motor current interference compensation
        compensated = calibrated - (k_motor * battery_current_amps)
        return compensated

    def calculate_tilt_compensated_heading(
        self,
        mag_corr: np.ndarray,
        roll_rad: float,
        pitch_rad: float,
        apply_declination: bool = True
    ) -> float:
        """
        Calculates tilt-compensated magnetic heading (azimuth) from calibrated 3D body magnetic vector.
        Projects body frame vector into level horizontal plane using Euler roll & pitch.
        Returns heading in radians [-pi, pi).
        """
        bx, by, bz = float(mag_corr[0]), float(mag_corr[1]), float(mag_corr[2])
        phi = float(roll_rad)
        theta = float(pitch_rad)

        cos_th = math.cos(theta)
        sin_th = math.sin(theta)
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)

        # Level plane projection
        bxh = bx * cos_th + by * sin_phi * sin_th + bz * cos_phi * sin_th
        byh = by * cos_phi - bz * sin_phi

        # Azimuth calculation (NED convention: clockwise from North)
        heading_mag = math.atan2(-byh, bxh)

        if apply_declination:
            heading_true = heading_mag + self.declination_rad
        else:
            heading_true = heading_mag

        # Wrap to [-pi, pi)
        return (heading_true + math.pi) % (2.0 * math.pi) - math.pi

    def is_magnetic_field_healthy(
        self,
        mag_corr: np.ndarray,
        tolerance_ratio: float = 0.25
    ) -> Tuple[bool, float, str]:
        """
        Dynamic Magnetic Anomaly Detector.
        Checks if the corrected magnetic field norm is within realistic Earth field bounds.
        """
        norm = float(np.linalg.norm(mag_corr))
        min_allowed = self.earth_field_ref * (1.0 - tolerance_ratio)
        max_allowed = self.earth_field_ref * (1.0 + tolerance_ratio)

        if norm < min_allowed:
            return False, norm, f"Magnetic field too low ({norm:.1f} uT < {min_allowed:.1f} uT)"
        elif norm > max_allowed:
            return False, norm, f"Magnetic field excessive/distorted ({norm:.1f} uT > {max_allowed:.1f} uT)"

        return True, norm, "Nominal Earth magnetic field"

    def process_dual_compass(
        self,
        raw_primary: np.ndarray,
        raw_secondary: np.ndarray,
        roll_rad: float,
        pitch_rad: float,
        battery_current_amps: float = 0.0
    ) -> DualCompassStatus:
        """
        Processes dual redundant magnetometers, checks health and angular consistency,
        and manages automatic failover.
        """
        corr1 = self.correct_measurement(raw_primary, battery_current_amps, compass_id=1)
        corr2 = self.correct_measurement(raw_secondary, battery_current_amps, compass_id=2)

        healthy1, norm1, msg1 = self.is_magnetic_field_healthy(corr1)
        healthy2, norm2, msg2 = self.is_magnetic_field_healthy(corr2)

        h1 = self.calculate_tilt_compensated_heading(corr1, roll_rad, pitch_rad)
        h2 = self.calculate_tilt_compensated_heading(corr2, roll_rad, pitch_rad)

        # Angular discrepancy in degrees
        angle_diff_rad = abs((h1 - h2 + math.pi) % (2.0 * math.pi) - math.pi)
        disc_deg = math.degrees(angle_diff_rad)

        anomaly = (not healthy1) or (disc_deg > 20.0 and healthy2)

        # Redundancy & failover logic
        if not healthy1 and healthy2:
            self.primary_fail_count += 1
            if self.primary_fail_count >= self.failover_threshold:
                self.active_compass = 2
        elif healthy1:
            if self.primary_fail_count > 0:
                self.primary_fail_count -= 1
            if self.primary_fail_count == 0:
                self.active_compass = 1

        active_heading = h1 if self.active_compass == 1 else h2
        status_msg = "Nominal Dual Compass Tracking"
        if self.active_compass == 2:
            status_msg = f"FAILOVER to Secondary Compass: {msg1}"
        elif disc_deg > 15.0:
            status_msg = f"Compass Heading Divergence Warning ({disc_deg:.1f} deg diff)"

        return DualCompassStatus(
            primary_healthy=healthy1,
            secondary_healthy=healthy2,
            active_compass_id=self.active_compass,
            heading_deg=math.degrees(active_heading) % 360.0,
            field_norm_primary=norm1,
            field_norm_secondary=norm2,
            angular_discrepancy_deg=disc_deg,
            anomaly_detected=anomaly,
            status_message=status_msg
        )
