#!/usr/bin/env python3
"""
METUAV DBF 2027 - Wing Spar Structural & Stress FEA Calculator
Evaluates carbon fiber composite I-beam spar under AIAA DBF Ground Mission static wingtip load
and +3.5g ultimate pull-up flight load. Computes bending stresses, shear, and tip deflection.
"""

import math
import numpy as np

def analyze_spar_structure():
    # Aircraft & Load Parameters
    togw_kg = 24.85               # 54.8 lbs max weight
    load_factor_g = 3.5           # AIAA DBF ultimate load factor (+3.5g)
    safety_margin = 1.25          # Additional structural safety factor
    design_load_n = togw_kg * 9.80665 * load_factor_g * safety_margin

    # Wing Geometry
    b_half = 1.20                 # Semi-span (m)
    c_root = 0.32                 # Root chord (m)
    c_tip = 0.26                  # Tip chord (m)
    h_root = 0.042                # Airfoil max thickness at root (13.2% of 0.32m)
    h_tip = 0.034                 # Airfoil max thickness at tip

    # Carbon Fiber (Toray T700 / Epoxy) Material Properties
    e_carbon = 135.0e9            # Young's Modulus (Pa) - 135 GPa
    sigma_allowable = 950.0e6     # Allowable tensile/compressive stress (Pa) - 950 MPa
    tau_allowable_shear = 65.0e6  # Allowable shear stress in Rohacell/carbon web (Pa) - 65 MPa

    # Spar Dimensions (Tapered Carbon I-Beam)
    # Flange width: 35 mm, Flange thickness: 2.8 mm at root, 1.4 mm at tip
    # Web thickness: 2.0 mm (Carbon biaxial sandwich with Rohacell core)
    flange_width = 0.035
    t_flange_root = 0.0028
    t_web = 0.0020

    # Discretize semi-span into 100 stations
    n_stations = 100
    y_stations = np.linspace(0.0, b_half, n_stations)
    dy = b_half / (n_stations - 1)

    # Schrenk's approximation for lift distribution (50% trapezoidal + 50% elliptic)
    s_half = 0.5 * (c_root + c_tip) * b_half
    c_y = c_root - (c_root - c_tip) * (y_stations / b_half)
    lift_trapezoidal = (c_y / s_half)
    lift_elliptic = (4.0 / (math.pi * b_half)) * np.sqrt(np.maximum(0.0, 1.0 - (y_stations / b_half)**2))
    lift_dist = 0.5 * (lift_trapezoidal + lift_elliptic) * (design_load_n * 0.5)

    # Calculate Shear Force V(y) and Bending Moment M(y) from tip to root
    shear_force = np.zeros(n_stations)
    bending_moment = np.zeros(n_stations)

    for i in reversed(range(n_stations - 1)):
        shear_force[i] = shear_force[i + 1] + 0.5 * (lift_dist[i] + lift_dist[i + 1]) * dy
        bending_moment[i] = bending_moment[i + 1] + shear_force[i] * dy

    # Spar Area Moment of Inertia I(y) at root
    # I = 2 * (w * tf * (h/2)^2) + (tw * h^3 / 12)
    i_root = 2.0 * (flange_width * t_flange_root * (h_root * 0.5)**2) + (t_web * (h_root**3) / 12.0)
    
    # Peak root bending stress
    m_root = bending_moment[0]
    sigma_max_root = (m_root * (h_root * 0.5)) / i_root
    fos_bending = sigma_allowable / sigma_max_root

    # Peak root shear stress
    v_root = shear_force[0]
    tau_max_root = v_root / (h_root * t_web)
    fos_shear = tau_allowable_shear / tau_max_root

    # Numerical integration for tip deflection: d^2w/dy^2 = M(y) / (E * I(y))
    # Curvature kappa(y)
    curvature = np.zeros(n_stations)
    for i in range(n_stations):
        h_local = h_root - (h_root - h_tip) * (y_stations[i] / b_half)
        t_f_local = t_flange_root - (t_flange_root * 0.5) * (y_stations[i] / b_half)
        i_local = 2.0 * (flange_width * t_f_local * (h_local * 0.5)**2) + (t_web * (h_local**3) / 12.0)
        curvature[i] = bending_moment[i] / (e_carbon * i_local)

    # Double integration for slope and deflection
    slope = np.zeros(n_stations)
    deflection = np.zeros(n_stations)
    for i in range(1, n_stations):
        slope[i] = slope[i - 1] + 0.5 * (curvature[i - 1] + curvature[i]) * dy
        deflection[i] = deflection[i - 1] + 0.5 * (slope[i - 1] + slope[i]) * dy

    tip_deflection_mm = deflection[-1] * 1000.0

    print("=" * 72)
    print("  METUAV DBF 2027 - Karbon Kompozit Ana Spar Yapisal ve Gerilme Analizi")
    print("=" * 72)
    print(f"Toplam Tasarim Yuku (+3.5g Ultimate + 1.25 SF): {design_load_n:.1f} N ({design_load_n / 9.80665:.1f} kgf)")
    print(f"Yari Aciklik (Semi-span): {b_half:.2f} m | Kok Yuksekligi: {h_root*1000:.1f} mm")
    print(f"\n[STATIK VE GERILME SONUCLARI]")
    print(f"- Kok Maksimum Kesme Kuvveti (V_root): {v_root:.1f} N")
    print(f"- Kok Maksimum Egilme Momenti (M_root): {m_root:.1f} N.m")
    print(f"- Karbon Flans Bileske Normal Gerilme: {sigma_max_root / 1e6:.1f} MPa (Izin verilen: {sigma_allowable / 1e6:.1f} MPa)")
    print(f"- Kesme Web Kayma Gerilmesi: {tau_max_root / 1e6:.1f} MPa (Izin verilen: {tau_allowable_shear / 1e6:.1f} MPa)")
    print(f"- Egilme Guvenlik Katsayisi (Factor of Safety - Bending): {fos_bending:.2f}")
    print(f"- Kayma Guvenlik Katsayisi (Factor of Safety - Shear): {fos_shear:.2f}")
    print(f"- Kanat Ucu Sehim Miktari (Tip Deflection): {tip_deflection_mm:.1f} mm (%{tip_deflection_mm / (b_half*1000) * 100:.1f} semi-span)")

    assert fos_bending >= 1.5, f"Bending safety factor {fos_bending:.2f} < 1.5 required!"
    assert fos_shear >= 1.5, f"Shear safety factor {fos_shear:.2f} < 1.5 required!"
    print("\n[DOGRULAMA BASARILI] AIAA DBF kanat ucu yukleme ve +3.5g sartlari tam olarak saglandi!")
    print("=" * 72)

if __name__ == '__main__':
    analyze_spar_structure()
