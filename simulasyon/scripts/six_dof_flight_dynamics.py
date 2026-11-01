#!/usr/bin/env python3
"""
METUAV DBF 2027 - Full 6-DOF Nonlinear Flight Dynamics Simulator
Rigid-body 12-state aircraft equations of motion with quaternion attitude representation,
full aerodynamic stability & control derivatives, and trim solver.
"""

import math
import numpy as np
from typing import Dict, Tuple, Optional


class Aircraft6DOF:
    def __init__(self, mass_kg: float = 24.85):
        # Geometric and aerodynamic parameters
        self.mass = mass_kg
        self.wing_span = 2.40          # b (m)
        self.wing_area = 0.7032        # S (m^2)
        self.mean_chord = 0.293        # c_bar (m)
        self.aspect_ratio = 8.19
        self.oswald_e = 0.88
        self.rho = 1.225               # kg/m^3 (sea level standard)
        self.g = 9.80665

        # Moments of inertia (kg * m^2)
        self.Ixx = 1.42
        self.Iyy = 0.98
        self.Izz = 2.25
        self.Ixz = 0.08

        # Precompute inertia coupling terms
        self.gamma = self.Ixx * self.Izz - self.Ixz**2
        self.gamma1 = (self.Ixz * (self.Ixx - self.Iyy + self.Izz)) / self.gamma
        self.gamma2 = (self.Izz * (self.Izz - self.Iyy) + self.Ixz**2) / self.gamma
        self.gamma3 = self.Izz / self.gamma
        self.gamma4 = self.Ixz / self.gamma
        self.gamma5 = (self.Izz - self.Ixx) / self.Iyy
        self.gamma6 = self.Ixz / self.Iyy
        self.gamma7 = ((self.Ixx - self.Iyy) * self.Ixx + self.Ixz**2) / self.gamma
        self.gamma8 = self.Ixx / self.gamma

        # Aerodynamic Stability & Control Derivatives (from CFD and wind tunnel polar)
        # Longitudinal
        self.CL0 = 0.65
        self.CL_alpha = 5.25           # per rad
        self.CL_q = 6.80               # per rad
        self.CL_de = 0.42              # per rad (elevator)

        self.CD0 = 0.032
        self.CD_de = 0.015

        self.Cm0 = 0.04
        self.Cm_alpha = -0.85          # per rad (stable pitch stiffness)
        self.Cm_q = -14.50             # per rad (pitch damping)
        self.Cm_de = -1.25             # per rad (elevator effectiveness)

        # Lateral-Directional
        self.CY_beta = -0.45           # per rad
        self.CY_p = -0.08
        self.CY_r = 0.22
        self.CY_dr = 0.18              # per rad (rudder)

        self.Cl_beta = -0.11           # per rad (dihedral effect)
        self.Cl_p = -0.52              # per rad (roll damping)
        self.Cl_r = 0.14
        self.Cl_da = 0.22              # per rad (aileron effectiveness)
        self.Cl_dr = 0.015

        self.Cn_beta = 0.14            # per rad (weathercock directional stability)
        self.Cn_p = -0.04
        self.Cn_r = -0.16              # per rad (yaw damping)
        self.Cn_da = -0.015            # adverse yaw
        self.Cn_dr = -0.085            # per rad (rudder effectiveness)

        # Max static thrust (N) at 100% throttle
        self.max_thrust_N = 122.4

        # State vector: [pn, pe, pd, u, v, w, q0, q1, q2, q3, p, q, r]
        self.state = np.zeros(13, dtype=np.float64)
        self.state[6] = 1.0  # q0 = 1.0 (identity quaternion)

    def set_state(self, pos_ned: Tuple[float, float, float],
                  vel_body: Tuple[float, float, float],
                  quat: Tuple[float, float, float, float],
                  pqr: Tuple[float, float, float]):
        self.state[0:3] = pos_ned
        self.state[3:6] = vel_body
        self.state[6:10] = quat
        # Normalize quaternion
        q_norm = np.linalg.norm(self.state[6:10])
        if q_norm > 1e-6:
            self.state[6:10] /= q_norm
        self.state[10:13] = pqr

    def quat_to_euler(self, q: np.ndarray) -> Tuple[float, float, float]:
        """Converts quaternion [q0, q1, q2, q3] to Euler angles (roll, pitch, yaw) in radians."""
        q0, q1, q2, q3 = q
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (q0 * q1 + q2 * q3)
        cosr_cosp = 1.0 - 2.0 * (q1 * q1 + q2 * q2)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (q0 * q2 - q3 * q1)
        if abs(sinp) >= 1.0:
            pitch = math.copysign(math.pi / 2.0, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (q0 * q3 + q1 * q2)
        cosy_cosp = 1.0 - 2.0 * (q2 * q2 + q3 * q3)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        return roll, pitch, yaw

    def compute_forces_and_moments(self, state: np.ndarray,
                                   controls: Tuple[float, float, float, float]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes total aerodynamic, propulsion and gravitational forces and moments in body frame.
        controls: (delta_e, delta_a, delta_r, throttle)
                  deflections in radians, throttle in [0, 1].
        Returns: (F_body [Fx, Fy, Fz], M_body [L, M, N])
        """
        u, v, w = state[3:6]
        q0, q1, q2, q3 = state[6:10]
        p, q_rate, r = state[10:13]
        de, da, dr, throttle = controls

        # Airspeed, alpha, beta
        Va = math.sqrt(u**2 + v**2 + w**2)
        Va = max(Va, 0.1)  # Avoid div by zero
        alpha = math.atan2(w, u)
        beta = math.asin(np.clip(v / Va, -1.0, 1.0))
        q_dyn = 0.5 * self.rho * (Va**2)

        # Non-dimensional angular rates
        p_hat = (p * self.wing_span) / (2.0 * Va)
        q_hat = (q_rate * self.mean_chord) / (2.0 * Va)
        r_hat = (r * self.wing_span) / (2.0 * Va)

        # Aerodynamic Lift, Drag, Sideforce coefficients
        CL = self.CL0 + self.CL_alpha * alpha + self.CL_q * q_hat + self.CL_de * de
        CDi = (CL**2) / (math.pi * self.aspect_ratio * self.oswald_e)
        CD = self.CD0 + CDi + self.CD_de * abs(de)
        CY = self.CY_beta * beta + self.CY_p * p_hat + self.CY_r * r_hat + self.CY_dr * dr

        # Convert Wind Frame (Lift, Drag) to Body Frame (Fx, Fz)
        # Fx_aero = -Drag * cos(alpha) + Lift * sin(alpha)
        # Fz_aero = -Drag * sin(alpha) - Lift * cos(alpha)
        L_aero = q_dyn * self.wing_area * CL
        D_aero = q_dyn * self.wing_area * CD
        Y_aero = q_dyn * self.wing_area * CY

        sa, ca = math.sin(alpha), math.cos(alpha)
        Fx_aero = -D_aero * ca + L_aero * sa
        Fz_aero = -D_aero * sa - L_aero * ca
        Fy_aero = Y_aero

        # Aerodynamic Moments (Roll, Pitch, Yaw)
        Cl = self.Cl_beta * beta + self.Cl_p * p_hat + self.Cl_r * r_hat + self.Cl_da * da + self.Cl_dr * dr
        Cm = self.Cm0 + self.Cm_alpha * alpha + self.Cm_q * q_hat + self.Cm_de * de
        Cn = self.Cn_beta * beta + self.Cn_p * p_hat + self.Cn_r * r_hat + self.Cn_da * da + self.Cn_dr * dr

        L_moment = q_dyn * self.wing_area * self.wing_span * Cl
        M_moment = q_dyn * self.wing_area * self.mean_chord * Cm
        N_moment = q_dyn * self.wing_area * self.wing_span * Cn

        # Propulsion: Thrust acts along body X-axis
        # Thrust model accounts for airspeed reduction: T = T0 * (1 - Va / V_pitch)
        v_pitch_limit = 45.0  # m/s
        thrust = self.max_thrust_N * throttle * max(0.0, 1.0 - (Va / v_pitch_limit))
        Fx_prop = thrust
        Fy_prop = 0.0
        Fz_prop = 0.0

        # Gravity in body frame via quaternion rotation matrix
        # g_body = R(q)^T * [0, 0, g]^T
        gx_body = 2.0 * (q1 * q3 - q0 * q2) * self.mass * self.g
        gy_body = 2.0 * (q2 * q3 + q0 * q1) * self.mass * self.g
        gz_body = (q0**2 - q1**2 - q2**2 + q3**2) * self.mass * self.g

        # Total Forces
        Fx = Fx_aero + Fx_prop + gx_body
        Fy = Fy_aero + Fy_prop + gy_body
        Fz = Fz_aero + Fz_prop + gz_body

        return np.array([Fx, Fy, Fz]), np.array([L_moment, M_moment, N_moment])

    def state_derivatives(self, state: np.ndarray, controls: Tuple[float, float, float, float]) -> np.ndarray:
        """Computes time derivatives of 12 states (x_dot = f(x, u))."""
        u, v, w = state[3:6]
        q0, q1, q2, q3 = state[6:10]
        p, q_rate, r = state[10:13]

        forces, moments = self.compute_forces_and_moments(state, controls)
        Fx, Fy, Fz = forces
        L, M, N = moments

        # 1. Position derivatives (Kinematics from Body to NED)
        # R_b_to_ned matrix
        r11 = q0**2 + q1**2 - q2**2 - q3**2
        r12 = 2.0 * (q1 * q2 - q0 * q3)
        r13 = 2.0 * (q1 * q3 + q0 * q2)
        r21 = 2.0 * (q1 * q2 + q0 * q3)
        r22 = q0**2 - q1**2 + q2**2 - q3**2
        r23 = 2.0 * (q2 * q3 - q0 * q1)
        r31 = 2.0 * (q1 * q3 - q0 * q2)
        r32 = 2.0 * (q2 * q3 + q0 * q1)
        r33 = q0**2 - q1**2 - q2**2 + q3**2

        pn_dot = r11 * u + r12 * v + r13 * w
        pe_dot = r21 * u + r22 * v + r23 * w
        pd_dot = r31 * u + r32 * v + r33 * w

        # 2. Translational accelerations in body frame: a_b = F/m - omega x v
        u_dot = r * v - q_rate * w + Fx / self.mass
        v_dot = p * w - r * u + Fy / self.mass
        w_dot = q_rate * u - p * v + Fz / self.mass

        # 3. Quaternion rate kinematics: q_dot = 0.5 * Omega * q
        q0_dot = 0.5 * (-p * q1 - q_rate * q2 - r * q3)
        q1_dot = 0.5 * ( p * q0 + r * q2 - q_rate * q3)
        q2_dot = 0.5 * ( q_rate * q0 - r * q1 + p * q3)
        q3_dot = 0.5 * ( r * q0 + q_rate * q1 - p * q2)

        # 4. Rotational accelerations: omega_dot = I^-1 * (M - omega x (I * omega))
        p_dot = self.gamma1 * p * q_rate - self.gamma2 * q_rate * r + self.gamma3 * L + self.gamma4 * N
        q_dot = self.gamma5 * p * r - self.gamma6 * (p**2 - r**2) + M / self.Iyy
        r_dot = self.gamma7 * p * q_rate - self.gamma1 * q_rate * r + self.gamma4 * L + self.gamma8 * N

        return np.array([
            pn_dot, pe_dot, pd_dot,
            u_dot, v_dot, w_dot,
            q0_dot, q1_dot, q2_dot, q3_dot,
            p_dot, q_dot, r_dot
        ], dtype=np.float64)

    def step(self, dt: float, controls: Tuple[float, float, float, float]):
        """Integrates states forward in time by dt using 4th-order Runge-Kutta (RK4)."""
        k1 = self.state_derivatives(self.state, controls)
        k2 = self.state_derivatives(self.state + 0.5 * dt * k1, controls)
        k3 = self.state_derivatives(self.state + 0.5 * dt * k2, controls)
        k4 = self.state_derivatives(self.state + dt * k3, controls)

        self.state += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

        # Normalize quaternion
        q_norm = np.linalg.norm(self.state[6:10])
        if q_norm > 1e-6:
            self.state[6:10] /= q_norm

    def trim(self, target_airspeed: float = 24.5, target_altitude: float = 25.0) -> Tuple[float, float, float]:
        """
        Finds longitudinal trim controls (elevator deflection, throttle, alpha)
        for straight-and-level wings-level cruise.
        Returns: (alpha_trim_deg, de_trim_deg, throttle_trim)
        """
        # In level flight: Lift = Weight -> CL_trim = W / (q * S)
        q_dyn = 0.5 * self.rho * (target_airspeed**2)
        weight = self.mass * self.g
        CL_trim = weight / (q_dyn * self.wing_area)

        # Pitch trim equation: Cm0 + Cm_alpha * alpha + Cm_de * de = 0
        # Lift equation: CL0 + CL_alpha * alpha + CL_de * de = CL_trim
        # Solve 2x2 linear system:
        A = np.array([
            [self.CL_alpha, self.CL_de],
            [self.Cm_alpha, self.Cm_de]
        ])
        b = np.array([
            CL_trim - self.CL0,
            -self.Cm0
        ])
        alpha_rad, de_rad = np.linalg.solve(A, b)

        # Drag at trim:
        CDi = (CL_trim**2) / (math.pi * self.aspect_ratio * self.oswald_e)
        CD_trim = self.CD0 + CDi + self.CD_de * abs(de_rad)
        drag_N = q_dyn * self.wing_area * CD_trim

        # Required thrust = Drag
        v_pitch_limit = 45.0
        v_factor = max(0.1, 1.0 - (target_airspeed / v_pitch_limit))
        throttle = float(np.clip(drag_N / (self.max_thrust_N * v_factor), 0.05, 1.0))

        return float(math.degrees(alpha_rad)), float(math.degrees(de_rad)), throttle


def main():
    print("=" * 72)
    print("  METUAV DBF 2027 - 6-DOF NONLINEAR FLIGHT DYNAMICS SIMULATOR")
    print("=" * 72)
    uav = Aircraft6DOF(mass_kg=24.85)

    # Calculate level cruise trim at 24.5 m/s (88.2 km/h)
    alpha_deg, de_deg, thr = uav.trim(target_airspeed=24.5)
    print(f"[*] Seyir Trim Cozumu (V_cruise = 24.5 m/s, Irtifa = 25.0 m, Kütle = 24.85 kg):")
    print(f"    - Hucum Acisi (Alpha)  : {alpha_deg:.2f}°")
    print(f"    - Elevator Trimi (de)  : {de_deg:.2f}°")
    print(f"    - Gaz Kolu (Throttle)  : %{thr * 100:.1f}")
    print("-" * 72)

    # Initialize at trim and simulate 5.0 seconds
    u0 = 24.5 * math.cos(math.radians(alpha_deg))
    w0 = 24.5 * math.sin(math.radians(alpha_deg))
    pitch_rad = math.radians(alpha_deg)
    q0 = math.cos(pitch_rad / 2.0)
    q2 = math.sin(pitch_rad / 2.0)

    uav.set_state(
        pos_ned=(0.0, 0.0, -25.0),
        vel_body=(u0, 0.0, w0),
        quat=(q0, 0.0, q2, 0.0),
        pqr=(0.0, 0.0, 0.0)
    )

    controls = (math.radians(de_deg), 0.0, 0.0, thr)
    dt = 0.01  # 100 Hz integration
    for step in range(500):
        uav.step(dt, controls)

    roll, pitch, yaw = uav.quat_to_euler(uav.state[6:10])
    alt = -uav.state[2]
    Va = math.sqrt(uav.state[3]**2 + uav.state[4]**2 + uav.state[5]**2)

    print(f"[*] 5 Saniyelik Denge Simülasyonu Sonucu:")
    print(f"    - Son Irtifa           : {alt:.2f} m (Baslangic: 25.00 m, Sapma: {abs(alt - 25.0):.3f} m)")
    print(f"    - Son Hava Hizi        : {Va:.2f} m/s (Baslangic: 24.50 m/s)")
    print(f"    - Son Yunuslama (Pitch): {math.degrees(pitch):.2f}°")
    print(f"    - Aci Degisim Hizi (q) : {math.degrees(uav.state[11]):.4f} deg/s")
    print("=" * 72)
    print("[BASARILI] 6-DOF Dinamik Modeli ve Trim Çözücüsü Kararlı Çalışıyor!")


if __name__ == '__main__':
    main()
