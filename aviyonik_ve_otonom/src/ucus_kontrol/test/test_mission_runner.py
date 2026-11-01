#!/usr/bin/env python3
"""
Unit test for Full Mission SITL Runner Prototype.
"""

import sys
import os
import pytest

# Add scripts directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts')))

from full_mission_sitl_runner import FullMissionPrototype


def test_full_autonomous_mission_prototype():
    sim = FullMissionPrototype()
    summary = sim.run_mission()

    assert summary["status"] == "MISSION_SUCCESS"
    assert summary["laps_completed"] >= 2
    assert summary["payload_dropped"] is True
    assert summary["drop_error_distance_m"] < 1.20, "Drop miss distance must be within AIAA DBF 1.20m bullseye"
    assert summary["total_flight_time_sec"] < 300.0, "Total flight time must be within 5-minute limit"
    assert summary["final_battery_soc_pct"] > 20.0, "Reserve battery capacity must remain > 20%"
