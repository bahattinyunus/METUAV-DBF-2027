#!/usr/bin/env python3
"""
METUAV DBF 2027 - Mission 3 Aero-Ballistic Dispersion & Dynamic Sightline Optimizer
Performs Monte Carlo stochastic release dispersion analysis and generates real-time
HUD sightline lead angle tables:
- Stochastic perturbations in airspeed, altitude, pitch, package tumbling drag (Cd*A),
  solenoid latency, and atmospheric Dryden gusts
- Circular Error Probable (CEP-50, CEP-95) and Bullseye hit probability (P < 1.20m)
- Dynamic Sightline Lead Angle (theta_sight) computation for PFD HUD target cueing
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class DispersionAnalysisResult:
    total_runs: int
    mean_lead_distance_m: float
    mean_cross_error_m: float
    cep_50_m: float
    cep_95_m: float
    std_downrange_m: float
    std_crossrange_m: float
    bullseye_hit_rate_pct: float
    optimal_release_lead_m: float
    nominal_fall_time_s: float


@dataclass
class HUDSightlineCue:
    airspeed_ms: float
    altitude_m: float
    headwind_ms: float
    lead_distance_m: float
    sightline_depression_deg: float
    fall_time_s: float


class BallisticDispersionOptimizer:
    """
    Monte Carlo stochastic payload trajectory dispersion solver and HUD lead angle generator.
    """

    def __init__(self,
                 payload_mass_kg: float = 11.20,
                 nominal_cda_m2: float = 0.0045,  # Cd * A for streamlined DBF cylindrical cargo
                 g_accel: float = 9.80665,
                 air_density_kg_m3: float = 1.225):
        self.mass = payload_mass_kg
        self.cda_nom = nominal_cda_m2
        self.g = g_accel
        self.rho = air_density_kg_m3

    def _integrate_single_drop(self,
                               x0: float, z0: float,
                               vx0: float, vz0: float,
                               cda: float,
                               wind_x: float, wind_z: float,
                               dt: float = 0.01) -> Tuple[float, float, float]:
        """
        Integrates single 3-DOF payload trajectory until ground impact (z = 0).
        Coordinates: x (forward downrange), z (altitude, 0 is ground).
        """
        x = x0
        z = z0
        vx = vx0
        vz = vz0
        t = 0.0

        while z > 0.0 and t < 15.0:
            # Relative velocity to wind
            v_rel_x = vx - wind_x
            v_rel_z = vz - wind_z
            v_rel = math.sqrt(v_rel_x**2 + v_rel_z**2)

            drag_factor = 0.5 * self.rho * cda / self.mass
            ax = -drag_factor * v_rel_x * v_rel
            az = -self.g - (drag_factor * v_rel_z * v_rel)

            # RK4-like integration step
            vx += ax * dt
            vz += az * dt
            x += vx * dt
            z += vz * dt
            t += dt

        return x, t, vx

    def compute_nominal_trajectory(self,
                                   airspeed_ms: float = 24.5,
                                   altitude_m: float = 25.0,
                                   headwind_ms: float = 0.0) -> Tuple[float, float]:
        """
        Calculates deterministic lead distance and time of fall for nominal release.
        """
        # Ground speed = Airspeed - Headwind
        vg0 = airspeed_ms - headwind_ms
        x_impact, t_fall, _ = self._integrate_single_drop(
            x0=0.0, z0=altitude_m,
            vx0=vg0, vz0=0.0,
            cda=self.cda_nom,
            wind_x=-headwind_ms, wind_z=0.0
        )
        return x_impact, t_fall

    def compute_dynamic_sightline_cue(self,
                                      airspeed_ms: float,
                                      altitude_m: float,
                                      headwind_ms: float = 0.0) -> HUDSightlineCue:
        """
        Calculates depressed sightline angle theta_sight = atan2(altitude, lead_distance).
        Used by the Primary Flight Display (PFD) HUD reticle to cue release point.
        """
        lead_dist, t_fall = self.compute_nominal_trajectory(airspeed_ms, altitude_m, headwind_ms)
        sightline_rad = math.atan2(altitude_m, max(lead_dist, 1.0))
        sightline_deg = math.degrees(sightline_rad)

        return HUDSightlineCue(
            airspeed_ms=airspeed_ms,
            altitude_m=altitude_m,
            headwind_ms=headwind_ms,
            lead_distance_m=round(lead_dist, 2),
            sightline_depression_deg=round(sightline_deg, 2),
            fall_time_s=round(t_fall, 2)
        )

    def run_monte_carlo_dispersion(self,
                                   n_runs: int = 500,
                                   nominal_airspeed_ms: float = 24.5,
                                   nominal_altitude_m: float = 25.0,
                                   headwind_mean_ms: float = 2.0,
                                   enable_wind_compensation: bool = True,
                                   random_seed: int = 42) -> DispersionAnalysisResult:
        """
        Runs full stochastic Monte Carlo dispersion simulation.
        When enable_wind_compensation is True, simulates closed-loop optical flow wind
        correction reducing residual wind variance to < 0.25 m/s.
        """
        np.random.seed(random_seed)

        # Baseline nominal lead
        nom_lead, nom_t_fall = self.compute_nominal_trajectory(
            nominal_airspeed_ms, nominal_altitude_m, headwind_mean_ms
        )

        impact_x_list = []
        impact_y_list = []

        wind_std = 0.20 if enable_wind_compensation else 1.00
        cross_std = 0.15 if enable_wind_compensation else 0.60
        v_std = 0.35 if enable_wind_compensation else 0.80

        for _ in range(n_runs):
            v_air = nominal_airspeed_ms + np.random.normal(0.0, v_std)
            alt = nominal_altitude_m + np.random.normal(0.0, 0.35)
            vz0 = np.random.normal(0.0, 0.15)
            cda_pert = self.cda_nom * np.random.uniform(0.92, 1.08)
            t_lag = max(0.010, np.random.normal(0.035, 0.004))

            wind_x = -headwind_mean_ms + np.random.normal(0.0, wind_std)
            wind_y = np.random.normal(0.0, cross_std)  # Crosswind gust

            # Aircraft advances during release lag
            x_start = (v_air + wind_x) * t_lag
            vx0 = v_air + wind_x

            x_imp, t_imp, _ = self._integrate_single_drop(
                x0=x_start, z0=alt,
                vx0=vx0, vz0=vz0,
                cda=cda_pert,
                wind_x=wind_x, wind_z=0.0
            )

            # Lateral drift from crosswind gust
            y_imp = wind_y * t_imp

            impact_x_list.append(x_imp)
            impact_y_list.append(y_imp)

        impact_x = np.array(impact_x_list)
        impact_y = np.array(impact_y_list)

        # Offsets relative to intended target center (at nominal lead)
        dx = impact_x - nom_lead
        dy = impact_y
        radial_errors = np.sqrt(dx**2 + dy**2)

        cep_50 = float(np.percentile(radial_errors, 50.0))
        cep_95 = float(np.percentile(radial_errors, 95.0))
        bullseye_hits = float(np.sum(radial_errors <= 1.20))
        hit_rate_pct = (bullseye_hits / n_runs) * 100.0

        return DispersionAnalysisResult(
            total_runs=n_runs,
            mean_lead_distance_m=round(float(np.mean(impact_x)), 2),
            mean_cross_error_m=round(float(np.mean(impact_y)), 3),
            cep_50_m=round(cep_50, 3),
            cep_95_m=round(cep_95, 3),
            std_downrange_m=round(float(np.std(impact_x)), 3),
            std_crossrange_m=round(float(np.std(impact_y)), 3),
            bullseye_hit_rate_pct=round(hit_rate_pct, 1),
            optimal_release_lead_m=round(nom_lead, 2),
            nominal_fall_time_s=round(nom_t_fall, 2)
        )
