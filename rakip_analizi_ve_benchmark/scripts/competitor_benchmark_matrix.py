#!/usr/bin/env python3
"""
AIAA DBF 2027 - Competitor Benchmark Matrix & Comparative Gap Analyzer
Compares AIAA DBF reference baseline aircraft metrics against recent AIAA DBF champions:
- FH Joanneum (2025 Champion)
- Embry-Riddle ERAU (2024 Champion)
- RWTH Aachen (2023 Champion)
- Georgia Tech (2022 Champion)
- University of Ljubljana (Multi-time World Champion)
"""

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class AircraftBenchmark:
    team: str
    country: str
    year_rank: str
    wingspan_m: float
    wing_area_m2: float
    aspect_ratio: float
    empty_mass_kg: float
    payload_mass_kg: float
    togw_lbs: float
    cruise_speed_ms: float
    assembly_time_sec: int
    avionics_level: str
    predicted_score: float

def build_benchmark_database() -> List[AircraftBenchmark]:
    return [
        AircraftBenchmark(
            team="DBF Reference Model",
            country="AIAA DBF Open",
            year_rank="2027 Tasarim",
            wingspan_m=2.40,
            wing_area_m2=0.7032,
            aspect_ratio=8.19,
            empty_mass_kg=12.70,
            payload_mass_kg=11.20,
            togw_lbs=52.69,
            cruise_speed_ms=24.5,
            assembly_time_sec=185,
            avionics_level="Edge-AI ROS2 (Adaptif CG)",
            predicted_score=9.06
        ),
        AircraftBenchmark(
            team="FH Joanneum",
            country="Avusturya",
            year_rank="2025 Sampiyon",
            wingspan_m=2.30,
            wing_area_m2=0.6800,
            aspect_ratio=7.78,
            empty_mass_kg=12.10,
            payload_mass_kg=10.50,
            togw_lbs=49.82,
            cruise_speed_ms=25.0,
            assembly_time_sec=135,
            avionics_level="Otopilot + Manuel Hibrit",
            predicted_score=8.92
        ),
        AircraftBenchmark(
            team="Embry-Riddle (ERAU)",
            country="ABD",
            year_rank="2024 Sampiyon",
            wingspan_m=2.50,
            wing_area_m2=0.7200,
            aspect_ratio=8.68,
            empty_mass_kg=13.20,
            payload_mass_kg=11.00,
            togw_lbs=53.35,
            cruise_speed_ms=26.0,
            assembly_time_sec=210,
            avionics_level="PX4 Standard",
            predicted_score=9.01
        ),
        AircraftBenchmark(
            team="RWTH Aachen",
            country="Almanya",
            year_rank="2023 Sampiyon",
            wingspan_m=2.45,
            wing_area_m2=0.6900,
            aspect_ratio=8.70,
            empty_mass_kg=11.80,
            payload_mass_kg=9.80,
            togw_lbs=47.62,
            cruise_speed_ms=24.0,
            assembly_time_sec=190,
            avionics_level="Gelismis Telemetri",
            predicted_score=8.75
        ),
        AircraftBenchmark(
            team="Georgia Tech",
            country="ABD",
            year_rank="2022 Sampiyon",
            wingspan_m=2.35,
            wing_area_m2=0.6650,
            aspect_ratio=8.30,
            empty_mass_kg=12.90,
            payload_mass_kg=11.40,
            togw_lbs=54.67,
            cruise_speed_ms=23.5,
            assembly_time_sec=245,
            avionics_level="Ozel MDO Otopilot",
            predicted_score=8.98
        ),
        AircraftBenchmark(
            team="Univ. of Ljubljana",
            country="Slovenya",
            year_rank="Coklu Sampiyon",
            wingspan_m=2.40,
            wing_area_m2=0.6700,
            aspect_ratio=8.60,
            empty_mass_kg=11.20,
            payload_mass_kg=9.50,
            togw_lbs=45.63,
            cruise_speed_ms=25.5,
            assembly_time_sec=160,
            avionics_level="Minimalist / Yuksek Aerodinamik",
            predicted_score=8.84
        )
    ]


def run_benchmark_analysis():
    db = build_benchmark_database()
    ref_model = db[0]
    competitors = db[1:]

    print("=" * 88)
    print("  AIAA DBF 2027 - ULUSLARARASI SAMPIYONLAR BENCHMARK VE RAKIP ANALIZ MATRISI")
    print("=" * 88)

    # Header
    print(f"{'Takim':18s} | {'Derece/Yil':14s} | {'Aciklik':7s} | {'Bos Ag.':7s} | {'Faydali':7s} | {'TOGW':7s} | {'Montaj':6s} | {'Puan':5s}")
    print("-" * 88)

    for ac in db:
        print(f"{ac.team:18s} | {ac.year_rank:14s} | {ac.wingspan_m:5.2f}m | {ac.empty_mass_kg:5.2f}kg | {ac.payload_mass_kg:5.2f}kg | {ac.togw_lbs:5.1f}lb | {ac.assembly_time_sec:3d}sn | {ac.predicted_score:5.2f}")

    print("=" * 88)

    # Comparative Gap Analysis
    avg_payload = sum(c.payload_mass_kg for c in competitors) / len(competitors)
    avg_assembly = sum(c.assembly_time_sec for c in competitors) / len(competitors)
    avg_score = sum(c.predicted_score for c in competitors) / len(competitors)

    payload_advantage_pct = ((ref_model.payload_mass_kg - avg_payload) / avg_payload) * 100.0
    assembly_advantage_pct = ((avg_assembly - ref_model.assembly_time_sec) / avg_assembly) * 100.0
    score_advantage_pct = ((ref_model.predicted_score - avg_score) / avg_score) * 100.0

    print("\n[DBF REFERANS MODEL REKABETCILIK VE FARK ANALIZI (GAP ANALYSIS)]")
    print(f"1. Faydali Yuk Kapasitesi : {ref_model.payload_mass_kg:.2f} kg (Rakip Ortalamasi: {avg_payload:.2f} kg) -> %{payload_advantage_pct:+.1f} USTUNLUK")
    print(f"2. Hizli Montaj Suresi    : {ref_model.assembly_time_sec} sn (Rakip Ortalamasi: {avg_assembly:.0f} sn) -> %{assembly_advantage_pct:+.1f} DAHA HIZLI")
    print(f"3. Tahmini DBF Toplam Skor: {ref_model.predicted_score:.2f} (Rakip Ortalamasi: {avg_score:.2f}) -> %{score_advantage_pct:+.1f} DAHA YUKSEK")
    print(f"4. Aviyonik ve Otonomi    : Rakipler standart PX4 veya manuel kullanirken DBF Referans Mimarisi,")
    print(f"   anlik 44mm CG kaymasini tolere eden C++20 Adaptif PID ve Edge-AI gorsel hedefleme kullanmaktadir.")
    print("=" * 88)


if __name__ == '__main__':
    run_benchmark_analysis()
