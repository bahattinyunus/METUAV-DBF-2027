#!/usr/bin/env python3
"""
✈️ AIAA DBF Open Engineering Framework - Unified Command-Line Interface (CLI)
=============================================================================
Usage:
    python dbf_cli.py info                 # Show aircraft specifications & compliance
    python dbf_cli.py test                 # Run all 147+ automated verification tests
    python dbf_cli.py analyze --all        # Execute complete aero, FEA, flutter, BEMT, thermal & MDO pipeline
    python dbf_cli.py visuals              # Regenerate all 13 high-resolution infographics
    python dbf_cli.py gcs                  # Launch real-time HTML5 Web GCS Server
"""

import sys
import os
import argparse
import subprocess


def print_banner():
    print(r"""
================================================================================
       _    ___    _       _       ____  ____  _____     ____ _     ___ 
      / \  |_ _|  / \     / \     |  _ \| __ )|  ___|   / ___| |   |_ _|
     / _ \  | |  / _ \   / _ \    | | | |  _ \| |_     | |   | |    | | 
    / ___ \ | | / ___ \ / ___ \   | |_| | |_) |  _|    | |___| |___ | | 
   /_/   \_\___/_/   \_/_/   \_\  |____/|____/|_|       \____|_____|___|
            AIAA DESIGN / BUILD / FLY - OPEN ENGINEERING CLI
================================================================================
""")


def cmd_info():
    print_banner()
    print("  [REFERANS UÇAK ÖZELLİKLERİ VE KURAL UYUMLULUĞU]")
    print("  " + "-" * 76)
    specs = [
        ("Maksimum Kalkış Ağırlığı (TOGW)", "23.90 kg (52.69 lbs)", "<= 55.0 lbs [UYUMLU - %4.2 Marjin]"),
        ("Kuru Yapısal Kütle (Dry Mass)", "12.70 kg (28.00 lbs)", "Karbon Toray T700 / Rohacell Sandviç"),
        ("Görev 2 Taşınan Yük (Medikal)", "11.20 kg (24.69 lbs)", "Gövde içi kilitli kargo haznesi"),
        ("Görev 3 Bırakılan Yük (2 Kutu)", "8.35 kg (18.41 lbs)", "Alttan açılır kapaklı mekanizma"),
        ("Kanat Açıklığı (b) & Alanı (S)", "2.40 m | 0.7032 m²", "Narinlik Oranı: AR = 8.19"),
        ("Taşıyıcı Profil (Ana Kanat)", "Selig 1223 (Cl=2.23)", "3D Cl_max = 1.96 (Re = 350,000)"),
        ("Stall / Seyir Hızı (Vs / Vc)", "17.0 m/s / 24.5 m/s", "Güvenli Uçuş Marjini (1.45 * Vs)"),
        ("Statik Kalkış İtkisi / Motor", "122.4 N (12.5 kgf)", "Scorpion 4035-330KV + 19x12E Karbon"),
        ("100 ft Sideline Gürültüsü", "76.5 dBA", "<= 85.0 dBA [UYUMLU - +8.5 dBA Marjin]"),
        ("Yer Görevi Montaj Süresi", "185 sn (3 dk 5 sn)", "<= 300 sn (5 dk) [%38 DAHA HIZLI]"),
        ("Tahmini DBF Toplam Puanı", "9.06 / 10.00", "Dünya Şampiyonları Karşılaştırmalı Zirve")
    ]
    for name, val, note in specs:
        print(f"  * {name:32s}: {val:22s} -> {note}")
    print("  " + "-" * 76)


def cmd_test():
    print_banner()
    print("  [BÜTÜNCÜL TEST VE DOĞRULAMA BATARYASI ÇALIŞTIRILIYOR...]")
    res = subprocess.run([sys.executable, "-m", "pytest", "-v"])
    sys.exit(res.returncode)


def cmd_analyze(target):
    print_banner()
    scripts = []
    if target in ["aero", "all"]:
        scripts.append(("Aerodinamik Polar & VLM", "aerodinamik/scripts/polar_analysis.py"))
        scripts.append(("Uçuş Zarfı & V-n Manevra", "aerodinamik/scripts/flight_envelope_vn_diagram.py"))
    if target in ["struct", "all"]:
        scripts.append(("Karbon Spar FEA", "mekanik_ve_yapisal/scripts/spar_stress_fea.py"))
        scripts.append(("Aeroelastik Flutter & Diverjans (P-K)", "mekanik_ve_yapisal/scripts/aeroelastic_pk_flutter_solver.py"))
        scripts.append(("Kütle & CG Bütçesi", "mekanik_ve_yapisal/scripts/mass_and_cg_calculator.py"))
    if target in ["prop", "all"]:
        scripts.append(("BEMT Pervane Optimizasyonu", "itki_ve_guc_sistemleri/scripts/bemt_propeller_optimizer.py"))
        scripts.append(("Batarya Termal Paket & Soğutma Kanalı", "itki_ve_guc_sistemleri/scripts/battery_thermal_pack_optimizer.py"))
        scripts.append(("Pervane Aeroakustik Gürültüsü", "itki_ve_guc_sistemleri/scripts/propeller_noise_mapper.py"))
    if target in ["avionics", "all"]:
        scripts.append(("Sensör Füzyonu & İnovasyon Teşhisi", "aviyonik_ve_otonom/scripts/sensor_fusion_innovation_monitor.py"))
    if target in ["mdo", "all"]:
        scripts.append(("MDO Çok Amaçlı Pareto", "optimizasyon_ve_mdo/scripts/dbf_pareto_optimizer.py"))
    if target in ["sim", "all"]:
        scripts.append(("Pylon Yarış Optimum Bank", "simulasyon/scripts/pylon_racing_optimal_bank.py"))

    for desc, script_path in scripts:
        print(f"\n>>> [ANALİZ BAŞLATILIYOR: {desc}] ({script_path})")
        subprocess.run([sys.executable, script_path])


def cmd_visuals():
    print_banner()
    print("  [13 ADET YÜKSEK ÇÖZÜNÜRLÜKLÜ TEKNİK İNFOGRAFİK VE BANNER YENİLENİYOR...]")
    subprocess.run([sys.executable, "docs/scripts/generate_repo_visuals.py"])


def cmd_gcs():
    print_banner()
    print("  [CANLI WEB GLASS COCKPIT YER İSTASYONU SUNUCUSU BAŞLATILIYOR (http://localhost:8080)...]")
    subprocess.run([sys.executable, "aviyonik_ve_otonom/src/telemetri/gcs_server.py"])


def main():
    parser = argparse.ArgumentParser(description="AIAA DBF Open Engineering Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("info", help="Show reference aircraft specifications")
    subparsers.add_parser("test", help="Run all automated verification unit tests")

    analyze_parser = subparsers.add_parser("analyze", help="Run engineering analysis pipeline")
    analyze_parser.add_argument("--target", choices=["aero", "struct", "prop", "mdo", "sim", "all"],
                                default="all", help="Discipline to analyze")

    subparsers.add_parser("visuals", help="Regenerate all 10 high-resolution infographics")
    subparsers.add_parser("gcs", help="Launch live HTML5 Ground Control Station")

    args = parser.parse_args()

    if args.command == "info" or not args.command:
        cmd_info()
    elif args.command == "test":
        cmd_test()
    elif args.command == "analyze":
        cmd_analyze(args.target)
    elif args.command == "visuals":
        cmd_visuals()
    elif args.command == "gcs":
        cmd_gcs()


if __name__ == "__main__":
    main()
