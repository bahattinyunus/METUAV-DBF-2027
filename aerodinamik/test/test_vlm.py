#!/usr/bin/env python3
"""
Unit tests for 3D Lifting-Line Aerodynamics & Stability Solver.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from vlm_aerodynamics_solver import VLMAerodynamicsSolver


def test_vlm_lift_and_induced_drag():
    solver = VLMAerodynamicsSolver()
    res = solver.solve_wing_circulation(alpha_deg=4.0, airspeed_ms=24.5)

    assert 0.5 < res["CL_3D"] < 1.2, "Cruise CL must be in realistic 0.5 - 1.2 range"
    assert 0.01 < res["CDi"] < 0.05, "Induced drag must be positive and bounded"
    assert 0.80 <= res["oswald_efficiency_e"] <= 0.95, "Planform efficiency must be ~0.88"


def test_longitudinal_static_stability():
    solver = VLMAerodynamicsSolver()
    stab = solver.compute_stability_and_neutral_point(cg_percent_mac=27.0)

    assert stab["CL_alpha_wing_per_rad"] > 4.0, "3D wing lift slope must be realistic (~4.8 /rad)"
    assert 0.10 < stab["d_eps_d_alpha"] < 0.40, "Downwash gradient must be between 0.10 and 0.40"
    assert stab["neutral_point_pct_mac"] > stab["cg_pct_mac"], "Neutral point must be aft of CG for stability"
    assert stab["static_margin_pct"] > 5.0, "Positive static margin required"
