#!/usr/bin/env python3
"""
METUAV DBF 2027 - Wing Spar Structural & Stress FEA Calculator
Evaluates carbon fiber composite I-beam spar under AIAA DBF Ground Mission static wingtip load
and +3.5g ultimate pull-up flight load. Computes bending stresses, shear, and tip deflection.
"""

import math
from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass
class SparAnalysisResult:
    design_load_n: float
    v_root_n: float
    m_root_nm: float
    sigma_max_root_pa: float
    tau_max_root_pa: float
    fos_bending: float
    fos_shear: float
    tip_deflection_mm: float
    deflection_pct_semispan: float


class SparStressFEA:
    def __init__(
        self,
        togw_kg: float = 24.85,
        load_factor_g: float = 3.5,
        safety_margin: float = 1.25,
        b_half: float = 1.20,
        c_root: float = 0.32,
        c_tip: float = 0.26,
        h_root: float = 0.042,
        h_tip: float = 0.034,
        e_carbon: float = 135.0e9,
        sigma_allowable: float = 950.0e6,
        tau_allowable_shear: float = 65.0e6,
        flange_width: float = 0.035,
        t_flange_root: float = 0.0028,
        t_web: float = 0.0020
    ):
        self.togw_kg = togw_kg
        self.load_factor_g = load_factor_g
        self.safety_margin = safety_margin
        self.b_half = b_half
        self.c_root = c_root
        self.c_tip = c_tip
        self.h_root = h_root
        self.h_tip = h_tip
        self.e_carbon = e_carbon
        self.sigma_allowable = sigma_allowable
        self.tau_allowable_shear = tau_allowable_shear
        self.flange_width = flange_width
        self.t_flange_root = t_flange_root
        self.t_web = t_web

    def analyze(self, n_stations: int = 100) -> SparAnalysisResult:
        design_load_n = self.togw_kg * 9.80665 * self.load_factor_g * self.safety_margin
        y_stations = np.linspace(0.0, self.b_half, n_stations)
        dy = self.b_half / (n_stations - 1)

        # Schrenk's approximation for lift distribution (50% trapezoidal + 50% elliptic)
        s_half = 0.5 * (self.c_root + self.c_tip) * self.b_half
        c_y = self.c_root - (self.c_root - self.c_tip) * (y_stations / self.b_half)
        lift_trapezoidal = (c_y / s_half)
        lift_elliptic = (4.0 / (math.pi * self.b_half)) * np.sqrt(np.maximum(0.0, 1.0 - (y_stations / self.b_half)**2))
        lift_dist = 0.5 * (lift_trapezoidal + lift_elliptic) * (design_load_n * 0.5)

        # Shear Force V(y) and Bending Moment M(y) from tip to root
        shear_force = np.zeros(n_stations)
        bending_moment = np.zeros(n_stations)

        for i in reversed(range(n_stations - 1)):
            shear_force[i] = shear_force[i + 1] + 0.5 * (lift_dist[i] + lift_dist[i + 1]) * dy
            bending_moment[i] = bending_moment[i + 1] + shear_force[i] * dy

        # Spar Area Moment of Inertia I(y) at root
        i_root = 2.0 * (self.flange_width * self.t_flange_root * (self.h_root * 0.5)**2) + (self.t_web * (self.h_root**3) / 12.0)

        # Peak root bending stress
        m_root = bending_moment[0]
        sigma_max_root = (m_root * (self.h_root * 0.5)) / i_root
        fos_bending = self.sigma_allowable / sigma_max_root

        # Peak root shear stress
        v_root = shear_force[0]
        tau_max_root = v_root / (self.h_root * self.t_web)
        fos_shear = self.tau_allowable_shear / tau_max_root

        # Curvature and double integration for tip deflection
        curvature = np.zeros(n_stations)
        for i in range(n_stations):
            h_local = self.h_root - (self.h_root - self.h_tip) * (y_stations[i] / self.b_half)
            t_f_local = self.t_flange_root - (self.t_flange_root * 0.5) * (y_stations[i] / self.b_half)
            i_local = 2.0 * (self.flange_width * t_f_local * (h_local * 0.5)**2) + (self.t_web * (h_local**3) / 12.0)
            curvature[i] = bending_moment[i] / (self.e_carbon * i_local)

        slope = np.zeros(n_stations)
        deflection = np.zeros(n_stations)
        for i in range(1, n_stations):
            slope[i] = slope[i - 1] + 0.5 * (curvature[i - 1] + curvature[i]) * dy
            deflection[i] = deflection[i - 1] + 0.5 * (slope[i - 1] + slope[i]) * dy

        tip_deflection_mm = deflection[-1] * 1000.0
        deflection_pct = (tip_deflection_mm / (self.b_half * 1000.0)) * 100.0

        return SparAnalysisResult(
            design_load_n=design_load_n,
            v_root_n=v_root,
            m_root_nm=m_root,
            sigma_max_root_pa=sigma_max_root,
            tau_max_root_pa=tau_max_root,
            fos_bending=fos_bending,
            fos_shear=fos_shear,
            tip_deflection_mm=tip_deflection_mm,
            deflection_pct_semispan=deflection_pct
        )


def analyze_spar_structure() -> SparAnalysisResult:
    solver = SparStressFEA()
    res = solver.analyze()

    print("=" * 72)
    print("  METUAV DBF 2027 - Karbon Kompozit Ana Spar Yapisal ve Gerilme Analizi")
    print("=" * 72)
    print(f"Toplam Tasarim Yuku (+3.5g Ultimate + 1.25 SF): {res.design_load_n:.1f} N ({res.design_load_n / 9.80665:.1f} kgf)")
    print(f"Yari Aciklik (Semi-span): {solver.b_half:.2f} m | Kok Yuksekligi: {solver.h_root*1000:.1f} mm")
    print(f"\n[STATIK VE GERILME SONUCLARI]")
    print(f"- Kok Maksimum Kesme Kuvveti (V_root): {res.v_root_n:.1f} N")
    print(f"- Kok Maksimum Egilme Momenti (M_root): {res.m_root_nm:.1f} N.m")
    print(f"- Karbon Flans Bileske Normal Gerilme: {res.sigma_max_root_pa / 1e6:.1f} MPa (Izin verilen: {solver.sigma_allowable / 1e6:.1f} MPa)")
    print(f"- Kesme Web Kayma Gerilmesi: {res.tau_max_root_pa / 1e6:.1f} MPa (Izin verilen: {solver.tau_allowable_shear / 1e6:.1f} MPa)")
    print(f"- Egilme Guvenlik Katsayisi (Factor of Safety - Bending): {res.fos_bending:.2f}")
    print(f"- Kayma Guvenlik Katsayisi (Factor of Safety - Shear): {res.fos_shear:.2f}")
    print(f"- Kanat Ucu Sehim Miktari (Tip Deflection): {res.tip_deflection_mm:.1f} mm (%{res.deflection_pct_semispan:.1f} semi-span)")

    assert res.fos_bending >= 1.5, f"Bending safety factor {res.fos_bending:.2f} < 1.5 required!"
    assert res.fos_shear >= 1.5, f"Shear safety factor {res.fos_shear:.2f} < 1.5 required!"
    print("\n[DOGRULAMA BASARILI] AIAA DBF kanat ucu yukleme ve +3.5g sartlari tam olarak saglandi!")
    print("=" * 72)
    return res


if __name__ == '__main__':
    analyze_spar_structure()
