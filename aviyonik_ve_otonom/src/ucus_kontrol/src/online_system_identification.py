#!/usr/bin/env python3
"""
AIAA DBF 2027 - Online Real-Time Aerodynamic System Identification
Implements Recursive Least Squares (RLS) with exponential forgetting factor (lambda)
to identify longitudinal and lateral stability derivatives (Cm_alpha, Cm_q, Cm_delta_e, Cl_beta, Cl_p)
directly from in-flight IMU, pitot-static, and servo telemetry streams.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class LongitudinalDerivatives:
    cm_0: float
    cm_alpha: float        # Pitch stiffness (1/rad, should be negative for stability)
    cm_q: float            # Pitch damping (rad^-1)
    cm_delta_e: float      # Elevator control effectiveness (1/rad, negative)
    covariance_norm: float
    residual_error: float


class OnlineAeroSystemIdentifier:
    def __init__(
        self,
        c_mac_m: float = 0.293,
        wing_area_m2: float = 0.7032,
        rho_air: float = 1.225,
        forgetting_factor: float = 0.992
    ):
        self.c_mac = c_mac_m
        self.s = wing_area_m2
        self.rho = rho_air
        self.lam = forgetting_factor

        # Parameter vector theta: [Cm_0, Cm_alpha, Cm_q, Cm_delta_e]
        self.num_params = 4
        self.theta = np.array([0.02, -0.65, -12.0, -1.25], dtype=float)

        # Covariance matrix P initialized with moderate confidence
        self.p_mat = np.eye(self.num_params, dtype=float) * 50.0

    def update_longitudinal(
        self,
        airspeed_ms: float,
        alpha_rad: float,
        q_pitch_rate_rad_s: float,
        delta_e_rad: float,
        pitch_moment_nm: float
    ) -> LongitudinalDerivatives:
        """
        Processes one telemetry sample and updates RLS parameter estimates.
        Pitch moment coefficient Cm = M / (q_inf * S * c_mac)
        Model: Cm = Cm_0 + Cm_alpha * alpha + Cm_q * (q * c / (2 * V)) + Cm_delta_e * delta_e
        """
        q_inf = max(0.5 * self.rho * (airspeed_ms ** 2), 5.0)
        cm_measured = pitch_moment_nm / (q_inf * self.s * self.c_mac)

        # Non-dimensionalized pitch rate q_hat = q * c / (2 * V)
        q_hat = (q_pitch_rate_rad_s * self.c_mac) / (2.0 * max(airspeed_ms, 1.0))

        # Regressor vector phi: [1, alpha, q_hat, delta_e]
        phi = np.array([1.0, alpha_rad, q_hat, delta_e_rad], dtype=float)

        # 1. Prediction error (residual)
        y_pred = float(np.dot(phi, self.theta))
        residual = cm_measured - y_pred

        # 2. Kalman gain vector K
        p_phi = self.p_mat @ phi
        denom = self.lam + float(phi @ p_phi)
        k_gain = p_phi / max(denom, 1e-6)

        # 3. Update parameter estimate theta
        self.theta += k_gain * residual

        # 4. Update covariance matrix P
        p_next = (self.p_mat - np.outer(k_gain, phi @ self.p_mat)) / self.lam
        # Ensure symmetry
        self.p_mat = 0.5 * (p_next + p_next.T)

        cov_norm = float(np.linalg.norm(self.p_mat))

        return LongitudinalDerivatives(
            cm_0=float(self.theta[0]),
            cm_alpha=float(self.theta[1]),
            cm_q=float(self.theta[2]),
            cm_delta_e=float(self.theta[3]),
            covariance_norm=cov_norm,
            residual_error=residual
        )
