import pytest
from optimizasyon_ve_mdo.scripts.dbf_pareto_optimizer import DBFParetoOptimizer, DesignSample


def test_pareto_optimizer_sampling():
    opt = DBFParetoOptimizer(n_samples=200, seed=123)
    samples = opt.sample_design_space()

    assert len(samples) == 200
    feasible = [s for s in samples if s.is_feasible]
    assert len(feasible) > 10

    for s in feasible:
        assert s.togw_lbs <= 55.0
        assert s.takeoff_roll_m <= 35.0


def test_pareto_front_extraction():
    opt = DBFParetoOptimizer(n_samples=250, seed=123)
    samples = opt.sample_design_space()
    pareto = opt.extract_pareto_front(samples)

    assert len(pareto) > 2
    # Check monotonicity of payload on Pareto front
    for i in range(len(pareto) - 1):
        assert pareto[i].payload_mass_kg <= pareto[i+1].payload_mass_kg


def test_sensitivity_indices():
    opt = DBFParetoOptimizer(n_samples=200, seed=123)
    samples = opt.sample_design_space()
    sens = opt.compute_sensitivity_indices(samples)

    assert abs(sum(sens.values()) - 1.0) < 1e-4
    # Payload mass is typically a dominant driver in DBF scoring
    assert sens["payload_mass"] > 0.20
