#!/usr/bin/env python3
"""
Unit tests for Carbon Leaf Spring Landing Gear Dynamic Drop Simulator.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from landing_gear_drop_simulator import LandingGearDropSimulator


def test_landing_gear_nominal_touchdown():
    """Verify landing gear absorbs nominal 1.0 m/s sink rate without excessive load factor."""
    sim = LandingGearDropSimulator(aircraft_mass_kg=24.85)
    res = sim.simulate_touchdown(sink_rate_ms=1.0)

    assert res["peak_load_factor_g"] < 3.0, "Landing gear load factor must be under 3.0g for airframe safety"
    assert res["peak_load_factor_g"] > 1.2, "Contact must produce load factor above level static weight"
    assert res["max_deflection_mm"] < 60.0, "Deflection must not exceed spring geometry limit (60mm)"
    assert res["propeller_min_clearance_mm"] >= 50.0, "Propeller clearance must exceed 50mm safety floor"
    assert res["energy_absorbed_J"] > 10.0, "Energy absorbed must account for kinetic + gravity work"
    assert res["pass_g_limit"] is True
    assert res["pass_deflection_limit"] is True
    assert res["pass_prop_clearance"] is True


def test_landing_gear_hard_landing_survivability():
    """Verify landing gear response under extreme 1.3 m/s sink rate condition."""
    sim = LandingGearDropSimulator(aircraft_mass_kg=24.85)
    res = sim.simulate_touchdown(sink_rate_ms=1.3)

    # In a hard landing, gear will deflect more and peak G will increase, but must remain bounded
    assert res["peak_load_factor_g"] < 4.0, "Touchdown load must not exceed ultimate airframe structural envelope"
    assert res["max_deflection_mm"] <= 70.0, "Physical bottoming limit"
    assert res["propeller_min_clearance_mm"] > 40.0, "Propeller must not strike tarmac in hard landing"
