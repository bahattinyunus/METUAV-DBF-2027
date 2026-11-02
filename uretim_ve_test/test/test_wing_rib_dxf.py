import os
import tempfile
import pytest
from uretim_ve_test.scripts.generate_wing_rib_dxf import AirfoilDxfGenerator

def test_airfoil_dxf_generation():
    gen = AirfoilDxfGenerator(chord_mm=320.0)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test_rib.dxf")
        gen.generate_dxf(out_file)

        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 500  # Valid DXF contents

        with open(out_file, 'r', encoding='ascii') as f:
            content = f.read()
            assert "HEADER" in content
            assert "POLYLINE" in content
            assert "AIRFOIL_OUTLINE" in content
            assert "SPAR_CUTOUT" in content
