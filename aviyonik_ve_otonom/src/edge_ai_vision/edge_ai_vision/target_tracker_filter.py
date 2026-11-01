#!/usr/bin/env python3
"""
METUAV DBF 2027 - Ground Target Kalman Tracking Filter
Filters noisy camera ground projections, gates false positive detections,
and maintains robust target coordinates even during high-bank turns and temporary dropouts.
"""

import math
import numpy as np
from typing import Optional, Tuple, Dict

class TargetKalmanTracker:
    def __init__(self, process_noise: float = 0.05, measurement_noise: float = 0.80):
        # State: [x, y, vx, vy] in world/NED frame
        self.state = np.zeros(4, dtype=np.float64)
        # Covariance matrix P
        self.P = np.eye(4, dtype=np.float64) * 10.0
        # Process noise Q
        self.Q = np.diag([process_noise, process_noise, process_noise * 0.1, process_noise * 0.1])
        # Measurement noise R
        self.R = np.eye(2, dtype=np.float64) * (measurement_noise ** 2)

        self.initialized = False
        self.missed_detections = 0
        self.max_coast_frames = 45  # 1.5 seconds at 30 FPS
        self.chi2_gate_threshold = 9.21  # 99% confidence gate for 2-DOF measurement

    def initialize(self, x: float, y: float):
        self.state = np.array([x, y, 0.0, 0.0], dtype=np.float64)
        self.P = np.diag([0.5, 0.5, 1.0, 1.0])
        self.initialized = True
        self.missed_detections = 0

    def predict(self, dt: float):
        """State extrapolation: x = F * x, P = F * P * F^T + Q."""
        if not self.initialized or dt <= 0.0001:
            return

        F = np.array([
            [1.0, 0.0, dt,  0.0],
            [0.0, 1.0, 0.0, dt ],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float64)

        self.state = F @ self.state
        self.P = F @ self.P @ F.T + self.Q

    def update(self, measured_x: float, measured_y: float) -> bool:
        """
        Measurement update with statistical outlier gating.
        Returns True if measurement was accepted, False if rejected as outlier.
        """
        if not self.initialized:
            self.initialize(measured_x, measured_y)
            return True

        # Measurement matrix H
        H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=np.float64)

        z = np.array([measured_x, measured_y], dtype=np.float64)
        y_residual = z - (H @ self.state)

        # Innovation covariance S = H * P * H^T + R
        S = H @ self.P @ H.T + self.R
        S_inv = np.linalg.inv(S)

        # Mahalanobis distance squared (d2 = y^T * S^-1 * y)
        d2 = float(y_residual.T @ S_inv @ y_residual)

        if d2 > self.chi2_gate_threshold:
            # Outlier rejected!
            self.missed_detections += 1
            return False

        # Kalman Gain K = P * H^T * S^-1
        K = self.P @ H.T @ S_inv
        self.state = self.state + K @ y_residual
        self.P = (np.eye(4) - K @ H) @ self.P
        self.missed_detections = 0
        return True

    def get_target_position(self) -> Tuple[float, float, float]:
        """Returns: (x, y, position_uncertainty_std_m)."""
        uncertainty = math.sqrt(max(0.0, self.P[0, 0] + self.P[1, 1]))
        return float(self.state[0]), float(self.state[1]), float(uncertainty)

    def is_tracking_valid(self) -> bool:
        return self.initialized and (self.missed_detections < self.max_coast_frames)


def main():
    print("=" * 68)
    print("  METUAV DBF 2027 - Hedef Takip Kalman Filtresi Testi")
    print("=" * 68)

    tracker = TargetKalmanTracker()
    true_target_x = 75.0
    true_target_y = 30.0

    # Simulate 50 measurements with noise and a few dropouts/outliers
    np.random.seed(42)
    dt = 0.033  # 30 FPS

    accepted = 0
    rejected = 0

    for i in range(60):
        tracker.predict(dt)

        if i == 25:
            # Huge outlier (e.g. false detection on runway marker at x=150, y=0)
            res = tracker.update(150.0, 0.0)
            if not res: rejected += 1
        elif 35 <= i <= 40:
            # Temporary target occlusion (plane banking, target outside FOV)
            pass  # Coasting only
        else:
            # Normal noisy detection
            noisy_x = true_target_x + np.random.normal(0.0, 0.45)
            noisy_y = true_target_y + np.random.normal(0.0, 0.45)
            res = tracker.update(noisy_x, noisy_y)
            if res: accepted += 1

    est_x, est_y, std = tracker.get_target_position()
    print(f"[OK] Gercek Hedef: X={true_target_x:.2f}m, Y={true_target_y:.2f}m")
    print(f"[OK] Kestirilen : X={est_x:.2f}m, Y={est_y:.2f}m (Belirsizlik: ±{std:.2f}m)")
    print(f"[OK] Filtreleme Istatistikleri: {accepted} gecerli olcum alindi, {rejected} aykiri deger reddedildi.")

    assert abs(est_x - true_target_x) < 0.20
    assert abs(est_y - true_target_y) < 0.20
    assert rejected == 1
    print("\n[BASARILI] Kalman Hedef Takip Filtresi Tam Hassasiyetle Calisiyor!")
    print("=" * 68)


if __name__ == '__main__':
    main()
