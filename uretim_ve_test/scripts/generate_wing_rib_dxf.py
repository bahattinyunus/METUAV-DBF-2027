#!/usr/bin/env python3
"""
METUAV DBF 2027 - CNC Laser Cutting DXF Rib Generator
Generates standard AutoCAD ASCII DXF files for Selig 1223 wing ribs.
Includes automated carbon spar cutouts, rear joiner holes, and weight-relief lightening cutouts.
"""

import os
import math
import numpy as np
from typing import List, Tuple

class AirfoilDxfGenerator:
    def __init__(self, chord_mm: float = 320.0):
        self.chord_mm = chord_mm
        # Normalized Selig 1223 profile coordinates (x/c, y/c)
        self.coords_norm = [
            (1.0000, 0.0000), (0.9500, 0.0125), (0.9000, 0.0270), (0.8000, 0.0545),
            (0.7000, 0.0785), (0.6000, 0.0980), (0.5000, 0.1115), (0.4000, 0.1180),
            (0.3000, 0.1150), (0.2000, 0.1020), (0.1000, 0.0750), (0.0500, 0.0530),
            (0.0200, 0.0335), (0.0000, 0.0000), (0.0100, -0.0180), (0.0500, -0.0280),
            (0.1000, -0.0295), (0.2000, -0.0230), (0.3000, -0.0120), (0.4000, 0.0010),
            (0.5000, 0.0125), (0.6000, 0.0210), (0.7000, 0.0250), (0.8000, 0.0230),
            (0.9000, 0.0150), (0.9500, 0.0080), (1.0000, 0.0000)
        ]

    def generate_dxf(self, output_path: str):
        # Scale coordinates to mm
        points = [(x * self.chord_mm, y * self.chord_mm) for x, y in self.coords_norm]

        # Spar cutout specs (located at 30% chord)
        spar_x = 0.30 * self.chord_mm
        spar_w = 35.0  # mm
        spar_h = 28.0  # mm

        # Rear joiner hole (located at 65% chord)
        rear_x = 0.65 * self.chord_mm
        rear_r = 6.0   # 12mm diameter tube

        # Lightening hole (located at 48% chord)
        hole_x = 0.48 * self.chord_mm
        hole_r = 14.0  # 28mm diameter circle

        with open(output_path, 'w', encoding='ascii') as f:
            # DXF Header
            f.write("0\nSECTION\n2\nHEADER\n0\nENDSEC\n")
            f.write("0\nSECTION\n2\nENTITIES\n")

            # 1. Outer Airfoil Perimeter (POLYLINE)
            f.write("0\nPOLYLINE\n8\nAIRFOIL_OUTLINE\n66\n1\n70\n1\n")
            for px, py in points:
                f.write(f"0\nVERTEX\n8\nAIRFOIL_OUTLINE\n10\n{px:.3f}\n20\n{py:.3f}\n30\n0.0\n")
            f.write("0\nSEQEND\n")

            # 2. Main Carbon Spar Cutout (4 lines forming rectangle)
            x0 = spar_x - spar_w / 2.0
            x1 = spar_x + spar_w / 2.0
            y0 = -5.0
            y1 = y0 + spar_h
            f.write(f"0\nLINE\n8\nSPAR_CUTOUT\n10\n{x0:.3f}\n20\n{y0:.3f}\n30\n0.0\n11\n{x1:.3f}\n21\n{y0:.3f}\n31\n0.0\n")
            f.write(f"0\nLINE\n8\nSPAR_CUTOUT\n10\n{x1:.3f}\n20\n{y0:.3f}\n30\n0.0\n11\n{x1:.3f}\n21\n{y1:.3f}\n31\n0.0\n")
            f.write(f"0\nLINE\n8\nSPAR_CUTOUT\n10\n{x1:.3f}\n20\n{y1:.3f}\n30\n0.0\n11\n{x0:.3f}\n21\n{y1:.3f}\n31\n0.0\n")
            f.write(f"0\nLINE\n8\nSPAR_CUTOUT\n10\n{x0:.3f}\n20\n{y1:.3f}\n30\n0.0\n11\n{x0:.3f}\n21\n{y0:.3f}\n31\n0.0\n")

            # 3. Rear Joiner Hole (CIRCLE)
            f.write(f"0\nCIRCLE\n8\nREAR_JOINER\n10\n{rear_x:.3f}\n20\n12.0\n30\n0.0\n40\n{rear_r:.3f}\n")

            # 4. Lightening Weight Reduction Hole (CIRCLE)
            f.write(f"0\nCIRCLE\n8\nLIGHTENING_HOLES\n10\n{hole_x:.3f}\n20\n15.0\n30\n0.0\n40\n{hole_r:.3f}\n")

            # DXF Footer
            f.write("0\nENDSEC\n0\nEOF\n")

        print(f"[DXF] Lazer kesim vektoru olusturuldu: {output_path} (Kord: {self.chord_mm:.1f} mm)")


def main():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'dxf_outputs')
    os.makedirs(out_dir, exist_ok=True)

    # Generate Root Rib (320mm) and Tip Rib (260mm)
    root_path = os.path.join(out_dir, 'selig1223_root_rib_320mm.dxf')
    tip_path = os.path.join(out_dir, 'selig1223_tip_rib_260mm.dxf')

    gen_root = AirfoilDxfGenerator(chord_mm=320.0)
    gen_root.generate_dxf(root_path)

    gen_tip = AirfoilDxfGenerator(chord_mm=260.0)
    gen_tip.generate_dxf(tip_path)


if __name__ == '__main__':
    main()
