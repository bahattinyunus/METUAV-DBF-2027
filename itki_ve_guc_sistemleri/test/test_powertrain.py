import pytest
from itki_ve_guc_sistemleri.scripts.powertrain_mission_simulator import PowertrainSystemMatcher

def test_powertrain_equilibrium_solve():
    matcher = PowertrainSystemMatcher()
    rpm, current, torque = matcher.solve_equilibrium_rpm(throttle=0.8, airspeed_ms=20.0, v_batt_est=22.2)
    assert 4000.0 < rpm < 8000.0
    assert 10.0 < current < 90.0
    assert torque > 0.3

def test_powertrain_mission_step():
    matcher = PowertrainSystemMatcher()
    pt = matcher.simulate_step(
        time_s=1.0,
        dt=0.1,
        throttle=0.7,
        airspeed_ms=22.0,
        current_motor_temp=32.0,
        current_batt_temp=32.0
    )
    assert pt.rpm > 3000.0
    assert pt.thrust_n > 10.0
    assert pt.voltage_v > 18.0
    assert pt.electric_power_w > 100.0
    assert pt.motor_efficiency > 0.60
    assert pt.motor_temp_c >= 32.0

def test_powertrain_flight_plan():
    matcher = PowertrainSystemMatcher()
    plan = [
        {"duration_s": 5.0, "throttle": 0.95, "airspeed_ms": 18.0},  # Takeoff
        {"duration_s": 10.0, "throttle": 0.60, "airspeed_ms": 24.5}, # Cruise
    ]
    results = matcher.run_mission_profile(plan, dt=1.0)
    assert len(results) == 15
    assert results[-1].soc_pct < 100.0
