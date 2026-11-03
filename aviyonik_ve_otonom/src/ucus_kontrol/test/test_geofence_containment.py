#!/usr/bin/env python3
"""
Unit tests for 3D Geofence & Boundary Containment Manager.
"""

import math
import pytest

from aviyonik_ve_otonom.src.ucus_kontrol.src.geofence_containment_manager import (
    GeofenceContainmentManager,
    GeofenceStatus
)


def test_geofence_inside_nominal():
    mgr = GeofenceContainmentManager()

    # Center of competition airfield (North=150m, East=100m, Alt=30m AGL)
    res = mgr.evaluate_containment(
        pos_north_m=150.0,
        pos_east_m=100.0,
        altitude_agl_m=30.0,
        vel_north_ms=20.0,
        vel_east_ms=0.0
    )

    assert res.is_contained is True
    assert res.status == GeofenceStatus.INSIDE_SAFE
    assert res.distance_to_boundary_m > 50.0
    assert res.recommended_action == "CONTINUE_MISSION"


def test_predictive_breach_detection():
    mgr = GeofenceContainmentManager(time_to_breach_warning_s=4.0)

    # Aircraft at East=410m (East boundary at East=450m) flying East at 25 m/s
    # Time to breach = (450 - 410) / 25 = 1.6s (< 4.0s)
    res = mgr.evaluate_containment(
        pos_north_m=100.0,
        pos_east_m=420.0,
        altitude_agl_m=25.0,
        vel_north_ms=0.0,
        vel_east_ms=25.0
    )

    assert res.is_contained is True
    assert res.status == GeofenceStatus.PREDICTIVE_BREACH
    assert res.time_to_breach_s < 4.0
    assert res.recommended_action == "BANK_ESCAPE_TURN"
    # Escape heading should steer back westward
    assert 180.0 <= res.escape_heading_deg <= 360.0 or 0.0 <= res.escape_heading_deg <= 30.0


def test_altitude_floor_and_ceiling_violations():
    mgr = GeofenceContainmentManager(min_altitude_agl_m=10.0, max_altitude_agl_m=120.0)

    # Violation 1: Ground floor breach (Alt = 5.0m AGL)
    res_floor = mgr.evaluate_containment(
        pos_north_m=150.0,
        pos_east_m=100.0,
        altitude_agl_m=5.0,
        vel_north_ms=15.0,
        vel_east_ms=0.0
    )
    assert res_floor.is_contained is False
    assert res_floor.status == GeofenceStatus.ALTITUDE_FLOOR_VIOLATION
    assert "PULL_UP" in res_floor.recommended_action

    # Violation 2: Above 400ft FAA ceiling (Alt = 135.0m AGL)
    res_ceil = mgr.evaluate_containment(
        pos_north_m=150.0,
        pos_east_m=100.0,
        altitude_agl_m=135.0,
        vel_north_ms=15.0,
        vel_east_ms=0.0
    )
    assert res_ceil.is_contained is False
    assert res_ceil.status == GeofenceStatus.ALTITUDE_CEILING_VIOLATION
    assert "DESCEND" in res_ceil.recommended_action


def test_perimeter_breach_failsafe():
    mgr = GeofenceContainmentManager()

    # Aircraft way beyond boundary (East = 600m)
    res_breach = mgr.evaluate_containment(
        pos_north_m=100.0,
        pos_east_m=650.0,
        altitude_agl_m=35.0,
        vel_north_ms=0.0,
        vel_east_ms=20.0
    )

    assert res_breach.is_contained is False
    assert res_breach.status == GeofenceStatus.BREACHED_FAILSAFE
    assert res_breach.recommended_action == "AUTONOMOUS_RTL_OR_TERMINATE"
