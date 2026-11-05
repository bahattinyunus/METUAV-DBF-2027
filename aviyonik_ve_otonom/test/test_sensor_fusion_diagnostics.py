#!/usr/bin/env python3
"""
Unit tests for Sensor Fusion Innovation & Fault Diagnostics Monitor.
"""

import pytest
import numpy as np
from aviyonik_ve_otonom.scripts.sensor_fusion_innovation_monitor import (
    SensorFaultThresholds,
    SensorFusionInnovationMonitor
)


def test_nis_1d_nominal_and_fault():
    mon = SensorFusionInnovationMonitor()
    # Nominal case: measurement close to prediction
    nis_nom, fault_nom = mon.compute_nis_1d(measurement=10.0, prediction=10.1, state_var=0.5, meas_var=0.5)
    assert not fault_nom
    assert nis_nom < mon.cfg.nis_chi2_threshold_1d

    # Glitch case: large discrepancy
    nis_glitch, fault_glitch = mon.compute_nis_1d(measurement=10.0, prediction=15.0, state_var=0.5, meas_var=0.5)
    assert fault_glitch
    assert nis_glitch > mon.cfg.nis_chi2_threshold_1d


def test_pitot_blockage_detection():
    mon = SensorFusionInnovationMonitor()
    # Clean pitot
    res_clean = mon.check_pitot_airspeed(pitot_airspeed_ms=25.0, groundspeed_ms=27.0, est_wind_ms=2.0)
    assert not res_clean["is_clogged"]

    # Blocked / iced pitot reading near 0 while aircraft flying at 25 m/s
    res_blocked = mon.check_pitot_airspeed(pitot_airspeed_ms=4.0, groundspeed_ms=25.0, est_wind_ms=0.0)
    assert res_blocked["is_clogged"]


def test_multivariate_gps_nis_and_lane_switch():
    mon = SensorFusionInnovationMonitor()
    assert mon.active_ekf_lane == 1

    # Induce 6 consecutive GPS anomalies to trigger lane failover
    for _ in range(6):
        mon.evaluate_sensor_sample(
            gps_pos=np.array([1000.0, 500.0, -100.0]), # Massive 900m glitch
            gps_pred=np.array([100.0, 50.0, -35.0]),
            baro_alt=35.0,
            baro_pred=35.0,
            pitot_aspd=25.0,
            groundspeed=25.0
        )

    assert mon.active_ekf_lane == 2
    assert len(mon.lane_switch_events) == 1
