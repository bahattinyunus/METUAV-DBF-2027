import pytest
from uretim_ve_test.scripts.composite_cure_cycle_simulator import CompositeCureSimulator

def test_composite_cure_kinetics():
    sim = CompositeCureSimulator(part_thickness_mm=2.5)
    history, report = sim.simulate_two_step_cure(
        ramp1_rate_c_min=2.0,
        dwell1_temp_c=60.0,
        dwell1_time_min=30.0,
        ramp2_rate_c_min=2.0,
        dwell2_temp_c=100.0,
        dwell2_time_min=60.0,
        dt_sec=5.0
    )

    # Final cure degree should exceed 90% (fully vitrified thermoset)
    assert report.final_cure_degree >= 0.90
    assert report.is_fully_cured is True
    # Gelation should occur during the cycle
    assert report.gelation_time_min > 0.0
    assert report.min_viscosity_pa_s < 1.0  # Liquid resin flows well into carbon fabric
    assert len(history) > 20

def test_exotherm_safety_envelope():
    sim = CompositeCureSimulator(part_thickness_mm=2.5)
    _, report = sim.simulate_two_step_cure(
        ramp1_rate_c_min=2.0,
        dwell1_temp_c=60.0,
        dwell1_time_min=30.0,
        ramp2_rate_c_min=2.0,
        dwell2_temp_c=100.0,
        dwell2_time_min=60.0,
        dt_sec=5.0
    )
    # Exothermic temperature spike must not exceed resin thermal degradation limit (160°C)
    assert report.peak_part_temp_c < 140.0
    assert report.max_exotherm_delta_c < 30.0
