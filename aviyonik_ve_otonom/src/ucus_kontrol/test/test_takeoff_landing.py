#!/usr/bin/env python3
"""
Unit tests for Autonomous Takeoff, Flare & Rollout State Machine.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from takeoff_landing_controller import TakeoffLandingController, FlightPhase


def test_takeoff_state_transitions():
    """Verify transitions from PREFLIGHT to GROUND_ROLL, ROTATION, and CLIMB_OUT."""
    ctl = TakeoffLandingController()
    assert ctl.phase == FlightPhase.PREFLIGHT

    ctl.arm()
    assert ctl.phase == FlightPhase.GROUND_ROLL

    # Still below rotation speed
    res = ctl.update(airspeed_ms=10.0, altitude_m=0.0, vertical_speed_ms=0.0, x_position_m=20.0, wheel_weight_on_wheels=True)
    assert res["phase"] == "GROUND_ROLL"
    assert res["throttle"] == 1.0

    # Cross rotation speed
    res = ctl.update(airspeed_ms=14.0, altitude_m=0.0, vertical_speed_ms=0.0, x_position_m=35.0, wheel_weight_on_wheels=True)
    assert res["phase"] == "ROTATION"
    assert res["pitch_target_deg"] > 5.0

    # Liftoff detected
    res = ctl.update(airspeed_ms=16.0, altitude_m=1.0, vertical_speed_ms=2.0, x_position_m=42.0, wheel_weight_on_wheels=False)
    assert res["phase"] == "CLIMB_OUT"
    assert ctl.liftoff_x == 42.0
    assert res["takeoff_compliant"] is True


def test_landing_flare_and_rollout():
    """Verify transition into FLARE, touchdown detection, and wheel braking rollout."""
    ctl = TakeoffLandingController()
    ctl.phase = FlightPhase.APPROACH

    # Approach descent at 3m
    res = ctl.update(airspeed_ms=15.5, altitude_m=3.0, vertical_speed_ms=-1.0, x_position_m=500.0, wheel_weight_on_wheels=False)
    assert res["phase"] == "APPROACH"

    # Reach flare altitude (< 2.0 m)
    res = ctl.update(airspeed_ms=14.0, altitude_m=1.5, vertical_speed_ms=-0.6, x_position_m=530.0, wheel_weight_on_wheels=False)
    assert res["phase"] == "FLARE"
    assert res["throttle"] == 0.0
    assert res["pitch_target_deg"] >= 4.0

    # Touchdown
    res = ctl.update(airspeed_ms=12.0, altitude_m=0.1, vertical_speed_ms=-0.2, x_position_m=550.0, wheel_weight_on_wheels=True)
    assert res["phase"] == "ROLLOUT"
    assert res["wheel_brakes"] > 0.5


def test_ground_effect_physics():
    """Verify Wieselsberger ground effect multiplier decreases with lower h/b."""
    ctl = TakeoffLandingController(wing_span_m=2.40)

    sigma_high = ctl.compute_ground_effect_factor(altitude_m=10.0)
    sigma_mid = ctl.compute_ground_effect_factor(altitude_m=1.2)
    sigma_low = ctl.compute_ground_effect_factor(altitude_m=0.2)

    assert sigma_high > 0.95, "Out of ground effect factor is close to 1.0"
    assert sigma_low < sigma_mid < sigma_high, "Ground effect strictly reduces induced drag multiplier"
    assert sigma_low >= 0.15, "Lower bound enforced for physical stability"
