#!/usr/bin/env python3
"""
AIAA DBF 2027 - 3D Geofence & Boundary Containment Manager
Implements AIAA DBF regulation airfield boundary containment:
- 2D Point-in-Polygon ray casting for complex competition flight boxes
- 3D altitude floor (min AGL) & ceiling (max AGL) checks
- Predictive Time-To-Breach (TTB) trajectory vector projection
- Autonomous escape heading and failsafe trigger (Warning -> Containment Turn -> RTL -> Flight Terminate)
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np


class GeofenceStatus(Enum):
    INSIDE_SAFE = "INSIDE_SAFE"
    PROXIMITY_WARNING = "PROXIMITY_WARNING"
    PREDICTIVE_BREACH = "PREDICTIVE_BREACH"
    BREACHED_FAILSAFE = "BREACHED_FAILSAFE"
    ALTITUDE_FLOOR_VIOLATION = "ALTITUDE_FLOOR_VIOLATION"
    ALTITUDE_CEILING_VIOLATION = "ALTITUDE_CEILING_VIOLATION"


@dataclass
class GeofenceBreachAssessment:
    status: GeofenceStatus
    is_contained: bool
    distance_to_boundary_m: float
    time_to_breach_s: float
    current_altitude_agl_m: float
    escape_heading_deg: float
    recommended_action: str
    message: str


class GeofenceContainmentManager:
    """
    Real-time 3D airspace containment and predictive boundary keeper for AIAA DBF.
    """

    def __init__(self,
                 polygon_vertices_ned: Optional[List[Tuple[float, float]]] = None,
                 min_altitude_agl_m: float = 10.0,
                 max_altitude_agl_m: float = 121.92,  # 400 ft FAA DBF max ceiling
                 proximity_threshold_m: float = 40.0,
                 time_to_breach_warning_s: float = 4.0):
        """
        Parameters
        ----------
        polygon_vertices_ned : List[Tuple[float, float]]
            List of (North, East) coordinates defining the airfield boundary polygon in meters.
        min_altitude_agl_m : float
            Minimum legal altitude AGL (ground separation safety limit).
        max_altitude_agl_m : float
            Maximum allowable ceiling (400 ft FAA / DBF regulation).
        """
        # Default DBF competition airfield polygon (Tucson / Wichita standard layout)
        if polygon_vertices_ned is None:
            self.vertices = [
                (-150.0, -200.0),
                (450.0, -200.0),
                (600.0, 150.0),
                (450.0, 450.0),
                (-150.0, 450.0),
                (-300.0, 150.0)
            ]
        else:
            self.vertices = list(polygon_vertices_ned)

        self.h_min = min_altitude_agl_m
        self.h_max = max_altitude_agl_m
        self.prox_thresh = proximity_threshold_m
        self.ttb_thresh = time_to_breach_warning_s

    def is_point_inside_polygon(self, north: float, east: float) -> bool:
        """
        Ray-casting algorithm: counts intersections of a horizontal ray (eastward)
        with the edges of the polygon.
        """
        n_vert = len(self.vertices)
        inside = False

        j = n_vert - 1
        for i in range(n_vert):
            xi, yi = self.vertices[i]
            xj, yj = self.vertices[j]

            # Check if ray crosses the line segment (yi, yj) at point east
            intersect = ((yi > east) != (yj > east)) and \
                        (north < (xj - xi) * (east - yi) / (yj - yi + 1e-12) + xi)
            if intersect:
                inside = not inside
            j = i

        return inside

    def compute_distance_and_inward_normal(self, north: float, east: float) -> Tuple[float, np.ndarray]:
        """
        Calculates distance from (north, east) to the nearest polygon boundary edge,
        and the inward-pointing 2D normal unit vector.
        """
        p = np.array([north, east], dtype=float)
        min_dist = float("inf")
        best_normal = np.array([0.0, 0.0], dtype=float)

        n_vert = len(self.vertices)
        for i in range(n_vert):
            p1 = np.array(self.vertices[i], dtype=float)
            p2 = np.array(self.vertices[(i + 1) % n_vert], dtype=float)

            edge = p2 - p1
            edge_len_sq = float(np.dot(edge, edge))
            if edge_len_sq < 1e-6:
                continue

            # Project p onto segment p1-p2
            t = max(0.0, min(1.0, float(np.dot(p - p1, edge)) / edge_len_sq))
            projection = p1 + t * edge
            diff = projection - p
            dist = float(np.linalg.norm(diff))

            if dist < min_dist:
                min_dist = dist
                # Outward or inward normal
                if dist > 1e-4:
                    normal = diff / dist  # Points towards nearest edge from current position
                else:
                    # Perpendicular to edge
                    normal = np.array([-edge[1], edge[0]]) / math.sqrt(edge_len_sq)
                best_normal = normal

        return min_dist, best_normal

    def evaluate_containment(self,
                             pos_north_m: float,
                             pos_east_m: float,
                             altitude_agl_m: float,
                             vel_north_ms: float,
                             vel_east_ms: float) -> GeofenceBreachAssessment:
        """
        Assesses 3D containment, calculates time-to-breach (TTB) along current trajectory vector,
        and generates an escape heading if fence is threatened.
        """
        is_inside_2d = self.is_point_inside_polygon(pos_north_m, pos_east_m)
        dist_to_fence, normal_to_fence = self.compute_distance_and_inward_normal(pos_north_m, pos_east_m)

        # Velocity vector
        vel = np.array([vel_north_ms, vel_east_ms], dtype=float)
        speed = float(np.linalg.norm(vel))

        # Velocity component towards boundary
        # normal_to_fence points from aircraft towards boundary when inside
        v_towards_fence = float(np.dot(vel, normal_to_fence)) if is_inside_2d else -float(np.dot(vel, normal_to_fence))

        if v_towards_fence > 0.1 and dist_to_fence > 0.0:
            ttb = dist_to_fence / v_towards_fence
        else:
            ttb = 999.0  # Flying away or stationary

        # Compute escape heading: Turn away from boundary back towards center of polygon
        centroid = np.mean(self.vertices, axis=0)
        vec_to_center = centroid - np.array([pos_north_m, pos_east_m])
        escape_rad = math.atan2(vec_to_center[1], vec_to_center[0])
        escape_deg = math.degrees(escape_rad) % 360.0

        # Assess containment status
        # 1. Altitude checks first
        if altitude_agl_m < self.h_min:
            return GeofenceBreachAssessment(
                status=GeofenceStatus.ALTITUDE_FLOOR_VIOLATION,
                is_contained=False,
                distance_to_boundary_m=dist_to_fence,
                time_to_breach_s=0.0,
                current_altitude_agl_m=altitude_agl_m,
                escape_heading_deg=escape_deg,
                recommended_action="PULL_UP_MAX_CLIMB",
                message=f"CRITICAL: Below altitude floor ({altitude_agl_m:.1f}m < {self.h_min:.1f}m)"
            )
        elif altitude_agl_m > self.h_max:
            return GeofenceBreachAssessment(
                status=GeofenceStatus.ALTITUDE_CEILING_VIOLATION,
                is_contained=False,
                distance_to_boundary_m=dist_to_fence,
                time_to_breach_s=0.0,
                current_altitude_agl_m=altitude_agl_m,
                escape_heading_deg=escape_deg,
                recommended_action="DESCEND_LEVEL_OFF",
                message=f"WARNING: Exceeded 400ft ceiling ({altitude_agl_m:.1f}m > {self.h_max:.1f}m)"
            )

        # 2. Horizontal 2D perimeter checks
        if not is_inside_2d:
            return GeofenceBreachAssessment(
                status=GeofenceStatus.BREACHED_FAILSAFE,
                is_contained=False,
                distance_to_boundary_m=dist_to_fence,
                time_to_breach_s=0.0,
                current_altitude_agl_m=altitude_agl_m,
                escape_heading_deg=escape_deg,
                recommended_action="AUTONOMOUS_RTL_OR_TERMINATE",
                message="BREACH DETECTED: Aircraft is outside competition geofence perimeter"
            )

        if ttb < self.ttb_thresh:
            return GeofenceBreachAssessment(
                status=GeofenceStatus.PREDICTIVE_BREACH,
                is_contained=True,
                distance_to_boundary_m=dist_to_fence,
                time_to_breach_s=round(ttb, 2),
                current_altitude_agl_m=altitude_agl_m,
                escape_heading_deg=escape_deg,
                recommended_action="BANK_ESCAPE_TURN",
                message=f"PREDICTIVE BREACH: Fence collision in {ttb:.1f}s, initiate {escape_deg:.0f}° escape turn"
            )

        if dist_to_fence < self.prox_thresh:
            return GeofenceBreachAssessment(
                status=GeofenceStatus.PROXIMITY_WARNING,
                is_contained=True,
                distance_to_boundary_m=round(dist_to_fence, 1),
                time_to_breach_s=round(ttb, 1),
                current_altitude_agl_m=altitude_agl_m,
                escape_heading_deg=escape_deg,
                recommended_action="MONITOR_COURSE",
                message=f"PROXIMITY WARNING: {dist_to_fence:.1f}m from perimeter"
            )

        return GeofenceBreachAssessment(
            status=GeofenceStatus.INSIDE_SAFE,
            is_contained=True,
            distance_to_boundary_m=round(dist_to_fence, 1),
            time_to_breach_s=round(ttb, 1),
            current_altitude_agl_m=altitude_agl_m,
            escape_heading_deg=escape_deg,
            recommended_action="CONTINUE_MISSION",
            message="Airspace containment nominal"
        )
