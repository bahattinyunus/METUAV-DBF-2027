import numpy as np
import pytest
from aviyonik_ve_otonom.src.ucus_kontrol.src.control_allocation_reconfiguration import FaultTolerantControlAllocator

def test_nominal_allocation():
    allocator = FaultTolerantControlAllocator()
    # Pure roll demand L = 5.0 N.m
    res = allocator.allocate(desired_moments_nm=np.array([5.0, 0.0, 0.0]))

    assert res.healthy_actuator_count == 7
    # Outboard right aileron should deflect upwards/downwards to generate positive roll
    assert abs(res.achieved_moments_nm[0] - 5.0) < 0.2
    assert abs(res.achieved_moments_nm[1]) < 0.2
    assert abs(res.achieved_moments_nm[2]) < 0.2

def test_jammed_aileron_fault_reconfiguration():
    allocator = FaultTolerantControlAllocator()
    # Inject fault: Outboard left aileron is physically stuck at +15 deg
    allocator.set_jammed_actuator("AILERON_OUTBOARD_LEFT", jammed_angle_deg=15.0)

    # Simulate dynamic response over several control cycles
    for _ in range(15):
        res = allocator.allocate(desired_moments_nm=np.array([0.0, 0.0, 0.0]), dt_sec=0.02)

    assert res.healthy_actuator_count == 6
    # Other ailerons and surfaces must compensate to maintain near-zero net roll error
    assert abs(res.achieved_moments_nm[0]) < 0.5
    # The jammed actuator must stay at 15.0 deg
    assert res.commanded_surfaces_deg[0] == 15.0
