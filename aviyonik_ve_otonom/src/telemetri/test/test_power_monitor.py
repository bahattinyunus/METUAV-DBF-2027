#!/usr/bin/env python3
"""
Unit tests for Avionics Power Monitor & CAN-Bus Telemetry Watchdog.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'telemetri')))

from avionics_power_monitor import AvionicsPowerMonitor


def test_rail_voltage_evaluation():
    """Verify detection of nominal voltages and brownout alert triggering."""
    mon = AvionicsPowerMonitor()

    # Nominal rail condition
    res_nom = mon.evaluate_rails(v_5v_rail=5.04, v_12v_rail=12.02, v_servo_rail=6.01)
    assert res_nom["status_5v"] == "HEALTHY"
    assert res_nom["status_12v"] == "HEALTHY"
    assert res_nom["status_servo"] == "HEALTHY"
    assert res_nom["brownout_alert"] is False

    # Brownout condition (5V rail drops to 4.65V)
    res_drop = mon.evaluate_rails(v_5v_rail=4.65, v_12v_rail=12.00, v_servo_rail=5.90)
    assert res_drop["status_5v"] == "CRITICAL"
    assert res_drop["brownout_alert"] is True


def test_servo_stall_detection():
    """Verify detection and debouncing of stalled servo channel."""
    mon = AvionicsPowerMonitor()

    # Single pulse below debounce counter
    res1 = mon.process_servo_telemetry({1: 0.3, 2: 3.8, 3: 0.2})
    assert res1["servo_fault_alert"] is False

    # Sustained over-current for 5 consecutive samples
    for _ in range(5):
        res_sustained = mon.process_servo_telemetry({1: 0.3, 2: 3.8, 3: 0.2})

    assert res_sustained["servo_fault_alert"] is True
    assert 2 in res_sustained["stalled_channels"]

    # Short circuit instantaneous detection
    res_short = mon.process_servo_telemetry({4: 6.5})
    assert 4 in res_short["short_circuit_channels"]
    assert res_short["servo_fault_alert"] is True


def test_can_bus_health_and_endurance():
    """Verify CAN-bus health score and flight endurance estimation."""
    mon = AvionicsPowerMonitor()

    # 100 clean frames
    for _ in range(100):
        mon.record_can_frame(True)

    can_res = mon.get_can_bus_health()
    assert can_res["error_rate"] == 0.0
    assert can_res["bus_health_pct"] == 100.0
    assert can_res["bus_nominal"] is True

    # Endurance calculation
    # 16,000 mAh battery, 80% SoC, 35A draw
    endurance_sec = mon.estimate_flight_endurance_sec(
        battery_soc_pct=80.0,
        battery_capacity_mah=16000.0,
        current_draw_a=35.0
    )
    assert 900.0 < endurance_sec < 1400.0, "Endurance should be around 18-20 minutes"
