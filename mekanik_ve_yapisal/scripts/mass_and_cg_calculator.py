#!/usr/bin/env python3
"""
AIAA DBF 2027 - Mass and Center of Gravity (CG) Budget Calculator
Tracks mass properties, CG location (X, Y, Z), and mass moments of inertia
across all AIAA DBF mission configurations to ensure strict compliance with 55 lbs limit.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class Component:
    name: str
    mass_kg: float
    x_m: float  # X from nose (+ aft)
    y_m: float  # Y from centerline (+ right)
    z_m: float  # Z from fuselage datum (+ up)


@dataclass
class MissionConfigReport:
    config_name: str
    total_mass_kg: float
    total_weight_lbs: float
    cg_x_m: float
    cg_y_m: float
    cg_z_m: float
    cg_mac_percent: float
    is_compliant: bool
    ixx_kg_m2: float
    iyy_kg_m2: float
    izz_kg_m2: float


class MassAndCGBudget:
    def __init__(self, mac_le_m: float = 0.38, mac_len_m: float = 0.293):
        self.mac_le = mac_le_m
        self.mac_len = mac_len_m

        self.base_components: List[Component] = [
            Component("Burun Konisi & Pitot Tupu", 0.18, 0.08, 0.0, 0.0),
            Component("Fircasiz Motor & Pervane (Scorpion SII-4035)", 0.65, 0.05, 0.0, 0.0),
            Component("ESC & Guc Dagitim Karti (120A HV)", 0.22, 0.18, 0.0, -0.02),
            Component("Pixhawk 6X & Sensor Paketi", 0.15, 0.32, 0.0, 0.05),
            Component("Jetson Orin Nano Edge-AI Kart & Kamera", 0.25, 0.28, 0.0, -0.06),
            Component("Batarya Paketi 6S2P LiPo 16000mAh", 2.20, 0.30, 0.0, -0.03),
            Component("Karbon-Sandvic Ana Govde Kabugu", 1.85, 0.55, 0.0, 0.0),
            Component("Karbon I-Beam Ana Kanat Spari", 1.45, 0.42, 0.0, 0.10),
            Component("Kopuk Dolgulu Kanat Yuzeyi & Kaplama", 2.10, 0.44, 0.0, 0.10),
            Component("Aileron Servolari (4x KST DS589MG)", 0.24, 0.46, 0.0, 0.08),
            Component("Inis Takimi (Karbon Bacaklar & Tekerlekler)", 1.25, 0.35, 0.0, -0.15),
            Component("Yatay & Dusey Kuyruk Yuzeyleri", 0.95, 1.42, 0.0, 0.12),
            Component("Kuyruk Servolari (Elevator/Rudder)", 0.16, 1.35, 0.0, 0.08),
            Component("Baglanti Elemanlari, Kablo Demeti & Telemetri", 0.70, 0.45, 0.0, 0.0),
            Component("Faydali Yuk Birakma Mekanizmasi (Servo/Kilit)", 0.35, 0.40, 0.0, -0.05),
        ]

        self.configs = {
            "Empty (Sistemler Dahil, Bataryasiz)": [],
            "Mission 1 (Staging - Yuksus 3 Tur)": [
                Component("Ucus Bataryasi", 0.85, 0.28, 0.0, -0.03)
            ],
            "Mission 2 (Maksimum Agirlik - 55 lbs TOGW Siniri)": [
                Component("Gorev 2 Agir Faydali Yuk (Medikal Kutular)", 11.20, 0.38, 0.0, -0.04)
            ],
            "Mission 3 (Pre-Drop - Delivery Yuku)": [
                Component("Gorev 3 Birakilabilir Yuk", 8.35, 0.36, 0.0, -0.05)
            ],
            "Mission 3 (Post-Drop - Yuksus Eve Donus)": []
        }

    def evaluate_configuration(self, config_name: str) -> MissionConfigReport:
        extra_items = self.configs.get(config_name, [])
        all_items = self.base_components + extra_items

        total_mass = sum(c.mass_kg for c in all_items)
        cg_x = sum(c.mass_kg * c.x_m for c in all_items) / total_mass
        cg_y = sum(c.mass_kg * c.y_m for c in all_items) / total_mass
        cg_z = sum(c.mass_kg * c.z_m for c in all_items) / total_mass

        weight_lbs = total_mass * 2.20462
        is_compliant = weight_lbs <= 55.0

        # Percentage of Mean Aerodynamic Chord (% MAC)
        cg_mac_percent = ((cg_x - self.mac_le) / self.mac_len) * 100.0

        # Point-mass approximation for moments of inertia about CG
        ixx = sum(c.mass_kg * ((c.y_m - cg_y)**2 + (c.z_m - cg_z)**2) for c in all_items)
        iyy = sum(c.mass_kg * ((c.x_m - cg_x)**2 + (c.z_m - cg_z)**2) for c in all_items)
        izz = sum(c.mass_kg * ((c.x_m - cg_x)**2 + (c.y_m - cg_y)**2) for c in all_items)

        return MissionConfigReport(
            config_name=config_name,
            total_mass_kg=total_mass,
            total_weight_lbs=weight_lbs,
            cg_x_m=cg_x,
            cg_y_m=cg_y,
            cg_z_m=cg_z,
            cg_mac_percent=cg_mac_percent,
            is_compliant=is_compliant,
            ixx_kg_m2=ixx,
            iyy_kg_m2=iyy,
            izz_kg_m2=izz
        )

    def evaluate_all(self) -> Dict[str, MissionConfigReport]:
        return {name: self.evaluate_configuration(name) for name in self.configs}


def calculate_mass_budget():
    budget = MassAndCGBudget()
    reports = budget.evaluate_all()

    print("=" * 72)
    print("  AIAA DBF 2027 - Kutle ve Agirlik Merkezi (CG) Butce Analizi")
    print("=" * 72)

    for name, r in reports.items():
        status = "UYGUN" if r.is_compliant else "LIMIT ASILDI"
        print(f"[*] {name}")
        print(f"    - Toplam Kutle: {r.total_mass_kg:.2f} kg | {r.total_weight_lbs:.2f} lbs [{status}]")
        print(f"    - CG X: {r.cg_x_m:.3f} m (%{r.cg_mac_percent:.1f} MAC) | CG Z: {r.cg_z_m:.3f} m")
        print(f"    - Atalet (Ixx, Iyy, Izz): ({r.ixx_kg_m2:.2f}, {r.iyy_kg_m2:.2f}, {r.izz_kg_m2:.2f}) kg*m^2")

    return reports


if __name__ == '__main__':
    calculate_mass_budget()
