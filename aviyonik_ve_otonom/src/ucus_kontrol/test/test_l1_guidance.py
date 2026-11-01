#!/usr/bin/env python3
"""
Unit tests for L1 Adaptive Nonlinear Guidance Law (NLGL) Path Follower.
"""

import math
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from l1_path_follower import L1PathFollower


def test_l1_lookahead_scaling():
    follower = L1PathFollower(damping_ratio=0.707, period_sec=12.0)
    l1_low = follower.compute_l1_distance(ground_speed=15.0)
    l1_high = follower.compute_l1_distance(ground_speed=30.0)

    assert l1_high > l1_low, "L1 distance must scale proportionally with ground speed"
    assert l1_low >= follower.min_l1


def test_straight_segment_cross_track_correction():
    follower = L1PathFollower()

    # Aircraft is 8m to the right (+East) of a North-bound path
    res = follower.track_straight_segment(
        p_aircraft=(100.0, 8.0),
        ground_velocity=(24.0, 0.0),
        p_segment_start=(0.0, 0.0),
        p_segment_end=(200.0, 0.0)
    )

    assert res["crosstrack_error_m"] == 8.0
    assert res["bank_angle_cmd_deg"] < 0.0, "Must command negative (left) bank to eliminate right error"
    assert abs(res["bank_angle_cmd_deg"]) <= 45.0, "Bank command must not exceed limit"


def test_orbit_guidance_centripetal():
    follower = L1PathFollower(max_bank_deg=45.0)

    # Aircraft on 30m circular radius
    res = follower.track_orbit(
        p_aircraft=(0.0, 30.0),
        ground_velocity=(-20.0, 0.0),
        center=(0.0, 0.0),
        radius=30.0,
        clockwise=True
    )

    assert abs(res["radial_error_m"]) < 1e-3
    assert res["bank_angle_cmd_deg"] > 0.0, "Must command positive (right) bank for clockwise turn"
