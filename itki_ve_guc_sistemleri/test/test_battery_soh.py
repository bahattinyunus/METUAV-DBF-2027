#!/usr/bin/env python3
"""
Unit tests for 6S LiPo Dual-RC Thevenin Battery SOH Model.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from battery_soh_estimator import BatteryTheveninModel


def test_battery_ocv_range():
    battery = BatteryTheveninModel()
    ocv_full = battery.get_ocv(1.0)
    ocv_empty = battery.get_ocv(0.0)

    assert 25.0 < ocv_full <= 25.3, "Full 6S pack OCV must be ~25.2V"
    assert 20.0 < ocv_empty < 21.0, "Empty 6S pack OCV must be ~20.7V"


def test_voltage_sag_under_takeoff_current():
    battery = BatteryTheveninModel()
    res = battery.update(current_amps=82.0, dt=1.0)

    # Voltage drop = I * R0 + v1 + v2
    assert res["terminal_voltage_v"] < res["ocv_v"]
    assert res["predicted_min_cell_v"] > 3.30, "Under max 85A pulse, cell must stay above 3.30V"
    assert res["safe_margin_over_cutoff_v"] > 2.0, "Must have > 2.0V margin over 19.8V cutoff"


def test_soh_degradation():
    # Degraded battery with doubled internal resistance
    battery = BatteryTheveninModel(r0_ohm=0.0144)
    res = battery.update(current_amps=10.0, dt=1.0)

    assert res["soh_pct"] < 50.0, "Doubled R0 should reflect degraded SOH"
