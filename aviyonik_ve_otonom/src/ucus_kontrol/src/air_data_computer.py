#!/usr/bin/env python3
"""
METUAV DBF 2027 - Air Data Computer (ADC) & Synthetic Aerodynamic Angle / Wind Estimator
Computes calibrated/true airspeed, pressure & density altitude, synthetic Angle of Attack (AoA)
and Sideslip (AoS) from inertial dynamics, and resolves 3D wind velocity vector relative to the aircraft.
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np


@dataclass
class AirDataState:
    indicated_airspeed_ms: float
    calibrated_airspeed_ms: float
    true_airspeed_ms: float
    dynamic_pressure_pa: float
    static_pressure_pa: float
    air_density_kg_m3: float
    pressure_altitude_m: float
    density_altitude_m: float
    synthetic_aoa_deg: float
    synthetic_sideslip_deg: float
    wind_speed_ms: float
    wind_direction_deg: float  # Direction wind is coming from (0-360)
    headwind_component_ms: float
    crosswind_component_ms: float


class AirDataComputer:
    """
    Air Data Computer and Synthetic Aerodynamic Angle Estimator.
    """

    # ISA constants
    P0 = 101325.0       # Pa (Sea-level standard pressure)
    T0 = 288.15         # K (15 deg C)
    RHO0 = 1.225        # kg/m^3
    R_GAS = 287.05      # J / (kg * K)
    LAPSE_RATE = 0.0065 # K / m
    G_ACCEL = 9.80665   # m / s^2

    def __init__(self,
                 aircraft_mass_kg: float = 24.85,
                 wing_area_m2: float = 0.7032,
                 cla_per_rad: float = 4.85,
                 cl0: float = 0.65,
                 cy_beta_per_rad: float = -0.45):
        self.mass = aircraft_mass_kg
        self.S_w = wing_area_m2
        self.cla = cla_per_rad
        self.cl0 = cl0
        self.cy_beta = cy_beta_per_rad

    def compute_airspeeds(self,
                          differential_pressure_pa: float,
                          static_pressure_pa: float,
                          ambient_temp_c: float = 15.0) -> Tuple[float, float, float, float, float]:
        """
        Calculates (IAS, CAS, TAS, local_density, dynamic_pressure).
        """
        qc = max(0.0, differential_pressure_pa)
        p_static = max(10000.0, static_pressure_pa)
        t_kelvin = max(200.0, ambient_temp_c + 273.15)

        # Local density from ideal gas law
        rho_local = p_static / (self.R_GAS * t_kelvin)

        # Incompressible IAS: sqrt(2 * qc / rho0)
        ias = math.sqrt((2.0 * qc) / self.RHO0)

        # Subsonic compressible CAS (Saint-Venant correction)
        gamma = 1.4
        if qc > 10.0:
            pr = (qc / self.P0) + 1.0
            cas = math.sqrt((2.0 * gamma / (gamma - 1.0)) * (self.R_GAS * self.T0) * (pr ** ((gamma - 1.0) / gamma) - 1.0))
        else:
            cas = ias

        # True Airspeed (TAS) = CAS * sqrt(rho0 / rho_local)
        tas = cas * math.sqrt(self.RHO0 / rho_local)
        q_dyn = 0.5 * rho_local * (tas**2)

        return ias, cas, tas, rho_local, q_dyn

    def compute_altitudes(self,
                          static_pressure_pa: float,
                          ambient_temp_c: float = 15.0) -> Tuple[float, float]:
        """
        Calculates Pressure Altitude and Density Altitude.
        """
        p_s = max(10000.0, static_pressure_pa)
        t_k = ambient_temp_c + 273.15

        # Standard pressure altitude
        exponent = (self.R_GAS * self.LAPSE_RATE) / self.G_ACCEL
        h_press = (self.T0 / self.LAPSE_RATE) * (1.0 - (p_s / self.P0)**exponent)

        # Density altitude
        rho = p_s / (self.R_GAS * t_k)
        h_dens = (self.T0 / self.LAPSE_RATE) * (1.0 - (rho / self.RHO0)**(1.0 / ( (self.G_ACCEL / (self.R_GAS * self.LAPSE_RATE)) - 1.0 )))

        return h_press, h_dens

    def estimate_synthetic_aerodynamic_angles(self,
                                             tas_ms: float,
                                             rho_kg_m3: float,
                                             accel_y_mps2: float,
                                             accel_z_mps2: float,
                                             roll_rad: float,
                                             pitch_rad: float) -> Tuple[float, float]:
        """
        Estimates synthetic Angle of Attack (AoA) and Sideslip (AoS) from body accelerations
        and dynamic pressure without physical vane sensors.
        """
        if tas_ms < 8.0:
            return 0.0, 0.0

        q_dyn = 0.5 * rho_kg_m3 * (tas_ms**2)

        # Aerodynamic Lift = m * (g * cos(pitch) * cos(roll) - accel_z)
        lift_n = self.mass * (self.G_ACCEL * math.cos(pitch_rad) * math.cos(roll_rad) - accel_z_mps2)
        cl = lift_n / max(q_dyn * self.S_w, 1e-3)

        # Alpha = (CL - CL0) / CLa
        alpha_rad = (cl - self.cl0) / self.cla
        alpha_deg = math.degrees(alpha_rad)
        alpha_deg = max(-8.0, min(18.0, alpha_deg))  # Physical wing limits

        # Sideforce = m * (accel_y - g * sin(roll) * cos(pitch))
        sideforce_n = self.mass * (accel_y_mps2 - self.G_ACCEL * math.sin(roll_rad) * math.cos(pitch_rad))
        cy = sideforce_n / max(q_dyn * self.S_w, 1e-3)

        # Sideslip Beta = CY / CY_beta
        beta_rad = cy / self.cy_beta
        beta_deg = math.degrees(beta_rad)
        beta_deg = max(-15.0, min(15.0, beta_deg))

        return alpha_deg, beta_deg

    def resolve_wind_vector(self,
                            ground_vel_ned_ms: Tuple[float, float, float],
                            tas_ms: float,
                            roll_rad: float,
                            pitch_rad: float,
                            yaw_rad: float,
                            aoa_rad: float = 0.0,
                            aos_rad: float = 0.0) -> Tuple[float, float, float, float]:
        """
        Resolves 3D wind velocity vector in NED frame:
        W = V_ground - R_b_n * V_air_body.
        Returns: (wind_speed_ms, wind_dir_deg, headwind_ms, crosswind_ms).
        """
        vn, ve, vd = ground_vel_ned_ms

        # Airspeed vector in body frame: [TAS * cos(aoa)*cos(aos), TAS * sin(aos), TAS * sin(aoa)*cos(aos)]
        u_a = tas_ms * math.cos(aoa_rad) * math.cos(aos_rad)
        v_a = tas_ms * math.sin(aos_rad)
        w_a = tas_ms * math.sin(aoa_rad) * math.cos(aos_rad)

        # Rotation matrix Body to NED
        cy, sy = math.cos(yaw_rad), math.sin(yaw_rad)
        cp, sp = math.cos(pitch_rad), math.sin(pitch_rad)
        cr, sr = math.cos(roll_rad), math.sin(roll_rad)

        r11 = cp * cy
        r12 = sr * sp * cy - cr * sy
        r13 = cr * sp * cy + sr * sy

        r21 = cp * sy
        r22 = sr * sp * sy + cr * cy
        r23 = cr * sp * sy - sr * cy

        r31 = -sp
        r32 = sr * cp
        r33 = cr * cp

        # Air velocity in NED
        v_air_n = r11 * u_a + r12 * v_a + r13 * w_a
        v_air_e = r21 * u_a + r22 * v_a + r23 * w_a

        # Wind = Ground - Air
        w_n = vn - v_air_n
        w_e = ve - v_air_e

        w_speed = math.sqrt(w_n**2 + w_e**2)
        # Meteorological wind direction: angle wind is blowing FROM
        w_dir_rad = math.atan2(-w_e, -w_n)
        w_dir_deg = math.degrees(w_dir_rad) % 360.0

        # Relative to aircraft heading
        rel_wind_angle = w_dir_rad - yaw_rad
        headwind = w_speed * math.cos(rel_wind_angle)
        crosswind = w_speed * math.sin(rel_wind_angle)

        return w_speed, w_dir_deg, headwind, crosswind

    def process_telemetry_frame(self,
                                diff_pressure_pa: float,
                                static_pressure_pa: float,
                                ambient_temp_c: float,
                                ground_vel_ned: Tuple[float, float, float],
                                accel_y: float,
                                accel_z: float,
                                roll_rad: float,
                                pitch_rad: float,
                                yaw_rad: float) -> AirDataState:
        """Processes one complete air data sensor frame."""
        ias, cas, tas, rho, q_dyn = self.compute_airspeeds(diff_pressure_pa, static_pressure_pa, ambient_temp_c)
        hp, hd = self.compute_altitudes(static_pressure_pa, ambient_temp_c)
        aoa_deg, aos_deg = self.estimate_synthetic_aerodynamic_angles(tas, rho, accel_y, accel_z, roll_rad, pitch_rad)
        w_spd, w_dir, hw, xw = self.resolve_wind_vector(
            ground_vel_ned, tas, roll_rad, pitch_rad, yaw_rad,
            math.radians(aoa_deg), math.radians(aos_deg)
        )

        return AirDataState(
            indicated_airspeed_ms=round(ias, 2),
            calibrated_airspeed_ms=round(cas, 2),
            true_airspeed_ms=round(tas, 2),
            dynamic_pressure_pa=round(q_dyn, 1),
            static_pressure_pa=round(static_pressure_pa, 1),
            air_density_kg_m3=round(rho, 4),
            pressure_altitude_m=round(hp, 1),
            density_altitude_m=round(hd, 1),
            synthetic_aoa_deg=round(aoa_deg, 2),
            synthetic_sideslip_deg=round(aos_deg, 2),
            wind_speed_ms=round(w_spd, 2),
            wind_direction_deg=round(w_dir, 1),
            headwind_component_ms=round(hw, 2),
            crosswind_component_ms=round(xw, 2)
        )
