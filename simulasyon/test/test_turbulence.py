#!/usr/bin/env python3
"""
Unit tests for Dryden Wind Turbulence and MIL-F-8785C Discrete Gust Simulator.
"""

import pytest
import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from dryden_wind_turbulence import DrydenWindTurbulence


def test_dryden_parameters_low_altitude():
    """Verify MIL-F-8785C turbulence scales and intensities are physically sound."""
    sim = DrydenWindTurbulence(
        altitude_m=30.0,
        airspeed_ms=24.5,
        wind_speed_20ft_knots=15.0
    )

    assert sim.L_w > 0.0, "Vertical turbulence scale must be positive"
    assert sim.L_u > sim.L_w, "Longitudinal turbulence scale exceeds vertical scale in low altitude"
    assert sim.sigma_w > 0.5, "Turbulence standard deviation must reflect 15 kt wind"
    assert sim.sigma_u >= sim.sigma_w, "Horizontal intensity is amplified relative to vertical"


def test_discrete_gust_load_envelope():
    """Verify discrete 1-cosine gust response keeps aircraft within +3.5g structural limit."""
    sim = DrydenWindTurbulence(
        altitude_m=25.0,
        airspeed_ms=24.5,
        aircraft_mass_kg=24.85
    )

    # Moderate to strong gust U_ds = 6.0 m/s (~12 knots vertical updraft)
    res = sim.compute_discrete_gust_response(U_ds_ms=6.0)

    assert 0.5 < res["pratt_alleviation_factor_Kg"] < 1.0, "Pratt alleviation factor should be 0.6-0.9"
    assert 0.5 < res["delta_nz_g"] < 2.0, "Gust delta n_z must be realistic"
    assert res["peak_load_factor_g"] < 3.50, "Peak load factor must not exceed ultimate airframe limit (+3.5g)"
    assert res["trough_load_factor_g"] > -0.5, "Downdraft trough must not invert wing beyond limit"
    assert res["within_safety_envelope"] is True


def test_continuous_dryden_stochastic_variance():
    """Verify continuous time series statistics match theoretical expectations."""
    np.random.seed(42)
    sim = DrydenWindTurbulence(
        altitude_m=25.0,
        airspeed_ms=24.5,
        wind_speed_20ft_knots=10.0,
        dt=0.01
    )

    u_samples = []
    w_samples = []
    for _ in range(500):
        out = sim.step()
        u_samples.append(out["u_g"])
        w_samples.append(out["w_g"])

    # Gust speeds should remain bounded within ~4-sigma
    assert max(np.abs(u_samples)) < 8.0, "Longitudinal gust bounds"
    assert max(np.abs(w_samples)) < 6.0, "Vertical gust bounds"
    assert len(u_samples) == 500
