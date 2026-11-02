import pytest
import math
from aviyonik_ve_otonom.src.ucus_kontrol.src.pylon_path_planner import PylonPathPlanner

def test_pylon_turn_radius_and_g_load():
    planner = PylonPathPlanner(nominal_airspeed_ms=24.5, max_bank_angle_deg=45.0)
    radius = planner.calculate_turn_radius(math.radians(45.0))
    # At 24.5 m/s and 45 deg bank: R = V^2 / (g * tan(45)) = 600.25 / 9.80665 ~ 61.2 m
    assert 55.0 < radius < 68.0

def test_wind_crab_correction():
    planner = PylonPathPlanner(nominal_airspeed_ms=25.0)
    # Wind from 90 deg (East, pure crosswind for a Northbound track)
    wca, vg = planner.calculate_wind_correction(
        desired_track_rad=0.0,
        wind_speed_ms=5.0,
        wind_dir_from_rad=math.radians(90.0)
    )
    # Crab angle must point into the wind (towards East, positive WCA)
    assert wca > 0.0
    assert math.degrees(abs(wca)) < 20.0
    assert vg > 0.0

def test_lap_waypoint_generation():
    planner = PylonPathPlanner(
        pylon_north_pos=(150.0, 0.0),
        pylon_south_pos=(-150.0, 0.0),
        nominal_airspeed_ms=24.5,
        max_bank_angle_deg=50.0
    )
    waypoints, perf = planner.generate_lap_waypoints(wind_speed_ms=4.0, wind_dir_deg=30.0)
    
    assert len(waypoints) > 20
    assert perf.total_distance_m > 600.0  # Straight legs (300m * 2) + turn arcs
    assert 20.0 < perf.lap_time_s < 70.0
    assert perf.max_g_load < 2.5
    assert perf.energy_consumed_wh_est > 1.0
