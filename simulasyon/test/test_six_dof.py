#!/usr/bin/env python3
"""
Unit tests for 6-DOF Nonlinear Flight Dynamics Simulator.
"""

import math
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from six_dof_flight_dynamics import Aircraft6DOF


def test_trim_solution_feasibility():
    uav = Aircraft6DOF(mass_kg=24.85)
    alpha_deg, de_deg, thr = uav.trim(target_airspeed=24.5)

    assert 1.0 < alpha_deg < 8.0, "Cruise alpha must be within realistic 1-8 deg range"
    assert -5.0 < de_deg < 5.0, "Elevator trim must be within small deflection range"
    assert 0.15 < thr < 0.60, "Level cruise throttle must have healthy thrust reserve"


def test_quaternion_euler_conversion():
    uav = Aircraft6DOF()
    # Test 30 deg pitch up
    p_rad = math.radians(30.0)
    q0 = math.cos(p_rad / 2.0)
    q2 = math.sin(p_rad / 2.0)
    r, p, y = uav.quat_to_euler(np.array([q0, 0.0, q2, 0.0]))

    assert abs(math.degrees(p) - 30.0) < 1e-3
    assert abs(math.degrees(r)) < 1e-3
    assert abs(math.degrees(y)) < 1e-3


def test_forces_at_equilibrium():
    uav = Aircraft6DOF(mass_kg=24.85)
    alpha_deg, de_deg, thr = uav.trim(target_airspeed=24.5)

    u0 = 24.5 * math.cos(math.radians(alpha_deg))
    w0 = 24.5 * math.sin(math.radians(alpha_deg))
    p_rad = math.radians(alpha_deg)
    q0 = math.cos(p_rad / 2.0)
    q2 = math.sin(p_rad / 2.0)

    uav.set_state(
        pos_ned=(0.0, 0.0, -25.0),
        vel_body=(u0, 0.0, w0),
        quat=(q0, 0.0, q2, 0.0),
        pqr=(0.0, 0.0, 0.0)
    )

    controls = (math.radians(de_deg), 0.0, 0.0, thr)
    forces, moments = uav.compute_forces_and_moments(uav.state, controls)

    # Net forces in equilibrium should be near zero relative to aircraft weight (244 N)
    weight = 24.85 * 9.80665
    assert abs(forces[0]) < 0.05 * weight, "Net Fx must be near zero at trim"
    assert abs(forces[2]) < 0.05 * weight, "Net Fz must be near zero at trim"
    assert abs(moments[1]) < 2.0, "Net pitching moment must be near zero at trim"
