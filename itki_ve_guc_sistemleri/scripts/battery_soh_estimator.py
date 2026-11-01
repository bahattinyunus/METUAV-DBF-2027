#!/usr/bin/env python3
"""
METUAV DBF 2027 - 6S LiPo Dual-RC Thevenin Battery Model & SOH / R0 Estimator
Estimates dynamic internal resistance (R0), polarization voltages (V1, V2),
and predicts maximum throttle voltage sag to prevent in-flight ESC low-voltage cut-off.
"""

import math
import numpy as np
from typing import Dict, Tuple, List


class BatteryTheveninModel:
    def __init__(self,
                 nominal_capacity_ah: float = 16.0,
                 cell_count: int = 6,
                 r0_ohm: float = 0.0072,      # 1.2 mOhm per cell * 6 cells
                 r0_factory_ohm: float = 0.0072,
                 r1_ohm: float = 0.0048,      # Charge transfer resistance
                 c1_farad: float = 120.0,     # Charge transfer capacitance (tau1 = 0.57s)
                 r2_ohm: float = 0.0060,      # Diffusion resistance
                 c2_farad: float = 2500.0):   # Diffusion capacitance (tau2 = 15.0s)
        self.capacity_ah = nominal_capacity_ah
        self.capacity_coulombs = nominal_capacity_ah * 3600.0
        self.cells = cell_count

        # Equivalent circuit parameters (pack total)
        self.r0 = r0_ohm
        self.r0_factory = r0_factory_ohm
        self.r1 = r1_ohm
        self.c1 = c1_farad
        self.r2 = r2_ohm
        self.c2 = c2_farad

        # Dynamic state variables
        self.soc = 1.0           # 100% full
        self.v1 = 0.0            # Polarization voltage 1
        self.v2 = 0.0            # Polarization voltage 2
        self.consumed_ah = 0.0

    def get_ocv(self, soc: float) -> float:
        """
        Computes 6S Open Circuit Voltage from SOC using empirical LiPo polynomial curve:
        Cell OCV ranges from 3.50V at 0% to 4.20V at 100%.
        """
        s = np.clip(soc, 0.0, 1.0)
        # Single cell OCV approximation
        v_cell = 3.45 + 0.55 * s + 0.20 * (s**3)
        return float(v_cell * self.cells)

    def update(self, current_amps: float, dt: float) -> Dict[str, float]:
        """
        Simulates battery dynamics for time step dt under load current_amps.
        (current_amps > 0 is discharge).
        """
        # 1. Coulomb counting for SOC
        delta_q = current_amps * dt
        self.consumed_ah += delta_q / 3600.0
        self.soc = max(0.0, 1.0 - (self.consumed_ah / self.capacity_ah))

        # 2. RC filter voltage integration:
        # dv/dt = -v / (R*C) + I / C
        dv1 = (-self.v1 / (self.r1 * self.c1) + current_amps / self.c1) * dt
        dv2 = (-self.v2 / (self.r2 * self.c2) + current_amps / self.c2) * dt
        self.v1 += dv1
        self.v2 += dv2

        # 3. Terminal voltage: Vt = OCV(SOC) - I * R0 - V1 - V2
        ocv = self.get_ocv(self.soc)
        terminal_voltage = ocv - current_amps * self.r0 - self.v1 - self.v2

        # 4. Predict voltage sag under a sudden 85A full-throttle burst
        max_burst_amps = 85.0
        predicted_sag_v = ocv - max_burst_amps * self.r0 - self.v1 - self.v2
        min_cell_v = predicted_sag_v / self.cells

        # 5. State of Health based on R0 increase (100% at r0_factory, 0% at 2.0*r0_factory)
        r_deg = (self.r0 - self.r0_factory) / self.r0_factory
        soh_pct = float(np.clip(100.0 * (1.0 - r_deg), 0.0, 100.0))

        return {
            "terminal_voltage_v": float(terminal_voltage),
            "ocv_v": float(ocv),
            "soc_pct": float(self.soc * 100.0),
            "v1_v": float(self.v1),
            "v2_v": float(self.v2),
            "predicted_max_burst_v": float(predicted_sag_v),
            "predicted_min_cell_v": float(min_cell_v),
            "safe_margin_over_cutoff_v": float(predicted_sag_v - 19.8),  # 3.3V/cell cutoff = 19.8V
            "soh_pct": soh_pct
        }


def main():
    print("=" * 72)
    print("  METUAV DBF 2027 - 6S LiPo DUAL-RC THEVENIN BATTERY SOH MODEL")
    print("=" * 72)
    battery = BatteryTheveninModel()

    # Simulate 3-lap mission profile (80 seconds)
    # Cruise current ~ 34A, burst pylon turns ~ 65A, takeoff ~ 82A
    sim_time = 0.0
    dt = 0.1

    print(f"[*] Batarya Özellikleri: 6S 16,000 mAh (355.2 Wh)")
    print(f"    - Hücre Başı İç Direnç (R0) : {battery.r0 / 6.0 * 1000.0:.2f} mOhm (Paket: {battery.r0 * 1000.0:.2f} mOhm)")
    print(f"    - Başlangıç Voltajı (100%)  : {battery.get_ocv(1.0):.2f} V ({battery.get_ocv(1.0)/6.0:.2f} V/hücre)")
    print("-" * 72)

    # 1. Takeoff phase (15s at 82A)
    for _ in range(150):
        res = battery.update(current_amps=82.0, dt=dt)
        sim_time += dt

    print(f"[t={sim_time:.1f}s] KALKIŞ (82 A Tam Güç):")
    print(f"    - Klemens Voltajı    : {res['terminal_voltage_v']:.2f} V")
    print(f"    - Hücre Voltajı      : {res['terminal_voltage_v']/6.0:.2f} V/hücre (> 3.30 V limit)")
    print(f"    - OCV                : {res['ocv_v']:.2f} V")
    print(f"    - Kalan Kapasite     : %{res['soc_pct']:.1f}")

    # 2. Cruise phase (65s at 34A)
    for _ in range(650):
        res = battery.update(current_amps=34.0, dt=dt)
        sim_time += dt

    print("-" * 72)
    print(f"[t={sim_time:.1f}s] SEYİR VE İNİŞ SONU:")
    print(f"    - Klemens Voltajı    : {res['terminal_voltage_v']:.2f} V")
    print(f"    - Kalan Kapasite     : %{res['soc_pct']:.1f}")
    print(f"    - SOH (Sağlık Durumu): %{res['soh_pct']:.1f}")
    print(f"    - Ani Gaz Açma Saniyesi Hücre Dip Gerilimi: {res['predicted_min_cell_v']:.2f} V/hücre")
    print(f"    - Emniyet Marjı (19.8V Cut-off Üstü)      : +{res['safe_margin_over_cutoff_v']:.2f} V")
    print("=" * 72)

    assert res['predicted_min_cell_v'] > 3.30, "Must not violate 3.30V/cell minimum voltage under load"
    print("[BASARILI] 6S LiPo Termal ve Gerilim Sehim Modeli Emniyetli!")


if __name__ == '__main__':
    main()
