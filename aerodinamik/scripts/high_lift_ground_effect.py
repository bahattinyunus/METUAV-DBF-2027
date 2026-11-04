#!/usr/bin/env python3
"""
AIAA DBF 2027 - High-Lift Flap Deflection & Ground Effect Aerodynamics Analyzer
Calculates 3D wing lift increment (Delta CL), induced drag reduction near runway ground (h/b < 0.5),
and stall speed margin under heavy takeoff payloads.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class GroundEffectPolar:
    height_above_ground_m: float
    height_to_span_ratio: float
    cl: float
    cd_profile: float
    cd_induced: float
    cd_total: float
    cl_over_cd: float
    v_stall_ms: float
    lift_to_weight_ratio: float


class HighLiftGroundEffectAnalyzer:
    def __init__(
        self,
        wing_span_b_m: float = 2.40,
        wing_area_s_m2: float = 0.7032,
        aspect_ratio: float = 8.19,
        oswald_e: float = 0.82,
        mass_takeoff_kg: float = 24.85,
        air_density_rho: float = 1.225
    ):
        self.b = wing_span_b_m
        self.s = wing_area_s_m2
        self.ar = aspect_ratio
        self.e = oswald_e
        self.mass = mass_takeoff_kg
        self.weight_n = mass_takeoff_kg * 9.80665
        self.rho = air_density_rho

    def calculate_flap_aerodynamics(self, flap_deflection_deg: float) -> Tuple[float, float, float]:
        """
        Computes 2D/3D lift increment and zero-lift drag increment from trailing-edge flap deflection.
        Returns: (cl_clean_max, delta_cl_flap, delta_cd0_flap)
        """
        # Selig 1223 high-lift clean characteristics
        cl_clean_max = 1.96

        delta_rad = math.radians(flap_deflection_deg)
        # Delta CL empirical high-lift formulation for 25% chord plain flap
        delta_cl = 0.9 * math.sin(delta_rad)
        # Parasitic drag penalty
        delta_cd0 = 0.0018 * flap_deflection_deg + 0.0003 * (flap_deflection_deg ** 2)

        return cl_clean_max, delta_cl, delta_cd0

    def calculate_ground_effect_factor(self, height_m: float) -> float:
        """
        Wieselsberger / McCormick ground effect interference factor sigma:
        sigma = (16 * (h/b)^2) / (1 + 16 * (h/b)^2)
        As h -> 0, sigma -> 0 (induced drag vanishes).
        As h >> b, sigma -> 1 (free-stream induced drag).
        """
        h_over_b = max(height_m / self.b, 0.02)
        h2 = h_over_b ** 2
        sigma = (16.0 * h2) / (1.0 + 16.0 * h2)
        return float(np.clip(sigma, 0.05, 1.0))

    def analyze_takeoff_climb(
        self,
        flap_deg: float = 15.0,
        height_steps_m: List[float] = [0.25, 0.50, 1.0, 1.5, 2.5, 5.0, 15.0],
        v_speed_ms: float = 19.5
    ) -> List[GroundEffectPolar]:
        cl_max_clean, delta_cl, delta_cd0 = self.calculate_flap_aerodynamics(flap_deg)
        cl_max_config = cl_max_clean + delta_cl
        cd0_total = 0.028 + delta_cd0

        polars: List[GroundEffectPolar] = []

        for h in height_steps_m:
            sigma = self.calculate_ground_effect_factor(h)
            h_b = h / self.b

            # Operating at 80% CL_max during rotation / ground roll transition
            cl_operating = 0.80 * cl_max_config
            # Induced drag with ground interference factor
            cd_ind = sigma * (cl_operating ** 2) / (math.pi * self.ar * self.e)
            cd_tot = cd0_total + cd_ind
            ld = cl_operating / cd_tot

            # Stall speed at this CL_max: V_stall = sqrt(2*W / (rho * S * CL_max))
            v_stall = math.sqrt((2.0 * self.weight_n) / (self.rho * self.s * cl_max_config))

            # Dynamic lift at speed v_speed_ms
            lift = 0.5 * self.rho * (v_speed_ms ** 2) * self.s * cl_operating
            l_w = lift / self.weight_n

            polars.append(GroundEffectPolar(
                height_above_ground_m=h,
                height_to_span_ratio=h_b,
                cl=cl_operating,
                cd_profile=cd0_total,
                cd_induced=cd_ind,
                cd_total=cd_tot,
                cl_over_cd=ld,
                v_stall_ms=v_stall,
                lift_to_weight_ratio=l_w
            ))

        return polars
