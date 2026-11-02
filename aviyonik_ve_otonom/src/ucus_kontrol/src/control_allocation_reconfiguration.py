#!/usr/bin/env python3
"""
METUAV DBF 2027 - Fault-Tolerant Control Allocation & Actuator Reconfiguration
Distributes desired 3-axis aerodynamic moments (Roll, Pitch, Yaw) across redundant control surfaces:
[Left Outboard Aileron, Left Inboard Aileron, Right Inboard Aileron, Right Outboard Aileron,
 Left Elevator, Right Elevator, Rudder].
Handles stuck/jammed servos and saturation limits using weighted pseudo-inverse & dynamic null-space projection.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AllocationResult:
    commanded_surfaces_deg: np.ndarray
    achieved_moments_nm: np.ndarray
    moment_errors_nm: np.ndarray
    is_saturated: bool
    healthy_actuator_count: int


class FaultTolerantControlAllocator:
    SURFACE_NAMES = [
        "AILERON_OUTBOARD_LEFT",
        "AILERON_INBOARD_LEFT",
        "AILERON_INBOARD_RIGHT",
        "AILERON_OUTBOARD_RIGHT",
        "ELEVATOR_LEFT",
        "ELEVATOR_RIGHT",
        "RUDDER"
    ]

    def __init__(
        self,
        deflection_limit_deg: float = 25.0,
        rate_limit_deg_s: float = 150.0
    ):
        self.num_actuators = len(self.SURFACE_NAMES)
        self.limit_deg = deflection_limit_deg
        self.rate_limit = rate_limit_deg_s

        # Control effectiveness matrix B (3x7) in N.m/deg at nominal cruise dynamic pressure (q_inf = 368 Pa)
        # Row 0: Roll (L)
        # Row 1: Pitch (M)
        # Row 2: Yaw (N)
        self.b_nominal = np.array([
            #  a_lo,   a_li,   a_ri,   a_ro,   e_l,    e_r,    rudder
            [-1.85,  -1.10,  +1.10,  +1.85,  -0.15,  +0.15,  +0.05 ],  # Roll L
            [+0.08,  +0.12,  +0.12,  +0.08,  -2.20,  -2.20,  +0.00 ],  # Pitch M
            [+0.12,  +0.06,  -0.06,  -0.12,  +0.00,  +0.00,  -1.65 ]   # Yaw N
        ], dtype=float)

        # Jammed actuator state: map of index -> jammed_angle_deg
        self.jammed_actuators: Dict[int, float] = {}
        self.prev_deflections = np.zeros(self.num_actuators)

    def set_jammed_actuator(self, surface_name: str, jammed_angle_deg: float):
        if surface_name in self.SURFACE_NAMES:
            idx = self.SURFACE_NAMES.index(surface_name)
            self.jammed_actuators[idx] = float(np.clip(jammed_angle_deg, -self.limit_deg, self.limit_deg))

    def clear_faults(self):
        self.jammed_actuators.clear()

    def allocate(
        self,
        desired_moments_nm: np.ndarray,
        dt_sec: float = 0.02
    ) -> AllocationResult:
        """
        Solves: M_des = B * delta
        accounting for jammed actuators delta_j = fixed.
        """
        desired_moments = np.asarray(desired_moments_nm, dtype=float).reshape(3)

        # Identify healthy and failed actuators
        healthy_indices = [i for i in range(self.num_actuators) if i not in self.jammed_actuators]
        n_healthy = len(healthy_indices)

        # Compute moment contribution from jammed actuators
        m_jammed = np.zeros(3)
        for idx, angle in self.jammed_actuators.items():
            m_jammed += self.b_nominal[:, idx] * angle

        # Effective moment required from healthy surfaces
        m_required = desired_moments - m_jammed

        # Reduced B matrix for healthy actuators
        b_healthy = self.b_nominal[:, healthy_indices]

        # Weighted Moore-Penrose Pseudo-Inverse: delta_h = B^+ * M_req
        # B^+ = W^-1 * B^T * (B * W^-1 * B^T)^-1
        b_pinv = np.linalg.pinv(b_healthy)
        delta_healthy_unconstrained = b_pinv @ m_required

        # Apply position and rate limits
        full_deflections = np.zeros(self.num_actuators)
        for idx, angle in self.jammed_actuators.items():
            full_deflections[idx] = angle

        is_saturated = False
        for k, h_idx in enumerate(healthy_indices):
            target = delta_healthy_unconstrained[k]

            # Rate limit
            max_step = self.rate_limit * dt_sec
            delta_step = target - self.prev_deflections[h_idx]
            clipped_step = np.clip(delta_step, -max_step, max_step)
            rate_limited = self.prev_deflections[h_idx] + clipped_step

            # Deflection position limit
            clipped_deflection = float(np.clip(rate_limited, -self.limit_deg, self.limit_deg))
            if abs(clipped_deflection - target) > 0.1:
                is_saturated = True

            full_deflections[h_idx] = clipped_deflection

        self.prev_deflections = full_deflections.copy()

        # Compute achieved moments
        achieved_moments = self.b_nominal @ full_deflections
        moment_error = desired_moments - achieved_moments

        return AllocationResult(
            commanded_surfaces_deg=full_deflections,
            achieved_moments_nm=achieved_moments,
            moment_errors_nm=moment_error,
            is_saturated=is_saturated,
            healthy_actuator_count=n_healthy
        )
