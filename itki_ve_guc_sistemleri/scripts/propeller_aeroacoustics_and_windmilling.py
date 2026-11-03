#!/usr/bin/env python3
"""
METUAV DBF 2027 - Propeller Aeroacoustics & In-Flight Windmilling Drag Engine
Calculates Farassat & Gutin-Deming rotational acoustic noise emissions (dB / dBA)
and models in-flight windmilling propeller drag, locked brake drag, and active
regenerative energy harvesting during descent.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AcousticAnalysisResult:
    rpm: float
    tip_speed_ms: float
    tip_mach: float
    helical_tip_mach: float
    blade_passing_freq_hz: float
    spl_total_db: float
    spl_dba: float
    thickness_noise_db: float
    loading_noise_db: float
    is_dbf_noise_compliant: bool
    noise_margin_dba: float


@dataclass
class WindmillingDragResult:
    airspeed_ms: float
    locked_drag_n: float
    windmilling_freewheel_drag_n: float
    regenerative_braking_drag_n: float
    regen_electrical_power_w: float
    regen_battery_current_a: float
    freewheel_rpm: float


class PropellerAeroacousticsAndWindmilling:
    """
    Acoustic emission solver and windmilling/regenerative braking physics engine.
    """

    def __init__(self,
                 prop_diameter_m: float = 0.4826,       # 19x12E propeller (19 inches)
                 prop_pitch_m: float = 0.3048,          # 12 inches pitch
                 num_blades: int = 2,
                 solidity: float = 0.082,
                 motor_kv: float = 280.0,
                 battery_voltage_v: float = 24.0,
                 observer_distance_m: float = 30.48,    # 100 ft sideline measurement
                 speed_of_sound_ms: float = 340.29,
                 air_density_kg_m3: float = 1.225):
        self.D = prop_diameter_m
        self.R = prop_diameter_m / 2.0
        self.pitch = prop_pitch_m
        self.B = num_blades
        self.sigma = solidity
        self.kv = motor_kv
        self.v_batt = battery_voltage_v
        self.r_obs = observer_distance_m
        self.c0 = speed_of_sound_ms
        self.rho = air_density_kg_m3

        # Reference acoustic pressure (auditory threshold = 20 micro-Pascal)
        self.P_REF = 20.0e-6

        # Disk area
        self.A_disk = math.pi * (self.R**2)

    def compute_a_weighting(self, freq_hz: float) -> float:
        """
        Computes IEC 61672 A-weighting correction in dB for auditory perception.
        """
        f = max(10.0, freq_hz)
        f2 = f**2
        f4 = f**4

        # A-weighting curve formula
        num = 12194**2 * f4
        denom = (f2 + 20.6**2) * math.sqrt((f2 + 107.7**2) * (f2 + 737.9**2)) * (f2 + 12194**2)
        ra = num / denom
        a_db = 20.0 * math.log10(ra) + 2.0
        return a_db

    def analyze_acoustic_emissions(self,
                                   rpm: float = 6800.0,
                                   thrust_n: float = 122.4,
                                   airspeed_ms: float = 24.5,
                                   sideline_angle_deg: float = 105.0, # Angle of peak acoustic radiation
                                   max_allowed_dba: float = 85.0      # DBF sideline decibel limit
                                   ) -> AcousticAnalysisResult:
        """
        Calculates propeller rotational noise using Gutin-Deming formulation:
        - Thickness noise from blade displacement volume
        - Loading noise from aerodynamic lift and drag dipole forces
        """
        omega = (2.0 * math.pi * rpm) / 60.0
        v_tip = omega * self.R
        m_tip = v_tip / self.c0
        m_hel = math.sqrt(v_tip**2 + airspeed_ms**2) / self.c0

        bpf = (self.B * rpm) / 60.0  # Blade passing frequency

        theta_rad = math.radians(sideline_angle_deg)
        sin_th = math.sin(theta_rad)
        cos_th = math.cos(theta_rad)

        # 1. Loading Noise (Thrust & Torque Dipoles):
        # Aerodynamic torque: Q = Thrust * pitch / (2 * pi * eta)
        q_torque = (thrust_n * self.pitch) / (2.0 * math.pi * 0.78)

        # First harmonic m=1 (frequency = BPF)
        arg = self.B * m_tip * sin_th
        # Bessel function approximation for J_B(arg)
        from scipy.special import jv
        j_b = float(jv(self.B, arg))

        # Root-mean-square pressure of loading noise (Gutin formula):
        p_load = (self.B * omega) / (2.0 * math.sqrt(2.0) * math.pi * self.c0 * self.r_obs) * \
                 abs(thrust_n * cos_th - (q_torque * self.c0) / (omega * (self.R**2))) * j_b

        # 2. Thickness Noise (Blade displacement monopole):
        # Volume of blade displacement V_b ~ 0.68 * c * t * R
        c_mean = 0.038 # mean blade chord
        t_max = 0.0035 # blade max thickness
        blade_vol = self.B * 0.68 * c_mean * t_max * self.R
        p_thick = (self.rho * (self.B * omega)**2 * blade_vol) / (4.0 * math.sqrt(2.0) * math.pi * self.r_obs) * j_b

        # Combine thickness and loading in quadrature
        p_total_rms = math.sqrt(p_load**2 + p_thick**2)

        spl_load_db = 20.0 * math.log10(max(p_load, 1e-12) / self.P_REF)
        spl_thick_db = 20.0 * math.log10(max(p_thick, 1e-12) / self.P_REF)
        spl_total_db = 20.0 * math.log10(max(p_total_rms, 1e-12) / self.P_REF)

        # A-weighted decibel
        delta_a = self.compute_a_weighting(bpf)
        spl_dba = spl_total_db + delta_a

        margin = max_allowed_dba - spl_dba
        compliant = spl_dba <= max_allowed_dba

        return AcousticAnalysisResult(
            rpm=round(rpm, 1),
            tip_speed_ms=round(v_tip, 1),
            tip_mach=round(m_tip, 3),
            helical_tip_mach=round(m_hel, 3),
            blade_passing_freq_hz=round(bpf, 1),
            spl_total_db=round(spl_total_db, 1),
            spl_dba=round(spl_dba, 1),
            thickness_noise_db=round(spl_load_db, 1),
            loading_noise_db=round(spl_thick_db, 1),
            is_dbf_noise_compliant=compliant,
            noise_margin_dba=round(margin, 1)
        )

    def evaluate_windmilling_and_regen_drag(self,
                                            airspeed_ms: float = 24.5,
                                            regen_current_target_a: float = 12.0) -> WindmillingDragResult:
        """
        Calculates propeller drag across 3 in-flight descent modes:
        1. Locked Propeller (ESC active DC brake clamped)
        2. Freewheeling Propeller (Windmilling, zero torque absorbed)
        3. Active Regenerative Braking (Harvesting electrical power back to 6S pack)
        """
        q = 0.5 * self.rho * (airspeed_ms**2)

        # 1. Locked Propeller Drag:
        # Frontal projected blade area drag: CD_locked ~ 1.25 * solidity
        cd_locked = 1.25 * self.sigma
        drag_locked = q * self.A_disk * cd_locked

        # 2. Freewheeling Unbraked Windmilling:
        # Acts like an actuator disk extracting no power but disturbing wake:
        # Incompressible actuator disk theory gives CD_wm ~ 0.78 - 0.84
        cd_freewheel = 0.80
        drag_freewheel = q * self.A_disk * cd_freewheel

        # Freewheeling RPM ~ V / pitch * 60 * slip_factor (slip ~ 0.85)
        rpm_freewheel = (airspeed_ms / self.pitch) * 60.0 * 0.85

        # 3. Active Regenerative Braking:
        # Aerodynamic power absorbed from airflow: P_aero = Drag_regen * V
        # Electrical power regenerated: P_elec = V_batt * I_regen
        # Efficiency of regen conversion ~ 72%
        eta_regen = 0.72
        p_regen_elec = self.v_batt * regen_current_target_a
        p_regen_mech = p_regen_elec / eta_regen
        drag_regen = (p_regen_mech / max(airspeed_ms, 1.0)) + drag_locked

        return WindmillingDragResult(
            airspeed_ms=round(airspeed_ms, 2),
            locked_drag_n=round(drag_locked, 2),
            windmilling_freewheel_drag_n=round(drag_freewheel, 2),
            regenerative_braking_drag_n=round(drag_regen, 2),
            regen_electrical_power_w=round(p_regen_elec, 1),
            regen_battery_current_a=round(regen_current_target_a, 1),
            freewheel_rpm=round(rpm_freewheel, 1)
        )
