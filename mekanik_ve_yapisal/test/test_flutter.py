#!/usr/bin/env python3
"""
Unit tests for Wing Aeroelastic Flutter & Divergence Analyzer.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from flutter_and_divergence_analyzer import WingFlutterAnalyzer


def test_analyzer_frequencies():
    analyzer = WingFlutterAnalyzer()
    res = analyzer.analyze_flutter(v_start=15.0, v_end=50.0, v_step=5.0)

    assert 8.0 < res["omega_h_hz"] < 15.0, "Wing first bending mode must be in 8-15 Hz range"
    assert 40.0 < res["omega_alpha_hz"] < 80.0, "Wing first torsional mode must be in 40-80 Hz range"
    assert res["omega_h_hz"] / res["omega_alpha_hz"] < 0.50, "Bending/torsion ratio must provide safe flutter separation"


def test_flutter_and_divergence_margins():
    analyzer = WingFlutterAnalyzer()
    res = analyzer.analyze_flutter(v_start=20.0, v_end=60.0, v_step=2.0)

    assert res["divergence_speed_ms"] > 100.0, "Divergence speed must be well above max flight speed"
    assert res["margin_over_dive_speed"] >= 1.20, "Flutter margin over dive speed (35 m/s) must exceed 1.20"
