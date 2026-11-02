import math
import pytest
from edge_ai_vision.optical_flow_wind_estimator import OpticalFlowWindEstimator

def test_optical_flow_ground_speed():
    est = OpticalFlowWindEstimator(camera_focal_length_px=800.0, filter_alpha=1.0)

    # Flying North at 25m altitude, Ground speed = 25 m/s
    # Flow: omega = -Vx / h = -25 / 25 = -1.0 rad/s -> pixel flow = -800 px/s
    res = est.estimate(
        pixel_flow_x_px_s=-800.0,
        pixel_flow_y_px_s=0.0,
        gyro_p_rad_s=0.0,
        gyro_q_rad_s=0.0,
        altitude_agl_m=25.0,
        heading_rad=0.0,
        pitot_airspeed_ms=25.0
    )

    assert res.is_valid is True
    assert abs(res.ground_speed_x_ms - 25.0) < 0.5
    assert abs(res.ground_speed_y_ms) < 0.5
    assert abs(res.synthetic_airspeed_ms - 25.0) < 0.5

def test_derotation_rejection():
    est = OpticalFlowWindEstimator(camera_focal_length_px=800.0, filter_alpha=1.0)

    # Hovering / stationary, but pitching down at q = 0.5 rad/s
    # Pitch causes pure rotational flow: pixel_flow = q * focal = 0.5 * 800 = +400 px/s
    res = est.estimate(
        pixel_flow_x_px_s=400.0,
        pixel_flow_y_px_s=0.0,
        gyro_p_rad_s=0.0,
        gyro_q_rad_s=0.5,
        altitude_agl_m=25.0,
        heading_rad=0.0,
        pitot_airspeed_ms=0.0
    )

    # After derotation (omega_flow - q = 0.5 - 0.5 = 0), ground speed must be 0!
    assert abs(res.ground_speed_x_ms) < 0.1
    assert abs(res.ground_speed_mag_ms) < 0.1

def test_synthetic_airspeed_backup_on_pitot_failure():
    est = OpticalFlowWindEstimator(camera_focal_length_px=800.0, filter_alpha=0.5)

    # Step 1: Calibrate with healthy pitot and a 5 m/s headwind
    for _ in range(10):
        est.estimate(
            pixel_flow_x_px_s=-640.0,  # Vg = 20 m/s
            pixel_flow_y_px_s=0.0,
            gyro_p_rad_s=0.0,
            gyro_q_rad_s=0.0,
            altitude_agl_m=25.0,
            heading_rad=0.0,
            pitot_airspeed_ms=25.0,
            is_pitot_healthy=True
        )

    # Step 2: Pitot clogs (reads 0.0 m/s), estimator provides synthetic airspeed
    res_backup = est.estimate(
        pixel_flow_x_px_s=-640.0,
        pixel_flow_y_px_s=0.0,
        gyro_p_rad_s=0.0,
        gyro_q_rad_s=0.0,
        altitude_agl_m=25.0,
        heading_rad=0.0,
        pitot_airspeed_ms=0.0,
        is_pitot_healthy=False
    )

    # Synthetic airspeed should stay near ~25 m/s despite pitot = 0!
    assert 22.0 < res_backup.synthetic_airspeed_ms < 28.0
