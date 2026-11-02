import pytest
from aerodinamik.scripts.high_lift_ground_effect import HighLiftGroundEffectAnalyzer

def test_flap_aerodynamic_increment():
    analyzer = HighLiftGroundEffectAnalyzer()
    cl_clean, delta_cl_15, cd0_15 = analyzer.calculate_flap_aerodynamics(15.0)
    cl_clean2, delta_cl_30, cd0_30 = analyzer.calculate_flap_aerodynamics(30.0)

    assert delta_cl_15 > 0.20
    assert delta_cl_30 > delta_cl_15
    assert cd0_30 > cd0_15

def test_ground_effect_induced_drag_reduction():
    analyzer = HighLiftGroundEffectAnalyzer()
    # At h = 0.24m (h/b = 0.1), sigma must be very low (< 0.20)
    sigma_low = analyzer.calculate_ground_effect_factor(0.24)
    # At h = 24.0m (h/b = 10.0), sigma must approach 1.0 (free flight)
    sigma_high = analyzer.calculate_ground_effect_factor(24.0)

    assert sigma_low < 0.25
    assert sigma_high > 0.98

def test_ground_effect_takeoff_climb_polar():
    analyzer = HighLiftGroundEffectAnalyzer()
    polars = analyzer.analyze_takeoff_climb(flap_deg=15.0)

    # Near the ground (first entry), L/D must be higher than at altitude (last entry)
    # due to induced drag suppression
    assert polars[0].cl_over_cd > polars[-1].cl_over_cd
    assert polars[0].cd_induced < polars[-1].cd_induced
    assert polars[0].v_stall_ms < 17.5  # Heavy TOGW stall speed with flaps
