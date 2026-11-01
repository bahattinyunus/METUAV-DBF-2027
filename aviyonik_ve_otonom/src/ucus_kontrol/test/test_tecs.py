import pytest
import math

class PythonAdaptiveTECS:
    def __init__(self):
        self.payload_mass_factor = 1.0
        self.throttle_integ = 0.0
        self.pitch_integ = 0.0
        self.g = 9.80665
        self.v_nominal = 24.5

    def set_mass_scale(self, mass_factor):
        self.payload_mass_factor = max(0.45, min(1.25, mass_factor))

    def update(self, h_error, v_error, climb_rate, airspeed_accel, roll_rad, dt):
        tau = 1.8
        h_dot_dem = max(-4.5, min(5.0, h_error / tau))
        v_dot_dem = max(-3.0, min(3.5, v_error / tau))
        kinetic_dem = (self.v_nominal * v_dot_dem) / self.g
        s_e_dem = h_dot_dem + kinetic_dem

        kinetic_act = (self.v_nominal * airspeed_accel) / self.g
        s_e_act = climb_rate + kinetic_act
        s_e_err = s_e_dem - s_e_act

        s_b_dem = h_dot_dem - kinetic_dem
        s_b_act = climb_rate - kinetic_act
        s_b_err = s_b_dem - s_b_act

        # Throttle
        k_thr_p = 0.12 * self.payload_mass_factor
        k_thr_i = 0.04 * self.payload_mass_factor
        self.throttle_integ = max(-0.3, min(0.4, self.throttle_integ + s_e_err * dt))
        base_throttle = 0.55 * self.payload_mass_factor
        throttle = max(0.0, min(1.0, base_throttle + k_thr_p * s_e_err + k_thr_i * self.throttle_integ))

        # Pitch
        k_pitch_p = 2.4 * self.payload_mass_factor
        k_pitch_i = 0.5 * self.payload_mass_factor
        self.pitch_integ = max(-4.0, min(4.0, self.pitch_integ + s_b_err * dt))
        cos_roll = max(math.cos(roll_rad), 0.35)
        roll_comp = 1.2 * ((1.0 / cos_roll) - 1.0) * (180.0 / math.pi)
        pitch = max(-15.0, min(18.0, 2.2 + k_pitch_p * s_b_err + k_pitch_i * self.pitch_integ + roll_comp))

        return throttle, pitch

def test_tecs_climb_demand():
    tecs = PythonAdaptiveTECS()
    # Below altitude target by 10m -> demands climb
    throttle, pitch = tecs.update(h_error=10.0, v_error=0.0, climb_rate=0.0, airspeed_accel=0.0, roll_rad=0.0, dt=0.02)
    assert throttle > 0.60
    assert pitch > 4.0

def test_tecs_payload_drop_scaling():
    tecs_heavy = PythonAdaptiveTECS()
    tecs_heavy.set_mass_scale(1.0)
    thr_heavy, _ = tecs_heavy.update(h_error=0.0, v_error=0.0, climb_rate=0.0, airspeed_accel=0.0, roll_rad=0.0, dt=0.02)

    tecs_light = PythonAdaptiveTECS()
    tecs_light.set_mass_scale(0.55)
    thr_light, _ = tecs_light.update(h_error=0.0, v_error=0.0, climb_rate=0.0, airspeed_accel=0.0, roll_rad=0.0, dt=0.02)

    # Lighter aircraft requires significantly less cruise throttle
    assert thr_light < thr_heavy * 0.70

def test_tecs_banking_lift_compensation():
    tecs = PythonAdaptiveTECS()
    # 45-degree bank turn
    _, pitch_banked = tecs.update(h_error=0.0, v_error=0.0, climb_rate=0.0, airspeed_accel=0.0, roll_rad=math.radians(45.0), dt=0.02)
    _, pitch_level = tecs.update(h_error=0.0, v_error=0.0, climb_rate=0.0, airspeed_accel=0.0, roll_rad=0.0, dt=0.02)

    assert pitch_banked > pitch_level
