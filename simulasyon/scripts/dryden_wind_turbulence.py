#!/usr/bin/env python3
"""
METUAV DBF 2027 - Dryden Wind Turbulence & MIL-F-8785C Discrete Gust Simulator
Models continuous low-altitude atmospheric turbulence (Dryden spectral density)
and discrete 1-cosine gust response with Pratt alleviation factor.
Simulates gust-induced load factors (delta n_z) and angular disturbance rates.
"""

import math
import numpy as np
from typing import Dict, Tuple, List


class DrydenWindTurbulence:
    """
    MIL-F-8785C / FAA Part 23 Dryden Atmospheric Turbulence Model.
    Generates stochastic gust velocity components [u_g, v_g, w_g] (m/s)
    and gust angular rates [p_g, q_g, r_g] (rad/s) via discrete shaping filters.
    """

    def __init__(self,
                 altitude_m: float = 25.0,
                 airspeed_ms: float = 24.5,
                 wind_speed_20ft_knots: float = 15.0,
                 wing_span_m: float = 2.40,
                 wing_chord_m: float = 0.293,
                 wing_area_m2: float = 0.7032,
                 aircraft_mass_kg: float = 24.85,
                 cl_alpha_rad: float = 4.85,
                 dt: float = 0.02):
        self.h = max(3.0, altitude_m)
        self.V = max(5.0, airspeed_ms)
        self.w20_ms = wind_speed_20ft_knots * 0.514444  # knots to m/s
        self.b = wing_span_m
        self.c_bar = wing_chord_m
        self.S = wing_area_m2
        self.m = aircraft_mass_kg
        self.cla = cl_alpha_rad
        self.dt = dt
        self.rho = 1.225
        self.g = 9.80665

        # Compute turbulence scales and intensities per MIL-F-8785C (Low altitude h < 1000 ft)
        self._update_parameters()

        # State filter memories for continuous filtering
        self.x_u = 0.0
        self.x_v = np.zeros(2)
        self.x_w = np.zeros(2)

    def _update_parameters(self):
        """Update scale lengths and turbulence standard deviations."""
        h_ft = self.h * 3.28084
        # Scale lengths (ft to meters)
        L_w_ft = h_ft
        L_u_ft = h_ft / ((0.177 + 0.000823 * h_ft)**1.2)
        L_v_ft = L_u_ft

        self.L_w = L_w_ft * 0.3048
        self.L_u = L_u_ft * 0.3048
        self.L_v = L_v_ft * 0.3048

        # Intensities
        self.sigma_w = 0.10 * self.w20_ms
        denom = (0.177 + 0.000823 * h_ft)**0.4
        self.sigma_u = self.sigma_w / denom
        self.sigma_v = self.sigma_u

    def step(self) -> Dict[str, float]:
        """
        Advance one time-step (dt) and return stochastic gust velocities and body rates.
        Uses exact Euler-Maruyama discretization of first and second-order shaping filters.
        """
        dt = self.dt
        V = self.V

        # White noise inputs N(0, 1)
        eta_u = np.random.normal(0.0, 1.0)
        eta_v = np.random.normal(0.0, 1.0)
        eta_w = np.random.normal(0.0, 1.0)

        # Longitudinal gust u_g: first order filter
        # du_g / dt = -(V / L_u) * u_g + sigma_u * sqrt(2 * V / (pi * L_u)) * eta_u
        tau_u = self.L_u / V
        gain_u = self.sigma_u * math.sqrt((2.0 * V) / (math.pi * self.L_u))
        self.x_u += (-self.x_u / tau_u + gain_u * eta_u) * dt
        u_g = self.x_u

        # Lateral gust v_g: second order filter
        # v_g(s) = sigma_v * sqrt(L_v / (pi * V)) * (1 + sqrt(3)*(L_v/V)*s) / (1 + (L_v/V)*s)^2
        tau_v = self.L_v / V
        omega_v = 1.0 / tau_v
        # Canonical 2-state representation: [x1, x2]' = [0, 1; -omega^2, -2*omega] [x1, x2] + [0; 1] * eta
        dx_v0 = self.x_v[1]
        dx_v1 = - (omega_v**2) * self.x_v[0] - 2.0 * omega_v * self.x_v[1] + eta_v
        self.x_v[0] += dx_v0 * dt
        self.x_v[1] += dx_v1 * dt
        gain_v = self.sigma_v * math.sqrt(self.L_v / (math.pi * V))
        v_g = gain_v * (self.x_v[0] + math.sqrt(3.0) * tau_v * self.x_v[1])

        # Vertical gust w_g: second order filter
        tau_w = self.L_w / V
        omega_w = 1.0 / tau_w
        dx_w0 = self.x_w[1]
        dx_w1 = - (omega_w**2) * self.x_w[0] - 2.0 * omega_w * self.x_w[1] + eta_w
        self.x_w[0] += dx_w0 * dt
        self.x_w[1] += dx_w1 * dt
        gain_w = self.sigma_w * math.sqrt(self.L_w / (math.pi * V))
        w_g = gain_w * (self.x_w[0] + math.sqrt(3.0) * tau_w * self.x_w[1])

        # Gust body rate approximations (Taylor spatial hypothesis)
        # p_g = -dw_g/dy ~ -(pi / (4 * b)) * w_g
        # q_g = dw_g/dx ~ -(pi / (4 * c_bar)) * (w_g / V)
        # r_g = -dv_g/dx ~ (pi / (3 * b)) * (v_g / V)
        p_g = -(math.pi / (4.0 * self.b)) * (w_g / V) * V * 0.15
        q_g = -(math.pi / (4.0 * self.c_bar)) * (w_g / V) * 0.20
        r_g = (math.pi / (3.0 * self.b)) * (v_g / V) * 0.20

        return {
            "u_g": float(u_g),
            "v_g": float(v_g),
            "w_g": float(w_g),
            "p_g": float(p_g),
            "q_g": float(q_g),
            "r_g": float(r_g)
        }

    def compute_discrete_gust_response(self, U_ds_ms: float = 6.0) -> Dict:
        """
        Evaluates discrete '1-cosine' gust load factor per FAR 23 / Pratt formulation.
        U_ds_ms: Design gust velocity (m/s), nominal ~6.0 m/s (~12 knots vertical gust).
        """
        # Wing loading W/S in N/m^2
        wing_loading = (self.m * self.g) / self.S

        # Mass ratio mu_g
        mu_g = (2.0 * wing_loading) / (self.rho * self.g * self.c_bar * self.cla)

        # Pratt gust alleviation factor K_g
        K_g = (0.88 * mu_g) / (5.3 + mu_g)

        # Peak vertical gust load factor increment Delta n_z
        delta_nz = (self.rho * K_g * U_ds_ms * self.V * self.cla) / (2.0 * wing_loading)

        # Total peak positive load factor
        n_z_peak = 1.0 + delta_nz
        n_z_trough = 1.0 - delta_nz

        # 1-cosine profile spatial history (gradient distance H = 25 * c_bar)
        H_gradient = 25.0 * self.c_bar
        distances = np.linspace(0.0, 2.0 * H_gradient, 100)
        profile = []
        for x in distances:
            if x <= 2.0 * H_gradient:
                w_x = (U_ds_ms / 2.0) * (1.0 - math.cos((math.pi * x) / H_gradient))
            else:
                w_x = 0.0
            profile.append(w_x)

        return {
            "wing_loading_Nm2": float(wing_loading),
            "mass_ratio_mu_g": float(mu_g),
            "pratt_alleviation_factor_Kg": float(K_g),
            "design_gust_speed_ms": float(U_ds_ms),
            "delta_nz_g": float(delta_nz),
            "peak_load_factor_g": float(n_z_peak),
            "trough_load_factor_g": float(n_z_trough),
            "structural_limit_g": 3.50,
            "within_safety_envelope": bool(n_z_peak <= 3.50 and n_z_trough >= -1.0)
        }


def main():
    print("=" * 72)
    print("  METUAV DBF 2027 - DRYDEN RÜZGAR TÜRBÜLANSI VE PRATT GUST ANALİZİ")
    print("=" * 72)
    sim = DrydenWindTurbulence(
        altitude_m=25.0,
        airspeed_ms=24.5,
        wind_speed_20ft_knots=15.0,
        aircraft_mass_kg=24.85
    )

    gust_res = sim.compute_discrete_gust_response(U_ds_ms=6.0)
    print(f"[*] Diskret 1-Cosine Rüzgar Hamlesi (U_ds = {gust_res['design_gust_speed_ms']} m/s):")
    print(f"    - Kanat Yüklemesi (W/S)     : {gust_res['wing_loading_Nm2']:.2f} N/m^2")
    print(f"    - Uçak Kütle Oranı (mu_g)   : {gust_res['mass_ratio_mu_g']:.2f}")
    print(f"    - Pratt Sönümleme Faktörü   : {gust_res['pratt_alleviation_factor_Kg']:.3f}")
    print(f"    - Delta Ivme Artisi (Delta n_z): +{gust_res['delta_nz_g']:.2f}g")
    print(f"    - Zirve Yük Faktörü (n_z)   : {gust_res['peak_load_factor_g']:.2f}g (Limit: <= 3.50g)")
    print(f"    - Yapısal Zarf Emniyeti     : {'Emniyetli (PASS)' if gust_res['within_safety_envelope'] else 'AŞILDI (FAIL)'}")

    print("\n[*] Sürekli Dryden Spektrumu Örnek Zaman Serisi (İlk 5 Adım):")
    for i in range(5):
        sample = sim.step()
        print(f"    t={i*sim.dt:.2f}s | u_g={sample['u_g']:+5.2f} m/s | v_g={sample['v_g']:+5.2f} m/s | w_g={sample['w_g']:+5.2f} m/s")

    print("=" * 72)


if __name__ == "__main__":
    main()
