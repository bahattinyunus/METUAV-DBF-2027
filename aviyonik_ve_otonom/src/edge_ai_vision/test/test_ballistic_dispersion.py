#!/usr/bin/env python3
"""
Unit tests for Mission 3 Aero-Ballistic Dispersion & Dynamic Sightline Optimizer.
"""

import math
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ballistic_dispersion_optimizer import BallisticDispersionOptimizer


def test_nominal_lead_and_sightline_cue():
    opt = BallisticDispersionOptimizer(payload_mass_kg=11.20)

    cue = opt.compute_dynamic_sightline_cue(
        airspeed_ms=24.5,
        altitude_m=25.0,
        headwind_ms=2.0
    )

    # Freefall time from 25m: t ~ sqrt(2*h/g) = sqrt(50/9.81) ~ 2.25s
    assert 2.10 <= cue.fall_time_s <= 2.45
    # Lead distance: (24.5 - 2.0) * 2.25 ~ 50.6m
    assert 45.0 <= cue.lead_distance_m <= 55.0
    # Sightline depression angle: atan(25 / 50) ~ 26.5 deg
    assert 20.0 <= cue.sightline_depression_deg <= 32.0


def test_monte_carlo_dispersion_with_wind_compensation():
    opt = BallisticDispersionOptimizer()

    mc = opt.run_monte_carlo_dispersion(
        n_runs=300,
        nominal_airspeed_ms=24.5,
        nominal_altitude_m=25.0,
        headwind_mean_ms=2.0,
        enable_wind_compensation=True
    )

    assert mc.total_runs == 300
    assert mc.cep_50_m < 1.50, "CEP-50 must be tighter than 1.50m with optical flow wind compensation"
    assert mc.cep_95_m < 3.50, "CEP-95 must stay safely bounded within competition outer circle"
    assert mc.bullseye_hit_rate_pct >= 50.0, "Majority of drops must fall within inner 1.20m bullseye"
    assert abs(mc.mean_cross_error_m) < 0.20, "Cross-track bias must be near zero"


def test_uncompensated_vs_compensated_performance():
    opt = BallisticDispersionOptimizer()

    mc_comp = opt.run_monte_carlo_dispersion(n_runs=200, enable_wind_compensation=True)
    mc_uncomp = opt.run_monte_carlo_dispersion(n_runs=200, enable_wind_compensation=False)

    # Compensated flight must achieve significantly lower dispersion and higher hit rate
    assert mc_comp.cep_50_m < mc_uncomp.cep_50_m
    assert mc_comp.bullseye_hit_rate_pct > mc_uncomp.bullseye_hit_rate_pct
