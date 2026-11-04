#!/usr/bin/env python3
"""
AIAA DBF 2027 - Drop Ballistics Computer
Computes 3-DOF aerodynamic trajectory of dropped payload during Mission 3.
Determines exact release trigger time based on ground speed, wind, altitude and aerodynamic drag.
"""

import math
import numpy as np

try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import PointStamped, TwistStamped
    from std_msgs.msg import Bool, Float32
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


class BallisticsSolver:
    """3-DOF Ballistics trajectory solver for dropped payload."""

    def __init__(self,
                 payload_mass_kg: float = 2.5,
                 drag_coefficient: float = 0.45,
                 frontal_area_m2: float = 0.018,
                 air_density: float = 1.225):
        self.mass = payload_mass_kg
        self.cd = drag_coefficient
        self.area = frontal_area_m2
        self.rho = air_density
        self.g = 9.80665

    def compute_trajectory(self,
                           altitude_m: float,
                           ground_speed_x: float,
                           ground_speed_y: float = 0.0,
                           initial_vz: float = 0.0,
                           wind_x: float = 0.0,
                           wind_y: float = 0.0,
                           dt: float = 0.01) -> tuple[float, float, float]:
        """
        Integrates payload trajectory using RK4 until ground impact (z <= 0).
        Returns: (impact_x, impact_y, time_of_fall) in meters and seconds.
        """
        if altitude_m <= 0.1:
            return 0.0, 0.0, 0.0

        # State: [x, y, z, vx, vy, vz]
        state = np.array([0.0, 0.0, altitude_m, ground_speed_x, ground_speed_y, initial_vz], dtype=np.float64)
        total_time = 0.0
        max_time = 30.0

        # Drag constant k = 0.5 * rho * Cd * A
        k = 0.5 * self.rho * self.cd * self.area

        def derivatives(s):
            x, y, z, vx, vy, vz = s
            # Airspeed relative to wind
            v_rel_x = vx - wind_x
            v_rel_y = vy - wind_y
            v_rel_z = vz
            v_rel = math.sqrt(v_rel_x * v_rel_x + v_rel_y * v_rel_y + v_rel_z * v_rel_z + 1e-6)

            drag_force = k * v_rel * v_rel
            ax = -(drag_force / self.mass) * (v_rel_x / v_rel)
            ay = -(drag_force / self.mass) * (v_rel_y / v_rel)
            az = -self.g - (drag_force / self.mass) * (v_rel_z / v_rel)

            return np.array([vx, vy, vz, ax, ay, az])

        while state[2] > 0.0 and total_time < max_time:
            # RK4 Integration step
            k1 = derivatives(state)
            k2 = derivatives(state + 0.5 * dt * k1)
            k3 = derivatives(state + 0.5 * dt * k2)
            k4 = derivatives(state + dt * k3)
            state += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            total_time += dt

        return float(state[0]), float(state[1]), float(total_time)

    def should_release(self,
                       target_dist_x: float,
                       target_dist_y: float,
                       altitude_m: float,
                       ground_speed_x: float,
                       tolerance_m: float = 1.2) -> tuple[bool, float]:
        """
        Calculates whether current aircraft position is within the optimal release window.
        target_dist_x: forward distance from aircraft to target on ground (m).
        Returns: (should_release, miss_distance_m)
        """
        impact_x, impact_y, t_fall = self.compute_trajectory(altitude_m, ground_speed_x)
        error_x = target_dist_x - impact_x
        error_total = math.sqrt(error_x * error_x + target_dist_y * target_dist_y)

        # We release if aircraft has reached or slightly passed the ballistic drop point
        release_trigger = (abs(error_x) <= tolerance_m) and (abs(target_dist_y) <= tolerance_m * 1.5)
        return release_trigger, float(error_total)


if ROS2_AVAILABLE:
    class RosDropBallisticsNode(Node):
        def __init__(self):
            super().__init__('drop_ballistics_computer')
            self.solver = BallisticsSolver()
            self.current_altitude = 25.0
            self.current_ground_speed = 22.0
            self.target_dist_x = 999.0
            self.target_dist_y = 999.0
            self.already_dropped = False

            self.trigger_pub = self.create_publisher(Bool, 'dbf/payload_drop_trigger', 10)
            self.error_pub = self.create_publisher(Float32, 'dbf/ballistics/miss_distance', 10)

            self.create_subscription(PointStamped, 'dbf/vision/target_ground_pos', self.target_cb, 10)
            self.create_subscription(TwistStamped, 'dbf/ground_velocity', self.vel_cb, 10)

            # 50 Hz evaluation timer
            self.timer = self.create_timer(0.02, self.eval_drop_window)
            self.get_logger().info("DropBallisticsComputer initialized.")

        def target_cb(self, msg: PointStamped):
            self.target_dist_x = msg.point.x
            self.target_dist_y = msg.point.y

        def vel_cb(self, msg: TwistStamped):
            vx = msg.twist.linear.x
            vy = msg.twist.linear.y
            self.current_ground_speed = math.sqrt(vx * vx + vy * vy)

        def eval_drop_window(self):
            if self.already_dropped:
                return

            trigger, err = self.solver.should_release(
                self.target_dist_x, self.target_dist_y,
                self.current_altitude, self.current_ground_speed
            )

            err_msg = Float32()
            err_msg.data = err
            self.error_pub.publish(err_msg)

            if trigger:
                self.get_logger().warn(f"OPTIMAL RELEASE WINDOW REACHED! Miss distance: {err:.2f}m")
                self.already_dropped = True
                drop_msg = Bool()
                drop_msg.data = True
                self.trigger_pub.publish(drop_msg)


def main(args=None):
    if ROS2_AVAILABLE:
        rclpy.init(args=args)
        node = RosDropBallisticsNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        print("[STANDALONE TEST] Testing Ballistics Solver...")
        solver = BallisticsSolver(payload_mass_kg=2.5, drag_coefficient=0.45, frontal_area_m2=0.015)
        impact_x, impact_y, t_fall = solver.compute_trajectory(altitude_m=25.0, ground_speed_x=22.0)
        print(f"Drop from 25m at 22m/s: impact_x={impact_x:.2f}m, t_fall={t_fall:.2f}s")
        trigger, err = solver.should_release(target_dist_x=impact_x, target_dist_y=0.0, altitude_m=25.0, ground_speed_x=22.0)
        print(f"Release check at target_x={impact_x:.2f}m -> Trigger: {trigger}, error: {err:.3f}m")


if __name__ == '__main__':
    main()
