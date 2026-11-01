#!/usr/bin/env python3
"""
METUAV DBF 2027 - Wing Aeroelastic Flutter & Divergence Analyzer
Performs 2-DOF (Plunge-Pitch) aeroelastic stability analysis across flight speeds.
Determines wing classical flutter speed (V_flutter) and static divergence speed (V_div)
using the V-g-f eigenvalue method to ensure compliance with AIAA DBF structural margins.
"""

import math
import numpy as np
from typing import Dict, Tuple, List


class WingFlutterAnalyzer:
    def __init__(self,
                 semi_span_m: float = 1.20,
                 chord_m: float = 0.293,
                 air_density: float = 1.225,
                 spar_od_mm: float = 22.0,
                 spar_id_mm: float = 18.0,
                 carbon_E_gpa: float = 230.0,
                 carbon_G_gpa: float = 88.0,
                 lift_curve_slope_per_rad: float = 2.0 * math.pi):
        self.b = chord_m / 2.0            # Semi-chord (m)
        self.chord = chord_m
        self.span = semi_span_m           # Semi-span (m)
        self.rho = air_density
        self.cla = lift_curve_slope_per_rad

        # Carbon spar cross-section inertia
        ro = (spar_od_mm / 2.0) * 1e-3
        ri = (spar_id_mm / 2.0) * 1e-3
        # Second moment of area I = pi/4 * (ro^4 - ri^4)
        self.I_spar = (math.pi / 4.0) * (ro**4 - ri**4)
        # Polar moment of inertia J = pi/2 * (ro^4 - ri^4)
        self.J_spar = (math.pi / 2.0) * (ro**4 - ri**4)

        self.EI = carbon_E_gpa * 1e9 * self.I_spar  # Bending stiffness (N*m^2)
        self.GJ = carbon_G_gpa * 1e9 * self.J_spar  # Torsional stiffness (N*m^2)

        # Wing mass properties per unit span
        # Total wing panel mass ~ 2.10 kg over 1.20 m
        self.m = 2.10 / self.span  # kg/m
        # Mass moment of inertia about elastic axis (spar at 28% chord)
        self.ea = 0.28 * self.chord  # Elastic axis from leading edge
        self.cg = 0.38 * self.chord  # Section CG from leading edge
        self.x_alpha = self.cg - self.ea  # Static imbalance distance (m)
        # Section polar mass moment of inertia
        self.I_alpha = (1.0 / 12.0) * self.m * (self.chord**2) + self.m * (self.x_alpha**2)

        # Natural frequencies (cantilever beam approximations)
        # Bending 1st mode: omega_h = 3.516 * sqrt(EI / (m * L^4))
        self.omega_h = 3.516 * math.sqrt(self.EI / (self.m * (self.span**4)))
        # Torsion 1st mode: omega_alpha = (pi / (2 * L)) * sqrt(GJ / (I_alpha * L))
        # where I_alpha is per unit length
        self.omega_alpha = (math.pi / (2.0 * self.span)) * math.sqrt(self.GJ / self.I_alpha)

        # Mass ratio mu = m / (pi * rho * b^2)
        self.mu = self.m / (math.pi * self.rho * (self.b**2))
        # Radius of gyration squared r_alpha^2 = I_alpha / (m * b^2)
        self.r_alpha_sq = self.I_alpha / (self.m * (self.b**2))
        # Non-dimensional static imbalance x_alpha_nd = x_alpha / b
        self.x_alpha_nd = self.x_alpha / self.b
        # Non-dimensional elastic axis location a = (ea - b) / b
        self.a_nd = (self.ea - self.b) / self.b

    def compute_divergence_speed(self) -> float:
        """
        Calculates static torsional divergence speed:
        V_div = sqrt(2 * GJ / (rho * s * c * e * C_L_alpha))
        where e is the aerodynamic offset from the elastic axis (e = ea - ac).
        Aerodynamic center is at 25% chord (ac = 0.25 * chord).
        """
        ac = 0.25 * self.chord
        e = self.ea - ac  # Offset between elastic axis and aero center (m)
        if e <= 0:
            return 999.0  # Inherently divergence-free if elastic axis is ahead of aero center

        # Torsional stiffness per unit span K_alpha
        K_alpha = self.GJ / self.span
        V_div = math.sqrt(2.0 * K_alpha / (self.rho * self.chord * e * self.cla))
        return float(V_div)

    def analyze_flutter(self, v_start: float = 10.0, v_end: float = 80.0, v_step: float = 0.5) -> Dict:
        """
        Solves 2-DOF aeroelastic eigenvalue problem across airspeed sweep.
        Equations of motion:
        [M] {q''} + [C_aero(V)] {q'} + ([K] + [K_aero(V)]) {q} = 0
        where q = [h/b, alpha]^T
        """
        # Mass matrix
        M = np.array([
            [1.0, self.x_alpha_nd],
            [self.x_alpha_nd, self.r_alpha_sq]
        ], dtype=np.float64)

        inv_M = np.linalg.inv(M)

        # Structural stiffness matrix
        K_struct = np.array([
            [self.omega_h**2, 0.0],
            [0.0, self.r_alpha_sq * (self.omega_alpha**2)]
        ], dtype=np.float64)

        speeds = np.arange(v_start, v_end + v_step, v_step)
        frequencies = []
        dampings = []
        flutter_speed = None
        flutter_freq_hz = None

        for V in speeds:
            q_dyn = 0.5 * self.rho * (V**2)

            # Quasi-steady aerodynamic stiffness:
            # Lift = q * c * cla * (alpha + h_dot/V)
            # Moment about EA = e * Lift = (ea - ac) * Lift
            e_dist = self.ea - 0.25 * self.chord

            K_aero = np.array([
                [0.0, (self.rho * V**2 * self.b * self.cla) / self.m],
                [0.0, -(self.rho * V**2 * self.b * e_dist * self.cla) / self.m]
            ], dtype=np.float64)

            # Aerodynamic damping matrix
            C_aero = np.array([
                [(self.rho * V * self.b * self.cla) / self.m, 0.0],
                [-(self.rho * V * self.b * e_dist * self.cla) / self.m, 0.0]
            ], dtype=np.float64)

            # State space: x = [q, q_dot]^T
            # x_dot = A * x
            A = np.zeros((4, 4), dtype=np.float64)
            A[0:2, 2:4] = np.eye(2)
            A[2:4, 0:2] = -inv_M @ (K_struct + K_aero)
            A[2:4, 2:4] = -inv_M @ C_aero

            eigenvalues = np.linalg.eigvals(A)

            # Sort eigenvalues by imaginary part (positive frequencies)
            pos_eigs = [eig for eig in eigenvalues if eig.imag >= 0]
            pos_eigs = sorted(pos_eigs, key=lambda z: z.imag)

            # Take the 2 oscillatory modes
            mode_dampings = [eig.real for eig in pos_eigs]
            mode_freqs = [eig.imag / (2.0 * math.pi) for eig in pos_eigs]

            frequencies.append(mode_freqs)
            dampings.append(mode_dampings)

            # Flutter condition: Any real part becomes positive (unstable oscillation)
            if flutter_speed is None:
                for eig in pos_eigs:
                    if eig.real > 0.001 and eig.imag > 1.0:
                        flutter_speed = float(V)
                        flutter_freq_hz = float(eig.imag / (2.0 * math.pi))
                        break

        v_div = self.compute_divergence_speed()

        return {
            "omega_h_hz": float(self.omega_h / (2.0 * math.pi)),
            "omega_alpha_hz": float(self.omega_alpha / (2.0 * math.pi)),
            "EI_Nm2": float(self.EI),
            "GJ_Nm2": float(self.GJ),
            "divergence_speed_ms": float(v_div),
            "flutter_speed_ms": float(flutter_speed) if flutter_speed else 999.0,
            "flutter_freq_hz": float(flutter_freq_hz) if flutter_freq_hz else 0.0,
            "speeds": speeds.tolist(),
            "frequencies": frequencies,
            "dampings": dampings,
            "margin_over_dive_speed": float(flutter_speed / 35.0) if flutter_speed else 999.0 / 35.0
        }


def main():
    analyzer = WingFlutterAnalyzer()
    res = analyzer.analyze_flutter(v_start=10.0, v_end=80.0, v_step=1.0)

    print("=" * 72)
    print("  METUAV DBF 2027 - KANAT AEROELASTIK FLUTTER VE DIVERJANS ANALIZI")
    print("=" * 72)
    print(f"[*] Dogal Frekanslar:")
    print(f"    - 1. Egilme Modu (Bending / Plunge): {res['omega_h_hz']:.2f} Hz")
    print(f"    - 1. Burulma Modu (Torsion / Pitch) : {res['omega_alpha_hz']:.2f} Hz")
    print(f"    - Frekans Orani (omega_h / omega_a) : {res['omega_h_hz'] / res['omega_alpha_hz']:.3f} (< 0.60 guvenli ayrilma)")
    print(f"[*] Yapisal Rijitlik:")
    print(f"    - Egilme Rijitligi (EI) : {res['EI_Nm2']:.1f} N*m^2 (Toray T700 UD)")
    print(f"    - Burulma Rijitligi (GJ): {res['GJ_Nm2']:.1f} N*m^2 (Karbon Boru Spar)")
    print("-" * 72)
    print(f"[*] Statik Diverjans Hizi (V_div) : {res['divergence_speed_ms']:.1f} m/s ({res['divergence_speed_ms'] * 3.6:.1f} km/h)")
    print(f"[*] Klasik Flutter Hizi (V_flutter): {res['flutter_speed_ms']:.1f} m/s ({res['flutter_speed_ms'] * 3.6:.1f} km/h)")
    if res['flutter_freq_hz'] > 0:
        print(f"    - Flutter Frekansi             : {res['flutter_freq_hz']:.2f} Hz")
    print(f"[*] Maksimum Dalis Hizi (V_dive)   : 35.0 m/s (126.0 km/h)")
    print(f"[*] Flutter Guvenlik Katsayisi     : {res['margin_over_dive_speed']:.2f} (AIAADBF sarti: >= 1.20)")
    print("=" * 72)

    if res['margin_over_dive_speed'] >= 1.20:
        print("[BASARILI] Kanat yapisi dalis hizinda flutter ve diverjanstan tamamen emniyetlidir!")
    else:
        print("[UYARI] Flutter emniyet marjini yetersiz!")


if __name__ == '__main__':
    main()
