#!/usr/bin/env python3
"""
Unit tests for Multi-Lap Racing Trajectory & Energy Optimizer.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from lap_time_trajectory_optimizer import LapTimeTrajectoryOptimizer


def test_straight_and_turn_simulation():
    opt = LapTimeTrajectoryOptimizer()

    # Test straight sprint
    sector_str, v_exit = opt.simulate_straight_sector(
        "SPRINT", length_m=304.8, v_entry=20.0, target_speed=26.0
    )
    assert sector_str.duration_s > 0.0
    assert 20.0 <= v_exit <= 28.0
    assert sector_str.load_factor_g == 1.0
    assert sector_str.energy_consumed_mah > 0.0

    # Test high-g coordinated turn
    sector_turn, v_turn_exit = opt.simulate_pylon_turn(
        "PYLON_TURN", turn_angle_deg=180.0, v_entry=24.0, bank_angle_deg=45.0
    )
    assert sector_turn.load_factor_g == pytest.approx(1.414, rel=0.02)
    assert sector_turn.duration_s > 0.0
    assert sector_turn.energy_consumed_wh > 0.0


def test_multi_lap_mission_modes_comparison():
    opt = LapTimeTrajectoryOptimizer()

    res_fast = opt.optimize_multi_lap_mission(target_laps=3, racing_mode="AGGRESSIVE_RACING")
    res_endur = opt.optimize_multi_lap_mission(target_laps=3, racing_mode="MAX_ENDURANCE")

    # Fast mode must yield faster lap time
    assert res_fast["mean_lap_time_s"] < res_endur["mean_lap_time_s"]
    assert res_fast["total_mission_time_s"] < res_endur["total_mission_time_s"]

    # Endurance mode must consume less total energy
    assert res_endur["total_energy_consumed_mah"] < res_fast["total_energy_consumed_mah"]
    assert res_endur["final_battery_soc_pct"] > res_fast["final_battery_soc_pct"]

    # In 5 minutes (300 s), both must achieve at least 5 laps
    assert res_fast["max_laps_in_5min_window"] >= 6
    assert res_endur["max_laps_in_5min_window"] >= 6


def test_battery_depletion_and_load_factor_limits():
    opt = LapTimeTrajectoryOptimizer()
    res = opt.optimize_multi_lap_mission(target_laps=3, racing_mode="BALANCED")

    # Structural load factor must stay within safe DBF design envelope (< 2.8g)
    for lap in res["laps"]:
        assert lap.peak_g_load <= 2.50
        assert lap.battery_soc_pct > 80.0  # 3 laps consume < 20% capacity
        assert len(lap.sectors) == 4
