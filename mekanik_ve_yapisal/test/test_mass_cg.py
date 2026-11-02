import pytest
from mekanik_ve_yapisal.scripts.mass_and_cg_calculator import MassAndCGBudget

def test_mass_limit_compliance_all_missions():
    budget = MassAndCGBudget()
    reports = budget.evaluate_all()

    for name, r in reports.items():
        # AIAA DBF strict 55.0 lbs rule
        assert r.is_compliant, f"{name} exceeds 55.0 lbs limit with {r.total_weight_lbs:.2f} lbs!"
        assert r.total_weight_lbs <= 55.0

def test_cg_margin_and_stability_range():
    budget = MassAndCGBudget()
    # Check Mission 2 (Heavy payload) and Mission 3 (Pre vs Post drop)
    m2 = budget.evaluate_configuration("Mission 2 (Maksimum Agirlik - 55 lbs TOGW Siniri)")
    m3_pre = budget.evaluate_configuration("Mission 3 (Pre-Drop - Delivery Yuku)")
    m3_post = budget.evaluate_configuration("Mission 3 (Post-Drop - Yuksus Eve Donus)")

    # Static margin: CG should be between 10% and 35% MAC for pitch stability
    for report in [m2, m3_pre, m3_post]:
        assert -5.0 < report.cg_mac_percent < 35.0, f"CG at {report.cg_mac_percent}% is outside flyable envelope!"

    # After payload drop, inertia and mass must reduce significantly
    assert m3_post.total_mass_kg < m3_pre.total_mass_kg
    assert m3_post.iyy_kg_m2 < m3_pre.iyy_kg_m2
