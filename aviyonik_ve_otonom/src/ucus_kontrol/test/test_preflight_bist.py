import numpy as np
import pytest
from aviyonik_ve_otonom.src.ucus_kontrol.src.preflight_bist_engine import PreFlightBISTEngine

def test_nominal_bist_pass():
    engine = PreFlightBISTEngine()
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
        payload_pin_v=3.30
    )

    assert cert.is_flight_authorized is True
    assert cert.failed_checks == 0
    assert cert.passed_checks == 6
    assert cert.flight_readiness_code == "METUAV-AIR-GO-2027"

def test_bist_rejection_on_servo_stall():
    engine = PreFlightBISTEngine()
    # High current 3.8A indicates a mechanically jammed elevator servo
    cert = engine.run_complete_preflight_bist(
        accel_z_samples=np.ones(50),
        gyro_norm_samples=np.zeros(50),
        pitot_samples=np.zeros(20),
        gps_sats=12,
        gps_hdop=0.90,
        servo_currents=np.array([1.1, 1.2, 3.8, 1.2, 1.3, 1.3, 1.0]),
        battery_voltage=24.8,
        cell_delta_v=0.01,
        payload_locked=True,
        payload_pin_v=3.30
    )

    assert cert.is_flight_authorized is False
    assert cert.failed_checks > 0
    assert cert.flight_readiness_code == "METUAV-ABORT-BIST-FAIL"
