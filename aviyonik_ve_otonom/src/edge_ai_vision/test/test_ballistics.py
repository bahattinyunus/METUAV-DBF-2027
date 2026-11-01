import pytest
import math
from edge_ai_vision.drop_ballistics_computer import BallisticsSolver
from edge_ai_vision.target_detector_node import GroundProjector

def test_ballistics_free_fall_time():
    """Verify that in zero drag limit, fall time approaches sqrt(2h/g)."""
    solver = BallisticsSolver(payload_mass_kg=100.0, drag_coefficient=0.0001, frontal_area_m2=0.001)
    altitude = 20.0
    impact_x, impact_y, t_fall = solver.compute_trajectory(altitude_m=altitude, ground_speed_x=0.0)

    expected_vacuum_time = math.sqrt(2.0 * altitude / 9.80665)
    assert abs(t_fall - expected_vacuum_time) < 0.05
    assert abs(impact_x) < 0.01
    assert abs(impact_y) < 0.01

def test_ballistics_forward_travel():
    """Verify forward distance with typical DBF parameters."""
    solver = BallisticsSolver(payload_mass_kg=2.5, drag_coefficient=0.45, frontal_area_m2=0.018)
    altitude = 25.0
    speed_x = 22.0
    impact_x, _, t_fall = solver.compute_trajectory(altitude_m=altitude, ground_speed_x=speed_x)

    # Ballistic forward throw should be between 35m and 55m for 22 m/s and 25m alt
    assert 35.0 < impact_x < 55.0
    assert 2.0 < t_fall < 2.5

def test_release_trigger_accuracy():
    """Verify release decision is within target tolerance."""
    solver = BallisticsSolver(payload_mass_kg=2.5, drag_coefficient=0.45, frontal_area_m2=0.018)
    impact_x, _, _ = solver.compute_trajectory(altitude_m=25.0, ground_speed_x=22.0)

    # Target is exactly where payload lands
    should_release, error = solver.should_release(target_dist_x=impact_x, target_dist_y=0.0,
                                                 altitude_m=25.0, ground_speed_x=22.0, tolerance_m=1.0)
    assert should_release is True
    assert error < 0.1

    # Far target should not trigger
    should_release_far, _ = solver.should_release(target_dist_x=impact_x + 10.0, target_dist_y=0.0,
                                                  altitude_m=25.0, ground_speed_x=22.0, tolerance_m=1.0)
    assert should_release_far is False

def test_ground_projector():
    """Verify camera ground projection at nadir."""
    proj = GroundProjector(fx=500.0, fy=500.0, cx=320.0, cy=240.0)
    dx, dy = proj.pixel_to_ground(u=320.0, v=240.0, altitude_m=30.0)
    assert abs(dx) < 1e-4
    assert abs(dy) < 1e-4
