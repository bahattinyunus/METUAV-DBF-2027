#!/usr/bin/env python3
"""
METUAV DBF 2027 - Advanced Composite Autoclave & Vacuum Bagging Cure Cycle Simulator
Simulates resin cure degree alpha(t), gelation threshold, dynamic viscosity evolution,
and exothermic peak temperature for Toray T700 / Epoxy aerospace wing skin and spar parts.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class CureStatePoint:
    time_min: float
    temperature_c: float
    cure_degree_alpha: float
    viscosity_pa_s: float
    exothermic_heat_w_kg: float
    is_gelled: bool


@dataclass
class CureCycleReport:
    total_cycle_time_min: float
    peak_part_temp_c: float
    final_cure_degree: float
    gelation_time_min: float
    min_viscosity_pa_s: float
    is_fully_cured: bool
    max_exotherm_delta_c: float


class CompositeCureSimulator:
    """
    Implements Kamal-Sourour autocatalytic cure kinetics and Castro-Macosko viscosity model:
    d(alpha)/dt = (k1 + k2 * alpha^m) * (1 - alpha)^n
    where ki = Ai * exp(-Ei / (R * T))
    """
    def __init__(
        self,
        resin_name: str = "Araldite LY5052 / Aradur 5052",
        part_thickness_mm: float = 2.5,
        total_heat_reaction_j_kg: float = 3.8e5,  # ~380 kJ/kg total heat of reaction
        specific_heat_resin: float = 1600.0,      # J / (kg * K)
        ambient_temp_c: float = 25.0
    ):
        self.resin_name = resin_name
        self.thickness_m = part_thickness_mm / 1000.0
        self.delta_h_total = total_heat_reaction_j_kg
        self.cp = specific_heat_resin
        self.t_amb = ambient_temp_c

        # Universal gas constant
        self.r_gas = 8.314  # J / (mol * K)
        self.t_ref_k = 298.15  # 25°C reference temperature

        # Kinetic parameters (Empirical values for aerospace epoxy systems)
        self.a1 = 1200.0    # 1/s
        self.e1 = 5.2e4     # J/mol
        self.a2 = 6500.0    # 1/s
        self.e2 = 4.8e4     # J/mol
        self.m = 0.55
        self.n = 1.45

        # Viscosity parameters
        self.eta_ref = 0.45  # Pa.s (initial low viscosity at 25°C)
        self.e_eta = 3.2e4   # J/mol
        self.alpha_gel = 0.42  # Gelation point threshold

    def calculate_rate_constants(self, temp_k: float) -> Tuple[float, float]:
        k1 = self.a1 * math.exp(-self.e1 / (self.r_gas * temp_k))
        k2 = self.a2 * math.exp(-self.e2 / (self.r_gas * temp_k))
        return k1, k2

    def calculate_viscosity(self, temp_k: float, alpha: float) -> float:
        """
        Modified Castro-Macosko viscosity model with relative Arrhenius temperature dependency:
        eta(T, alpha) = eta_ref * exp(E_eta/R * (1/T - 1/T_ref)) * (alpha_gel / (alpha_gel - alpha))^(1.6)
        """
        arrhenius_factor = math.exp((self.e_eta / self.r_gas) * (1.0 / temp_k - 1.0 / self.t_ref_k))
        if alpha >= self.alpha_gel:
            return 1e4  # Vitrified solid

        ratio = self.alpha_gel / max(self.alpha_gel - alpha, 1e-4)
        visc = self.eta_ref * arrhenius_factor * (ratio ** 1.6)
        return float(np.clip(visc, 0.01, 1e4))

    def simulate_two_step_cure(
        self,
        ramp1_rate_c_min: float = 2.0,
        dwell1_temp_c: float = 60.0,
        dwell1_time_min: float = 60.0,
        ramp2_rate_c_min: float = 1.5,
        dwell2_temp_c: float = 100.0,
        dwell2_time_min: float = 180.0,
        dt_sec: float = 2.0
    ) -> Tuple[List[CureStatePoint], CureCycleReport]:
        time_sec = 0.0
        alpha = 0.01  # Initial conversion
        part_temp_c = self.t_amb

        history: List[CureStatePoint] = []
        gelation_time_min = -1.0
        min_viscosity = 1e6
        peak_temp = self.t_amb
        max_exotherm = 0.0

        t_ramp1_end = (dwell1_temp_c - self.t_amb) / (ramp1_rate_c_min / 60.0)
        t_dwell1_end = t_ramp1_end + (dwell1_time_min * 60.0)
        t_ramp2_end = t_dwell1_end + (dwell2_temp_c - dwell1_temp_c) / (ramp2_rate_c_min / 60.0)
        total_sim_time_sec = t_ramp2_end + (dwell2_time_min * 60.0)

        # Thermal heat transfer parameters
        h_oven = 65.0           # W / m^2 K
        rho_composite = 1450.0  # kg/m^3
        l_char = max(self.thickness_m / 2.0, 0.0005)
        heat_coupling = h_oven / (rho_composite * l_char * self.cp)

        while time_sec <= total_sim_time_sec:
            time_min = time_sec / 60.0

            # Oven setpoint schedule
            if time_sec < t_ramp1_end:
                oven_temp_c = self.t_amb + (ramp1_rate_c_min / 60.0) * time_sec
            elif time_sec < t_dwell1_end:
                oven_temp_c = dwell1_temp_c
            elif time_sec < t_ramp2_end:
                oven_temp_c = dwell1_temp_c + (ramp2_rate_c_min / 60.0) * (time_sec - t_dwell1_end)
            else:
                oven_temp_c = dwell2_temp_c

            part_temp_k = max(part_temp_c + 273.15, 273.15)
            k1, k2 = self.calculate_rate_constants(part_temp_k)

            # Reaction rate
            d_alpha_dt = (k1 + k2 * (alpha ** self.m)) * ((1.0 - alpha) ** self.n)
            d_alpha_dt = max(0.0, min(d_alpha_dt, 0.05))

            # Exothermic heat generation
            q_exotherm = self.delta_h_total * d_alpha_dt
            q_reaction = q_exotherm / self.cp

            # Heat transfer balance
            d_tpart_dt = heat_coupling * (oven_temp_c - part_temp_c) + q_reaction

            # Semi-implicit Euler integration step
            alpha += d_alpha_dt * dt_sec
            alpha = min(alpha, 0.999)
            part_temp_c += d_tpart_dt * dt_sec

            # Tracking metrics
            if part_temp_c > peak_temp:
                peak_temp = part_temp_c
            exotherm_delta = max(0.0, part_temp_c - oven_temp_c)
            if exotherm_delta > max_exotherm:
                max_exotherm = exotherm_delta

            visc = self.calculate_viscosity(part_temp_k, alpha)
            if visc < min_viscosity:
                min_viscosity = visc

            is_gelled = alpha >= self.alpha_gel
            if is_gelled and gelation_time_min < 0:
                gelation_time_min = time_min

            # Sample every 60 seconds
            if int(time_sec) % 60 == 0:
                history.append(CureStatePoint(
                    time_min=time_min,
                    temperature_c=part_temp_c,
                    cure_degree_alpha=alpha,
                    viscosity_pa_s=visc,
                    exothermic_heat_w_kg=q_exotherm,
                    is_gelled=is_gelled
                ))

            time_sec += dt_sec

        report = CureCycleReport(
            total_cycle_time_min=total_sim_time_sec / 60.0,
            peak_part_temp_c=peak_temp,
            final_cure_degree=alpha,
            gelation_time_min=gelation_time_min,
            min_viscosity_pa_s=min_viscosity,
            is_fully_cured=alpha >= 0.90,
            max_exotherm_delta_c=max_exotherm
        )

        return history, report
