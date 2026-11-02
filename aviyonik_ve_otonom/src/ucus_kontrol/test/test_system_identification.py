import numpy as np
import pytest
from aviyonik_ve_otonom.src.ucus_kontrol.src.online_system_identification import OnlineAeroSystemIdentifier

def test_rls_convergence():
    sid = OnlineAeroSystemIdentifier()

    # Ground truth values: Cm_alpha = -0.75, Cm_q = -14.0, Cm_delta_e = -1.35
    true_cm0 = 0.03
    true_cm_a = -0.75
    true_cm_q = -14.0
    true_cm_de = -1.35

    airspeed = 24.5
    q_inf = 0.5 * 1.225 * (airspeed ** 2)
    s_ref = 0.7032
    c_ref = 0.293

    # Feed 150 simulated telemetry cycles with small noise
    np.random.seed(42)
    for _ in range(150):
        alpha = np.radians(np.random.uniform(-4.0, 8.0))
        q = np.radians(np.random.uniform(-15.0, 15.0))
        delta_e = np.radians(np.random.uniform(-10.0, 10.0))

        q_hat = (q * c_ref) / (2.0 * airspeed)
        cm_true = true_cm0 + true_cm_a * alpha + true_cm_q * q_hat + true_cm_de * delta_e
        m_pitch = cm_true * (q_inf * s_ref * c_ref) + np.random.normal(0.0, 0.05)

        res = sid.update_longitudinal(
            airspeed_ms=airspeed,
            alpha_rad=alpha,
            q_pitch_rate_rad_s=q,
            delta_e_rad=delta_e,
            pitch_moment_nm=m_pitch
        )

    # Cm_alpha should converge near -0.75 and remain statically stable (< 0)
    assert res.cm_alpha < -0.40
    assert res.cm_q < -5.0
    assert res.cm_delta_e < -0.80
    assert abs(res.residual_error) < 0.20
