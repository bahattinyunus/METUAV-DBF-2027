#!/usr/bin/env python3
"""
AIAA DBF 2027 - Target Detection Node
Edge-AI Vision node for detecting ground targets during Mission 3.
Transforms pixel centroids into ground coordinates using camera pinhole model and aircraft attitude.
"""

import sys
import math
import numpy as np

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image, CameraInfo
    from geometry_msgs.msg import PointStamped, PoseStamped
    from cv_bridge import CvBridge
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


class GroundProjector:
    """Projects image pixel coordinates onto flat ground using camera model and aircraft pose."""

    def __init__(self, fx: float = 381.3, fy: float = 381.3, cx: float = 320.0, cy: float = 240.0):
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy

    def pixel_to_ground(self, u: float, v: float, altitude_m: float, roll_rad: float = 0.0, pitch_rad: float = 0.0) -> tuple[float, float]:
        """
        Calculate relative ground position (dx forward, dy right) in meters.
        u, v: image coordinates in pixels.
        altitude_m: height above ground level.
        roll_rad, pitch_rad: aircraft orientation.
        """
        if altitude_m <= 0.1:
            return 0.0, 0.0

        # Normalized coordinates (v inverted because image y points down)
        cam_x = (u - self.cx) / self.fx
        cam_y = (self.cy - v) / self.fy

        # Project rays to ground plane considering small body attitude
        dx_forward = altitude_m * (cam_y - math.tan(pitch_rad))
        dy_right = altitude_m * (cam_x + math.tan(roll_rad))

        return float(dx_forward), float(dy_right)


class TargetDetectorNode:
    """Core Target Detection Logic compatible with ROS2 and standalone simulation."""

    def __init__(self):
        self.projector = GroundProjector()
        self.altitude = 30.0
        self.roll = 0.0
        self.pitch = 0.0

    def detect_in_image(self, bgr_frame: np.ndarray) -> tuple[bool, tuple[float, float], float]:
        """
        Detects concentric bullseye target in the given BGR frame.
        Returns: (found, (center_x, center_y), confidence)
        """
        if bgr_frame is None or bgr_frame.size == 0:
            return False, (0.0, 0.0), 0.0

        try:
            import cv2
        except ImportError:
            # Fallback if cv2 is not installed in local environment
            return False, (0.0, 0.0), 0.0

        # Convert to HSV color space for robust detection under changing daylight
        hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)

        # Orange / Red / High-visibility DBF target color range
        lower_target1 = np.array([0, 100, 100])
        upper_target1 = np.array([12, 255, 255])
        lower_target2 = np.array([170, 100, 100])
        upper_target2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_target1, upper_target1)
        mask2 = cv2.inRange(hsv, lower_target2, upper_target2)
        combined_mask = cv2.bitwise_or(mask1, mask2)

        # Morphological operations to suppress noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False, (0.0, 0.0), 0.0

        best_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(best_contour)

        if area < 120.0:  # Minimum pixel area threshold
            return False, (0.0, 0.0), 0.0

        moments = cv2.moments(best_contour)
        if moments["m00"] <= 1e-4:
            return False, (0.0, 0.0), 0.0

        cx = float(moments["m10"] / moments["m00"])
        cy = float(moments["m01"] / moments["m00"])

        # Circularity measure
        perimeter = cv2.arcLength(best_contour, True)
        circularity = 4 * math.pi * (area / (perimeter * perimeter + 1e-5))
        confidence = min(1.0, max(0.0, circularity))

        return (confidence > 0.45), (cx, cy), float(confidence)


if ROS2_AVAILABLE:
    class RosTargetDetectorNode(Node):
        def __init__(self):
            super().__init__('target_detector_node')
            self.detector = TargetDetectorNode()
            self.bridge = CvBridge()

            self.target_pub = self.create_publisher(PointStamped, 'dbf/vision/target_ground_pos', 10)
            self.create_subscription(Image, 'camera/image_raw', self.image_callback, 10)
            self.create_subscription(PoseStamped, 'dbf/pose', self.pose_callback, 10)
            self.get_logger().info("TargetDetectorNode initialized.")

        def pose_callback(self, msg: PoseStamped):
            self.detector.altitude = max(msg.pose.position.z, 0.5)

        def image_callback(self, msg: Image):
            try:
                cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            except Exception as e:
                self.get_logger().warn(f"Failed to convert image: {e}")
                return

            found, (cx, cy), conf = self.detector.detect_in_image(cv_img)
            if found:
                dx, dy = self.detector.projector.pixel_to_ground(cx, cy, self.detector.altitude)
                pt = PointStamped()
                pt.header.stamp = self.get_clock().now().to_msg()
                pt.header.frame_id = "base_link"
                pt.point.x = dx
                pt.point.y = dy
                pt.point.z = 0.0
                self.target_pub.publish(pt)


def main(args=None):
    if ROS2_AVAILABLE:
        rclpy.init(args=args)
        node = RosTargetDetectorNode()
        rclpy.spin(node)
        rclpy.shutdown()
    else:
        print("[STANDALONE TEST] ROS2 not installed in this environment. Testing geometry logic...")
        detector = TargetDetectorNode()
        dx, dy = detector.projector.pixel_to_ground(320.0, 240.0, 30.0)
        print(f"Boresight projection at 30m altitude: dx={dx:.2f}m, dy={dy:.2f}m")


if __name__ == '__main__':
    main()
