#!/usr/bin/env python3
"""
Unit tests for Ground Target Kalman Tracker and Ground Projector.
"""

import math
import numpy as np
import pytest
import sys
import os

# Add edge_ai_vision to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'edge_ai_vision')))

from target_tracker_filter import TargetKalmanTracker
from target_detector_node import GroundProjector


def test_tracker_initialization():
    tracker = TargetKalmanTracker()
    assert not tracker.initialized
    tracker.initialize(75.0, 30.0)
    assert tracker.initialized
    pos_x, pos_y, cert = tracker.get_target_position()
    assert abs(pos_x - 75.0) < 1e-4
    assert abs(pos_y - 30.0) < 1e-4
    assert cert > 0.0


def test_tracker_convergence_with_noise():
    tracker = TargetKalmanTracker(process_noise=0.01, measurement_noise=0.5)
    tracker.initialize(70.0, 0.0)

    # True target is at (75.0, 0.0)
    true_x, true_y = 75.0, 0.0
    np.random.seed(42)

    for _ in range(40):
        tracker.predict(0.05)
        noisy_x = true_x + np.random.normal(0, 0.3)
        noisy_y = true_y + np.random.normal(0, 0.3)
        tracker.update(noisy_x, noisy_y)

    est_x, est_y, _ = tracker.get_target_position()
    assert abs(est_x - true_x) < 0.25
    assert abs(est_y - true_y) < 0.25


def test_tracker_outlier_gating():
    tracker = TargetKalmanTracker()
    tracker.initialize(50.0, 10.0)

    for _ in range(10):
        tracker.predict(0.05)
        tracker.update(50.0, 10.0)

    # Wild outlier (100 meters away)
    tracker.predict(0.05)
    accepted = tracker.update(150.0, 110.0)
    assert not accepted, "Outlier should be rejected by Mahalanobis Chi-square gate"

    est_x, est_y, _ = tracker.get_target_position()
    assert abs(est_x - 50.0) < 1.0


def test_ground_projector_geometry():
    projector = GroundProjector(fx=381.3, fy=381.3, cx=320.0, cy=240.0)

    # Center pixel (320, 240) looking straight down at 25m alt -> dx=0, dy=0
    dx, dy = projector.pixel_to_ground(320.0, 240.0, altitude_m=25.0)
    assert abs(dx) < 1e-3
    assert abs(dy) < 1e-3

    # Pixel offset forward (v = 100 < cy=240)
    dx_fwd, dy_fwd = projector.pixel_to_ground(320.0, 100.0, altitude_m=25.0)
    assert dx_fwd > 0.0, "v < cy should correspond to forward ground distance"
    assert abs(dy_fwd) < 1e-3
