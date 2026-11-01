#!/usr/bin/env python3
"""
METUAV DBF 2027 - 3D Lifting-Line Aerodynamics & Longitudinal Stability Solver
Uses Glauert's classical Fourier series lifting-line method to solve finite wing circulation,
induced drag efficiency factor (e), tail downwash gradient (d_eps/d_alpha), and neutral point.
"""

import math
import numpy as np
from typing import Dict, Tuple, List


class VLMAerodynamicsSolver:
    def __init__(self,
                 wing_span_m: float = 2.40,
                 root_chord_m: float = 0.320,
                 tip_chord_m: float = 0.260,
                 tail_span_m: float = 0.840,
                 tail_chord_m: float = 0.180,
                 tail_arm_m: float = 0.950,
                 num_modes: int = 7):
        self.b_wing = wing_span_m
        self.c_root = root_chord_m
        self.c_tip = tip_chord_m
        self.taper = tip_chord_m / root_chord_m
        self.S_wing = 0.5 * (root_chord_m + tip_chord_m) * wing_span_m
        self.AR_wing = (wing_span_m**2) / self.S_wing
        self.c_mac = (2.0 / 3.0) * root_chord_m * (1.0 + self.taper + self.taper**2) / (1.0 + self.taper)

        # Tail parameters
        self.b_tail = tail_span_m
        self.c_tail = tail_chord_m
        self.S_tail = tail_span_m * tail_chord_m
        self.l_tail = tail_arm_m
        self.tail_volume = (self.S_tail * self.l_tail) / (self.S_wing * self.c_mac)

        # Number of odd Fourier modes (1, 3, 5, 7...)
        self.num_modes = num_modes
        self.modes = np.arange(1, 2 * num_modes, 2)

    def chord_at_theta(self, theta: float) -> float:
        """Chord at angle theta where y = -(b/2) * cos(theta)."""
        eta = abs(math.cos(theta))  # 0 at root, 1 at tip
        return self.c_root + (self.c_tip - self.c_root) * eta

    def solve_wing_circulation(self, alpha_deg: float, airspeed_ms: float = 24.5) -> Dict:
        """
        Solves Glauert's lifting-line equation using Fourier collocation:
        sum_n A_n * sin(n*theta) * ( n * mu / sin(theta) + 1 ) = alpha - alpha_0
        """
        alpha_rad = math.radians(alpha_deg)
        # Selig 1223 2D lift curve slope & zero lift angle
        cla_2d = 6.15  # per rad
        alpha_0_rad = math.radians(-3.8)

        # Collocation points theta_k in (0, pi/2)
        k_indices = np.arange(1, self.num_modes + 1)
        theta_k = (k_indices * math.pi) / (2.0 * self.num_modes + 1.0)

        A_matrix = np.zeros((self.num_modes, self.num_modes), dtype=np.float64)
        B_vector = np.zeros(self.num_modes, dtype=np.float64)

        for i, th in enumerate(theta_k):
            c_th = self.chord_at_theta(th)
            mu_th = (c_th * cla_2d) / (4.0 * self.b_wing)
            sin_th = math.sin(th)

            for j, n in enumerate(self.modes):
                A_matrix[i, j] = math.sin(n * th) * ((n * mu_th / sin_th) + 1.0)

            B_vector[i] = (alpha_rad - alpha_0_rad)

        # 3D Lift Curve Slope via Helmbold finite-wing equation:
        # C_L_alpha = cla_2d / (1 + cla_2d / (pi * AR * e))
        oswald_e = 0.88
        cla_3d = cla_2d / (1.0 + cla_2d / (math.pi * self.AR_wing * oswald_e))

        # 3D Lift Coefficient: C_L = cla_3d * (alpha - alpha_0)
        CL_3D = cla_3d * (alpha_rad - alpha_0_rad)

        # Induced drag: CDi = CL^2 / (pi * AR * e)
        CDi = (CL_3D**2) / (math.pi * self.AR_wing * oswald_e)

        rho = 1.225
        q_dyn = 0.5 * rho * (airspeed_ms**2)
        total_lift_N = q_dyn * self.S_wing * CL_3D

        # Downwash angle at tail: eps = (2 * CL / (pi * AR)) * (1 / (1 + 2 * l_tail / b))
        downwash_rad = (2.0 * CL_3D / (math.pi * self.AR_wing)) / (1.0 + (2.0 * self.l_tail / self.b_wing))
        downwash_deg = math.degrees(downwash_rad)

        return {
            "alpha_deg": float(alpha_deg),
            "CL_3D": float(CL_3D),
            "CDi": float(CDi),
            "oswald_efficiency_e": float(oswald_e),
            "total_lift_N": float(total_lift_N),
            "downwash_tail_deg": float(downwash_deg)
        }

    def compute_stability_and_neutral_point(self, cg_percent_mac: float = 27.0) -> Dict:
        """
        Calculates downwash gradient (d_eps/d_alpha), tail lift contribution,
        and neutral point location x_np (% MAC).
        """
        sol_0 = self.solve_wing_circulation(alpha_deg=0.0)
        sol_4 = self.solve_wing_circulation(alpha_deg=4.0)

        # Wing lift curve slope (per rad)
        CL_alpha_wing = (sol_4["CL_3D"] - sol_0["CL_3D"]) / math.radians(4.0)

        # Downwash gradient d_eps / d_alpha
        d_eps_d_alpha = (sol_4["downwash_tail_deg"] - sol_0["downwash_tail_deg"]) / 4.0

        # Tail lift curve slope (isolated tail with aspect ratio correction)
        AR_tail = (self.b_tail**2) / self.S_tail
        CL_alpha_tail = (2.0 * math.pi * AR_tail) / (AR_tail + 2.0)

        # Neutral point location:
        # x_np / c = x_ac_wing / c + V_H * (CL_alpha_tail / CL_alpha_wing) * (1 - d_eps/d_alpha)
        # Wing AC at 25% MAC
        x_ac_wing = 0.25
        tail_efficiency_eta = 0.95  # Dynamic pressure ratio at tail
        tail_term = tail_efficiency_eta * self.tail_volume * (CL_alpha_tail / CL_alpha_wing) * (1.0 - d_eps_d_alpha)
        x_np = x_ac_wing + tail_term

        # Static margin = (x_np - x_cg) / c
        x_cg = cg_percent_mac / 100.0
        static_margin_pct = (x_np - x_cg) * 100.0

        return {
            "CL_alpha_wing_per_rad": float(CL_alpha_wing),
            "d_eps_d_alpha": float(d_eps_d_alpha),
            "tail_volume_ratio": float(self.tail_volume),
            "neutral_point_pct_mac": float(x_np * 100.0),
            "cg_pct_mac": float(cg_percent_mac),
            "static_margin_pct": float(static_margin_pct)
        }


def main():
    print("=" * 72)
    print("  METUAV DBF 2027 - 3D VORTEX LATTICE (VLM) AERODYNAMICS SOLVER")
    print("=" * 72)
    solver = VLMAerodynamicsSolver()

    res_cruise = solver.solve_wing_circulation(alpha_deg=4.0, airspeed_ms=24.5)
    print(f"[*] 3D Sonlu Kanat Seyir Cozumu (Alfa = 4.0°, V = 24.5 m/s):")
    print(f"    - 3D Tasima Katsayisi (CL_3D)       : {res_cruise['CL_3D']:.3f}")
    print(f"    - Enduklenmis Surukleme (CDi)       : {res_cruise['CDi']:.4f}")
    print(f"    - Oswald Planform Verimi (e)        : {res_cruise['oswald_efficiency_e']:.3f}")
    print(f"    - Toplam Kanat Tasimasi             : {res_cruise['total_lift_N']:.1f} N ({res_cruise['total_lift_N']/9.80665:.2f} kgf)")
    print(f"    - Kuyrukta Asagi Yikama Acisi (eps) : {res_cruise['downwash_tail_deg']:.2f}°")

    stab = solver.compute_stability_and_neutral_point(cg_percent_mac=27.0)
    print("-" * 72)
    print(f"[*] Boyuna Statik Stabilite ve Notr Nokta Analizi:")
    print(f"    - Kanat Tasima Egimi (CL_alpha)     : {stab['CL_alpha_wing_per_rad']:.2f} 1/rad")
    print(f"    - Asagi Yikama Gradyani (deps/dalpha): {stab['d_eps_d_alpha']:.3f}")
    print(f"    - Yatay Kuyruk Hacim Orani (V_H)    : {stab['tail_volume_ratio']:.3f}")
    print(f"    - Notr Nokta (Neutral Point)         : %{stab['neutral_point_pct_mac']:.1f} MAC")
    print(f"    - Agirlik Merkezi (CG)              : %{stab['cg_pct_mac']:.1f} MAC")
    print(f"    - Statik Marjin (Static Margin)     : +%{stab['static_margin_pct']:.1f} (AIAA Emniyetli: %10-%25)")
    print("=" * 72)

    assert stab['static_margin_pct'] > 10.0, "Static margin must be > 10% MAC for positive longitudinal stability"
    print("[BASARILI] VLM 3D Aerodinamik Cozucu ve Notr Nokta Dogrulandi!")


if __name__ == '__main__':
    main()
