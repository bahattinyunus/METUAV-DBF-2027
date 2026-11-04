import pytest
from aerodinamik.scripts.flight_envelope_vn_diagram import FlightEnvelopeAnalyzer, AircraftParameters


def test_flight_envelope_speeds():
    analyzer = FlightEnvelopeAnalyzer()
    speeds = analyzer.calculate_corner_speeds()

    assert speeds["vs1_ms"] > 14.0
    assert speeds["vs1_ms"] < 20.0
    assert speeds["va_ms"] > speeds["vs1_ms"]
    assert speeds["vc_ms"] >= speeds["vs1_ms"]
    assert speeds["vd_ms"] > speeds["vc_ms"]


def test_pratt_gust_alleviation():
    analyzer = FlightEnvelopeAnalyzer()
    kg = analyzer.compute_pratt_gust_factor()

    assert 0.5 < kg < 1.0
    dn = analyzer.compute_gust_load_increment(speed_ms=24.5, gust_speed_ms=6.0)
    assert 0.4 < dn < 1.6
    # Total gust load must remain within +3.5g limit
    assert 1.0 + dn <= 3.50


def test_envelope_curves_shape():
    analyzer = FlightEnvelopeAnalyzer()
    curves = analyzer.generate_envelope_curves()

    assert len(curves["v_arr"]) == 150
    assert max(curves["n_pos_envelope"]) <= 3.50 + 1e-4
    assert min(curves["n_neg_envelope"]) >= -1.50 - 1e-4
