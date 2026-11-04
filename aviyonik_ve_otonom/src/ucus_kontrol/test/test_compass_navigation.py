#!/usr/bin/env python3
"""
AIAA DBF 2027 - Unit tests for Compass Navigation & Magnetometer Calibration Engine (Pusula Testleri)
"""

import math
import numpy as np
import pytest

from aviyonik_ve_otonom.src.ucus_kontrol.src.compass_navigation_calibrator import (
    CompassNavigationCalibrator,
    CompassCalibrationResult,
    DualCompassStatus
)
from aviyonik_ve_otonom.src.ucus_kontrol.src.preflight_bist_engine import PreFlightBISTEngine


def test_3d_ellipsoid_calibration_synthetic_sphere():
    """Verify that 3D ellipsoid fit accurately extracts hard-iron center and soft-iron matrix."""
    calibrator = CompassNavigationCalibrator(earth_field_ref_ut=50.0)

    # Ground truth: Hard-iron bias [15.0, -10.0, 8.0] and soft-iron scales [40.0, 55.0, 45.0]
    true_bias = np.array([15.0, -10.0, 8.0])
    true_radii = np.array([40.0, 55.0, 45.0])

    np.random.seed(123)
    n_pts = 300
    u = np.random.uniform(0.0, 2.0 * np.pi, n_pts)
    v = np.random.uniform(0.0, np.pi, n_pts)

    x = true_bias[0] + true_radii[0] * np.cos(u) * np.sin(v) + np.random.normal(0, 0.15, n_pts)
    y = true_bias[1] + true_radii[1] * np.sin(u) * np.sin(v) + np.random.normal(0, 0.15, n_pts)
    z = true_bias[2] + true_radii[2] * np.cos(v) + np.random.normal(0, 0.15, n_pts)
    raw_samples = np.column_stack([x, y, z])

    res = calibrator.fit_ellipsoid_3d(raw_samples, target_norm_ut=50.0)

    assert res.is_valid is True
    assert res.fitness_grade in ["A+", "A"]
    assert res.rms_residual_error < 1.0

    # Center must match within 0.5 uT
    np.testing.assert_allclose(res.hard_iron_bias, true_bias, atol=0.6)

    # Calibrated samples should all lie near sphere of radius 50.0 uT
    calibrator.set_primary_calibration(res.hard_iron_bias, res.soft_iron_matrix)
    calibrated = np.array([calibrator.correct_measurement(pt, compass_id=1) for pt in raw_samples])
    norms = np.linalg.norm(calibrated, axis=1)
    assert np.mean(norms) == pytest.approx(50.0, rel=0.02)
    assert np.std(norms) < 0.6


def test_motor_current_interference_compensation():
    """Verify compensation of high-throttle battery current magnetic distortion."""
    calibrator = CompassNavigationCalibrator(earth_field_ref_ut=48.5)

    # Set nominal primary calibration
    calibrator.set_primary_calibration(hard_iron=np.zeros(3), soft_iron=np.eye(3))

    # True Earth field vector [30.0, 0.0, 38.0] uT
    b_earth = np.array([30.0, 0.0, 38.0])

    # ESC current induction K = [0.12, -0.05, 0.25] uT / Amp
    k_true = np.array([0.12, -0.05, 0.25])

    # Simulate throttle ramp from 0A to 60A
    currents = np.linspace(0.0, 60.0, 25)
    mag_samples = np.array([b_earth + k_true * cur for cur in currents])

    k_est = calibrator.calibrate_motor_interference(currents, mag_samples, compass_id=1)
    np.testing.assert_allclose(k_est, k_true, atol=0.01)

    # At full sprint 55A cruise, raw mag is heavily contaminated
    raw_55a = b_earth + k_true * 55.0
    corr_55a = calibrator.correct_measurement(raw_55a, battery_current_amps=55.0, compass_id=1)

    # Corrected measurement matches pure Earth field
    np.testing.assert_allclose(corr_55a, b_earth, atol=0.05)


def test_tilt_compensated_heading():
    """Verify level-plane projection removes roll and pitch errors."""
    calibrator = CompassNavigationCalibrator(earth_field_ref_ut=50.0, declination_deg=0.0)

    # Earth magnetic field in NED: North=30 uT, East=0 uT, Down=40 uT
    b_ned = np.array([30.0, 0.0, 40.0])

    # Test cases: (yaw_deg, pitch_deg, roll_deg)
    test_cases = [
        (0.0, 0.0, 0.0),
        (45.0, 15.0, -10.0),
        (90.0, -12.0, 20.0),
        (180.0, 25.0, 15.0),
        (-60.0, -15.0, -25.0),
    ]

    for yaw_deg, pitch_deg, roll_deg in test_cases:
        yaw = math.radians(yaw_deg)
        pitch = math.radians(pitch_deg)
        roll = math.radians(roll_deg)

        # Body rotation: R_nb = Rz(yaw) * Ry(pitch) * Rx(roll)
        # B_body = R_nb^T * B_ned = Rx(-roll) * Ry(-pitch) * Rz(-yaw) * B_ned
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cr, sr = math.cos(roll), math.sin(roll)

        # R_bn
        r11 = cp * cy
        r12 = cp * sy
        r13 = -sp

        r21 = sr * sp * cy - cr * sy
        r22 = sr * sp * sy + cr * cy
        r23 = sr * cp

        r31 = cr * sp * cy + sr * sy
        r32 = cr * sp * sy - sr * cy
        r33 = cr * cp

        b_body = np.array([
            r11 * b_ned[0] + r12 * b_ned[1] + r13 * b_ned[2],
            r21 * b_ned[0] + r22 * b_ned[1] + r23 * b_ned[2],
            r31 * b_ned[0] + r32 * b_ned[1] + r33 * b_ned[2]
        ])

        est_heading_rad = calibrator.calculate_tilt_compensated_heading(
            b_body, roll_rad=roll, pitch_rad=pitch, apply_declination=False
        )

        expected_yaw_wrapped = (yaw + math.pi) % (2.0 * math.pi) - math.pi
        assert est_heading_rad == pytest.approx(expected_yaw_wrapped, abs=1e-4)


def test_magnetic_anomaly_rejection():
    """Verify anomalous external fields (e.g. proximity to rebar or iron) are rejected."""
    calibrator = CompassNavigationCalibrator(earth_field_ref_ut=48.5)

    # Nominal field ~ 48.5 uT
    nominal_field = np.array([28.0, 5.0, 39.0])
    healthy, norm, msg = calibrator.is_magnetic_field_healthy(nominal_field)
    assert healthy is True
    assert 45.0 <= norm <= 52.0

    # Distorted field near metal runway structure (~ 80 uT)
    distorted_field = np.array([55.0, 30.0, 60.0])
    healthy_dist, norm_dist, msg_dist = calibrator.is_magnetic_field_healthy(distorted_field)
    assert healthy_dist is False
    assert norm_dist > 60.0
    assert "excessive/distorted" in msg_dist


def test_dual_compass_voting_and_failover():
    """Verify seamless switchover when primary compass is jammed or saturated."""
    calibrator = CompassNavigationCalibrator(earth_field_ref_ut=48.5)
    calibrator.set_primary_calibration(np.zeros(3), np.eye(3))
    calibrator.set_secondary_calibration(np.zeros(3), np.eye(3))

    b_nominal = np.array([30.0, 0.0, 38.0])
    b_jammed = np.array([90.0, 40.0, 110.0])  # Severely corrupted primary

    # Initially both healthy
    status = calibrator.process_dual_compass(b_nominal, b_nominal, 0.0, 0.0)
    assert status.active_compass_id == 1
    assert status.primary_healthy is True
    assert status.secondary_healthy is True

    # Primary gets distorted over multiple cycles
    for _ in range(5):
        status = calibrator.process_dual_compass(b_jammed, b_nominal, 0.0, 0.0)

    # Should have triggered failover to Secondary (ID 2)
    assert status.active_compass_id == 2
    assert status.primary_healthy is False
    assert status.secondary_healthy is True
    assert "FAILOVER" in status.status_message


def test_preflight_bist_compass_integration():
    """Verify PreFlight BIST engine validates compass alongside IMU, GPS, and servos."""
    engine = PreFlightBISTEngine()

    nominal_mag = np.random.normal(48.5 / np.sqrt(3), 0.5, (100, 3))

    cert = engine.run_complete_preflight_bist(
        accel_z_samples=np.random.normal(1.0, 0.01, 100),
        gyro_norm_samples=np.random.normal(0.01, 0.005, 100),
        pitot_samples=np.random.normal(0.2, 0.1, 50),
        gps_sats=14,
        gps_hdop=0.85,
        servo_currents=np.array([1.2, 1.4, 1.1, 1.3, 1.5, 1.5, 1.0]),
        battery_voltage=24.8,
        cell_delta_v=0.012,
        payload_locked=True,
        payload_pin_v=3.30,
        mag_samples=nominal_mag
    )

    assert cert.is_flight_authorized is True
    assert cert.total_checks == 7
    assert cert.passed_checks == 7
    assert cert.failed_checks == 0

    # Distorted compass should fail pre-arm
    corrupted_mag = np.random.normal(85.0 / np.sqrt(3), 1.0, (100, 3))
    cert_fail = engine.run_complete_preflight_bist(
        accel_z_samples=np.random.normal(1.0, 0.01, 100),
        gyro_norm_samples=np.random.normal(0.01, 0.005, 100),
        pitot_samples=np.random.normal(0.2, 0.1, 50),
        gps_sats=14,
        gps_hdop=0.85,
        servo_currents=np.array([1.2, 1.4, 1.1, 1.3, 1.5, 1.5, 1.0]),
        battery_voltage=24.8,
        cell_delta_v=0.012,
        payload_locked=True,
        payload_pin_v=3.30,
        mag_samples=corrupted_mag
    )

    assert cert_fail.is_flight_authorized is False
    assert cert_fail.failed_checks == 1
    assert "ABORT" in cert_fail.flight_readiness_code
