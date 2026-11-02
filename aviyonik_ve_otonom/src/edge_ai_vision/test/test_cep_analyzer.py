import pytest
from aviyonik_ve_otonom.src.edge_ai_vision.cep_monte_carlo_analyzer import CEPMonteCarloAnalyzer

def test_single_drop_trajectory():
    analyzer = CEPMonteCarloAnalyzer(payload_mass_kg=2.5, nominal_altitude_m=25.0)
    pt = analyzer.simulate_single_drop(
        wind_gust_x=0.0,
        wind_gust_y=0.0,
        servo_delay_s=0.05,
        tracking_noise_x=0.0,
        tracking_noise_y=0.0
    )
    # Under exact nominal conditions, radial error should be virtually zero
    assert 2.0 < pt.fall_time_s < 2.5
    assert pt.radial_error_m < 0.10
    assert pt.impact_velocity_ms > 20.0

def test_monte_carlo_cep_accuracy():
    analyzer = CEPMonteCarloAnalyzer(target_radius_m=2.0)
    report = analyzer.run_monte_carlo(num_runs=300, seed=123)

    assert report.total_runs == 300
    # CEP-50 under turbulent wind should be under 1.20 meters
    assert report.cep_50_m < 1.20
    # CEP-95 should be under 2.50 meters
    assert report.cep_95_m < 2.50
    # Hit rate into 2.0m target circle should exceed 85%
    assert report.target_hit_rate_pct > 85.0
