#!/usr/bin/env python3
"""
AIAA DBF Open Engineering Framework - Flight Envelope & V-n Maneuver / Gust Diagram Analyzer
Computes:
- Aerodynamic stall lines for positive (+Cl_max) and negative (-Cl_max) lift
- Structural design load limits (+3.5g / -1.5g as per AIAA DBF / FAR 23)
- Maneuvering corner velocity (Va), cruise speed (Vc), dive speed (Vd)
- Pratt gust lines for 15 ft/s and 30 ft/s discrete gusts
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class AircraftParameters:
    togw_kg: float = 23.90          # 52.69 lbs
    wing_area_m2: float = 0.7032     # S
    wingspan_m: float = 2.40         # b
    cl_max_pos: float = 1.96        # Selig 1223 3D finite wing
    cl_max_neg: float = -0.90       # Inverted flap/camber
    cla_rad: float = 4.85           # dCL/dalpha (1/rad)
    limit_load_pos: float = 3.50    # +3.5g AIAA limit
    limit_load_neg: float = -1.50   # -1.5g inverted limit
    rho: float = 1.225              # Sea level air density (kg/m3)


class FlightEnvelopeAnalyzer:
    def __init__(self, params: AircraftParameters = None):
        self.p = params or AircraftParameters()
        self.w_newton = self.p.togw_kg * 9.80665
        self.wing_loading = self.w_newton / self.p.wing_area_m2  # N/m2

    def calculate_corner_speeds(self) -> Dict[str, float]:
        """Compute key envelope design speeds in m/s and knots."""
        # Vs1 (1g stall speed)
        vs1 = math.sqrt((2.0 * self.wing_loading) / (self.p.rho * self.p.cl_max_pos))

        # Va (Corner maneuvering speed at limit +3.5g)
        va = vs1 * math.sqrt(self.p.limit_load_pos)

        # Vc (Design cruise speed) - nominal 24.5 m/s
        vc = max(24.5, 1.35 * vs1)

        # Vd (Design dive speed: minimum 1.25 * Vc)
        vd = 1.35 * vc

        # Vs_neg (Negative 1g stall speed)
        vs_neg = math.sqrt((2.0 * self.wing_loading) / (self.p.rho * abs(self.p.cl_max_neg)))

        return {
            "vs1_ms": vs1,
            "va_ms": va,
            "vc_ms": vc,
            "vd_ms": vd,
            "vs_neg_ms": vs_neg,
            "vs1_kts": vs1 * 1.94384,
            "va_kts": va * 1.94384,
            "vc_kts": vc * 1.94384,
            "vd_kts": vd * 1.94384,
        }

    def compute_pratt_gust_factor(self) -> float:
        """Compute Pratt gust alleviation factor (Kg) as per FAR 23."""
        # Mean geometric chord
        c_bar = self.p.wing_area_m2 / self.p.wingspan_m
        mu_g = (2.0 * self.wing_loading) / (self.p.rho * c_bar * self.p.cla_rad * 9.80665)
        # Pratt alleviation factor formula: Kg = 0.88 * mu_g / (5.3 + mu_g)
        kg = (0.88 * mu_g) / (5.3 + mu_g)
        return float(kg)

    def compute_gust_load_increment(self, speed_ms: float, gust_speed_ms: float) -> float:
        """Calculate load factor increment Delta_n = (Kg * rho * Cla * V * Ude) / (2 * (W/S))."""
        kg = self.compute_pratt_gust_factor()
        delta_n = (kg * self.p.rho * self.p.cla_rad * speed_ms * gust_speed_ms) / (2.0 * self.wing_loading)
        return float(delta_n)

    def generate_envelope_curves(self, v_max: float = 38.0, n_points: int = 150) -> Dict[str, np.ndarray]:
        """Generate arrays for plotting the complete V-n envelope."""
        v_arr = np.linspace(0.1, v_max, n_points)

        # Stall limits as function of speed
        q_arr = 0.5 * self.p.rho * (v_arr ** 2)
        n_pos_stall = (q_arr * self.p.cl_max_pos) / self.wing_loading
        n_neg_stall = -(q_arr * abs(self.p.cl_max_neg)) / self.wing_loading

        # Cap by structural limits
        n_pos_envelope = np.minimum(n_pos_stall, self.p.limit_load_pos)
        n_neg_envelope = np.maximum(n_neg_stall, self.p.limit_load_neg)

        speeds = self.calculate_corner_speeds()
        vd = speeds["vd_ms"]

        # Mask after Vd
        mask = v_arr <= vd
        return {
            "v_arr": v_arr,
            "n_pos_stall": n_pos_stall,
            "n_neg_stall": n_neg_stall,
            "n_pos_envelope": n_pos_envelope,
            "n_neg_envelope": n_neg_envelope,
            "speeds": speeds,
            "mask_dive": mask
        }


def run_envelope_analysis():
    analyzer = FlightEnvelopeAnalyzer()
    res = analyzer.calculate_corner_speeds()
    kg = analyzer.compute_pratt_gust_factor()
    dn_gust = analyzer.compute_gust_load_increment(speed_ms=res["vc_ms"], gust_speed_ms=6.0)

    print("=" * 72)
    print("  AIAA DBF OPEN FRAMEWORK - UÇUŞ ZARFI VE V-n DİYAGRAMI ANALİZİ")
    print("=" * 72)
    print(f"  TOGW (Kalkış Kütlesi)   : {analyzer.p.togw_kg:.2f} kg ({analyzer.p.togw_kg*2.20462:.2f} lbs)")
    print(f"  Kanat Yüklemesi (W/S)   : {analyzer.wing_loading:.1f} N/m²")
    print(f"  Perdövites Hızı (Vs1)   : {res['vs1_ms']:.2f} m/s ({res['vs1_kts']:.1f} knot)")
    print(f"  Köşe Manevra Hızı (Va)  : {res['va_ms']:.2f} m/s ({res['va_kts']:.1f} knot)")
    print(f"  Seyir Hızı (Vc)         : {res['vc_ms']:.2f} m/s ({res['vc_kts']:.1f} knot)")
    print(f"  Tasarım Dalış Hızı (Vd) : {res['vd_ms']:.2f} m/s ({res['vd_kts']:.1f} knot)")
    print(f"  Pratt Gust Faktörü (Kg) : {kg:.4f}")
    print(f"  6.0 m/s Rüzgar Hamlesi  : Delta_n = {dn_gust:+.2f}g (Zirve n = {1.0+dn_gust:.2f}g <= +3.5g)")
    print("=" * 72)


if __name__ == "__main__":
    run_envelope_analysis()
