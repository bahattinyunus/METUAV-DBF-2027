import pytest
import numpy as np
from itki_ve_guc_sistemleri.scripts.propeller_noise_mapper import PropellerNoiseMapper, PropellerAcousticParams


def test_propeller_acoustic_calculation():
    mapper = PropellerNoiseMapper()
    res = mapper.compute_acoustic_pressures(distance_m=30.48, theta_deg=90.0)

    # Tip Mach should be subsonic (< 0.75) for 19x12 at 6800 RPM
    assert 0.40 < res["tip_mach"] < 0.70
    assert 200.0 < res["bpf_hz"] < 250.0

    # Sideline noise must strictly adhere to AIAA DBF 85 dBA rule
    assert res["spl_dba"] < 85.0
    assert res["margin_to_85_limit"] > 5.0  # At least 5 dBA margin


def test_noise_directivity_and_grid():
    mapper = PropellerNoiseMapper()
    angles, levels = mapper.generate_polar_directivity(distance_m=30.48)

    assert len(angles) == 100
    assert len(levels) == 100
    assert np.all(levels < 90.0)

    X, Y, Z = mapper.generate_ground_footprint_grid(x_span_m=20.0, y_span_m=20.0, n_pts=15)
    assert Z.shape == (15, 15)
    assert np.all(np.isfinite(Z))
