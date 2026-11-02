import pytest
import math
from itki_ve_guc_sistemleri.scripts.bemt_propeller_optimizer import BEMTPropellerOptimizer

def test_bemt_static_thrust():
    opt = BEMTPropellerOptimizer(diameter_in=19.0, pitch_in=12.0)
    # At zero flight speed (static condition), thrust must be positive and significant
    res = opt.analyze_advance_ratio(rpm=6800.0, v_flight_ms=0.0)
    assert res["thrust_n"] > 50.0
    assert res["thrust_kgf"] > 5.0
    assert res["torque_nm"] > 0.5
    assert res["power_w"] > 500.0
    assert res["efficiency_eta"] == 0.0  # Efficiency is zero at zero velocity

def test_bemt_cruise_efficiency():
    opt = BEMTPropellerOptimizer(diameter_in=19.0, pitch_in=12.0)
    # At cruise condition: 24.5 m/s, 6800 RPM
    res = opt.analyze_advance_ratio(rpm=6800.0, v_flight_ms=24.5)
    assert res["thrust_n"] > 10.0
    assert 0.5 < res["efficiency_eta"] < 0.90
    assert res["advance_ratio_J"] > 0.3

def test_bemt_blade_count_scaling():
    opt2 = BEMTPropellerOptimizer(diameter_in=18.0, pitch_in=10.0, num_blades=2)
    opt3 = BEMTPropellerOptimizer(diameter_in=18.0, pitch_in=10.0, num_blades=3)
    res2 = opt2.analyze_advance_ratio(rpm=6000.0, v_flight_ms=15.0)
    res3 = opt3.analyze_advance_ratio(rpm=6000.0, v_flight_ms=15.0)
    # 3-blade propeller produces more thrust and absorbs more torque
    assert res3["thrust_n"] > res2["thrust_n"]
    assert res3["torque_nm"] > res2["torque_nm"]
