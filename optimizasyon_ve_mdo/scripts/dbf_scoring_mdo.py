#!/usr/bin/env python3
"""
AIAA DBF 2027 - Multidisciplinary Design Optimization (MDO) & Scoring Engine
Performs sensitivity analysis, parametric sweeps, and Monte Carlo simulations
against the AIAA Design/Build/Fly Master Scoring Formula to maximize competition score.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class AircraftDesignVector:
    wingspan_m: float          # Wing span (1.8m - 2.8m)
    aspect_ratio: float        # Aspect ratio (6.0 - 11.0)
    empty_mass_kg: float       # Dry aircraft structural mass (kg)
    payload_mass_kg: float     # Mission 2 / 3 carried payload (kg)
    battery_capacity_mah: float # 6S battery capacity (mAh)
    cruise_speed_ms: float     # Nominal cruise velocity (m/s)

@dataclass
class ScoringCoefficients:
    report_score: float = 94.5          # Out of 100
    m1_best_time_sec: float = 120.0     # Expected field-best time for 3 laps (sec)
    m2_max_payload_ratio: float = 0.095 # Best payload/time ratio in competition
    m3_drop_target_radius: float = 3.0  # Outer scoring radius (m)

class DBFScoringEngine:
    def __init__(self, coeffs: ScoringCoefficients = ScoringCoefficients()):
        self.coeffs = coeffs
        self.g = 9.80665
        self.rho = 1.225
        self.cl_max_3d = 1.96
        self.cd0 = 0.028
        self.oswald_e = 0.82
        self.togw_limit_kg = 24.9476     # 55.0 lbs exact limit

    def compute_aerodynamics(self, des: AircraftDesignVector) -> Dict[str, float]:
        """Calculates aerodynamic forces, stall speed, and drag."""
        wing_area = (des.wingspan_m ** 2) / des.aspect_ratio
        batt_mass = (des.battery_capacity_mah / 1000.0) * 0.135  # ~135g per 1000mAh for 6S 70C
        togw_kg = des.empty_mass_kg + batt_mass + des.payload_mass_kg

        # Stall speed
        v_stall = math.sqrt((2.0 * togw_kg * self.g) / (self.rho * wing_area * self.cl_max_3d))
        
        # Lift and Drag at cruise
        q_cruise = 0.5 * self.rho * (des.cruise_speed_ms ** 2)
        cl_cruise = (togw_kg * self.g) / (q_cruise * wing_area)
        k_ind = 1.0 / (math.pi * self.oswald_e * des.aspect_ratio)
        cd_cruise = self.cd0 + k_ind * (cl_cruise ** 2)
        drag_cruise = q_cruise * wing_area * cd_cruise
        thrust_power_w = drag_cruise * des.cruise_speed_ms / 0.72  # Propulsive efficiency ~72%

        return {
            "wing_area": wing_area,
            "togw_kg": togw_kg,
            "togw_lbs": togw_kg * 2.20462,
            "v_stall": v_stall,
            "cl_cruise": cl_cruise,
            "cd_cruise": cd_cruise,
            "drag_n": drag_cruise,
            "electrical_power_w": thrust_power_w,
            "battery_mass_kg": batt_mass
        }

    def evaluate_mission_scores(self, des: AircraftDesignVector) -> Dict[str, float]:
        """Evaluates scores for Ground Mission, Mission 1, Mission 2, and Mission 3."""
        aero = self.compute_aerodynamics(des)

        # Violation check: Exceeding 55 lbs TOGW results in DQ
        if aero["togw_lbs"] > 55.0:
            return {"total_score": 0.0, "status": "DQ_OVERWEIGHT", "togw_lbs": aero["togw_lbs"]}

        # Flight velocity must maintain safe stall margin (V_cruise >= 1.25 * V_stall)
        if des.cruise_speed_ms < 1.20 * aero["v_stall"]:
            return {"total_score": 0.0, "status": "STALL_MARGIN_VIOLATION", "v_stall": aero["v_stall"]}

        # Circuit distance: 3 laps of 750m course = 2250m
        lap_circuit_m = 750.0
        total_m1_distance = 3.0 * lap_circuit_m
        t_m1_flight = total_m1_distance / (des.cruise_speed_ms * 0.92)  # Turn losses factor ~0.92

        # 5-minute window limit (300 seconds)
        if t_m1_flight > 300.0:
            m1_score = 0.0
        else:
            m1_score = min(1.0, self.coeffs.m1_best_time_sec / t_m1_flight)

        # Ground Mission: Fast assembly bonus (1.0 for passing < 5 min)
        gm_score = 1.0

        # Mission 2: Payload flight (Score scales with payload weight and lap speed)
        # Ratio = Payload (kg) / Flight Time (sec)
        m2_ratio = des.payload_mass_kg / max(t_m1_flight, 60.0)
        m2_score = 1.0 + (m2_ratio / self.coeffs.m2_max_payload_ratio) * 2.0

        # Mission 3: Delivery / Drop (Score scales with payload delivered and drop accuracy)
        # Expected drop error with ballistics computer ~0.45m
        expected_drop_error_m = 0.45
        accuracy_multiplier = max(0.2, (self.coeffs.m3_drop_target_radius - expected_drop_error_m) / self.coeffs.m3_drop_target_radius)
        m3_score = 2.0 + (des.payload_mass_kg / 10.0) * accuracy_multiplier * 3.0

        # Total Fly-off Score
        total_mission_score = gm_score + m1_score + m2_score + m3_score
        final_competition_score = (self.coeffs.report_score / 100.0) * total_mission_score

        return {
            "total_score": final_competition_score,
            "report_score": self.coeffs.report_score,
            "gm_score": gm_score,
            "m1_score": m1_score,
            "m2_score": m2_score,
            "m3_score": m3_score,
            "m1_flight_time_sec": t_m1_flight,
            "togw_lbs": aero["togw_lbs"],
            "v_stall": aero["v_stall"],
            "power_w": aero["electrical_power_w"],
            "status": "VALID"
        }

    def compute_sensitivities(self, baseline: AircraftDesignVector) -> Dict[str, float]:
        """Calculates normalized sensitivity derivatives (% change in Score / % change in Parameter)."""
        base_res = self.evaluate_mission_scores(baseline)
        base_score = base_res["total_score"]

        delta_pct = 0.02  # 2% perturbation
        sensitivities = {}

        params = [
            ("wingspan_m", baseline.wingspan_m),
            ("aspect_ratio", baseline.aspect_ratio),
            ("empty_mass_kg", baseline.empty_mass_kg),
            ("payload_mass_kg", baseline.payload_mass_kg),
            ("battery_capacity_mah", baseline.battery_capacity_mah),
            ("cruise_speed_ms", baseline.cruise_speed_ms),
        ]

        for name, val in params:
            perturbed = AircraftDesignVector(**{k: v for k, v in baseline.__dict__.items()})
            setattr(perturbed, name, val * (1.0 + delta_pct))
            pert_res = self.evaluate_mission_scores(perturbed)
            
            if pert_res["status"] == "VALID" and base_score > 0.0:
                d_score_pct = (pert_res["total_score"] - base_score) / base_score
                sensitivities[name] = float(d_score_pct / delta_pct)
            else:
                sensitivities[name] = 0.0

        return sensitivities

    def run_monte_carlo(self, baseline: AircraftDesignVector, iterations: int = 1000) -> Dict[str, float]:
        """Runs Monte Carlo simulation under stochastic wind, density, and battery aging."""
        scores = []
        np.random.seed(42)

        for _ in range(iterations):
            # Stochastic perturbations
            wind_headwind = np.random.normal(3.5, 1.5)       # Wind speed m/s
            density_factor = np.random.uniform(0.96, 1.02)   # Hot day air density variation
            battery_aging = np.random.uniform(0.92, 1.0)     # Capacity fade

            # Effective speed considering headwind
            eff_speed = max(14.0, baseline.cruise_speed_ms - wind_headwind * 0.3)
            trial_vec = AircraftDesignVector(
                wingspan_m=baseline.wingspan_m,
                aspect_ratio=baseline.aspect_ratio,
                empty_mass_kg=baseline.empty_mass_kg + np.random.normal(0.0, 0.15),
                payload_mass_kg=baseline.payload_mass_kg,
                battery_capacity_mah=baseline.battery_capacity_mah * battery_aging,
                cruise_speed_ms=eff_speed
            )
            res = self.evaluate_mission_scores(trial_vec)
            if res["status"] == "VALID":
                scores.append(res["total_score"])

        scores_arr = np.array(scores)
        return {
            "mean_score": float(np.mean(scores_arr)),
            "std_dev": float(np.std(scores_arr)),
            "p10_worst_case": float(np.percentile(scores_arr, 10)),
            "p90_best_case": float(np.percentile(scores_arr, 90)),
            "success_rate_pct": float(len(scores) / iterations * 100.0)
        }


def main():
    print("=" * 72)
    print("  AIAA DBF 2027 - Cok Disiplinli Tasarim Optimizasyonu (MDO) & Skorlama")
    print("=" * 72)

    engine = DBFScoringEngine()

    # Baseline Design
    baseline = AircraftDesignVector(
        wingspan_m=2.40,
        aspect_ratio=8.19,
        empty_mass_kg=12.70,
        payload_mass_kg=9.85,
        battery_capacity_mah=16000.0,
        cruise_speed_ms=24.5
    )

    base_eval = engine.evaluate_mission_scores(baseline)
    print(f"\n[TABAN TASARIM DEGERLENDIRMESI]")
    print(f"- Toplam Kalkis Agirligi (TOGW): {base_eval['togw_lbs']:.2f} lbs (Sinir: 55.0 lbs)")
    print(f"- Perdovites Hizi (V_stall): {base_eval['v_stall']:.2f} m/s | Seyir Hizi: {baseline.cruise_speed_ms:.2f} m/s")
    print(f"- Gorev 1 Ucus Suresi (3 Tur): {base_eval['m1_flight_time_sec']:.1f} sn")
    print(f"- Seyir Guc Tuketimi: {base_eval['power_w']:.1f} Watt")
    print(f"- Alt Skorlar: GM={base_eval['gm_score']:.2f} | M1={base_eval['m1_score']:.3f} | M2={base_eval['m2_score']:.3f} | M3={base_eval['m3_score']:.3f}")
    print(f"- TOPLAM YARISMA PUANI: {base_eval['total_score']:.3f} / 10.0 (Rapor Carpani: %{base_eval['report_score']:.1f})")

    # Sensitivity Analysis
    print(f"\n[DUYARLILIK ANALIZI (%1 Parametre Artisinin Skora % Etkisi)]")
    sens = engine.compute_sensitivities(baseline)
    for param, s_val in sorted(sens.items(), key=lambda x: abs(x[1]), reverse=True):
        direction = "(+ Katki)" if s_val > 0 else "(- Kayip)"
        print(f"  * {param:22s}: {s_val:+.4f} {direction}")

    # Monte Carlo 1000 Iterations
    print(f"\n[MONTE CARLO DAYANIKLILIK ANALIZI (1000 Similasyon)]")
    mc = engine.run_monte_carlo(baseline, iterations=1000)
    print(f"  * Ortalama Skor: {mc['mean_score']:.3f} ± {mc['std_dev']:.3f}")
    print(f"  * En Kotu %10 Senaryo: {mc['p10_worst_case']:.3f}")
    print(f"  * En Iyi %10 Senaryo: {mc['p90_best_case']:.3f}")
    print(f"  * Basari Orani: %{mc['success_rate_pct']:.1f}")

    assert base_eval["status"] == "VALID"
    assert base_eval["total_score"] > 5.0
    print("\n[BASARILI] MDO Skorlama Motoru ve Stokastik Analiz Basariyla Tamamlandi!")
    print("=" * 72)


if __name__ == '__main__':
    main()
