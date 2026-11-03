import math
import pytest
from itki_ve_guc_sistemleri.scripts.propeller_aeroacoustics_and_windmilling import (
    PropellerAeroacousticsAndWindmilling,
    AcousticAnalysisResult,
    WindmillingDragResult
)

def test_aeroacoustics_tip_speed_and_bpf():
    model = PropellerAeroacousticsAndWindmilling(
        prop_diameter_m=0.4826, # 19"
        prop_pitch_m=0.3048,    # 12"
        num_blades=2
    )
    res = model.analyze_acoustic_emissions(rpm=6800.0, thrust_n=120.0, airspeed_ms=24.5)
    
    # BPF for 2-blade prop at 6800 RPM: (2 * 6800) / 60 = 226.67 Hz
    assert abs(res.blade_passing_freq_hz - 226.7) < 1.0
    
    # Tip speed: omega * R = (2*pi*6800/60) * 0.2413 = 171.8 m/s
    assert abs(res.tip_speed_ms - 171.8) < 1.5
    
    # Tip Mach: ~ 171.8 / 340.29 = 0.505
    assert 0.48 < res.tip_mach < 0.53

def test_aeroacoustics_dbf_sideline_noise_compliance():
    model = PropellerAeroacousticsAndWindmilling()
    res = model.analyze_acoustic_emissions(rpm=6800.0, thrust_n=122.4, sideline_angle_deg=105.0)
    
    # At 100 ft (30.48 m), dBA should be reasonable (< 85 dBA DBF sound limit)
    assert res.spl_total_db > 50.0
    assert res.spl_dba < 85.0
    assert res.is_dbf_noise_compliant is True
    assert res.noise_margin_dba > 0.0

def test_windmilling_freewheel_vs_locked_vs_regen_drag():
    model = PropellerAeroacousticsAndWindmilling()
    drag_res = model.evaluate_windmilling_and_regen_drag(airspeed_ms=24.5, regen_current_target_a=12.0)
    
    # Freewheeling propeller creates massive actuator disk disturbance, greater drag than locked
    assert drag_res.windmilling_freewheel_drag_n > drag_res.locked_drag_n
    
    # Regenerative drag active extraction
    assert drag_res.regenerative_braking_drag_n > drag_res.locked_drag_n
    assert drag_res.regen_electrical_power_w == 24.0 * 12.0 # 288 W
    assert drag_res.freewheel_rpm > 3500.0
