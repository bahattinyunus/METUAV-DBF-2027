import pytest
from optimizasyon_ve_mdo.scripts.dbf_scoring_mdo import DBFScoringEngine, AircraftDesignVector

def test_mdo_baseline_validity():
    engine = DBFScoringEngine()
    baseline = AircraftDesignVector(
        wingspan_m=2.40,
        aspect_ratio=8.19,
        empty_mass_kg=12.70,
        payload_mass_kg=9.85,
        battery_capacity_mah=16000.0,
        cruise_speed_ms=24.5
    )
    res = engine.evaluate_mission_scores(baseline)
    assert res["status"] == "VALID"
    assert res["togw_lbs"] <= 55.0
    assert res["total_score"] > 8.0

def test_overweight_disqualification():
    engine = DBFScoringEngine()
    # Design exceeding 55 lbs TOGW limit
    heavy_design = AircraftDesignVector(
        wingspan_m=2.40,
        aspect_ratio=8.19,
        empty_mass_kg=18.0,
        payload_mass_kg=12.0,
        battery_capacity_mah=20000.0,
        cruise_speed_ms=24.5
    )
    res = engine.evaluate_mission_scores(heavy_design)
    assert res["status"] == "DQ_OVERWEIGHT"
    assert res["total_score"] == 0.0

def test_stall_margin_enforcement():
    engine = DBFScoringEngine()
    # Speed dangerously below stall speed
    slow_design = AircraftDesignVector(
        wingspan_m=2.40,
        aspect_ratio=8.19,
        empty_mass_kg=12.70,
        payload_mass_kg=9.85,
        battery_capacity_mah=16000.0,
        cruise_speed_ms=10.0  # V_stall is ~16.9 m/s
    )
    res = engine.evaluate_mission_scores(slow_design)
    assert res["status"] == "STALL_MARGIN_VIOLATION"
    assert res["total_score"] == 0.0
