#!/usr/bin/env python3
"""
AIAA DBF Open Engineering Framework - LiPo Battery Pack Thermal & Cooling Duct Optimizer
Models:
- Transient heat generation during DBF flight profile: Joule heating I^2*R_int + Entropic reversible heat
- Temperature & SOC dependent battery internal resistance
- Forced air cooling via NACA/scoop duct (Dittus-Boelter convective heat transfer)
- Core-to-surface 2-node lumped capacitance thermal dynamics
- Duct drag penalty vs cell operating temperature optimization
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class BatteryPackConfig:
    cell_count_series: int = 6           # 6S LiPo
    cell_count_parallel: int = 2         # 2P (6S2P)
    cell_capacity_ah: float = 4.5        # 4.5 Ah per cell (Total 9.0 Ah)
    nominal_voltage_v: float = 22.2      # 3.7V * 6
    pack_mass_kg: float = 1.35           # Total battery mass
    specific_heat_cp: float = 950.0      # J / (kg * K) for LiPo pouch/cylindrical
    r_internal_mohm: float = 12.0        # Pack base internal resistance at 25C (mOhm)
    temp_ambient_c: float = 25.0         # Ambient OAT
    max_safe_temp_c: float = 60.0        # Max allowable safe temperature
    pack_surface_area_m2: float = 0.065  # Exposed surface area in duct


@dataclass
class CoolingDuctConfig:
    duct_inlet_area_cm2: float = 18.0    # Inlet cross-section area in cm^2
    duct_hydraulic_diam_m: float = 0.04  # Hydraulic diameter (D_h)
    ram_recovery_eff: float = 0.75       # Inlet dynamic pressure recovery
    air_density: float = 1.225           # kg/m^3
    air_viscosity: float = 1.81e-5       # Pa*s
    air_thermal_conductivity: float = 0.026 # W / (m * K)
    prandtl_number: float = 0.71


class BatteryThermalOptimizer:
    def __init__(self, pack: BatteryPackConfig = None, duct: CoolingDuctConfig = None):
        self.pack = pack or BatteryPackConfig()
        self.duct = duct or CoolingDuctConfig()

    def get_internal_resistance(self, temp_c: float, soc: float) -> float:
        """
        Internal resistance as a function of temperature and state of charge (SOC).
        At lower temps, R_int rises; at very low SOC, R_int rises.
        """
        temp_k = temp_c + 273.15
        ref_temp_k = 298.15 # 25 C
        # Arrhenius temperature scaling
        arrhenius_factor = math.exp(1200.0 * (1.0 / temp_k - 1.0 / ref_temp_k))
        # SOC penalty below 20%
        soc_factor = 1.0 + 0.8 * max(0.0, 0.2 - soc)**2
        return (self.pack.r_internal_mohm * 1e-3) * arrhenius_factor * soc_factor

    def compute_convection_coefficient(self, airspeed_ms: float) -> float:
        """
        Computes convective heat transfer coefficient h (W/m^2*K) using Dittus-Boelter.
        Air velocity inside duct is scaled by ram recovery and inlet ratio.
        """
        if airspeed_ms < 0.5:
            return 8.0 # Natural convection limit
        v_duct = airspeed_ms * math.sqrt(self.duct.ram_recovery_eff) * 0.55
        re = (self.duct.air_density * v_duct * self.duct.duct_hydraulic_diam_m) / self.duct.air_viscosity
        re = max(100.0, re)
        # Nu = 0.023 * Re^0.8 * Pr^0.4
        nu = 0.023 * (re ** 0.8) * (self.duct.prandtl_number ** 0.4)
        h = (nu * self.duct.air_thermal_conductivity) / self.duct.duct_hydraulic_diam_m
        return float(max(8.0, h))

    def simulate_mission_flight(self, mission_profile: List[Tuple[float, float, float]] = None) -> Dict[str, np.ndarray]:
        """
        Simulate mission profile.
        mission_profile is a list of tuples: (duration_s, current_amps, airspeed_ms)
        Default profile represents DBF 3-lap mission:
        - Takeoff run & initial climb: 15s @ 95A, 18 m/s
        - Lap 1 cruise & pylon turns: 50s @ 55A, 28 m/s
        - Lap 2 cruise & pylon turns: 50s @ 52A, 28 m/s
        - Lap 3 cruise & sprint: 50s @ 60A, 30 m/s
        - Approach & Landing: 20s @ 15A, 16 m/s
        """
        if mission_profile is None:
            mission_profile = [
                (15.0, 95.0, 18.0),
                (50.0, 55.0, 28.0),
                (50.0, 52.0, 28.0),
                (50.0, 60.0, 30.0),
                (20.0, 15.0, 16.0)
            ]

        dt = 0.5
        t_hist, temp_core_hist, temp_surf_hist, soc_hist, heat_gen_hist = [], [], [], [], []

        t_curr = 0.0
        temp_core = self.pack.temp_ambient_c
        temp_surf = self.pack.temp_ambient_c
        soc = 1.0 # 100% initial charge
        total_capacity_as = self.pack.cell_capacity_ah * self.pack.cell_count_parallel * 3600.0

        # Thermal masses & thermal resistance
        # Lumped 2-node: Core -> Surface (internal conduction) -> Air (convection)
        c_core = self.pack.pack_mass_kg * self.pack.specific_heat_cp * 0.70 # 70% thermal mass in core
        c_surf = self.pack.pack_mass_kg * self.pack.specific_heat_cp * 0.30 # 30% thermal mass at surface
        r_core_surf = 0.18 # K/W thermal conduction resistance from core to outer jacket

        for dur, current_a, v_air in mission_profile:
            n_steps = int(dur / dt)
            for _ in range(n_steps):
                r_int = self.get_internal_resistance(temp_core, soc)
                q_joule = (current_a ** 2) * r_int
                # Reversible entropic heat (approx 0.15 * Q_joule during high discharge)
                q_entropic = current_a * 0.002 * (temp_core + 273.15)
                q_gen = q_joule + q_entropic

                h_conv = self.compute_convection_coefficient(v_air)
                q_cond = (temp_core - temp_surf) / r_core_surf
                q_conv = h_conv * self.pack.pack_surface_area_m2 * (temp_surf - self.pack.temp_ambient_c)

                # Transient differential equations
                d_temp_core = (q_gen - q_cond) / c_core
                d_temp_surf = (q_cond - q_conv) / c_surf

                temp_core += d_temp_core * dt
                temp_surf += d_temp_surf * dt
                soc -= (current_a * dt) / total_capacity_as
                soc = max(0.01, soc)
                t_curr += dt

                t_hist.append(t_curr)
                temp_core_hist.append(temp_core)
                temp_surf_hist.append(temp_surf)
                soc_hist.append(soc)
                heat_gen_hist.append(q_gen)

        return {
            "time_s": np.array(t_hist),
            "temp_core_c": np.array(temp_core_hist),
            "temp_surf_c": np.array(temp_surf_hist),
            "soc": np.array(soc_hist),
            "heat_gen_w": np.array(heat_gen_hist),
            "max_core_temp_c": float(np.max(temp_core_hist)),
            "max_surf_temp_c": float(np.max(temp_surf_hist)),
            "remaining_soc_pct": float(soc * 100.0)
        }

    def compute_cooling_drag_penalty(self, airspeed_ms: float = 28.0) -> float:
        """
        Calculates the aerodynamic cooling drag (Newtons) introduced by the duct.
        Duct drag = Cd_duct * 0.5 * rho * V^2 * A_inlet
        """
        q_inf = 0.5 * self.duct.air_density * (airspeed_ms ** 2)
        inlet_m2 = self.duct.duct_inlet_area_cm2 * 1e-4
        cd_duct = 0.22 # Typical NACA submerged scoop with internal friction
        return float(cd_duct * q_inf * inlet_m2)


def run_battery_analysis():
    pack = BatteryPackConfig()
    duct = CoolingDuctConfig(duct_inlet_area_cm2=18.0)
    optimizer = BatteryThermalOptimizer(pack, duct)
    res = optimizer.simulate_mission_flight()

    print("=" * 72)
    print("  AIAA DBF OPEN FRAMEWORK - BATARYA TERMAL PAKET VE SOĞUTMA ANALİZİ")
    print("=" * 72)
    print(f"  Batarya Paketi           : {pack.cell_count_series}S{pack.cell_count_parallel}P LiPo ({pack.nominal_voltage_v}V, {pack.cell_capacity_ah*pack.cell_count_parallel:.1f}Ah)")
    print(f"  Toplam Batarya Ağırlığı  : {pack.pack_mass_kg:.2f} kg")
    print(f"  Ortam Sıcaklığı (OAT)    : {pack.temp_ambient_c:.1f} °C")
    print(f"  Maksimum Çekirdek Sıcaklık: {res['max_core_temp_c']:.1f} °C (Emniyet Sınırı: {pack.max_safe_temp_c:.1f} °C)")
    print(f"  Maksimum Yüzey Sıcaklığı : {res['max_surf_temp_c']:.1f} °C")
    print(f"  Kalan Batarya Kapasitesi : %{res['remaining_soc_pct']:.1f}")
    print(f"  Kanal Soğutma Sürüklemesi: {optimizer.compute_cooling_drag_penalty():.3f} N")
    print("=" * 72)


if __name__ == "__main__":
    run_battery_analysis()
