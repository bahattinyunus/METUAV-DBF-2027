#!/usr/bin/env python3
"""
AIAA DBF 2027 - Brushless Motor & Battery Thermal Dynamics Simulator
Simulates stator winding temperature and LiPo internal temperature
during the intense 5-minute AIAA DBF mission flight profile.
"""

import math
import numpy as np
from typing import Dict, List, Tuple

class PropulsionThermalSimulator:
    def __init__(self):
        # Motor specs: Scorpion SII-4035-330KV
        self.r_motor_ohm_20c = 0.021     # Motor winding internal resistance at 20C (Ohms)
        self.alpha_cu = 0.00393          # Temperature coefficient of resistance for copper (1/C)
        self.motor_mass_kg = 0.465       # Stator + rotor mass (kg)
        self.c_th_motor = 420.0 * self.motor_mass_kg  # Heat capacity (J/K) for Copper/Iron ~ 195 J/K
        self.surface_area_motor = 0.028  # Outer stator surface area (m^2)

        # Battery specs: 6S 16000mAh 70C LiPo
        self.r_batt_internal = 0.012     # Internal pack resistance (Ohms)
        self.batt_mass_kg = 2.15         # kg
        self.c_th_batt = 950.0 * self.batt_mass_kg    # LiPo heat capacity ~ 2042 J/K
        self.surface_area_batt = 0.095   # Battery surface area (m^2)

        # Ambient conditions (Competition at Wichita/Tucson airfield: hot day)
        self.t_ambient = 32.0            # °C (Hot field ambient)

    def simulate_mission_profile(self, total_time_sec: float = 300.0, dt: float = 0.1) -> Dict[str, np.ndarray]:
        """
        Simulates 5-minute flight:
        - 0-20s: Full throttle takeoff climb (Current = 85 A, Airspeed = 18 m/s)
        - 20-260s: Cruise flight with 3 laps (Current = 34 A, Airspeed = 24.5 m/s)
        - 260-300s: Descent and landing approach (Current = 14 A, Airspeed = 17 m/s)
        """
        n_steps = int(total_time_sec / dt)
        time_arr = np.linspace(0.0, total_time_sec, n_steps)
        
        t_motor_arr = np.zeros(n_steps)
        t_batt_arr = np.zeros(n_steps)
        current_arr = np.zeros(n_steps)

        # Initial temperatures equal to ambient
        t_motor = self.t_ambient
        t_batt = self.t_ambient

        for i, t in enumerate(time_arr):
            # Profile phases
            if t < 25.0:
                current = 82.0
                v_air = 18.0
            elif t < 265.0:
                current = 33.5
                v_air = 24.5
            else:
                current = 14.0
                v_air = 17.0

            current_arr[i] = current

            # Motor resistance adjusted for current temperature
            r_motor = self.r_motor_ohm_20c * (1.0 + self.alpha_cu * (t_motor - 20.0))
            p_copper_loss = (current ** 2) * r_motor
            p_iron_loss = 45.0 * (v_air / 24.5) ** 1.4  # Eddy currents & hysteresis
            p_loss_motor = p_copper_loss + p_iron_loss

            # Convective heat transfer coefficient (enhanced by propeller slipstream)
            h_motor = 28.0 + 14.5 * math.sqrt(v_air)
            q_cool_motor = h_motor * self.surface_area_motor * (t_motor - self.t_ambient)

            d_t_motor = ((p_loss_motor - q_cool_motor) / self.c_th_motor) * dt
            t_motor += d_t_motor
            t_motor_arr[i] = t_motor

            # Battery thermal dynamics
            p_loss_batt = (current ** 2) * self.r_batt_internal
            h_batt = 12.0 + 6.0 * math.sqrt(v_air * 0.3)  # Duct cooling inside fuselage
            q_cool_batt = h_batt * self.surface_area_batt * (t_batt - self.t_ambient)

            d_t_batt = ((p_loss_batt - q_cool_batt) / self.c_th_batt) * dt
            t_batt += d_t_batt
            t_batt_arr[i] = t_batt

        return {
            "time_sec": time_arr,
            "current_a": current_arr,
            "t_motor_c": t_motor_arr,
            "t_batt_c": t_batt_arr
        }


def main():
    print("=" * 72)
    print("  AIAA DBF 2027 - Motor ve Batarya 5 Dakikalik Termal Dinamik Analizi")
    print("=" * 72)

    sim = PropulsionThermalSimulator()
    res = sim.simulate_mission_profile()

    max_t_motor = float(np.max(res["t_motor_c"]))
    final_t_motor = float(res["t_motor_c"][-1])
    max_t_batt = float(np.max(res["t_batt_c"]))
    final_t_batt = float(res["t_batt_c"][-1])

    print(f"Baslangic Ortam Sicakligi: {sim.t_ambient:.1f}°C")
    print(f"\n[MOTOR TERMAL SONUCLARI]")
    print(f"- Maksimum Sargi Sicakligi: {max_t_motor:.1f}°C (Guvenli Limit: < 105.0°C)")
    print(f"- Ucus Sonu Sicakligi: {final_t_motor:.1f}°C")
    print(f"- Termal Guvenlik Marjini: {105.0 - max_t_motor:.1f}°C")

    print(f"\n[BATARYA TERMAL SONUCLARI]")
    print(f"- Maksimum Hucre Sicakligi: {max_t_batt:.1f}°C (Guvenli Limit: < 60.0°C)")
    print(f"- Ucus Sonu Sicakligi: {final_t_batt:.1f}°C")
    print(f"- Termal Guvenlik Marjini: {60.0 - max_t_batt:.1f}°C")

    assert max_t_motor < 100.0, f"Motor temperature {max_t_motor:.1f}C exceeded safety threshold!"
    assert max_t_batt < 55.0, f"Battery temperature {max_t_batt:.1f}C exceeded safety threshold!"
    print("\n[BASARILI] Termal tasarim ve hava kanali sogutma performansi tam onay aldi!")
    print("=" * 72)


if __name__ == '__main__':
    main()
