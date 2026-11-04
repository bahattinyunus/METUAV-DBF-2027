#!/usr/bin/env python3
"""
AIAA DBF 2027 - Autonomous Takeoff, Flare & Braking Sequence State Machine
Controls ground roll, rotation (V_r), liftoff, climb-out, glide path approach,
flare with Wieselsberger ground effect compensation, and rollout braking.
"""

import enum
import math
from typing import Dict, Tuple, Optional


class FlightPhase(enum.Enum):
    PREFLIGHT = 0
    GROUND_ROLL = 1
    ROTATION = 2
    CLIMB_OUT = 3
    EN_ROUTE = 4
    APPROACH = 5
    FLARE = 6
    ROLLOUT = 7
    STOPPED = 8


class TakeoffLandingController:
    """
    Finite State Machine and guidance controller for automated runway takeoff and landing.
    Enforces DBF strict takeoff limits (< 200 ft / 61 m) and gentle flare touchdown.
    """

    def __init__(self,
                 stall_speed_ms: float = 12.0,
                 best_climb_speed_ms: float = 18.0,
                 wing_span_m: float = 2.40,
                 takeoff_distance_limit_m: float = 61.0,
                 climb_screen_height_m: float = 15.0,
                 flare_entry_altitude_m: float = 2.0,
                 target_touchdown_sink_ms: float = -0.4):
        self.v_stall = stall_speed_ms
        self.v_rot = 1.15 * stall_speed_ms       # ~13.8 m/s
        self.v_climb = best_climb_speed_ms      # 18.0 m/s
        self.v_app = 1.30 * stall_speed_ms        # ~15.6 m/s
        self.wing_span = wing_span_m
        self.max_takeoff_dist = takeoff_distance_limit_m
        self.h_screen = climb_screen_height_m
        self.h_flare = flare_entry_altitude_m
        self.sink_flare_target = target_touchdown_sink_ms

        self.phase = FlightPhase.PREFLIGHT
        self.ground_roll_start_x = 0.0
        self.liftoff_x = 0.0
        self.touchdown_x = 0.0
        self.armed = False

    def arm(self):
        """Arm the system for takeoff."""
        self.armed = True
        self.phase = FlightPhase.GROUND_ROLL
        self.ground_roll_start_x = 0.0

    def compute_ground_effect_factor(self, altitude_m: float) -> float:
        """
        Wieselsberger ground effect factor sigma_ge on induced drag:
        sigma_ge = 16*(h/b)^2 / (1 + 16*(h/b)^2).
        Returns induced drag multiplier (0.0 to 1.0).
        """
        if altitude_m <= 0.05:
            h_eff = 0.05
        else:
            h_eff = altitude_m

        h_over_b = h_eff / self.wing_span
        sigma = (16.0 * (h_over_b**2)) / (1.0 + 16.0 * (h_over_b**2))
        return float(min(1.0, max(0.15, sigma)))

    def update(self,
               airspeed_ms: float,
               altitude_m: float,
               vertical_speed_ms: float,
               x_position_m: float,
               wheel_weight_on_wheels: bool) -> Dict:
        """
        State machine update loop.
        Returns control demands:
        - throttle_norm: 0.0 to 1.0
        - pitch_target_deg: target fuselage pitch angle
        - wheel_brakes_norm: 0.0 to 1.0
        - ground_effect_sigma: Wieselsberger induced drag factor
        - phase: current FlightPhase string
        """
        throttle = 0.0
        pitch_target = 0.0
        wheel_brakes = 0.0
        sigma_ge = self.compute_ground_effect_factor(altitude_m)

        # First check phase transition triggers
        if self.phase == FlightPhase.GROUND_ROLL:
            if airspeed_ms >= self.v_rot:
                self.phase = FlightPhase.ROTATION

        elif self.phase == FlightPhase.ROTATION:
            if not wheel_weight_on_wheels and altitude_m > 0.5:
                self.liftoff_x = x_position_m
                self.phase = FlightPhase.CLIMB_OUT

        elif self.phase == FlightPhase.CLIMB_OUT:
            if altitude_m >= self.h_screen:
                self.phase = FlightPhase.EN_ROUTE

        elif self.phase == FlightPhase.APPROACH:
            if altitude_m <= self.h_flare:
                self.phase = FlightPhase.FLARE

        elif self.phase == FlightPhase.FLARE:
            if wheel_weight_on_wheels and altitude_m < 0.2:
                self.touchdown_x = x_position_m
                self.phase = FlightPhase.ROLLOUT

        elif self.phase == FlightPhase.ROLLOUT:
            if airspeed_ms < 1.0:
                self.phase = FlightPhase.STOPPED

        # Now compute actuator demands based on active phase
        if self.phase == FlightPhase.PREFLIGHT:
            throttle = 0.0
            pitch_target = 0.0
            wheel_brakes = 1.0  # Parking brake

        elif self.phase == FlightPhase.GROUND_ROLL:
            throttle = 1.0      # 100% full takeoff thrust
            pitch_target = 0.0  # Keep nose level to minimize drag on rollout
            wheel_brakes = 0.0

        elif self.phase == FlightPhase.ROTATION:
            throttle = 1.0
            pitch_target = 8.5  # Positive rotation pitch to achieve liftoff
            wheel_brakes = 0.0

        elif self.phase == FlightPhase.CLIMB_OUT:
            throttle = 0.90
            pitch_target = 10.0 # Maintain climb attitude
            wheel_brakes = 0.0

        elif self.phase == FlightPhase.EN_ROUTE:
            throttle = 0.55     # Cruise throttle
            pitch_target = 2.5
            wheel_brakes = 0.0

        elif self.phase == FlightPhase.APPROACH:
            throttle = 0.35     # Steady 3-degree glide slope
            pitch_target = 0.5
            wheel_brakes = 0.0

        elif self.phase == FlightPhase.FLARE:
            throttle = 0.0      # Idle throttle
            pitch_target = 4.5  # Flare rotation
            wheel_brakes = 0.0

        elif self.phase == FlightPhase.ROLLOUT:
            throttle = 0.0
            pitch_target = 0.0  # Nosewheel down for steering authority
            wheel_brakes = 0.85 # Strong mechanical braking

        elif self.phase == FlightPhase.STOPPED:
            throttle = 0.0
            pitch_target = 0.0
            wheel_brakes = 1.0  # Hold full parking brakes

        takeoff_dist = self.liftoff_x - self.ground_roll_start_x if self.liftoff_x > 0 else (x_position_m - self.ground_roll_start_x)

        return {
            "phase": self.phase.name,
            "throttle": float(throttle),
            "pitch_target_deg": float(pitch_target),
            "wheel_brakes": float(wheel_brakes),
            "ground_effect_sigma": float(sigma_ge),
            "takeoff_distance_m": float(takeoff_dist),
            "takeoff_compliant": bool(takeoff_dist <= self.max_takeoff_dist)
        }


def main():
    print("=" * 72)
    print("  AIAA DBF 2027 - OTONOM KALKIS VE INIS FAZ YONETICISI")
    print("=" * 72)
    ctl = TakeoffLandingController()
    ctl.arm()

    # Simulate Takeoff Sequence
    print("[*] Kalkis Dizisi Simulasyonu (Full Throttle Acceleration):")
    speed = 0.0
    x = 0.0
    alt = 0.0
    dt = 0.1
    wow = True

    while ctl.phase in [FlightPhase.GROUND_ROLL, FlightPhase.ROTATION, FlightPhase.CLIMB_OUT]:
        if ctl.phase in [FlightPhase.GROUND_ROLL, FlightPhase.ROTATION]:
            speed += 3.2 * dt  # Acceleration ~0.33g
            x += speed * dt
            if speed >= ctl.v_rot:
                alt += 0.5 * dt
                if alt > 0.5:
                    wow = False
        elif ctl.phase == FlightPhase.CLIMB_OUT:
            alt += 2.8 * dt
            x += speed * dt

        res = ctl.update(
            airspeed_ms=speed,
            altitude_m=alt,
            vertical_speed_ms=2.8 if not wow else 0.0,
            x_position_m=x,
            wheel_weight_on_wheels=wow
        )

        if ctl.phase == FlightPhase.EN_ROUTE:
            break

    print(f"    - Liftoff Mesafesi          : {ctl.liftoff_x:.2f} m (Limit: <= 61.0 m / 200 ft)")
    print(f"    - Ekran Irtifasina Erisim   : {alt:.2f} m, Mesafe: {x:.2f} m")
    print(f"    - DBF Kalkis Kural Durumu   : {'UYGUN (PASS)' if ctl.liftoff_x <= 61.0 else 'KURAL DISI (FAIL)'}")

    # Simulate Flare Ground Effect
    print("\n[*] Wieselsberger Zemin Etkisi (Ground Effect) Analizi:")
    for h in [5.0, 2.0, 1.0, 0.5, 0.2]:
        sigma = ctl.compute_ground_effect_factor(h)
        print(f"    - Irtifa h = {h:3.1f}m (h/b={h/ctl.wing_span:4.2f}) -> Induklenmis Surukleme Carpani: {sigma:4.2f}")

    print("=" * 72)


if __name__ == "__main__":
    main()
