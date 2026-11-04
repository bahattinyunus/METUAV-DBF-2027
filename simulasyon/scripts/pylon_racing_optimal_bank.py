#!/usr/bin/env python3
"""
AIAA DBF Open Engineering Framework - Pylon Racing Optimal Bank & Energy Trajectory Solver
Optimizes:
- Pylon turn radius and coordinated bank angle (phi) under 0 - 12 m/s headwind/crosswind
- Dynamic load factor n(t) = 1/cos(phi) and induced drag spike during 180-deg turns
- Trade-off between aggressive high-g turn (shorter path) vs moderate turn (lower induced drag energy)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class RacingCondition:
    air_speed_ms: float = 24.5
    wind_speed_ms: float = 5.0
    wind_direction_deg: float = 0.0 # 0 deg = down the runway
    togw_kg: float = 23.90
    wing_area_m2: float = 0.7032
    aspect_ratio: float = 8.19
    oswald_e: float = 0.88
    straightaway_m: float = 304.8   # 1000 ft straightaway between pylons
    rho: float = 1.225


class PylonRacingOptimalBank:
    def __init__(self, condition: RacingCondition = None):
        self.c = condition or RacingCondition()
        self.w_newton = self.c.togw_kg * 9.80665

    def evaluate_turn_profile(self, bank_angle_deg: float) -> Dict[str, float]:
        """
        Evaluate time, distance, and energy consumption for a 180-degree turn
        given a constant coordinated bank angle.
        """
        phi_rad = math.radians(min(65.0, max(15.0, bank_angle_deg)))

        # Load factor
        n_load = 1.0 / math.cos(phi_rad)

        # Turn radius R = V^2 / (g * tan(phi))
        r_turn_m = (self.c.air_speed_ms ** 2) / (9.80665 * math.tan(phi_rad))

        # 180-degree turn distance
        turn_dist_m = math.pi * r_turn_m

        # Time to complete 180 turn
        turn_time_s = turn_dist_m / self.c.air_speed_ms

        # Dynamic pressure & Induced drag
        q = 0.5 * self.c.rho * (self.c.air_speed_ms ** 2)
        cl_turn = (n_load * self.w_newton) / (q * self.c.wing_area_m2)

        cd_ind = (cl_turn ** 2) / (math.pi * self.c.aspect_ratio * self.c.oswald_e)
        d_ind_n = q * self.c.wing_area_m2 * cd_ind

        # Parasitic drag (Cd0 ~ 0.024)
        cd0 = 0.024
        d_par_n = q * self.c.wing_area_m2 * cd0
        d_total_n = d_ind_n + d_par_n

        # Mechanical work required in Joules
        work_j = d_total_n * turn_dist_m

        # Power required in Watts
        power_w = d_total_n * self.c.air_speed_ms / 0.75  # 75% powertrain efficiency

        # Battery mAh drained (at nominal 22.2V 6S)
        mah_drain = (power_w * (turn_time_s / 3600.0) / 22.2) * 1000.0

        return {
            "bank_angle_deg": bank_angle_deg,
            "load_factor_g": n_load,
            "turn_radius_m": r_turn_m,
            "turn_time_s": turn_time_s,
            "cl_turn": cl_turn,
            "drag_n": d_total_n,
            "power_w": power_w,
            "mah_drain": mah_drain,
            "work_kj": work_j / 1000.0
        }

    def find_pareto_optimal_bank(self, bank_range_deg: Tuple[float, float] = (25.0, 60.0)) -> Dict[str, float]:
        """Scan bank angle spectrum to find fastest vs most energy-efficient angles."""
        angles = np.linspace(bank_range_deg[0], bank_range_deg[1], 70)
        results = [self.evaluate_turn_profile(a) for a in angles]

        # Minimum energy turn
        min_energy_res = min(results, key=lambda x: x["mah_drain"])

        # Fastest turn
        fastest_res = min(results, key=lambda x: x["turn_time_s"])

        # Balanced (compromise objective: time * energy)
        balanced_res = min(results, key=lambda x: x["turn_time_s"] * x["mah_drain"])

        return {
            "min_energy_bank_deg": min_energy_res["bank_angle_deg"],
            "min_energy_mah": min_energy_res["mah_drain"],
            "fastest_bank_deg": fastest_res["bank_angle_deg"],
            "fastest_time_s": fastest_res["turn_time_s"],
            "balanced_bank_deg": balanced_res["bank_angle_deg"],
            "balanced_time_s": balanced_res["turn_time_s"],
            "balanced_mah": balanced_res["mah_drain"]
        }


def run_racing_study():
    solver = PylonRacingOptimalBank()
    res = solver.find_pareto_optimal_bank()

    print("=" * 72)
    print("  AIAA DBF OPEN FRAMEWORK - PYLON PARKURU OPTİMUM YATIŞ VE ENERJİ ANALİZİ")
    print("=" * 72)
    print(f"  En Hızlı Dönüş Açısı : {res['fastest_bank_deg']:.1f}° (Dönüş Süresi: {res['fastest_time_s']:.2f} sn)")
    print(f"  En Verimli Dönüş Açısı: {res['min_energy_bank_deg']:.1f}° (Dönüş Enerjisi: {res['min_energy_mah']:.1f} mAh)")
    print(f"  Dengeli Yarış Açısı  : {res['balanced_bank_deg']:.1f}° (Süre: {res['balanced_time_s']:.2f} sn, {res['balanced_mah']:.1f} mAh)")
    print("=" * 72)


if __name__ == "__main__":
    run_racing_study()
