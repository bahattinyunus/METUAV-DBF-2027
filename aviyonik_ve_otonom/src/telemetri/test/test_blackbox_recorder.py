import os
import tempfile
import pytest
from aviyonik_ve_otonom.src.telemetri.flight_blackbox_recorder import FlightBlackboxRecorder, BlackboxFrame

def test_blackbox_recorder_flow():
    recorder = FlightBlackboxRecorder()
    recorder.start_recording()

    # Record 50 frames (1 second at 50Hz)
    for i in range(50):
        t = i * 0.02
        frame = BlackboxFrame(
            timestamp_s=t,
            airspeed_ms=24.5,
            altitude_m=25.0 + t * 0.5,
            roll_deg=2.0,
            pitch_deg=1.5,
            yaw_deg=45.0,
            accel_x_g=0.02,
            accel_y_g=0.01,
            accel_z_g=1.05,
            gyro_p_deg_s=0.1,
            gyro_q_deg_s=-0.05,
            gyro_r_deg_s=0.02,
            voltage_v=24.2 - t * 0.01,
            current_a=32.5,
            motor_temp_c=45.0 + t * 0.1,
            servo_pwm_us=[1500, 1500, 1500, 1500, 1520, 1520, 1500],
            fdir_flags=0
        )
        recorder.record_frame(frame)

    recorder.stop_recording()
    diag = recorder.analyze_flight_diagnostics()

    assert diag.frame_count == 50
    assert 45.0 < diag.mean_sample_rate_hz < 55.0
    assert diag.vibration_rms_g < 0.20
    assert diag.clipping_event_count == 0
    assert diag.is_airframe_healthy is True

def test_blackbox_json_persistence():
    recorder = FlightBlackboxRecorder()
    recorder.start_recording()
    recorder.record_frame(BlackboxFrame(
        timestamp_s=0.0, airspeed_ms=20.0, altitude_m=10.0,
        roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0,
        accel_x_g=0.0, accel_y_g=0.0, accel_z_g=1.0,
        gyro_p_deg_s=0.0, gyro_q_deg_s=0.0, gyro_r_deg_s=0.0,
        voltage_v=25.0, current_a=10.0, motor_temp_c=30.0,
        servo_pwm_us=[1500]*7, fdir_flags=0
    ))
    recorder.stop_recording()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "flight_log.json")
        recorder.save_to_json(out_path)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 100
