#!/usr/bin/env python3
"""
METUAV DBF 2027 - Blended Winglet Aerodynamic & Vortex Attenuation Optimizer
Computes effective aspect ratio improvement (AR_eff), induced drag reduction (CDi),
Trefftz plane lift distribution, wing root bending moment impact, and
Burnham-Hallock wingtip vortex tangential velocity field decay.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class WingletOptimizationResult:
    wing_span_m: float
    winglet_height_m: float
    height_to_span_ratio: float
    cant_angle_deg: float
    sweep_angle_deg: float
    ar_geometric: float
    ar_effective: float
    ar_effective_ratio: float
    induced_drag_reduction_percent: float
    root_bending_moment_increase_percent: float
    l_over_d_clean: float
    l_over_d_with_winglet: float
    net_aerodynamic_efficiency_gain_percent: float


@dataclass
class VortexProfileResult:
    radial_distances_m: List[float]
    v_theta_baseline_ms: List[float]
    v_theta_winglet_ms: List[float]
    peak_vortex_velocity_baseline_ms: float
    peak_vortex_velocity_winglet_ms: float
    core_velocity_reduction_percent: float
    vortex_core_radius_m: float


class WingletAeroOptimizer:
    """
    Non-planar aerodynamic Trefftz plane solver and Burnham-Hallock vortex model
    for competitive blended winglet design.
    """

    def __init__(self,
                 wing_span_m: float = 2.40,
                 wing_area_m2: float = 0.816,
                 oswald_clean: float = 0.86,
                 design_cl: float = 0.65,
                 cd0: float = 0.024,
                 rho: float = 1.225,
                 v_inf: float = 24.5):
        self.b = wing_span_m
        self.S = wing_area_m2
        self.AR = (self.b ** 2) / self.S
        self.e_clean = oswald_clean
        self.cl = design_cl
        self.cd0 = cd0
        self.rho = rho
        self.v_inf = v_inf

    def evaluate_winglet_performance(self,
                                     winglet_height_m: float = 0.18,
                                     cant_angle_deg: float = 75.0,
                                     sweep_angle_deg: float = 35.0,
                                     taper_ratio: float = 0.45) -> WingletOptimizationResult:
        """
        Calculates effective aspect ratio AR_eff, induced drag reduction factor,
        and root bending moment increase using Kroo / Whitcomb non-planar lifting-line formulations.
        """
        h_ratio = winglet_height_m / self.b
        cant_rad = math.radians(cant_angle_deg)
        sweep_rad = math.radians(sweep_angle_deg)

        # Kroo non-planar correction factor for canted blended winglets:
        # AR_eff = AR * (1 + 1.45 * (h/b) * cos((90 - cant)/2) * cos(sweep)^0.25)
        dihedral_effect = math.cos(math.radians(90.0 - cant_angle_deg) / 2.0)
        sweep_factor = math.cos(sweep_rad) ** 0.25
        k_ar = 1.0 + 1.45 * h_ratio * dihedral_effect * sweep_factor
        ar_eff = self.AR * k_ar

        # Oswald efficiency factor slight adjustment (winglet end-plate sealing effect)
        e_winglet = self.e_clean * (1.0 + 0.03 * (h_ratio / 0.075))

        # Induced drag coefficient baseline vs winglet:
        # CDi = CL^2 / (pi * AR * e)
        cdi_clean = (self.cl ** 2) / (math.pi * self.AR * self.e_clean)
        cdi_winglet = (self.cl ** 2) / (math.pi * ar_eff * e_winglet)
        cdi_reduction_pct = ((cdi_clean - cdi_winglet) / cdi_clean) * 100.0

        # Wetted area friction drag penalty of winglet:
        s_winglet = 2.0 * winglet_height_m * (0.18 * (1.0 + taper_ratio) / 2.0) # 2 tips
        cd0_penalty = self.cd0 * (s_winglet / self.S) * 1.15
        cd_total_clean = self.cd0 + cdi_clean
        cd_total_winglet = (self.cd0 + cd0_penalty) + cdi_winglet

        l_over_d_clean = self.cl / cd_total_clean
        l_over_d_winglet = self.cl / cd_total_winglet
        net_gain_pct = ((l_over_d_winglet - l_over_d_clean) / l_over_d_clean) * 100.0

        # Wing root bending moment penalty (aerodynamic side force moment arm):
        # Delta M_root / M_root_0 ~ (1.20 * h/b * sin(cant)) / (1 + 1.5 * h/b)
        root_moment_pct = ((1.20 * h_ratio * math.sin(cant_rad)) / (1.0 + 1.5 * h_ratio)) * 100.0

        return WingletOptimizationResult(
            wing_span_m=round(self.b, 3),
            winglet_height_m=round(winglet_height_m, 3),
            height_to_span_ratio=round(h_ratio, 4),
            cant_angle_deg=round(cant_angle_deg, 1),
            sweep_angle_deg=round(sweep_angle_deg, 1),
            ar_geometric=round(self.AR, 2),
            ar_effective=round(ar_eff, 2),
            ar_effective_ratio=round(k_ar, 3),
            induced_drag_reduction_percent=round(cdi_reduction_pct, 2),
            root_bending_moment_increase_percent=round(root_moment_pct, 2),
            l_over_d_clean=round(l_over_d_clean, 2),
            l_over_d_with_winglet=round(l_over_d_winglet, 2),
            net_aerodynamic_efficiency_gain_percent=round(net_gain_pct, 2)
        )

    def compute_burnham_hallock_vortex_decay(self,
                                             winglet_height_m: float = 0.18,
                                             num_points: int = 50) -> VortexProfileResult:
        """
        Burnham-Hallock wake vortex velocity profile model:
        V_theta(r) = (Gamma_0 / (2*pi*r)) * [r^2 / (r^2 + r_c^2)]
        Compares baseline wingtip concentrated vortex core with winglet-diffused vortex core.
        """
        # Baseline total circulation Gamma_0:
        # L = 0.5 * rho * V^2 * S * CL
        lift = 0.5 * self.rho * (self.v_inf ** 2) * self.S * self.cl
        gamma_0_baseline = (4.0 * lift) / (math.pi * self.rho * self.v_inf * self.b)

        # Baseline vortex core radius (typically 3.5% to 5% of semi-span)
        r_c_baseline = 0.04 * (self.b / 2.0)

        # Winglet diffuses vorticity into vertical shear layer:
        # Circulation split/shed over larger volume: Gamma_effective ~ 0.78 * Gamma_0
        # Core radius expanded: r_c_winglet ~ 1.85 * r_c_baseline
        gamma_0_winglet = gamma_0_baseline * 0.80
        r_c_winglet = r_c_baseline * 1.80

        r_array = np.linspace(0.005, 0.40, num_points)
        v_baseline = []
        v_winglet = []

        for r in r_array:
            # Baseline V_theta
            v_b = (gamma_0_baseline / (2.0 * math.pi * r)) * (r**2 / (r**2 + r_c_baseline**2))
            # Winglet V_theta
            v_w = (gamma_0_winglet / (2.0 * math.pi * r)) * (r**2 / (r**2 + r_c_winglet**2))
            v_baseline.append(float(v_b))
            v_winglet.append(float(v_w))

        peak_b = max(v_baseline)
        peak_w = max(v_winglet)
        vel_reduction_pct = ((peak_b - peak_w) / peak_b) * 100.0

        return VortexProfileResult(
            radial_distances_m=[round(float(r), 4) for r in r_array],
            v_theta_baseline_ms=[round(v, 2) for v in v_baseline],
            v_theta_winglet_ms=[round(v, 2) for v in v_winglet],
            peak_vortex_velocity_baseline_ms=round(peak_b, 2),
            peak_vortex_velocity_winglet_ms=round(peak_w, 2),
            core_velocity_reduction_percent=round(vel_reduction_pct, 1),
            vortex_core_radius_m=round(r_c_winglet, 3)
        )
