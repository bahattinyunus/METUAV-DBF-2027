#!/usr/bin/env python3
"""
Unit tests for Aeroelastic Stability, Trim & Control Reversal Analyzer.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from flight_stability_and_trim import FlightStabilityAndTrimAnalyzer


def test_neutral_point_and_downwash():
    analyzer = FlightStabilityAndTrimAnalyzer()
    x_np = analyzer.compute_neutral_point()

    # Neutral point of the wing-tail combination must be behind wing aerodynamic center (~24% MAC)
    assert 48.0 < x_np < 62.0, f"Neutral point ({x_np:.1f}% MAC) must be in realistic tail-backed range"
    assert 0.25 < analyzer.d_eps_d_alpha < 0.45, "Downwash gradient must be physically consistent"


def test_dbf_mission_stages_stability():
    analyzer = FlightStabilityAndTrimAnalyzer()
    stages = analyzer.analyze_dbf_mission_stages()

    # Verify all 4 DBF mission loading conditions maintain positive static margin
    for stage_name, data in stages.items():
        stab = data["stability"]
        assert stab.is_statically_stable is True
        assert stab.static_margin_pct >= 5.0, f"Stage {stage_name} must have >= 5% static margin"
        assert stab.cm_alpha_per_rad < -0.30, f"Stage {stage_name} must have restoring pitch stiffness"

        # Verify trim equilibrium at cruise (24.5 m/s)
        trim_cruise = data["trim_cruise_24ms"]
        assert not trim_cruise.is_elevator_saturated
        assert -15.0 < trim_cruise.delta_e_trim_deg < 15.0
        assert -3.0 < trim_cruise.alpha_trim_deg < 8.0


def test_aeroelastic_aileron_reversal_margin():
    analyzer = FlightStabilityAndTrimAnalyzer()

    # High-modulus carbon fiber spar box (GJ = 4850 N*m^2)
    carbon_margin = analyzer.compute_aileron_reversal(torsional_stiffness_gj_nm2=4850.0, dive_speed_ms=35.0)
    assert carbon_margin.is_aeroelastically_safe is True
    assert carbon_margin.reversal_safety_factor > 2.0
    assert carbon_margin.aileron_reversal_speed_ms > 35.0 * 1.35

    # Baseline lightweight structure (GJ = 150 N*m^2)
    balsa_margin = analyzer.compute_aileron_reversal(torsional_stiffness_gj_nm2=150.0, dive_speed_ms=35.0)
    assert balsa_margin.is_aeroelastically_safe is True
    assert balsa_margin.reversal_safety_factor >= 1.35


def test_dutch_roll_dynamic_damping():
    analyzer = FlightStabilityAndTrimAnalyzer()
    res = analyzer.evaluate_dutch_roll_damping(airspeed_ms=24.5)

    assert res["meets_mil_spec"] is True
    assert res["damping_ratio_zeta"] >= 0.08, "Dutch roll damping must satisfy MIL-F-8785C Level 1"
    assert 0.5 < res["frequency_hz"] < 2.0, "Natural frequency must be well within typical fixed-wing bandwidth"
