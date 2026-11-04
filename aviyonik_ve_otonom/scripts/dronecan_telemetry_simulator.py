#!/usr/bin/env python3
"""
AIAA DBF Open Engineering Framework - DroneCAN / UAVCAN Telemetry Node Simulator
Simulates high-speed CAN-bus telemetry broadcast for:
- ESC motor RPM, voltage, current, and temperature (uORB / DroneCAN standard)
- Smart Battery Management System (BMS) individual 6S cell voltages & SOH
- Flight surface digital servo bus health (torque, load, deflection angle)
"""

import math
import struct
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class DroneCANMessage:
    can_id: int
    data_bytes: bytes
    timestamp_s: float
    message_type: str


class DroneCANTelemetrySimulator:
    def __init__(self, node_id: int = 42):
        self.node_id = node_id
        self.seq_id = 0

    def encode_esc_status(self, rpm: float, voltage_v: float, current_a: float, temp_c: float) -> DroneCANMessage:
        """
        Encodes DroneCAN ESC status (DataType: uavcan.equipment.esc.Status).
        Payload: 4 bytes RPM (uint32), 2 bytes Voltage (uint16 in mV),
                 2 bytes Current (int16 in 10mA), 1 byte Temp (int8 in C).
        """
        rpm_int = int(max(0, min(65535, rpm)))
        v_mv = int(max(0, min(65535, voltage_v * 1000.0)))
        i_10ma = int(max(-32768, min(32767, current_a * 100.0)))
        t_c = int(max(-40, min(125, temp_c)))

        payload = struct.pack("<HHhB", rpm_int, v_mv, i_10ma, t_c)
        can_id = 0x10000000 | (0x0400 << 8) | self.node_id

        self.seq_id += 1
        return DroneCANMessage(
            can_id=can_id,
            data_bytes=payload,
            timestamp_s=time.time(),
            message_type="uavcan.equipment.esc.Status"
        )

    def decode_esc_status(self, msg: DroneCANMessage) -> Dict[str, float]:
        """Decodes raw DroneCAN ESC status packet back into physical SI units."""
        rpm_int, v_mv, i_10ma, t_c = struct.unpack("<HHhB", msg.data_bytes)
        return {
            "rpm": float(rpm_int),
            "voltage_v": v_mv / 1000.0,
            "current_a": i_10ma / 100.0,
            "temp_c": float(t_c)
        }

    def encode_battery_cells(self, cell_voltages_v: List[float]) -> DroneCANMessage:
        """
        Encodes individual 6S cell voltages in mV (uint16 each).
        DataType: uavcan.equipment.power.BatteryInfoAux.
        """
        assert len(cell_voltages_v) == 6, "Must provide exactly 6 cell voltages for 6S LiPo"
        mv_list = [int(v * 1000.0) for v in cell_voltages_v]
        payload = struct.pack("<6H", *mv_list)
        can_id = 0x10000000 | (0x0420 << 8) | self.node_id

        return DroneCANMessage(
            can_id=can_id,
            data_bytes=payload,
            timestamp_s=time.time(),
            message_type="uavcan.equipment.power.BatteryInfoAux"
        )

    def decode_battery_cells(self, msg: DroneCANMessage) -> List[float]:
        """Decodes raw CAN bytes back to list of cell voltages in Volts."""
        mvs = struct.unpack("<6H", msg.data_bytes)
        return [mv / 1000.0 for mv in mvs]

    def encode_servo_feedback(self, servo_id: int, pos_deg: float, current_ma: float) -> DroneCANMessage:
        """Encodes digital servo feedback (angle deflection & torque/current)."""
        angle_centi_deg = int(pos_deg * 100.0)
        i_ma = int(current_ma)
        payload = struct.pack("<BhH", servo_id, angle_centi_deg, i_ma)
        can_id = 0x10000000 | (0x0440 << 8) | self.node_id

        return DroneCANMessage(
            can_id=can_id,
            data_bytes=payload,
            timestamp_s=time.time(),
            message_type="uavcan.equipment.actuator.Status"
        )

    def decode_servo_feedback(self, msg: DroneCANMessage) -> Dict[str, float]:
        """Decodes servo telemetry."""
        servo_id, angle_cd, i_ma = struct.unpack("<BhH", msg.data_bytes)
        return {
            "servo_id": servo_id,
            "pos_deg": angle_cd / 100.0,
            "current_ma": float(i_ma)
        }


def run_dronecan_demo():
    sim = DroneCANTelemetrySimulator(node_id=15)
    print("=" * 72)
    print("  AIAA DBF OPEN FRAMEWORK - DRONECAN / UAVCAN BUS SİMÜLATÖRÜ")
    print("=" * 72)

    # 1. ESC telemetry
    esc_msg = sim.encode_esc_status(rpm=6800.0, voltage_v=24.55, current_a=34.2, temp_c=58)
    esc_decoded = sim.decode_esc_status(esc_msg)
    print(f"  [ESC STATUS] -> Devir: {esc_decoded['rpm']:.0f} RPM | Gerilim: {esc_decoded['voltage_v']:.2f} V | Akım: {esc_decoded['current_a']:.1f} A | Sıcaklık: {esc_decoded['temp_c']:.0f}°C")

    # 2. Battery cells
    cells = [4.12, 4.10, 4.11, 4.09, 4.12, 4.10]
    batt_msg = sim.encode_battery_cells(cells)
    batt_decoded = sim.decode_battery_cells(batt_msg)
    print(f"  [6S BMS AUX] -> Hücreler: {batt_decoded} V (Toplam: {sum(batt_decoded):.2f} V)")

    # 3. Servo status
    srv_msg = sim.encode_servo_feedback(servo_id=1, pos_deg=-3.5, current_ma=420.0)
    srv_decoded = sim.decode_servo_feedback(srv_msg)
    print(f"  [SERVO STAT] -> Servo #{srv_decoded['servo_id']} | Açı: {srv_decoded['pos_deg']:+.1f}° | Akım: {srv_decoded['current_ma']:.0f} mA")
    print("=" * 72)


if __name__ == "__main__":
    run_dronecan_demo()
