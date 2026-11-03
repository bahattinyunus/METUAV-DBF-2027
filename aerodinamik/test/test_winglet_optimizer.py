import pytest
from aerodinamik.scripts.winglet_aero_optimizer import (
    WingletAeroOptimizer,
    WingletOptimizationResult,
    VortexProfileResult
)

def test_winglet_ar_effective_and_induced_drag_reduction():
    opt = WingletAeroOptimizer(wing_span_m=2.40, wing_area_m2=0.816, design_cl=0.65)
    res = opt.evaluate_winglet_performance(winglet_height_m=0.18, cant_angle_deg=75.0, sweep_angle_deg=35.0)
    
    # Check geometric AR = 2.40^2 / 0.816 = 7.0588 ~ 7.06
    assert abs(res.ar_geometric - 7.06) < 0.1
    
    # Effective AR should increase by ~ 6% to 10%
    assert res.ar_effective > res.ar_geometric
    assert 1.05 < res.ar_effective_ratio < 1.15
    
    # Induced drag reduction should be between 5% and 15%
    assert 5.0 < res.induced_drag_reduction_percent < 15.0
    
    # Root bending moment penalty should remain modest (< 10%)
    assert 0.0 < res.root_bending_moment_increase_percent < 10.0
    
    # Net L/D should show positive gain
    assert res.net_aerodynamic_efficiency_gain_percent > 0.0
    assert res.l_over_d_with_winglet > res.l_over_d_clean

def test_winglet_burnham_hallock_vortex_attenuation():
    opt = WingletAeroOptimizer(wing_span_m=2.40, wing_area_m2=0.816, design_cl=0.65)
    vortex_res = opt.compute_burnham_hallock_vortex_decay(winglet_height_m=0.18, num_points=40)
    
    # Vortex peak tangential velocity should be significantly reduced with winglet
    assert vortex_res.peak_vortex_velocity_winglet_ms < vortex_res.peak_vortex_velocity_baseline_ms
    assert vortex_res.core_velocity_reduction_percent > 30.0
    
    # Vortex core radius expands
    assert vortex_res.vortex_core_radius_m > 0.05
    assert len(vortex_res.v_theta_winglet_ms) == 40
