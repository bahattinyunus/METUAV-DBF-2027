#!/usr/bin/env python3
"""
METUAV DBF 2027 - Integrated Powertrain & Energy Matcher
Unifies BEMT propeller aerodynamics, brushless motor electromechanics,
dual-RC battery pack dynamics, and thermal heat transfer into a coherent simulation.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from .bemt_propeller_optimizer import BEMTPropellerOptimizer
from .motor_thermal_simulator import PropulsionThermalSimulator
from .battery_soh_estimator import BatteryTheveninModel


@dataclass
class PowertrainOperatingPoint:
    time_s: float
    airspeed_ms: float
    throttle_pct: float
    rpm: float
    thrust_n: float
    thrust_kgf: float
    voltage_v: float
    current_a: float
    electric_power_w: float
    propeller_power_w: float
    motor_efficiency: float
    propeller_efficiency: float
    overall_efficiency: float
    motor_temp_c: float
    battery_temp_c: float
    soc_pct: float


class PowertrainSystemMatcher:
    """
    Coupled powertrain simulator:
    Throttle + Airspeed -> Motor Back-EMF / Torque Balance -> RPM ->
    BEMT Thrust & Torque -> Battery Current Draw & Dual-RC Voltage Sag ->
    Thermal Loss & Heat Dissipation.
    """
    def __init__(
        self,
        motor_kv: float = 330.0,
        motor_rm_ohm: float = 0.021,
        motor_io_a: float = 1.8,
        esc_resistance_ohm: float = 0.003,
        prop_dia_in: float = 19.0,
        prop_pitch_in: float = 12.0,
        cell_count: int = 6,
        capacity_mah: float = 16000.0,
        ambient_temp_c: float = 32.0
    ):
        self.kv = motor_kv
        self.rm = motor_rm_ohm
        self.io = motor_io_a
        self.r_esc = esc_resistance_ohm
        self.cell_count = cell_count

        self.prop_solver = BEMTPropellerOptimizer(diameter_in=prop_dia_in, pitch_in=prop_pitch_in)
        self.thermal_model = PropulsionThermalSimulator()
        self.thermal_model.t_ambient = ambient_temp_c
        self.battery = BatteryTheveninModel(nominal_capacity_ah=capacity_mah / 1000.0, cell_count=cell_count)

        # Torque constant Kt = 1 / (Kv * 2*pi / 60)
        self.kt = 60.0 / (2.0 * math.pi * self.kv)

    def solve_equilibrium_rpm(self, throttle: float, airspeed_ms: float, v_batt_est: float) -> Tuple[float, float, float]:
        """
        Solves for steady-state RPM where motor electrical torque equals propeller aerodynamic torque.
        Returns: (rpm, current_a, torque_nm)
        """
        throttle = np.clip(throttle, 0.0, 1.0)
        if throttle < 0.02:
            return 0.0, self.io, 0.0

        v_effective = v_batt_est * throttle

        # Bisection / iterative root search for RPM
        rpm_low = 1000.0
        rpm_high = v_effective * self.kv * 1.05

        rpm_sol = rpm_low
        torque_sol = 0.0
        current_sol = 0.0

        for _ in range(15):
            rpm_mid = 0.5 * (rpm_low + rpm_high)
            # Propeller aerodynamic torque from BEMT
            prop_res = self.prop_solver.analyze_advance_ratio(rpm=rpm_mid, v_flight_ms=airspeed_ms)
            q_prop = prop_res["torque_nm"]

            # Back-EMF
            v_bemf = rpm_mid / self.kv
            i_motor = max(self.io, (v_effective - v_bemf) / (self.rm + self.r_esc))
            q_motor = (i_motor - self.io) * self.kt

            residual = q_motor - q_prop
            if residual > 0:
                rpm_low = rpm_mid
            else:
                rpm_high = rpm_mid

            rpm_sol = rpm_mid
            torque_sol = q_prop
            current_sol = i_motor

        return rpm_sol, current_sol, torque_sol

    def simulate_step(
        self,
        time_s: float,
        dt: float,
        throttle: float,
        airspeed_ms: float,
        current_motor_temp: float,
        current_batt_temp: float
    ) -> PowertrainOperatingPoint:
        """
        Steps the coupled electrical, aeromechanical, and thermal states by dt.
        """
        # Estimated loaded battery terminal voltage
        v_terminal_est = self.battery.get_ocv(self.battery.soc)

        rpm, current_a, torque_nm = self.solve_equilibrium_rpm(throttle, airspeed_ms, v_terminal_est)

        # Step battery model with the calculated current
        batt_res = self.battery.update(current_amps=current_a, dt=dt)
        v_terminal = batt_res["terminal_voltage_v"]
        soc_pct = batt_res["soc_pct"]

        # Propeller aeromechanics
        prop_res = self.prop_solver.analyze_advance_ratio(rpm=max(rpm, 100.0), v_flight_ms=airspeed_ms)
        thrust_n = prop_res["thrust_n"] if rpm > 500 else 0.0
        thrust_kgf = thrust_n / 9.80665

        p_elec = v_terminal * current_a
        p_shaft = (torque_nm * (2.0 * math.pi * rpm / 60.0)) if rpm > 500 else 0.0
        p_thrust = thrust_n * airspeed_ms

        eta_motor = (p_shaft / p_elec) if p_elec > 10.0 else 0.0
        eta_prop = prop_res["efficiency_eta"]
        eta_overall = (p_thrust / p_elec) if p_elec > 10.0 else 0.0

        # Thermal step
        # Copper loss with temperature correction
        r_motor_hot = self.rm * (1.0 + self.thermal_model.alpha_cu * (current_motor_temp - 20.0))
        p_copper = (current_a ** 2) * r_motor_hot
        p_iron = 45.0 * ((airspeed_ms / 24.5) ** 1.4) * (rpm / 6800.0)
        p_loss_m = p_copper + p_iron

        h_motor = 28.0 + 14.5 * math.sqrt(max(airspeed_ms, 1.0))
        q_cool_m = h_motor * self.thermal_model.surface_area_motor * (current_motor_temp - self.thermal_model.t_ambient)
        d_tm = ((p_loss_m - q_cool_m) / self.thermal_model.c_th_motor) * dt
        next_motor_temp = current_motor_temp + d_tm

        p_loss_b = (current_a ** 2) * self.thermal_model.r_batt_internal
        h_batt = 12.0 + 6.0 * math.sqrt(max(airspeed_ms * 0.3, 0.5))
        q_cool_b = h_batt * self.thermal_model.surface_area_batt * (current_batt_temp - self.thermal_model.t_ambient)
        d_tb = ((p_loss_b - q_cool_b) / self.thermal_model.c_th_batt) * dt
        next_batt_temp = current_batt_temp + d_tb

        return PowertrainOperatingPoint(
            time_s=time_s,
            airspeed_ms=airspeed_ms,
            throttle_pct=throttle * 100.0,
            rpm=rpm,
            thrust_n=thrust_n,
            thrust_kgf=thrust_kgf,
            voltage_v=v_terminal,
            current_a=current_a,
            electric_power_w=p_elec,
            propeller_power_w=p_shaft,
            motor_efficiency=np.clip(eta_motor, 0.0, 0.95),
            propeller_efficiency=np.clip(eta_prop, 0.0, 0.90),
            overall_efficiency=np.clip(eta_overall, 0.0, 0.85),
            motor_temp_c=next_motor_temp,
            battery_temp_c=next_batt_temp,
            soc_pct=soc_pct
        )

    def run_mission_profile(
        self,
        flight_plan: List[Dict[str, float]],
        dt: float = 0.5
    ) -> List[PowertrainOperatingPoint]:
        """
        Runs a sequential flight plan containing legs with (duration_s, throttle, airspeed_ms).
        """
        history: List[PowertrainOperatingPoint] = []
        t_curr = 0.0
        m_temp = self.thermal_model.t_ambient
        b_temp = self.thermal_model.t_ambient

        for leg in flight_plan:
            dur = leg["duration_s"]
            thr = leg["throttle"]
            spd = leg["airspeed_ms"]

            n_steps = int(dur / dt)
            for _ in range(n_steps):
                pt = self.simulate_step(
                    time_s=t_curr,
                    dt=dt,
                    throttle=thr,
                    airspeed_ms=spd,
                    current_motor_temp=m_temp,
                    current_batt_temp=b_temp
                )
                m_temp = pt.motor_temp_c
                b_temp = pt.battery_temp_c
                t_curr += dt
                history.append(pt)

        return history
