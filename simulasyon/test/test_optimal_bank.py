import pytest
from simulasyon.scripts.pylon_racing_optimal_bank import PylonRacingOptimalBank, RacingCondition


def test_turn_profile_evaluation():
    solver = PylonRacingOptimalBank()
    prof45 = solver.evaluate_turn_profile(bank_angle_deg=45.0)

    assert prof45["load_factor_g"] == pytest.approx(1.414, abs=0.01)
    assert 50.0 < prof45["turn_radius_m"] < 80.0
    assert prof45["turn_time_s"] > 4.0
    assert prof45["mah_drain"] > 0.0


def test_pareto_bank_angles():
    solver = PylonRacingOptimalBank()
    res = solver.find_pareto_optimal_bank()

    # Higher bank gives faster turn
    assert res["fastest_bank_deg"] > res["min_energy_bank_deg"]
    assert res["fastest_time_s"] <= res["balanced_time_s"]
