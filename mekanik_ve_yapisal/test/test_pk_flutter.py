#!/usr/bin/env python3
"""
Unit tests for the Aeroelastic PK-Method Flutter and Divergence Solver.
"""

import pytest
import numpy as np
from mekanik_ve_yapisal.scripts.aeroelastic_pk_flutter_solver import (
    WingStructuralParams,
    AeroelasticPKSolver
)


def test_theodorsen_function_limits():
    solver = AeroelasticPKSolver()
    # At very high k -> C(k) approaches 0.5
    c_high = solver.theodorsen_function(100.0)
    assert 0.45 <= c_high.real <= 0.60
    # At very low k -> C(k) approaches 1.0
    c_low = solver.theodorsen_function(0.001)
    assert 0.90 <= c_low.real <= 1.05


def test_pk_solver_zero_velocity():
    solver = AeroelasticPKSolver()
    f1, z1, f2, z2 = solver.solve_flutter_at_airspeed(0.0)
    assert abs(f1 - solver.p.bending_freq_hz) < 0.1
    assert abs(f2 - solver.p.torsion_freq_hz) < 0.1
    assert z1 > 0.0
    assert z2 > 0.0


def test_static_divergence_speed():
    solver = AeroelasticPKSolver()
    v_div = solver.calculate_static_divergence_speed()
    # Divergence speed should be comfortably higher than dive speed (33.1 m/s)
    assert v_div > 50.0


def test_scan_airspeed_range():
    solver = AeroelasticPKSolver()
    res = solver.scan_airspeed_range(v_max=40.0, n_pts=20)
    assert len(res["v_arr"]) == 20
    assert len(res["f_bending"]) == 20
    assert len(res["z_bending"]) == 20
    assert res["divergence_speed_ms"] > 0
    assert res["flutter_speed_ms"] > 33.1  # Flight envelope safe margin
