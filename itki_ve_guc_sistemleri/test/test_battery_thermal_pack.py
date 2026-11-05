#!/usr/bin/env python3
"""
Unit tests for Battery Pack Thermal Optimizer & Cooling Duct Analysis.
"""

import pytest
from itki_ve_guc_sistemleri.scripts.battery_thermal_pack_optimizer import (
    BatteryPackConfig,
    CoolingDuctConfig,
    BatteryThermalOptimizer
)


def test_battery_internal_resistance():
    opt = BatteryThermalOptimizer()
    r_cold = opt.get_internal_resistance(15.0, 0.8)
    r_warm = opt.get_internal_resistance(35.0, 0.8)
    # Higher temp should lower internal resistance
    assert r_warm < r_cold

    # Low SOC penalty check
    r_low_soc = opt.get_internal_resistance(25.0, 0.05)
    r_full_soc = opt.get_internal_resistance(25.0, 0.90)
    assert r_low_soc > r_full_soc


def test_convection_coefficient_scaling():
    opt = BatteryThermalOptimizer()
    h_still = opt.compute_convection_coefficient(0.0)
    h_flight = opt.compute_convection_coefficient(25.0)
    assert h_still >= 8.0
    assert h_flight > h_still


def test_mission_thermal_simulation():
    opt = BatteryThermalOptimizer()
    res = opt.simulate_mission_flight()
    assert len(res["time_s"]) > 0
    # Core temp should rise during high-current flight
    assert res["max_core_temp_c"] > opt.pack.temp_ambient_c
    # Pack should not overheat beyond safety limit under forced cooling
    assert res["max_core_temp_c"] < 65.0
    # Remaining SOC should be positive and less than 100%
    assert 20.0 < res["remaining_soc_pct"] < 90.0


def test_duct_drag_penalty():
    opt = BatteryThermalOptimizer()
    drag = opt.compute_cooling_drag_penalty(airspeed_ms=28.0)
    assert 0.0 < drag < 2.0  # Duct drag should be minimal (typically < 1.0 N)
