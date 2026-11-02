import pytest
from mekanik_ve_yapisal.scripts.spar_stress_fea import SparStressFEA

def test_spar_stress_safety_factors():
    solver = SparStressFEA()
    res = solver.analyze()

    # AIAA DBF requirements: Factor of Safety >= 1.5 against ultimate load
    assert res.fos_bending >= 1.5, f"Bending safety factor {res.fos_bending:.2f} is insufficient!"
    assert res.fos_shear >= 1.5, f"Shear safety factor {res.fos_shear:.2f} is insufficient!"

def test_spar_tip_deflection():
    solver = SparStressFEA()
    res = solver.analyze()

    # Tip deflection under +3.5g ultimate load should not exceed 10% of semi-span (120 mm)
    assert res.tip_deflection_mm < 120.0
    assert res.deflection_pct_semispan < 10.0
    assert res.v_root_n > 0.0
    assert res.m_root_nm > 0.0
