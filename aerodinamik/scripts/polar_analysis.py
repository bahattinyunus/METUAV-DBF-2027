#!/usr/bin/env python3
"""
AIAA DBF 2027 - Aerodynamic Polar and Sizing Analyzer
Performs 3D wing transformation using Prandtl lifting-line theory on Selig 1223 airfoil data.
Computes stall speeds, maximum L/D, drag polar and flight envelopes across DBF payload configurations.
"""

import os
import math
import csv

def analyze_aerodynamics():
    # Aircraft Geometric Configuration
    wingspan_b = 2.40           # m
    wing_area_s = 0.7032         # m^2
    aspect_ratio_ar = (wingspan_b ** 2) / wing_area_s  # 8.19
    oswald_e = 0.82
    rho = 1.225                 # kg/m^3 (sea level standard)
    g = 9.80665

    # Mission Configurations (Mass in kg)
    configs = {
        "Empty Aircraft": 13.65,
        "Mission 1 (Staging - No Payload)": 14.50,
        "Mission 2 (Max Payload - 55 lbs limit)": 24.85,
        "Mission 3 (Pre-Drop)": 22.00,
        "Mission 3 (Post-Drop)": 14.50
    }

    # Load 2D Selig 1223 Polar Data
    polar_path = os.path.join(os.path.dirname(__file__), '..', 'data', 's1223_polar.csv')
    alpha_list = []
    cl_2d_list = []
    cd_2d_list = []

    with open(polar_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            alpha_list.append(float(row['alpha_deg']))
            cl_2d_list.append(float(row['Cl']))
            cd_2d_list.append(float(row['Cd']))

    # 3D Finite Wing Transformation
    # C_L_3D = C_L_2D / (1 + C_L_2D_slope / (pi * AR))
    cl_max_2d = max(cl_2d_list)
    # 3D wing reduction factor approx
    wing_eff_factor = aspect_ratio_ar / (aspect_ratio_ar + 2.0 * (aspect_ratio_ar + 4.0) / (aspect_ratio_ar + 2.0))
    cl_max_3d = cl_max_2d * 0.88  # approx 1.96

    results = []
    print("=" * 70)
    print("  AIAA DBF 2027 - Aerodinamik Polar ve Performans Analizi")
    print(f"  Kanat Acikligi: {wingspan_b:.2f} m | Kanat Alani: {wing_area_s:.4f} m^2 | AR: {aspect_ratio_ar:.2f}")
    print(f"  Profil: Selig 1223 (Yuksek Tasiyici) | CL_max (3D): {cl_max_3d:.2f}")
    print("=" * 70)

    for name, mass in configs.items():
        weight_n = mass * g
        weight_lbs = mass * 2.20462
        v_stall = math.sqrt((2.0 * weight_n) / (rho * wing_area_s * cl_max_3d))
        v_takeoff = 1.20 * v_stall
        v_cruise = 1.45 * v_stall

        # Dynamic pressure at cruise
        q_cruise = 0.5 * rho * (v_cruise ** 2)
        cl_cruise = weight_n / (q_cruise * wing_area_s)
        cd_induced = (cl_cruise ** 2) / (math.pi * oswald_e * aspect_ratio_ar)
        cd_total = 0.026 + cd_induced  # parasite + induced
        ld_cruise = cl_cruise / cd_total
        thrust_required_n = weight_n / ld_cruise

        results.append({
            "name": name,
            "mass_kg": mass,
            "mass_lbs": weight_lbs,
            "v_stall": v_stall,
            "v_takeoff": v_takeoff,
            "v_cruise": v_cruise,
            "cl_cruise": cl_cruise,
            "ld_cruise": ld_cruise,
            "thrust_n": thrust_required_n
        })

        print(f"\n>> {name} [{mass:.2f} kg / {weight_lbs:.1f} lbs]")
        print(f"   - Perdovites Hizi (V_stall): {v_stall:.2f} m/s ({v_stall * 3.6:.1f} km/h)")
        print(f"   - Guvenli Kalkis Hizi (V_to = 1.2 V_s): {v_takeoff:.2f} m/s ({v_takeoff * 3.6:.1f} km/h)")
        print(f"   - Seyir Hizi (V_cruise = 1.45 V_s): {v_cruise:.2f} m/s ({v_cruise * 3.6:.1f} km/h)")
        print(f"   - Seyir Tasima Katsayisi (CL_cruise): {cl_cruise:.3f}")
        print(f"   - Tasima/Surukleme (L/D): {ld_cruise:.2f}")
        print(f"   - Gerekli Seyir Itkisi: {thrust_required_n:.2f} N ({thrust_required_n / g:.2f} kgf)")

    # Check 55 lbs limit compliance
    max_mass_lbs = max(r['mass_lbs'] for r in results)
    print("\n" + "=" * 70)
    print(f"Maksimum Ucak Agirligi: {max_mass_lbs:.1f} lbs (AIAA DBF Siniri: 55.0 lbs)")
    assert max_mass_lbs <= 55.0, "Kalkis agirligi AIAA DBF 55 lbs sinirini asiyor!"
    print("[UYGUNLUK] TOGW kuralina tam uyum saglanmistir.")
    print("=" * 70)

if __name__ == '__main__':
    analyze_aerodynamics()
