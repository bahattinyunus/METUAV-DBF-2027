#!/usr/bin/env python3
"""
Unit tests for Air Data Computer (ADC) & Synthetic Aerodynamic Angle / Wind Estimator.
"""

import math
import pytest

from aviyonik_ve_otonom.src.ucus_kontrol.src.air_data_computer import AirDataComputer


def test_airspeed_and_altitude_calculations():
    adc = AirDataComputer()

    # Cruise condition: dynamic pressure = 367.7 Pa (corresponds to 24.5 m/s at sea level)
    ias, cas, tas, rho, q_dyn = adc.compute_airspeeds(
        differential_pressure_pa=367.7,
        static_pressure_pa=101325.0,
        ambient_temp_c=15.0
    )

    assert ias == pytest.approx(24.5, abs=0.1)
    assert tas == pytest.approx(24.5, abs=0.2)
    assert rho == pytest.approx(1.225, abs=0.01)

    # Standard altitude
    hp, hd = adc.compute_altitudes(static_pressure_pa=101325.0, ambient_temp_c=15.0)
    assert hp == pytest.approx(0.0, abs=1.0)
    assert hd == pytest.approx(0.0, abs=1.0)

    # 1000m altitude pressure ~ 89874 Pa
    hp_1k, _ = adc.compute_altitudes(static_pressure_pa=89874.0, ambient_temp_c=8.5)
    assert hp_1k == pytest.approx(1000.0, abs=5.0)


def test_synthetic_aoa_and_sideslip_estimation():
    adc = AirDataComputer(aircraft_mass_kg=24.85, wing_area_m2=0.7032)

    # Steady level cruise at 24.5 m/s, 1g load factor (accel_z = 0 m/s^2 body relative to gravity)
    # L = m * g = 24.85 * 9.80665 = 243.7 N
    # q = 0.5 * 1.225 * 24.5^2 = 367.7 Pa
    # CL = 243.7 / (367.7 * 0.7032) = 0.942
    # Alpha = (0.942 - 0.65) / 4.85 rad = 0.0602 rad = 3.45 deg
    aoa_deg, aos_deg = adc.estimate_synthetic_aerodynamic_angles(
        tas_ms=24.5,
        rho_kg_m3=1.225,
        accel_y_mps2=0.0,
        accel_z_mps2=0.0,
        roll_rad=0.0,
        pitch_rad=math.radians(3.5)
    )

    assert 2.5 < aoa_deg < 4.5, f"Estimated synthetic AoA ({aoa_deg:.2f} deg) must match trim lift condition"
    assert abs(aos_deg) < 0.5, "Sideslip must be near zero in symmetric flight"


def test_3d_wind_vector_resolution():
    adc = AirDataComputer()

    # Aircraft heading North (yaw = 0) with TAS = 25 m/s
    # Wind is pure headwind from North at 5 m/s (Ground speed = 20 m/s)
    w_speed, w_dir, headwind, crosswind = adc.resolve_wind_vector(
        ground_vel_ned_ms=(20.0, 0.0, 0.0),
        tas_ms=25.0,
        roll_rad=0.0,
        pitch_rad=0.0,
        yaw_rad=0.0
    )

    assert w_speed == pytest.approx(5.0, abs=0.1)
    assert w_dir == pytest.approx(0.0, abs=2.0)  # Wind blowing from 0 deg North
    assert headwind == pytest.approx(5.0, abs=0.1)
    assert abs(crosswind) < 0.1
