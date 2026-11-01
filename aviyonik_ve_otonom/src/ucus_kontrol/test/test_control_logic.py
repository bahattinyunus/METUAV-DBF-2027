import pytest
import math

class PythonEnergyManagerModel:
    def __init__(self, capacity_mah=16000.0, min_cell_v=3.55):
        self.capacity_mah = capacity_mah
        self.min_cell_v = min_cell_v
        self.consumed_mah = 0.0

    def step(self, dt, voltage, current):
        self.consumed_mah += (current * dt / 3.6)
        soc = 100.0 * (1.0 - (self.consumed_mah / self.capacity_mah))
        cell_v = voltage / 6.0
        
        alert = "NOMINAL"
        if cell_v < 3.40 or soc < 10.0:
            alert = "EMERGENCY"
        elif cell_v < self.min_cell_v or soc < 20.0:
            alert = "CRITICAL_RTL"
        elif cell_v < 3.70 or soc < 35.0:
            alert = "WARNING"
            
        return max(0.0, soc), cell_v, alert

def test_energy_manager_consumption():
    mgr = PythonEnergyManagerModel(capacity_mah=16000.0)
    # 5 minutes at 35A cruise
    dt = 1.0
    for _ in range(300):
        soc, cell_v, alert = mgr.step(dt, voltage=22.8, current=35.0)

    # Consumed = 35 * 300 / 3.6 = 2916.6 mAh out of 16000 mAh (~18.2% consumed -> ~81.8% SoC left)
    assert 80.0 < soc < 83.0
    assert alert == "NOMINAL"

def test_energy_manager_low_voltage_rtl():
    mgr = PythonEnergyManagerModel(capacity_mah=16000.0, min_cell_v=3.55)
    # Voltage drops below 3.55V/cell (21.3V for 6S)
    soc, cell_v, alert = mgr.step(1.0, voltage=21.0, current=20.0)
    assert cell_v == 3.50
    assert alert == "CRITICAL_RTL"
