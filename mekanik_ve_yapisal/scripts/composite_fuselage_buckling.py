#!/usr/bin/env python3
"""
AIAA DBF 2027 - Composite Sandwich Fuselage Buckling & Quick-Disconnect Joint Analyzer
Evaluates carbon/Rohacell sandwich fuselage monocoque structural integrity under AIAA DBF
flight and landing maneuver loads:
- Global sandwich panel buckling (Euler-Johnson wide-column with transverse shear compliance)
- Face sheet micro-wrinkling critical stress
- Core transverse shear failure under ultimate empennage aerodynamic gusts
- Wing-to-fuselage 4-pin quick-disconnect shear, bearing, and tear-out margins of safety (5-min assembly rule)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class SandwichPanelResult:
    panel_width_m: float
    bending_moment_applied_nm: float
    torsion_applied_nm: float
    axial_load_per_width_nm: float
    global_buckling_load_nm: float
    buckling_margin_of_safety: float
    wrinkling_stress_pa: float
    face_stress_applied_pa: float
    wrinkling_margin_of_safety: float
    core_shear_applied_pa: float
    core_shear_allowable_pa: float
    core_shear_margin_of_safety: float
    is_structurally_sound: bool


@dataclass
class QuickDisconnectJointResult:
    num_pins: int
    pin_diameter_mm: float
    pin_shear_stress_pa: float
    pin_shear_margin_of_safety: float
    lug_bearing_stress_pa: float
    lug_bearing_margin_of_safety: float
    tear_out_margin_of_safety: float
    assembly_time_seconds: float
    meets_5min_rule: bool


class CompositeFuselageBucklingAnalyzer:
    """
    Finite-strip & analytical sandwich stability solver for lightweight UAV fuselage monocoques.
    """

    def __init__(self,
                 fuselage_width_m: float = 0.22,
                 fuselage_height_m: float = 0.26,
                 fuselage_length_m: float = 1.65,
                 face_thickness_m: float = 0.0005,       # 0.5mm Toray T700 CF fabric (2 plies)
                 core_thickness_m: float = 0.006,        # 6.0mm Rohacell 51 IG-F foam core
                 e_face_pa: float = 64.0e9,              # Quasi-isotropic carbon fabric modulus
                 nu_face: float = 0.30,
                 e_core_pa: float = 75.0e6,              # Rohacell 51 IG-F compressive modulus
                 g_core_pa: float = 24.0e6,              # Rohacell 51 shear modulus
                 tau_core_allowable_pa: float = 800.0e3, # 0.80 MPa shear strength
                 sigma_face_allowable_pa: float = 550.0e6 # Carbon fabric allowable compression
                 ):
        self.width = fuselage_width_m
        self.height = fuselage_height_m
        self.length = fuselage_length_m
        self.t_f = face_thickness_m
        self.t_c = core_thickness_m
        self.d = core_thickness_m + face_thickness_m  # Distance between face centers

        self.E_f = e_face_pa
        self.nu_f = nu_face
        self.E_c = e_core_pa
        self.G_c = g_core_pa
        self.tau_core_allow = tau_core_allowable_pa
        self.sigma_face_allow = sigma_face_allowable_pa

        # Flexural stiffness of sandwich per unit width: D = E_f * t_f * d^2 / (2 * (1 - nu^2))
        self.D_sandwich = (self.E_f * self.t_f * (self.d**2)) / (2.0 * (1.0 - self.nu_f**2))

        # Core transverse shear stiffness per unit width: S = G_c * d^2 / t_c
        self.S_shear = (self.G_c * (self.d**2)) / self.t_c

    def evaluate_sandwich_panel(self,
                                applied_bending_moment_nm: float = 185.0,
                                applied_torsion_nm: float = 65.0,
                                applied_shear_n: float = 240.0) -> SandwichPanelResult:
        """
        Evaluates global buckling, face sheet wrinkling, and core shear margins under tail gust loads.
        """
        # Section modulus of thin-walled rectangular monocoque:
        # I_xx ~ 2 * [t_f * b * (h/2)^2] + 2 * [t_f * h^3 / 12] (considering 2 faces)
        # Total effective skin thickness on each side = 2 * t_f
        t_skin = 2.0 * self.t_f
        i_xx = (2.0 * (t_skin * self.width * ((self.height / 2.0)**2))) + ((2.0 * t_skin * (self.height**3)) / 12.0)

        # Compressive force per unit width on top skin: N_x = (M / I_xx) * (h / 2) * t_skin
        sigma_comp = (applied_bending_moment_nm / max(i_xx, 1e-9)) * (self.height / 2.0)
        n_x_applied = sigma_comp * t_skin

        # 1. Global Panel Buckling (wide column with transverse shear compliance):
        # N_cr = (pi^2 * D / b^2) / [1 + (pi^2 * D / (b^2 * S))]
        k_x = 4.0  # Simply supported rectangular panel aspect ratio factor
        b_panel = self.width
        euler_term = (k_x * (math.pi**2) * self.D_sandwich) / (b_panel**2)
        n_cr_global = euler_term / (1.0 + (euler_term / self.S_shear))

        ms_buckling = (n_cr_global / max(n_x_applied, 1.0)) - 1.0

        # 2. Face Sheet Wrinkling (Hoff & Mautner formulation):
        # sigma_wr = 0.5 * (E_f * E_c * G_c)^(1/3)
        sigma_wrinkling = 0.5 * ((self.E_f * self.E_c * self.G_c)**(1.0 / 3.0))
        # Applied stress on single face sheet:
        sigma_face_applied = sigma_comp
        ms_wrinkling = (sigma_wrinkling / max(sigma_face_applied, 1.0)) - 1.0

        # 3. Core Transverse Shear:
        # tau_core = V / (d * 2 * h) (carried by the two vertical sidewall sandwich cores)
        tau_core = applied_shear_n / (self.d * 2.0 * self.height)
        ms_core_shear = (self.tau_core_allow / max(tau_core, 1.0)) - 1.0

        is_sound = (ms_buckling >= 0.0) and (ms_wrinkling >= 0.0) and (ms_core_shear >= 0.0)

        return SandwichPanelResult(
            panel_width_m=self.width,
            bending_moment_applied_nm=applied_bending_moment_nm,
            torsion_applied_nm=applied_torsion_nm,
            axial_load_per_width_nm=round(n_x_applied, 1),
            global_buckling_load_nm=round(n_cr_global, 1),
            buckling_margin_of_safety=round(ms_buckling, 2),
            wrinkling_stress_pa=round(sigma_wrinkling, 1),
            face_stress_applied_pa=round(sigma_face_applied, 1),
            wrinkling_margin_of_safety=round(ms_wrinkling, 2),
            core_shear_applied_pa=round(tau_core, 1),
            core_shear_allowable_pa=round(self.tau_core_allow, 1),
            core_shear_margin_of_safety=round(ms_core_shear, 2),
            is_structurally_sound=is_sound
        )

    def evaluate_quick_disconnect_joint(self,
                                        design_lift_n: float = 1066.2,
                                        num_pins: int = 4,
                                        pin_diameter_mm: float = 8.0,
                                        pin_shear_allowable_pa: float = 450.0e6, # Titanium Ti-6Al-4V / 303 Stainless
                                        lug_thickness_mm: float = 6.0,
                                        lug_bearing_allowable_pa: float = 380.0e6, # Carbon composite bearing limit
                                        edge_distance_ratio: float = 2.5
                                        ) -> QuickDisconnectJointResult:
        """
        Analyzes the 4-pin quick-disconnect wing-to-fuselage attachment mechanism.
        Checks shear stress in pins, bearing stress in composite lugs, and edge tear-out.
        """
        # Load per pin (double shear assumed on wing-fuselage clevis brackets)
        load_per_pin = design_lift_n / num_pins
        d_pin_m = pin_diameter_mm / 1000.0
        t_lug_m = lug_thickness_mm / 1000.0

        # Double shear: tau = F / (2 * A_pin)
        a_pin = math.pi * ((d_pin_m / 2.0)**2)
        tau_pin = load_per_pin / (2.0 * a_pin)
        ms_pin_shear = (pin_shear_allowable_pa / max(tau_pin, 1.0)) - 1.0

        # Bearing stress: sigma_br = F / (d_pin * t_lug)
        sigma_bearing = load_per_pin / (d_pin_m * t_lug_m)
        ms_bearing = (lug_bearing_allowable_pa / max(sigma_bearing, 1.0)) - 1.0

        # Tear-out margin of safety (edge distance e >= 2.5 * d):
        # Allowable tear-out load P_to = 2 * (e - d/2) * t * tau_shear_lam
        tau_interlam_shear = 55.0e6 # Interlaminar shear of carbon laminate
        p_tear_out = 2.0 * ((edge_distance_ratio * d_pin_m) - (d_pin_m / 2.0)) * t_lug_m * tau_interlam_shear
        ms_tear_out = (p_tear_out / max(load_per_pin, 1.0)) - 1.0

        # Assembly time model: 4 push-button ball-lock pins @ 7.5 seconds per pin = 30 seconds
        total_assembly_time = num_pins * 7.5
        meets_rule = (total_assembly_time <= 60.0) and (ms_pin_shear >= 0.0) and (ms_bearing >= 0.0)

        return QuickDisconnectJointResult(
            num_pins=num_pins,
            pin_diameter_mm=pin_diameter_mm,
            pin_shear_stress_pa=round(tau_pin, 1),
            pin_shear_margin_of_safety=round(ms_pin_shear, 2),
            lug_bearing_stress_pa=round(sigma_bearing, 1),
            lug_bearing_margin_of_safety=round(ms_bearing, 2),
            tear_out_margin_of_safety=round(ms_tear_out, 2),
            assembly_time_seconds=round(total_assembly_time, 1),
            meets_5min_rule=meets_rule
        )
