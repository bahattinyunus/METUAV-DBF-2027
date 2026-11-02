import pytest
from itki_ve_guc_sistemleri.scripts.motor_thermal_simulator import PropulsionThermalSimulator

def test_thermal_simulator_baseline():
    sim = PropulsionThermalSimulator()
    res = sim.simulate_mission_profile(total_time_sec=60.0, dt=0.5)
    
    # Check output keys and array sizes
    assert "time_sec" in res
    assert "t_motor_c" in res
    assert "t_batt_c" in res
    assert len(res["time_sec"]) == 120

    # Under high takeoff current, motor and battery should heat up
    assert res["t_motor_c"][-1] > sim.t_ambient
    assert res["t_batt_c"][-1] > sim.t_ambient

def test_thermal_limits_within_safe_margin():
    sim = PropulsionThermalSimulator()
    res = sim.simulate_mission_profile(total_time_sec=300.0, dt=0.2)
    
    max_motor_temp = max(res["t_motor_c"])
    max_batt_temp = max(res["t_batt_c"])

    # High performance brushless motor insulation class H is rated to 180°C.
    # Safe operating margin is below 110°C.
    assert max_motor_temp < 110.0
    # LiPo battery safe temperature limit is below 65°C.
    assert max_batt_temp < 60.0
