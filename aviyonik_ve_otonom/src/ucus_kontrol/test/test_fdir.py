#!/usr/bin/env python3
"""
Unit tests for Sensor Failure Detection, Isolation and Recovery (FDIR) Manager.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from fdir_manager import FDIRManager, FDIRStatus


def test_fdir_nominal():
    fdir = FDIRManager()
    diag = fdir.evaluate_system_health(
        pitot_airspeed=24.5, gps_ground_speed=24.0,
        baro_alt=25.0, gps_alt=25.0,
        battery_voltage=24.6, current_a=30.0,
        pos_north=0.0, pos_east=0.0, altitude_agl=25.0
    )
    assert diag["status"] == "NOMINAL"
    assert diag["recommended_action"] == "CONTINUE_MISSION"
    assert diag["pitot_healthy"] is True


def test_fdir_pitot_blockage_debounce():
    fdir = FDIRManager()
    # 4 bad samples should still be within debounce window
    for _ in range(4):
        diag = fdir.evaluate_system_health(
            pitot_airspeed=0.0, gps_ground_speed=24.0,
            baro_alt=25.0, gps_alt=25.0,
            battery_voltage=24.6, current_a=30.0,
            pos_north=0.0, pos_east=0.0, altitude_agl=25.0
        )
    assert diag["status"] == "NOMINAL"

    # 5th bad sample trips into DEGRADED with fallback synthetic airspeed
    diag = fdir.evaluate_system_health(
        pitot_airspeed=0.0, gps_ground_speed=24.0,
        baro_alt=25.0, gps_alt=25.0,
        battery_voltage=24.6, current_a=30.0,
        pos_north=0.0, pos_east=0.0, altitude_agl=25.0
    )
    assert diag["status"] == "DEGRADED"
    assert diag["pitot_healthy"] is False
    assert diag["reliable_airspeed_ms"] == 24.0


def test_fdir_battery_critical_cutoff():
    fdir = FDIRManager()
    # Voltage dropping below 3.30V/cell (19.8V for 6S)
    diag = fdir.evaluate_system_health(
        pitot_airspeed=24.0, gps_ground_speed=24.0,
        baro_alt=25.0, gps_alt=25.0,
        battery_voltage=19.5, current_a=60.0,  # 3.25V/cell
        pos_north=0.0, pos_east=0.0, altitude_agl=25.0
    )
    assert diag["status"] == "CRITICAL"
    assert diag["recommended_action"] == "FAILSAFE_EMERGENCY_LAND"
    assert diag["battery_healthy"] is False


def test_fdir_geofence_breach():
    fdir = FDIRManager(geofence_half_width_m=500.0)
    diag = fdir.evaluate_system_health(
        pitot_airspeed=24.0, gps_ground_speed=24.0,
        baro_alt=25.0, gps_alt=25.0,
        battery_voltage=24.6, current_a=30.0,
        pos_north=520.0, pos_east=0.0, altitude_agl=25.0  # Outside bounds
    )
    assert diag["status"] == "CRITICAL"
    assert diag["recommended_action"] == "FAILSAFE_IMMEDIATE_RTL"
    assert diag["geofence_compliant"] is False
