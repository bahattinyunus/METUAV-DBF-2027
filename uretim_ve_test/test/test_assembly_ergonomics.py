import pytest
from uretim_ve_test.scripts.assembly_ergonomics_optimizer import AssemblyErgonomicsOptimizer

def test_assembly_timeline_within_5_minute_limit():
    opt = AssemblyErgonomicsOptimizer(time_limit_s=300.0)
    report = opt.calculate_parallel_assembly_timeline()

    # Must be strictly under 300s (AIAA DBF rule)
    assert report.is_compliant is True
    assert report.total_duration_s < 200.0  # We achieve ~119s
    assert report.safety_margin_s > 100.0

def test_crew_workload_balance():
    opt = AssemblyErgonomicsOptimizer()
    report = opt.calculate_parallel_assembly_timeline()

    crew1_util = report.crew_utilization_pct["CREW_1"]
    crew2_util = report.crew_utilization_pct["CREW_2"]

    # Both crew members should have balanced tasks (> 50% utilization)
    assert crew1_util > 50.0
    assert crew2_util > 50.0
    assert len(report.critical_path_steps) > 0
