#!/usr/bin/env python3
"""
Unit tests for Composite Sandwich Fuselage Buckling & Quick-Disconnect Joint Analyzer.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from composite_fuselage_buckling import CompositeFuselageBucklingAnalyzer


def test_sandwich_fuselage_panel_structural_margins():
    analyzer = CompositeFuselageBucklingAnalyzer()
    res = analyzer.evaluate_sandwich_panel(
        applied_bending_moment_nm=185.0,
        applied_torsion_nm=65.0,
        applied_shear_n=240.0
    )

    assert res.is_structurally_sound is True
    assert res.buckling_margin_of_safety > 10.0, "Global sandwich panel buckling must have large safety margin"
    assert res.wrinkling_margin_of_safety > 20.0, "Face sheet micro-wrinkling must be safely prevented"
    assert res.core_shear_margin_of_safety > 2.0, "Rohacell foam core shear margin must be positive"
    assert res.core_shear_applied_pa < res.core_shear_allowable_pa


def test_wing_fuselage_quick_disconnect_pins():
    analyzer = CompositeFuselageBucklingAnalyzer()
    joint = analyzer.evaluate_quick_disconnect_joint(
        design_lift_n=1066.2,
        num_pins=4,
        pin_diameter_mm=8.0
    )

    assert joint.meets_5min_rule is True
    assert joint.assembly_time_seconds <= 45.0, "4-pin wing latch must assemble in < 45 seconds"
    assert joint.pin_shear_margin_of_safety > 10.0
    assert joint.lug_bearing_margin_of_safety > 10.0
    assert joint.tear_out_margin_of_safety > 5.0
