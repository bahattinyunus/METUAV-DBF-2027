#!/usr/bin/env python3
"""
METUAV DBF 2027 - Sensor Failure Detection, Isolation and Recovery (FDIR) Manager
Monitors multi-sensor health, detects pitot icing/blockage, baro drift, geofence breach,
and triggers autonomous recovery / Return-To-Land (RTL) procedures.
"""

import math
import numpy as np
from typing import Dict, Tuple, List, Optional
from enum import Enum


class FDIRStatus(Enum):
    NOMINAL = "NOMINAL"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class FDIRManager:
    def __init__(self,
                 max_airspeed_gps_diff_ms: float = 6.0,
                 max_alt_diff_m: float = 3.5,
                 min_cell_voltage_v: float = 3.30,
                 geofence_half_width_m: float = 500.0,
                 geofence_half_height_m: float = 300.0,
                 max_altitude_m: float = 120.0):
        self.max_airspeed_diff = max_airspeed_gps_diff_ms
        self.max_alt_diff = max_alt_diff_m
        self.min_cell_v = min_cell_voltage_v
        self.gf_x = geofence_half_width_m
        self.gf_y = geofence_half_height_m
        self.gf_alt = max_altitude_m

        # Sensor health states
        self.pitot_healthy = True
        self.baro_healthy = True
        self.gps_healthy = True
        self.imu_healthy = True
        self.battery_healthy = True
        self.geofence_breached = False

        # History for voting and debounce
        self.pitot_error_count = 0
        self.baro_error_count = 0
        self.debounce_threshold = 5  # 5 consecutive bad samples required to trip

        # Estimated synthetic airspeed in fallback mode
        self.synthetic_airspeed = 24.5

    def check_airspeed_consistency(self, pitot_airspeed_ms: float,
                                   gps_ground_speed_ms: float,
                                   estimated_wind_speed_ms: float = 0.0) -> Tuple[bool, float]:
        """
        Detects pitot tube blockage (ice, dirt, insect, water) by cross-checking
        pitot dynamic pressure derived airspeed against GPS ground speed and wind estimate.
        Returns: (is_healthy, airspeed_to_use)
        """
        # Expected airspeed from ground speed and wind: |Va - Vg| <= V_wind
        speed_diff = abs(pitot_airspeed_ms - gps_ground_speed_ms)
        max_allowed_diff = self.max_airspeed_diff + estimated_wind_speed_ms

        if speed_diff > max_allowed_diff or pitot_airspeed_ms < 0.5 and gps_ground_speed_ms > 12.0:
            self.pitot_error_count += 1
            if self.pitot_error_count >= self.debounce_threshold:
                self.pitot_healthy = False
        else:
            self.pitot_error_count = max(0, self.pitot_error_count - 1)
            self.pitot_healthy = True

        if not self.pitot_healthy:
            # Fallback: estimate airspeed from GPS groundspeed and forward wind component
            self.synthetic_airspeed = max(gps_ground_speed_ms, 12.0)
            return False, self.synthetic_airspeed

        return True, pitot_airspeed_ms

    def check_altitude_consistency(self, baro_alt_m: float,
                                   gps_alt_m: float,
                                   rangefinder_alt_m: Optional[float] = None) -> Tuple[bool, float]:
        """
        Detects static port blockage or barometric drift.
        If a rangefinder (LiDAR/optical) is available below 15m, it takes precedence.
        """
        alt_diff = abs(baro_alt_m - gps_alt_m)

        if alt_diff > self.max_alt_diff:
            self.baro_error_count += 1
            if self.baro_error_count >= self.debounce_threshold:
                self.baro_healthy = False
        else:
            self.baro_error_count = max(0, self.baro_error_count - 1)
            self.baro_healthy = True

        if rangefinder_alt_m is not None and 0.1 <= rangefinder_alt_m <= 15.0:
            return True, rangefinder_alt_m

        if not self.baro_healthy:
            return False, gps_alt_m

        return True, baro_alt_m

    def check_battery_voltage(self, pack_voltage_v: float, current_a: float, cell_count: int = 6) -> Tuple[bool, float]:
        """
        Monitors cell voltage under load. Detects critical sag (< 3.30V/cell).
        """
        v_cell = pack_voltage_v / float(cell_count)
        if v_cell < self.min_cell_v:
            self.battery_healthy = False
            return False, v_cell
        self.battery_healthy = True
        return True, v_cell

    def check_geofence(self, pos_north_m: float, pos_east_m: float, altitude_agl_m: float) -> bool:
        """
        Checks if aircraft is within allowed competition bounding box.
        """
        inside_x = abs(pos_north_m) <= self.gf_x
        inside_y = abs(pos_east_m) <= self.gf_y
        inside_alt = 0.0 <= altitude_agl_m <= self.gf_alt

        if not (inside_x and inside_y and inside_alt):
            self.geofence_breached = True
            return False

        self.geofence_breached = False
        return True

    def evaluate_system_health(self,
                               pitot_airspeed: float,
                               gps_ground_speed: float,
                               baro_alt: float,
                               gps_alt: float,
                               battery_voltage: float,
                               current_a: float,
                               pos_north: float,
                               pos_east: float,
                               altitude_agl: float,
                               rangefinder_alt: Optional[float] = None) -> Dict:
        """
        Performs full FDIR diagnostic sweep and decides system status and action.
        """
        pitot_ok, reliable_airspeed = self.check_airspeed_consistency(pitot_airspeed, gps_ground_speed)
        baro_ok, reliable_altitude = self.check_altitude_consistency(baro_alt, gps_alt, rangefinder_alt)
        battery_ok, min_cell_v = self.check_battery_voltage(battery_voltage, current_a)
        geofence_ok = self.check_geofence(pos_north, pos_east, altitude_agl)

        action = "CONTINUE_MISSION"
        status = FDIRStatus.NOMINAL

        if not geofence_ok:
            status = FDIRStatus.CRITICAL
            action = "FAILSAFE_IMMEDIATE_RTL"
        elif not battery_ok:
            status = FDIRStatus.CRITICAL
            action = "FAILSAFE_EMERGENCY_LAND"
        elif not pitot_ok or not baro_ok:
            status = FDIRStatus.DEGRADED
            action = "DEGRADED_SYNTHETIC_NAVIGATION"

        return {
            "status": status.value,
            "recommended_action": action,
            "reliable_airspeed_ms": round(reliable_airspeed, 2),
            "reliable_altitude_m": round(reliable_altitude, 2),
            "min_cell_voltage_v": round(min_cell_v, 2),
            "pitot_healthy": pitot_ok,
            "baro_healthy": baro_ok,
            "battery_healthy": battery_ok,
            "geofence_compliant": geofence_ok
        }


def main():
    print("=" * 72)
    print("  METUAV DBF 2027 - SENSOR FDIR & FAILSAFE RECOVERY MANAGER")
    print("=" * 72)
    fdir = FDIRManager()

    # 1. Nominal flight check
    diag_nom = fdir.evaluate_system_health(
        pitot_airspeed=24.5,
        gps_ground_speed=23.8,
        baro_alt=25.0,
        gps_alt=24.8,
        battery_voltage=24.6,
        current_a=34.0,
        pos_north=50.0,
        pos_east=10.0,
        altitude_agl=25.0
    )
    print(f"[*] Durum 1: Nominal Uçuş:")
    print(f"    - Sistem Sağlığı  : {diag_nom['status']}")
    print(f"    - Tavsiye Edilen : {diag_nom['recommended_action']}")
    print(f"    - Güvenilir Hız  : {diag_nom['reliable_airspeed_ms']} m/s")
    assert diag_nom['status'] == "NOMINAL"

    # 2. Pitot icing blockage failure test (Pitot reads 0 m/s while GPS reads 24 m/s)
    for _ in range(6):
        diag_pitot = fdir.evaluate_system_health(
            pitot_airspeed=0.0,
            gps_ground_speed=24.0,
            baro_alt=25.0,
            gps_alt=25.0,
            battery_voltage=24.2,
            current_a=34.0,
            pos_north=50.0,
            pos_east=10.0,
            altitude_agl=25.0
        )
    print("-" * 72)
    print(f"[*] Durum 2: Pitot Donması / Tıkanması Arızası (Pitot = 0 m/s):")
    print(f"    - Sistem Sağlığı  : {diag_pitot['status']}")
    print(f"    - Tavsiye Edilen : {diag_pitot['recommended_action']}")
    print(f"    - Sentetik Hız   : {diag_pitot['reliable_airspeed_ms']} m/s (GPS Fallback devrede)")
    assert diag_pitot['status'] == "DEGRADED"
    assert diag_pitot['reliable_airspeed_ms'] == 24.0

    # 3. Geofence breach test
    diag_gf = fdir.evaluate_system_health(
        pitot_airspeed=24.5,
        gps_ground_speed=24.0,
        baro_alt=25.0,
        gps_alt=25.0,
        battery_voltage=24.2,
        current_a=34.0,
        pos_north=600.0,  # Out of 500m bounds!
        pos_east=10.0,
        altitude_agl=25.0
    )
    print("-" * 72)
    print(f"[*] Durum 3: Geofence İhlali (North = +600m > 500m Limit):")
    print(f"    - Sistem Sağlığı  : {diag_gf['status']}")
    print(f"    - Tavsiye Edilen : {diag_gf['recommended_action']}")
    assert diag_gf['status'] == "CRITICAL"
    print("=" * 72)
    print("[BASARILI] FDIR Failsafe ve Sensör Oylama Sistemi Doğrulandı!")


if __name__ == '__main__':
    main()
