import pytest
from rakip_analizi_ve_benchmark.scripts.competitor_benchmark_matrix import build_benchmark_database

def test_benchmark_database_structure():
    db = build_benchmark_database()
    assert len(db) >= 6
    baseline = db[0]
    assert baseline.team == "DBF Reference Model"
    assert baseline.togw_lbs <= 55.0

def test_baseline_competitiveness():
    db = build_benchmark_database()
    baseline = db[0]
    competitors = db[1:]

    avg_payload = sum(c.payload_mass_kg for c in competitors) / len(competitors)
    # DBF Baseline payload must be competitive with top world champions
    assert baseline.payload_mass_kg >= avg_payload

    # All aircraft must adhere to 55 lbs TOGW limit
    for ac in db:
        assert ac.togw_lbs <= 55.0, f"{ac.team} exceeds 55 lbs TOGW limit!"
        assert ac.assembly_time_sec <= 300, f"{ac.team} exceeds 5-minute assembly limit!"
