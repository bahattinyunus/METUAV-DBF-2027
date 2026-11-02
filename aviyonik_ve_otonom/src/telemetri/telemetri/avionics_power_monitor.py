#!/usr/bin/env python3
"""
METUAV DBF 2027 - Smart Avionics PDB & CAN-Bus Telemetry Monitor
Monitors dual BEC rails (5V/12V), 6S propulsion power, servo bus current spikes
(detecting aerodynamic hinge stalls / mechanical jams), and UAVCAN bus health.
"""

import time
import math
from typing import Dict, List, Optional, Tuple


class AvionicsPowerMonitor:
    """
    Intelligent Power Distribution Board (PDB) and UAVCAN telemetry health monitor.
    Protects flight controller from brownouts by diagnosing servo stalls and rail dips.
    """

    def __init__(self,
                 bec_5v_nominal: float = 5.05,
                 bec_12v_nominal: float = 12.00,
                 servo_rail_nominal_v: float = 6.00,
                 servo_stall_current_thresh_a: float = 3.50,
                 servo_short_current_thresh_a: float = 6.00,
                 brownout_warning_v: float = 4.75):
        self.v_5v_nom = bec_5v_nominal
        self.v_12v_nom = bec_12v_nominal
        self.v_servo_nom = servo_rail_nominal_v
        self.i_stall_thresh = servo_stall_current_thresh_a
        self.i_short_thresh = servo_short_current_thresh_a
        self.v_brownout = brownout_warning_v

        # Channel current history for stall debounce
        self.servo_overcurrent_counters = {ch: 0 for ch in range(1, 9)}
        self.stall_counter_limit = 5  # 5 consecutive samples ~0.25s

        # UAVCAN bus statistics
        self.can_frames_total = 0
        self.can_frames_error = 0

    def evaluate_rails(self,
                       v_5v_rail: float,
                       v_12v_rail: float,
                       v_servo_rail: float) -> Dict[str, any]:
        """Verify voltage regulation on critical electronic buses."""
        err_5v = abs(v_5v_rail - self.v_5v_nom) / self.v_5v_nom
        err_12v = abs(v_12v_rail - self.v_12v_nom) / self.v_12v_nom
        err_servo = abs(v_servo_rail - self.v_servo_nom) / self.v_servo_nom

        brownout_risk = v_5v_rail < self.v_brownout

        status_5v = "HEALTHY" if err_5v <= 0.05 else ("CRITICAL" if brownout_risk else "WARNING")
        status_12v = "HEALTHY" if err_12v <= 0.08 else "WARNING"
        status_servo = "HEALTHY" if err_servo <= 0.10 else "WARNING"

        return {
            "v_5v": float(v_5v_rail),
            "status_5v": status_5v,
            "v_12v": float(v_12v_rail),
            "status_12v": status_12v,
            "v_servo": float(v_servo_rail),
            "status_servo": status_servo,
            "brownout_alert": bool(brownout_risk)
        }

    def process_servo_telemetry(self,
                                channel_currents_a: Dict[int, float]) -> Dict[str, any]:
        """
        Detect aerodynamic binding or mechanical jams per servo channel.
        channel_currents_a: dict mapping servo channel (1-8) to current in Amperes.
        """
        stalled_channels = []
        short_circuit_channels = []
        total_servo_current = 0.0

        for ch, current in channel_currents_a.items():
            total_servo_current += current
            if current >= self.i_short_thresh:
                short_circuit_channels.append(ch)
                self.servo_overcurrent_counters[ch] += 1
            elif current >= self.i_stall_thresh:
                self.servo_overcurrent_counters[ch] += 1
                if self.servo_overcurrent_counters[ch] >= self.stall_counter_limit:
                    stalled_channels.append(ch)
            else:
                self.servo_overcurrent_counters[ch] = max(0, self.servo_overcurrent_counters[ch] - 1)

        fault_detected = (len(stalled_channels) > 0) or (len(short_circuit_channels) > 0)

        return {
            "total_servo_current_a": float(total_servo_current),
            "stalled_channels": stalled_channels,
            "short_circuit_channels": short_circuit_channels,
            "servo_fault_alert": bool(fault_detected)
        }

    def record_can_frame(self, frame_valid: bool):
        """Record CAN-bus physical frame integrity."""
        self.can_frames_total += 1
        if not frame_valid:
            self.can_frames_error += 1

    def get_can_bus_health(self) -> Dict[str, float]:
        """Compute CAN error rate and bus health score."""
        if self.can_frames_total == 0:
            error_rate = 0.0
        else:
            error_rate = self.can_frames_error / self.can_frames_total

        health_pct = max(0.0, (1.0 - error_rate * 10.0) * 100.0)

        return {
            "total_frames": self.can_frames_total,
            "error_frames": self.can_frames_error,
            "error_rate": float(error_rate),
            "bus_health_pct": float(health_pct),
            "bus_nominal": bool(error_rate < 0.02)
        }

    def estimate_flight_endurance_sec(self,
                                     battery_soc_pct: float,
                                     battery_capacity_mah: float,
                                     current_draw_a: float) -> float:
        """Estimate remaining flight endurance in seconds under current discharge load."""
        if current_draw_a <= 0.1:
            return 3600.0  # Cap at 1 hour for zero current

        remaining_capacity_ah = (battery_capacity_mah * 1e-3) * (battery_soc_pct / 100.0)
        # 80% DoD safety limit
        usable_capacity_ah = max(0.0, remaining_capacity_ah - (battery_capacity_mah * 1e-3 * 0.15))
        endurance_hours = usable_capacity_ah / current_draw_a
        return float(endurance_hours * 3600.0)


def main():
    print("=" * 72)
    print("  METUAV DBF 2027 - AKILLI PDB VE UAVCAN TELEMETRI MONITORU")
    print("=" * 72)
    pdb = AvionicsPowerMonitor()

    # 1. Rail Evaluation
    rail_res = pdb.evaluate_rails(v_5v_rail=5.02, v_12v_rail=11.95, v_servo_rail=5.98)
    print("[*] Voltaj Regülasyon Durumu:")
    print(f"    - 5V Aviyonik Rail : {rail_res['v_5v']:.2f}V ({rail_res['status_5v']})")
    print(f"    - 12V Kamera Rail  : {rail_res['v_12v']:.2f}V ({rail_res['status_12v']})")
    print(f"    - 6V Servo Rail    : {rail_res['v_servo']:.2f}V ({rail_res['status_servo']})")
    print(f"    - Brownout Riski   : {'YOK (GUVENLI)' if not rail_res['brownout_alert'] else 'KRITIK DUSUS!'}")

    # 2. Servo Stall Simulation
    print("\n[*] Servo Hinge Stall / Sıkışma Testi (Kanal 2 Elevatör Sıkışması):")
    # Simulate 6 ticks of heavy current on CH2 (e.g. 4.2A elevator stall)
    for i in range(6):
        res = pdb.process_servo_telemetry({
            1: 0.45,  # Aileron Left
            2: 4.20,  # Elevator Stalled!
            3: 0.50,  # Rudder
            4: 0.40,  # Aileron Right
            5: 0.10   # Payload latch
        })
    print(f"    - Toplam Servo Akımı : {res['total_servo_current_a']:.2f} A")
    print(f"    - Kilitlenen Kanal   : CH {res['stalled_channels']}")
    print(f"    - Arıza Uyarısı      : {'ALARM AKTIF' if res['servo_fault_alert'] else 'NORMAL'}")

    # 3. UAVCAN Bus Health
    for _ in range(98):
        pdb.record_can_frame(True)
    for _ in range(2):
        pdb.record_can_frame(False)
    can_res = pdb.get_can_bus_health()
    print("\n[*] UAVCAN Haberleşme Sağlığı:")
    print(f"    - Toplam Paket       : {can_res['total_frames']}")
    print(f"    - Paket Hata Oranı   : %{can_res['error_rate']*100:.1f}")
    print(f"    - Veri Yolu Sağlığı  : %{can_res['bus_health_pct']:.1f} (Nominal: {can_res['bus_nominal']})")

    # 4. Endurance
    endurance = pdb.estimate_flight_endurance_sec(
        battery_soc_pct=85.0,
        battery_capacity_mah=16000.0,
        current_draw_a=35.0
    )
    print(f"\n[*] 35.0A Seyir Akımında Tahmini Uçuş Süresi: {endurance/60.0:.1f} Dakika ({endurance:.0f} sn)")
    print("=" * 72)


if __name__ == "__main__":
    main()
