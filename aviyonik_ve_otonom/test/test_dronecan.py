import pytest
from aviyonik_ve_otonom.scripts.dronecan_telemetry_simulator import DroneCANTelemetrySimulator, DroneCANMessage


def test_dronecan_esc_encoding_decoding():
    sim = DroneCANTelemetrySimulator(node_id=12)
    msg = sim.encode_esc_status(rpm=6800.0, voltage_v=24.50, current_a=35.0, temp_c=55)

    assert msg.message_type == "uavcan.equipment.esc.Status"
    assert len(msg.data_bytes) == 7

    decoded = sim.decode_esc_status(msg)
    assert decoded["rpm"] == pytest.approx(6800.0, abs=1.0)
    assert decoded["voltage_v"] == pytest.approx(24.50, abs=0.01)
    assert decoded["current_a"] == pytest.approx(35.0, abs=0.1)
    assert decoded["temp_c"] == 55.0


def test_dronecan_battery_cells():
    sim = DroneCANTelemetrySimulator(node_id=12)
    cells_in = [4.15, 4.14, 4.16, 4.13, 4.15, 4.14]
    msg = sim.encode_battery_cells(cells_in)

    assert msg.message_type == "uavcan.equipment.power.BatteryInfoAux"
    assert len(msg.data_bytes) == 12

    cells_out = sim.decode_battery_cells(msg)
    assert len(cells_out) == 6
    for v_in, v_out in zip(cells_in, cells_out):
        assert v_in == pytest.approx(v_out, abs=0.005)


def test_dronecan_servo_feedback():
    sim = DroneCANTelemetrySimulator(node_id=12)
    msg = sim.encode_servo_feedback(servo_id=3, pos_deg=12.5, current_ma=680.0)

    decoded = sim.decode_servo_feedback(msg)
    assert decoded["servo_id"] == 3
    assert decoded["pos_deg"] == pytest.approx(12.5, abs=0.05)
    assert decoded["current_ma"] == 680.0
