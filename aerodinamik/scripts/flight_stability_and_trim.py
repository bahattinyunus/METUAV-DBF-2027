#!/usr/bin/env python3
"""
AIAA DBF 2027 - Aeroelastic Stability, Trim & Control Reversal Analyzer
Solves longitudinal static margins across all 4 DBF mission stages, computes trimmed
elevator deflection and alpha across flight speed envelopes, verifies pitch control authority,
calculates dynamic aeroelastic aileron reversal speed (V_R), and evaluates Dutch-roll damping.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class MissionCGConfig:
    name: str
    mass_kg: float
    cg_pct_mac: float
    description: str


@dataclass
class TrimSolution:
    airspeed_ms: float
    alpha_trim_deg: float
    delta_e_trim_deg: float
    cl_trim: float
    dynamic_pressure_pa: float
    is_elevator_saturated: bool


@dataclass
class StabilityReport:
    cg_pct_mac: float
    neutral_point_pct_mac: float
    static_margin_pct: float
    cm_alpha_per_rad: float
    cl_alpha_wing_per_rad: float
    downwash_gradient: float
    is_statically_stable: bool


@dataclass
class AeroelasticMargin:
    torsional_stiffness_nm_rad: float
    reversal_dynamic_pressure_pa: float
    aileron_reversal_speed_ms: float
    dive_speed_ms: float
    reversal_safety_factor: float
    is_aeroelastically_safe: bool


class FlightStabilityAndTrimAnalyzer:
    """
    Flight dynamics stability margin, downwash coupling, control surface trim,
    and aeroelastic control reversal solver.
    """

    def __init__(self,
                 wingspan_m: float = 2.40,
                 wing_area_m2: float = 0.7032,
                 mac_m: float = 0.293,
                 tail_span_m: float = 0.840,
                 tail_area_m2: float = 0.1512,
                 tail_arm_m: float = 0.950,
                 aspect_ratio: float = 8.19,
                 air_density_kg_m3: float = 1.225):
        self.b_w = wingspan_m
        self.S_w = wing_area_m2
        self.c_mac = mac_m
        self.b_t = tail_span_m
        self.S_t = tail_area_m2
        self.l_t = tail_arm_m
        self.AR_w = aspect_ratio
        self.rho = air_density_kg_m3
        self.g = 9.80665

        # Tail volume coefficient: V_h = (S_t * l_t) / (S_w * c_mac)
        self.V_h = (self.S_t * self.l_t) / (self.S_w * self.c_mac)

        # Aerodynamic baseline coefficients
        self.cl0_wing = 0.65
        self.cla_2d = 6.15  # per rad
        # Helmbold 3D lift slope: CLa = cla_2d / (sqrt(1 + (cla_2d / (pi*AR))^2) + cla_2d / (pi*AR))
        self.cla_w = self.cla_2d / (math.sqrt(1.0 + (self.cla_2d / (math.pi * self.AR_w))**2) + (self.cla_2d / (math.pi * self.AR_w)))

        # Horizontal tail lift curve slope (AR_t ~ 4.67)
        self.AR_t = (self.b_t**2) / self.S_t
        self.cla_t = 5.80 / (math.sqrt(1.0 + (5.80 / (math.pi * self.AR_t))**2) + (5.80 / (math.pi * self.AR_t)))

        # Downwash gradient de/da = 2 * CLa_w / (pi * AR_w)
        self.d_eps_d_alpha = (2.0 * self.cla_w) / (math.pi * self.AR_w)

        # Aerodynamic center of wing (Selig 1223 high camber ~ 24.2% MAC)
        self.x_ac_w_pct = 24.2

        # Fuselage destabilizing effect dCm_fus / dCL
        self.fuselage_destab = 0.035

        # Control surface derivatives
        self.cl_de = 0.42    # per rad
        self.cm_de = -1.25   # per rad
        self.cm0_wing = -0.12 # Pitching moment at zero lift (Selig 1223 high-lift camber)

        # Actuator limits
        self.elevator_min_deg = -25.0
        self.elevator_max_deg = +20.0

    def compute_neutral_point(self) -> float:
        """
        Calculates stick-fixed neutral point (x_np) as percentage of MAC:
        x_np = x_ac_w + V_h * (CLa_t / CLa_w) * (1 - de/da) - (dCm_fus / dCL)
        """
        tail_contrib = self.V_h * (self.cla_t / self.cla_w) * (1.0 - self.d_eps_d_alpha)
        x_np_fraction = (self.x_ac_w_pct / 100.0) + tail_contrib - self.fuselage_destab
        return float(x_np_fraction * 100.0)

    def evaluate_longitudinal_stability(self, cg_pct_mac: float) -> StabilityReport:
        """Evaluates static margin, pitch stiffness, and neutral point."""
        x_np = self.compute_neutral_point()
        static_margin = x_np - cg_pct_mac

        # Cm_alpha = -CLa_w * (static_margin / 100)
        cm_alpha = -self.cla_w * (static_margin / 100.0)

        is_stable = (static_margin >= 5.0) and (cm_alpha < -0.25)

        return StabilityReport(
            cg_pct_mac=round(cg_pct_mac, 2),
            neutral_point_pct_mac=round(x_np, 2),
            static_margin_pct=round(static_margin, 2),
            cm_alpha_per_rad=round(cm_alpha, 3),
            cl_alpha_wing_per_rad=round(self.cla_w, 3),
            downwash_gradient=round(self.d_eps_d_alpha, 3),
            is_statically_stable=is_stable
        )

    def solve_trim(self, airspeed_ms: float, mass_kg: float, cg_pct_mac: float) -> TrimSolution:
        """
        Solves simultaneous lift and pitch equilibrium for alpha_trim and delta_e_trim:
        [ CLa_tot   CL_de ] [ alpha   ] = [ CL_req - CL0 ]
        [ Cma_tot   Cm_de ] [ delta_e ]   [ -Cm0         ]
        """
        q = 0.5 * self.rho * (airspeed_ms**2)
        weight_n = mass_kg * self.g
        cl_req = weight_n / (q * self.S_w)

        # Net lift slope and net pitching stiffness
        x_np = self.compute_neutral_point()
        sm = (x_np - cg_pct_mac) / 100.0
        cm_alpha = -self.cla_w * sm

        # Total CL_alpha including horizontal tail: CLa_tot = CLa_w + (S_t/S_w)*CLa_t*(1 - de/da)
        cla_tot = self.cla_w + (self.S_t / self.S_w) * self.cla_t * (1.0 - self.d_eps_d_alpha)

        # Zero-alpha moments
        # Cm0_total = Cm0_wing - V_h * CLa_t * (i_tail - eps_0)
        cm0_tot = self.cm0_wing + 0.16  # Tail preset incidence +2.5 deg

        A = np.array([
            [cla_tot, self.cl_de],
            [cm_alpha, self.cm_de]
        ])
        b = np.array([
            cl_req - self.cl0_wing,
            -cm0_tot
        ])

        try:
            sol = np.linalg.solve(A, b)
            alpha_trim_rad = float(sol[0])
            de_trim_rad = float(sol[1])
        except np.linalg.LinAlgError:
            alpha_trim_rad = 0.05
            de_trim_rad = 0.0

        alpha_trim_deg = math.degrees(alpha_trim_rad)
        de_trim_deg = math.degrees(de_trim_rad)

        saturated = (de_trim_deg < self.elevator_min_deg) or (de_trim_deg > self.elevator_max_deg)

        return TrimSolution(
            airspeed_ms=round(airspeed_ms, 2),
            alpha_trim_deg=round(alpha_trim_deg, 2),
            delta_e_trim_deg=round(de_trim_deg, 2),
            cl_trim=round(cl_req, 3),
            dynamic_pressure_pa=round(q, 1),
            is_elevator_saturated=saturated
        )

    def analyze_dbf_mission_stages(self) -> Dict[str, Dict]:
        """
        Evaluates stability and trim across all 4 AIAA DBF mission loading conditions:
        1. Ferry / Empty dry flight
        2. Mission 2 Full Cargo flight
        3. Mission 3 Pre-Drop carrying 12 payload packages
        4. Mission 3 Post-Drop immediate transition (sudden CG shift)
        """
        stages = [
            MissionCGConfig("FERRY_EMPTY", 12.70, 26.5, "Dry aircraft with no payload"),
            MissionCGConfig("MISSION_2_CARGO", 24.85, 27.8, "Max payload internal cargo configuration"),
            MissionCGConfig("MISSION_3_PRE_DROP", 23.90, 28.2, "External payload dispenser full"),
            MissionCGConfig("MISSION_3_POST_DROP", 15.50, 34.5, "Post-drop immediate state with +44mm aft CG shift")
        ]

        results = {}
        for stg in stages:
            stab = self.evaluate_longitudinal_stability(stg.cg_pct_mac)
            trim_cruise = self.solve_trim(airspeed_ms=24.5, mass_kg=stg.mass_kg, cg_pct_mac=stg.cg_pct_mac)
            trim_slow = self.solve_trim(airspeed_ms=16.5, mass_kg=stg.mass_kg, cg_pct_mac=stg.cg_pct_mac)

            results[stg.name] = {
                "config": stg,
                "stability": stab,
                "trim_cruise_24ms": trim_cruise,
                "trim_slow_16ms": trim_slow
            }

        return results

    def compute_aileron_reversal(self,
                                 torsional_stiffness_gj_nm2: float = 4850.0,
                                 dive_speed_ms: float = 35.0) -> AeroelasticMargin:
        """
        Calculates aeroelastic aileron control reversal speed (V_R).
        Reversal occurs when dynamic pressure twists wing box, completely neutralizing aileron roll authority:
        q_R = (G * J / L_span) / (e * c^2 * S_aileron * (CLa / CLa_da) * (-dCm/dda))
        """
        semi_span = self.b_w / 2.0
        c_mean = self.c_mac

        # Distance between aerodynamic center and elastic axis e = (x_ea - x_ac)
        # Elastic axis at carbon spar web (~35% chord), AC at ~24% chord -> e = 0.11 * c
        e_offset = 0.11 * c_mean

        # Aileron derivatives
        cla_da = 2.10    # per rad
        cm_da = -0.45    # per rad (pitching moment induced by aileron deflection)
        s_aileron = 0.082 # m^2

        # Equivalent torsional spring stiffness K_theta = G * J / semi_span
        k_theta = torsional_stiffness_gj_nm2 / semi_span

        # Dynamic pressure at reversal
        # q_R = -k_theta * cla_da / (e_offset * c_mean * s_aileron * self.cla_w * cm_da)
        denom = e_offset * c_mean * s_aileron * abs(cm_da) * (self.cla_w / cla_da)
        q_reversal = k_theta / max(denom, 1e-6)

        # Airspeed at reversal
        v_reversal = math.sqrt((2.0 * q_reversal) / self.rho)

        sf = v_reversal / dive_speed_ms
        is_safe = (sf >= 1.35) and (v_reversal > dive_speed_ms * 1.35)

        return AeroelasticMargin(
            torsional_stiffness_nm_rad=round(k_theta, 1),
            reversal_dynamic_pressure_pa=round(q_reversal, 1),
            aileron_reversal_speed_ms=round(v_reversal, 2),
            dive_speed_ms=round(dive_speed_ms, 2),
            reversal_safety_factor=round(sf, 2),
            is_aeroelastically_safe=is_safe
        )

    def evaluate_dutch_roll_damping(self,
                                    airspeed_ms: float = 24.5,
                                    izz_kgm2: float = 2.25,
                                    cn_beta: float = 0.095,
                                    cn_r: float = -0.180) -> Dict[str, float]:
        """
        Evaluates lateral-directional Dutch-roll natural frequency (omega_n)
        and damping ratio (zeta) according to MIL-F-8785C standards.
        """
        q = 0.5 * self.rho * (airspeed_ms**2)
        b = self.b_w
        s = self.S_w

        # Dutch roll natural frequency: omega_n^2 = (q * S * b * Cn_beta) / Izz
        omega_n2 = (q * s * b * cn_beta) / izz_kgm2
        omega_n = math.sqrt(max(omega_n2, 1e-4))

        # Damping: 2 * zeta * omega_n = -(q * S * b^2 * Cn_r) / (2 * Izz * V)
        damping_term = -(q * s * (b**2) * cn_r) / (2.0 * izz_kgm2 * airspeed_ms)
        zeta = damping_term / (2.0 * omega_n)

        return {
            "airspeed_ms": airspeed_ms,
            "omega_n_rad_s": round(omega_n, 3),
            "frequency_hz": round(omega_n / (2.0 * math.pi), 3),
            "damping_ratio_zeta": round(zeta, 3),
            "meets_mil_spec": zeta >= 0.08  # MIL-F-8785C Level 1 requirement
        }
