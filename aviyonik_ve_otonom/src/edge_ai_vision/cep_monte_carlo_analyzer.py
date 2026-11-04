#!/usr/bin/env python3
"""
AIAA DBF 2027 - Stochastic Monte Carlo Drop Trajectory & CEP Analyzer
Runs 1000+ stochastic flight runs with random Dryden wind gusts, servo latency jitter,
and camera tracking noise to quantify CEP-50 and CEP-95 accuracy for Mission 3.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np

from edge_ai_vision.drop_ballistics_computer import BallisticsSolver


@dataclass
class ImpactPoint:
    x_error_m: float
    y_error_m: float
    radial_error_m: float
    fall_time_s: float
    impact_velocity_ms: float


@dataclass
class CEPAnalysisReport:
    total_runs: int
    cep_50_m: float
    cep_95_m: float
    mean_radial_error_m: float
    std_radial_error_m: float
    target_hit_rate_pct: float   # Hits within target_radius_m
    min_error_m: float
    max_error_m: float


class CEPMonteCarloAnalyzer:
    def __init__(
        self,
        payload_mass_kg: float = 2.5,
        drag_coefficient: float = 0.45,
        frontal_area_m2: float = 0.018,
        nominal_altitude_m: float = 25.0,
        nominal_airspeed_ms: float = 24.5,
        target_radius_m: float = 2.0,
        rho_air: float = 1.225,
        nominal_servo_delay_s: float = 0.05
    ):
        self.mass = payload_mass_kg
        self.cd = drag_coefficient
        self.area = frontal_area_m2
        self.alt = nominal_altitude_m
        self.airspeed = nominal_airspeed_ms
        self.target_radius = target_radius_m
        self.rho = rho_air
        self.nom_delay = nominal_servo_delay_s

        self.solver = BallisticsSolver(
            payload_mass_kg=payload_mass_kg,
            drag_coefficient=drag_coefficient,
            frontal_area_m2=frontal_area_m2,
            air_density=rho_air
        )

        # Baseline predicted advance forward travel under zero wind
        nom_x, _, self.nominal_tof = self.solver.compute_trajectory(
            altitude_m=self.alt,
            ground_speed_x=self.airspeed,
            ground_speed_y=0.0
        )
        self.nominal_release_advance = nom_x + self.airspeed * self.nom_delay

    def simulate_single_drop(
        self,
        wind_gust_x: float,
        wind_gust_y: float,
        servo_delay_s: float,
        tracking_noise_x: float,
        tracking_noise_y: float
    ) -> ImpactPoint:
        """
        Simulates drop with stochastic disturbances:
        - wind_gust_x, wind_gust_y (m/s)
        - servo_delay_s (s)
        - tracking_noise_x, tracking_noise_y (m)
        """
        # Actual flight advance until physical release
        actual_release_x = tracking_noise_x + self.airspeed * servo_delay_s
        actual_release_y = tracking_noise_y

        # Trajectory integration with wind
        impact_x, impact_y, tof = self.solver.compute_trajectory(
            altitude_m=self.alt,
            ground_speed_x=self.airspeed,
            ground_speed_y=0.0,
            wind_x=wind_gust_x,
            wind_y=wind_gust_y
        )

        total_impact_x = actual_release_x + impact_x
        total_impact_y = actual_release_y + impact_y

        # Error relative to compensated target line
        error_x = total_impact_x - self.nominal_release_advance
        error_y = total_impact_y
        radial_error = math.sqrt(error_x**2 + error_y**2)

        return ImpactPoint(
            x_error_m=error_x,
            y_error_m=error_y,
            radial_error_m=radial_error,
            fall_time_s=tof,
            impact_velocity_ms=math.sqrt(self.airspeed**2 + (9.80665 * tof)**2)
        )

    def run_monte_carlo(self, num_runs: int = 500, seed: int = 42) -> CEPAnalysisReport:
        np.random.seed(seed)
        radial_errors = []

        # Stochastic disturbances:
        # Wind gusts: Mean = 0, Std = 0.75 m/s (Dryden gust)
        wind_x = np.random.normal(0.0, 0.75, num_runs)
        wind_y = np.random.normal(0.0, 0.60, num_runs)
        # Servo release jitter around nominal 50ms (Std = 8ms)
        servo_delays = np.random.normal(self.nom_delay, 0.008, num_runs)
        # Vision tracking projection error (Std = 0.15m)
        track_x = np.random.normal(0.0, 0.15, num_runs)
        track_y = np.random.normal(0.0, 0.15, num_runs)

        for i in range(num_runs):
            pt = self.simulate_single_drop(
                wind_gust_x=wind_x[i],
                wind_gust_y=wind_y[i],
                servo_delay_s=servo_delays[i],
                tracking_noise_x=track_x[i],
                tracking_noise_y=track_y[i]
            )
            radial_errors.append(pt.radial_error_m)

        arr = np.sort(np.array(radial_errors))
        cep_50 = float(np.percentile(arr, 50))
        cep_95 = float(np.percentile(arr, 95))
        hit_count = int(np.sum(arr <= self.target_radius))
        hit_rate = (hit_count / num_runs) * 100.0

        return CEPAnalysisReport(
            total_runs=num_runs,
            cep_50_m=round(cep_50, 3),
            cep_95_m=round(cep_95, 3),
            mean_radial_error_m=round(float(np.mean(arr)), 3),
            std_radial_error_m=round(float(np.std(arr)), 3),
            target_hit_rate_pct=round(hit_rate, 1),
            min_error_m=round(float(np.min(arr)), 3),
            max_error_m=round(float(np.max(arr)), 3)
        )
