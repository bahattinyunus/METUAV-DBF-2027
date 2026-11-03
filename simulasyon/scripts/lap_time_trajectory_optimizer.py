#!/usr/bin/env python3
"""
METUAV DBF 2027 - Multi-Lap Racing Trajectory & Energy Optimizer
Simulates and optimizes flight performance across the official AIAA DBF competition course:
- 1000 ft (304.8m) straightaway sprint
- High-G coordinated pylon turns (180° / 360°)
- Calculates energy consumption (Wh, mAh), sector-by-sector lap times, and max lap endurance in 5-minute window.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class TrajectorySector:
    sector_name: str
    length_m: float
    duration_s: float
    entry_airspeed_ms: float
    exit_airspeed_ms: float
    mean_bank_deg: float
    load_factor_g: float
    mean_thrust_n: float
    mean_power_w: float
    energy_consumed_wh: float
    energy_consumed_mah: float


@dataclass
class LapSummary:
    lap_number: int
    lap_time_s: float
    total_distance_m: float
    average_speed_ms: float
    peak_g_load: float
    lap_energy_wh: float
    lap_energy_mah: float
    remaining_battery_mah: float
    battery_soc_pct: float
    sectors: List[TrajectorySector]


class LapTimeTrajectoryOptimizer:
    """
    Trajectory and propulsion energy integrator over the AIAA DBF race circuit.
    Solves 2D/3D dynamic flight path equations taking into account aerodynamic drag,
    induced drag from turn load factor, propeller efficiency, and battery discharge kinetics.
    """

    def __init__(self,
                 mass_kg: float = 24.85,
                 wing_area_m2: float = 0.7032,
                 aspect_ratio: float = 8.19,
                 cd0: float = 0.032,
                 oswald_e: float = 0.88,
                 battery_capacity_mah: float = 16000.0,
                 battery_nominal_v: float = 22.8,  # 6S LiPo nominal voltage
                 propulsive_efficiency: float = 0.74,
                 max_thrust_n: float = 145.0):
        self.mass = mass_kg
        self.S_w = wing_area_m2
        self.AR = aspect_ratio
        self.cd0 = cd0
        self.oswald_e = oswald_e
        self.batt_cap_mah = battery_capacity_mah
        self.v_batt = battery_nominal_v
        self.eta_prop = propulsive_efficiency
        self.max_thrust = max_thrust_n

        self.rho = 1.225
        self.g = 9.80665
        self.k_ind = 1.0 / (math.pi * self.oswald_e * self.AR)

        # DBF Official Course dimensions
        self.straight_length_m = 304.8  # 1000 ft runway length
        self.max_bank_limit_deg = 55.0  # Max structural / stall-safe bank angle
        self.max_g_limit = 2.80

    def compute_drag(self, airspeed_ms: float, load_factor: float = 1.0) -> float:
        """Calculates total aerodynamic drag including induced drag from turn load factor n."""
        q = 0.5 * self.rho * (airspeed_ms**2)
        weight = self.mass * self.g
        cl = (load_factor * weight) / max(q * self.S_w, 1e-4)

        cd = self.cd0 + self.k_ind * (cl**2)
        drag_n = q * self.S_w * cd
        return drag_n

    def compute_electrical_power(self, thrust_n: float, airspeed_ms: float) -> Tuple[float, float]:
        """Returns (electrical_power_w, battery_current_a)."""
        mech_power = thrust_n * airspeed_ms
        elec_power = mech_power / self.eta_prop
        elec_power = max(elec_power, 45.0)  # Avionics & idling baseline draw
        current_a = elec_power / self.v_batt
        return elec_power, current_a

    def simulate_straight_sector(self,
                                 name: str,
                                 length_m: float,
                                 v_entry: float,
                                 target_speed: float,
                                 dt: float = 0.05) -> Tuple[TrajectorySector, float]:
        """Simulates accelerating or cruising along straightaway sprint."""
        t = 0.0
        dist = 0.0
        v = v_entry
        total_energy_j = 0.0
        thrust_sum = 0.0
        power_sum = 0.0
        steps = 0

        while dist < length_m:
            drag = self.compute_drag(v, load_factor=1.0)
            if v < target_speed:
                thrust = min(self.max_thrust, drag + self.mass * 2.2)  # 2.2 m/s^2 forward acceleration
            else:
                thrust = drag  # Steady cruise

            accel = (thrust - drag) / self.mass
            v += accel * dt
            dist += v * dt
            t += dt

            p_elec, _ = self.compute_electrical_power(thrust, v)
            total_energy_j += p_elec * dt
            thrust_sum += thrust
            power_sum += p_elec
            steps += 1

        energy_wh = total_energy_j / 3600.0
        energy_mah = (energy_wh / self.v_batt) * 1000.0

        sector = TrajectorySector(
            sector_name=name,
            length_m=round(dist, 1),
            duration_s=round(t, 2),
            entry_airspeed_ms=round(v_entry, 2),
            exit_airspeed_ms=round(v, 2),
            mean_bank_deg=0.0,
            load_factor_g=1.0,
            mean_thrust_n=round(thrust_sum / steps, 1),
            mean_power_w=round(power_sum / steps, 1),
            energy_consumed_wh=round(energy_wh, 2),
            energy_consumed_mah=round(energy_mah, 1)
        )
        return sector, v

    def simulate_pylon_turn(self,
                            name: str,
                            turn_angle_deg: float,
                            v_entry: float,
                            bank_angle_deg: float,
                            dt: float = 0.05) -> Tuple[TrajectorySector, float]:
        """Simulates a high-G coordinated turn around an AIAA DBF pylon."""
        bank_rad = math.radians(min(bank_angle_deg, self.max_bank_limit_deg))
        load_factor = 1.0 / math.cos(bank_rad)
        v = v_entry

        # Coordinated turn radius & yaw rate
        radius = (v**2) / (self.g * math.tan(bank_rad))
        omega_turn = (self.g * math.tan(bank_rad)) / v  # rad/s

        arc_length = math.radians(turn_angle_deg) * radius
        dist = 0.0
        t = 0.0
        total_energy_j = 0.0
        thrust_sum = 0.0
        power_sum = 0.0
        steps = 0

        while dist < arc_length:
            drag = self.compute_drag(v, load_factor=load_factor)
            thrust = min(self.max_thrust, drag)  # Maintain speed in turn
            accel = (thrust - drag) / self.mass
            v += accel * dt
            dist += v * dt
            t += dt

            p_elec, _ = self.compute_electrical_power(thrust, v)
            total_energy_j += p_elec * dt
            thrust_sum += thrust
            power_sum += p_elec
            steps += 1

        energy_wh = total_energy_j / 3600.0
        energy_mah = (energy_wh / self.v_batt) * 1000.0

        sector = TrajectorySector(
            sector_name=name,
            length_m=round(dist, 1),
            duration_s=round(t, 2),
            entry_airspeed_ms=round(v_entry, 2),
            exit_airspeed_ms=round(v, 2),
            mean_bank_deg=round(bank_angle_deg, 1),
            load_factor_g=round(load_factor, 2),
            mean_thrust_n=round(thrust_sum / steps, 1),
            mean_power_w=round(power_sum / steps, 1),
            energy_consumed_wh=round(energy_wh, 2),
            energy_consumed_mah=round(energy_mah, 1)
        )
        return sector, v

    def simulate_single_lap(self,
                            lap_number: int,
                            initial_speed_ms: float,
                            cruise_speed_target: float,
                            bank_angle_deg: float,
                            current_batt_mah: float) -> Tuple[LapSummary, float, float]:
        """Simulates one complete regulation lap (Straight 1 -> Pylon 1 -> Straight 2 -> Pylon 2)."""
        sectors = []
        v_curr = initial_speed_ms

        # 1. Straightaway sprint leg 1
        s1, v_curr = self.simulate_straight_sector(
            "STRAIGHTAWAY_SPRINT_1", self.straight_length_m, v_curr, cruise_speed_target
        )
        sectors.append(s1)

        # 2. Pylon 1 turn (180 deg)
        p1, v_curr = self.simulate_pylon_turn(
            "PYLON_1_COORDINATED_TURN", 180.0, v_curr, bank_angle_deg
        )
        sectors.append(p1)

        # 3. Straightaway sprint leg 2
        s2, v_curr = self.simulate_straight_sector(
            "STRAIGHTAWAY_SPRINT_2", self.straight_length_m, v_curr, cruise_speed_target
        )
        sectors.append(s2)

        # 4. Pylon 2 turn (180 deg)
        p2, v_curr = self.simulate_pylon_turn(
            "PYLON_2_COORDINATED_TURN", 180.0, v_curr, bank_angle_deg
        )
        sectors.append(p2)

        # Aggregate lap performance
        lap_time = sum(s.duration_s for s in sectors)
        total_dist = sum(s.length_m for s in sectors)
        lap_energy_wh = sum(s.energy_consumed_wh for s in sectors)
        lap_energy_mah = sum(s.energy_consumed_mah for s in sectors)

        rem_mah = max(0.0, current_batt_mah - lap_energy_mah)
        soc_pct = (rem_mah / self.batt_cap_mah) * 100.0
        peak_g = max(s.load_factor_g for s in sectors)

        summary = LapSummary(
            lap_number=lap_number,
            lap_time_s=round(lap_time, 2),
            total_distance_m=round(total_dist, 1),
            average_speed_ms=round(total_dist / max(lap_time, 0.1), 2),
            peak_g_load=round(peak_g, 2),
            lap_energy_wh=round(lap_energy_wh, 2),
            lap_energy_mah=round(lap_energy_mah, 1),
            remaining_battery_mah=round(rem_mah, 1),
            battery_soc_pct=round(soc_pct, 1),
            sectors=sectors
        )

        return summary, v_curr, rem_mah

    def optimize_multi_lap_mission(self,
                                   target_laps: int = 3,
                                   racing_mode: str = "BALANCED") -> Dict:
        """
        Runs complete multi-lap mission optimization.
        Modes:
        - "AGGRESSIVE_RACING": Bank 50 deg, Sprint at 30 m/s (Fastest lap time)
        - "BALANCED": Bank 45 deg, Sprint at 26 m/s (Optimal endurance and speed)
        - "MAX_ENDURANCE": Bank 38 deg, Sprint at 22 m/s (Maximum lap count)
        """
        if racing_mode == "AGGRESSIVE_RACING":
            bank = 50.0
            v_cruise = 30.0
        elif racing_mode == "MAX_ENDURANCE":
            bank = 38.0
            v_cruise = 22.0
        else:  # BALANCED
            bank = 45.0
            v_cruise = 26.0

        v_curr = 18.0  # Exit speed from takeoff climbout
        batt_mah = self.batt_cap_mah

        laps: List[LapSummary] = []
        for i in range(1, target_laps + 1):
            lap, v_curr, batt_mah = self.simulate_single_lap(
                lap_number=i,
                initial_speed_ms=v_curr,
                cruise_speed_target=v_cruise,
                bank_angle_deg=bank,
                current_batt_mah=batt_mah
            )
            laps.append(lap)

        total_time_s = sum(l.lap_time_s for l in laps)
        total_energy_mah = sum(l.lap_energy_mah for l in laps)

        # Max laps achievable in 5.0 minute window (300 seconds)
        mean_lap_time = total_time_s / len(laps)
        mean_lap_mah = total_energy_mah / len(laps)

        laps_by_time = int(300.0 / mean_lap_time)
        laps_by_battery = int((self.batt_cap_mah * 0.80) / mean_lap_mah)  # 80% usable capacity
        max_possible_laps = min(laps_by_time, laps_by_battery)

        return {
            "mode": racing_mode,
            "bank_angle_deg": bank,
            "target_cruise_speed_ms": v_cruise,
            "completed_laps": len(laps),
            "total_mission_time_s": round(total_time_s, 2),
            "mean_lap_time_s": round(mean_lap_time, 2),
            "total_energy_consumed_mah": round(total_energy_mah, 1),
            "final_battery_soc_pct": round(laps[-1].battery_soc_pct, 1),
            "max_laps_in_5min_window": max_possible_laps,
            "laps": laps
        }
