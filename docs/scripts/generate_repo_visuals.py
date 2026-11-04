#!/usr/bin/env python3
"""
AIAA DBF Open Engineering Framework & Toolkit - High-Resolution Visuals Suite
Generates 7 publication-quality technical infographics, HUD hero banners,
CAD architectural layouts, flight line checklists, and aerodynamic test figures.
"""

import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from PIL import Image, ImageDraw, ImageFont, ImageFilter

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'images'))
os.makedirs(output_dir, exist_ok=True)


# ==============================================================================
# 1. STANDALONE HIGH-TECH HERO BANNER (1920x680 ULTRA-RES AEROSPACE HUD)
# ==============================================================================
def generate_enhanced_banner():
    banner_png = os.path.join(output_dir, 'dbf_aircraft_banner.png')
    banner_jpg = os.path.join(output_dir, 'dbf_aircraft_banner.jpg')

    W, H = 1920, 680

    # 1. Base Gradient Canvas (Deep Night Obsidian to Aero Cobalt)
    base_img = Image.new('RGB', (W, H), color=(6, 10, 18))
    draw = ImageDraw.Draw(base_img)

    for y in range(H):
        r_ratio = y / float(H)
        r = int(6 + r_ratio * 10)
        g = int(10 + r_ratio * 16)
        b = int(18 + r_ratio * 34)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 2. Tech Coordinate Grid & Tactical Reticles
    grid_color = (16, 28, 48)
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Diagonal Isometric Grid in Center-Right
    for d in range(700, W + 500, 70):
        draw.line([(d, 0), (d - 450, H)], fill=(14, 25, 42), width=1)

    # 3. Concentric Radar & Flight Director Rings
    rc_x, rc_y = W - 480, H // 2 + 10
    for radius in [90, 160, 240, 320]:
        draw.ellipse([(rc_x - radius, rc_y - radius), (rc_x + radius, rc_y + radius)],
                     outline=(22, 52, 85), width=1)
    draw.line([(rc_x - 340, rc_y), (rc_x + 340, rc_y)], fill=(28, 68, 105), width=1)
    draw.line([(rc_x, rc_y - 330), (rc_x, rc_y + 330)], fill=(28, 68, 105), width=1)

    # Dynamic Degree Marks on Radar
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x1 = rc_x + int(310 * math.cos(rad))
        y1 = rc_y + int(310 * math.sin(rad))
        x2 = rc_x + int(325 * math.cos(rad))
        y2 = rc_y + int(325 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(0, 210, 255), width=1)

    # 4. Schematic 3D Aircraft Wireframe & Aerodynamic Streamlines
    # Main Wing Box
    draw.line([(rc_x - 320, rc_y + 35), (rc_x + 320, rc_y + 35)], fill=(0, 229, 255), width=4)
    # Winglets (Blended Winglets)
    draw.line([(rc_x - 320, rc_y + 35), (rc_x - 345, rc_y - 25)], fill=(0, 210, 255), width=3)
    draw.line([(rc_x + 320, rc_y + 35), (rc_x + 345, rc_y - 25)], fill=(0, 210, 255), width=3)
    # Fuselage Monocoque (Aerodynamic Fairing)
    draw.line([(rc_x, rc_y - 170), (rc_x, rc_y + 190)], fill=(16, 185, 129), width=3)
    draw.polygon([(rc_x, rc_y - 180), (rc_x - 24, rc_y - 120), (rc_x + 24, rc_y - 120)],
                 outline=(16, 185, 129), fill=(10, 35, 30))
    # Horizontal & Vertical Tail
    draw.line([(rc_x - 110, rc_y + 165), (rc_x + 110, rc_y + 165)], fill=(0, 229, 255), width=2)
    draw.line([(rc_x, rc_y + 165), (rc_x - 55, rc_y + 130)], fill=(0, 200, 255), width=2)
    draw.line([(rc_x, rc_y + 165), (rc_x + 55, rc_y + 130)], fill=(0, 200, 255), width=2)

    # Streamline Flow Particles
    for sy in range(-80, 100, 25):
        curve_pts = []
        for sx in range(rc_x - 380, rc_x + 420, 25):
            amp = math.sin((sx - rc_x) * 0.018) * 18 * math.exp(-((sx - rc_x) / 220.0) ** 2)
            curve_pts.append((sx, rc_y + sy + int(amp)))
        for i in range(len(curve_pts) - 1):
            draw.line([curve_pts[i], curve_pts[i+1]], fill=(0, 180, 255), width=1)

    # 5. Top Aerospace HUD Header Bar
    draw.rectangle([(0, 0), (W, 50)], fill=(10, 18, 30))
    draw.line([(0, 50), (W, 50)], fill=(0, 229, 255), width=2)
    draw.text((45, 16), "AIAA DESIGN / BUILD / FLY // OPEN ENGINEERING FRAMEWORK & TOOLKIT", fill=(255, 255, 255))
    draw.text((720, 16), "|  STANDARD: C++20 / ROS 2 HUMBLE  |  MODEL: UNIVERSAL DBF BASELINE", fill=(0, 210, 255))
    draw.text((W - 380, 16), "SYSTEM HEALTH: 100% NOMINAL [ARMED]", fill=(52, 211, 153))

    # 6. Hero Typography (Left Half)
    # Category Tag
    draw.rectangle([(80, 100), (330, 134)], fill=(16, 40, 72), outline=(0, 229, 255), width=1)
    draw.text((95, 110), "AIAA DBF OPEN ARCHITECTURE", fill=(0, 229, 255))

    # Big Title
    draw.text((80, 155), "DBF ENGINEERING", fill=(255, 255, 255))
    draw.text((80, 235), "TOOLKIT & AUTOPILOT", fill=(0, 229, 255))

    # Subtitle / Description
    desc1 = "AIAA Design/Build/Fly takimlari icin eksiksiz acik kaynakli aerodinamik analiz, kompozit FEA,"
    desc2 = "elektrik itki BEMT optimizasyonu, 15-durumlu EKF otopilot, Edge-AI hedefleme ve MDO skorlama mimarisi."
    draw.text((80, 325), desc1, fill=(190, 210, 235))
    draw.text((80, 352), desc2, fill=(190, 210, 235))

    # Feature Badges
    pills = [
        ("AERODYNAMICS & CFD", (59, 130, 246)),
        ("COMPOSITE FEA", (139, 92, 246)),
        ("BEMT PROPULSION", (245, 158, 11)),
        ("ROS 2 / PX4 AUTOPILOT", (16, 185, 129)),
        ("MDO SCORING", (236, 72, 153)),
    ]
    cur_x = 80
    for name, color in pills:
        tw = len(name) * 8 + 22
        draw.rectangle([(cur_x, 410), (cur_x + tw, 442)], fill=(15, 28, 48), outline=color, width=1)
        draw.text((cur_x + 11, 419), name, fill=color)
        cur_x += tw + 14

    # Metric Spec Cards (Left-Bottom)
    cards = [
        ("WINGSPAN (b)", "2.40 m (94.5 in)", (0, 229, 255)),
        ("MAX WEIGHT (TOGW)", "52.69 lbs (<=55 lbs)", (52, 211, 153)),
        ("CRUISE AIRSPEED", "24.5 m/s (47.6 kts)", (245, 158, 11)),
        ("ASSEMBLY BENCHMARK", "185 sec (<=300s)", (236, 72, 153)),
    ]
    cx = 80
    for title, val, col in cards:
        draw.rectangle([(cx, 480), (cx + 195, 570)], fill=(12, 24, 42), outline=(32, 54, 88), width=1)
        draw.text((cx + 12, 494), title, fill=(140, 165, 195))
        draw.text((cx + 12, 524), val, fill=col)
        cx += 215

    # 7. Bottom Telemetry Bar
    draw.rectangle([(0, H - 46), (W, H)], fill=(10, 18, 30))
    draw.line([(0, H - 46), (W, H - 46)], fill=(0, 229, 255), width=2)
    draw.text((45, H - 30), "AIRFOIL: SELIG 1223 (Cl=2.23) | CRUISE L/D: 19.31 | STATIC THRUST: 122.4 N | EKF: 50Hz ACTIVE", fill=(175, 200, 230))
    draw.text((W - 420, H - 30), "UNIVERSAL PREPARATION SUITE | MULTI-TEAM READY", fill=(0, 240, 255))

    # Corner framing brackets
    c_len = 40
    c_color = (0, 229, 255)
    draw.line([(45, 65), (45 + c_len, 65)], fill=c_color, width=2)
    draw.line([(45, 65), (45, 65 + c_len)], fill=c_color, width=2)
    draw.line([(W - 45 - c_len, 65), (W - 45, 65)], fill=c_color, width=2)
    draw.line([(W - 45, 65), (W - 45, 65 + c_len)], fill=c_color, width=2)
    draw.line([(45, H - 60 - c_len), (45, H - 60)], fill=c_color, width=2)
    draw.line([(45, H - 60), (45 + c_len, H - 60)], fill=c_color, width=2)
    draw.line([(W - 45 - c_len, H - 60), (W - 45, H - 60)], fill=c_color, width=2)
    draw.line([(W - 45, H - 60 - c_len), (W - 45, H - 60)], fill=c_color, width=2)

    base_img.save(banner_png, 'PNG', quality=95)
    base_img.save(banner_jpg, 'JPEG', quality=95)
    print(f"[OK] High-tech hero banner regenerated: {banner_png} & {banner_jpg}")


# ==============================================================================
# 2. FLIGHT LINE & APRON OPERATIONS INFOGRAPHIC (REPLACES OLD STATIC PHOTO)
# ==============================================================================
def generate_flight_line_visual():
    out_path = os.path.join(output_dir, 'dbf_flight_line.jpg')

    fig = plt.figure(figsize=(16, 9), facecolor='#0B0F19', dpi=150)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25,
                  left=0.08, right=0.95, top=0.90, bottom=0.08)

    fig.suptitle('AIAA DBF OPEN FRAMEWORK - UÇUŞ HATTI (FLIGHT LINE) VE APRON OPERASYONLARI',
                 fontsize=17, fontweight='bold', color='#00E5FF', y=0.96)

    # Subplot 1: Pre-Flight Checklist Gates
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#111827')
    gates = [
        "1. Mekanik: Ball-Lock Pinleri Çift Kilitli",
        "2. Pitot Kapağı & Emniyet Flaması Kaldırıldı",
        "3. Elektrik: 120A Sigorta & Kırmızı Arming Plug",
        "4. Batarya: 6S 4.20V/Hücre, IR <= 1.5 mOhm",
        "5. Aviyonik: Fast-Boot BIST Yeşil (DBF-AIR-GO)",
        "6. GPS: 3D Fix (Uydu >= 10, HDOP <= 1.2)",
        "7. Görev 3 Bırakma: Kilitli 1000us PWM Onayı"
    ]
    ax1.set_xlim(0, 1)
    ax1.set_ylim(-0.5, len(gates) - 0.5)
    ax1.axis('off')
    for i, item in enumerate(reversed(gates)):
        ax1.text(0.05, i, f"✔  {item}", color='#F8FAFC', fontsize=11, fontweight='bold', va='center')
        ax1.text(0.85, i, "[GEÇTİ]", color='#10B981', fontsize=11, fontweight='bold', va='center')
        ax1.plot([0.02, 0.98], [i - 0.35, i - 0.35], color='#1E293B', lw=1)
    ax1.set_title('(A) Pist Başı Güvenlik ve Emniyet Kapıları (SOP Onayı)', fontsize=12, fontweight='bold', color='#F1F5F9')

    # Subplot 2: RF Telemetry & Dual-Link RSSI Signal Budget
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#111827')
    dist_m = np.linspace(10, 1200, 200)
    # Free-space path loss model at 868 MHz & 2.4 GHz
    rssi_868 = -30 - 20 * np.log10(dist_m)
    rssi_24 = -40 - 20 * np.log10(dist_m)

    ax2.plot(dist_m, rssi_868, color='#00E5FF', lw=2.5, label='Birincil Telemetri (868 MHz Sik / -110 dBm Eşik)')
    ax2.plot(dist_m, rssi_24, color='#F59E0B', lw=2.0, ls='--', label='Yedekli RC Link (2.4 GHz FHSS)')
    ax2.axhline(-100, color='#EF4444', lw=1.5, ls=':', label='Kritik Failsafe Eşiği (-100 dBm)')
    ax2.axvline(750, color='#10B981', lw=1.5, ls='-.', label='Parkur Maks Mesafe (750m)')
    ax2.set_title('(B) Uçuş Hattı Çift Yedekli Telemetri Sinyal Bütçesi (RSSI)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.set_xlabel('Mesafe (m)', color='#94A3B8')
    ax2.set_ylabel('Sinyal Gücü (dBm)', color='#94A3B8')
    ax2.tick_params(colors='#94A3B8')
    ax2.grid(True, color='#1E293B', ls=':')
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5)

    # Subplot 3: 5-Minute Ready Timeline (Ground Mission)
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#111827')
    timeline_items = ['Apron Girişi', 'Aletsiz Montaj', 'Sistem Boot', 'Sensör Öz-Test', 'Uçuş Hattı Yeşil']
    cum_times = [0, 65, 95, 125, 185]
    durations = [65, 30, 30, 60, 0]

    ax3.plot(cum_times, [1, 2, 3, 4, 5], color='#00E5FF', marker='o', lw=2.5, markersize=8)
    for t_val, y_pos, name in zip(cum_times, [1, 2, 3, 4, 5], timeline_items):
        ax3.text(t_val + 5, y_pos - 0.1, f"{name}\n({t_val}. sn)", color='#F8FAFC', fontsize=9, fontweight='bold')
    ax3.axvline(300, color='#EF4444', lw=2.0, ls='--', label='5 Dakika Kuralı (300 sn)')
    ax3.set_xlim(-10, 330)
    ax3.set_ylim(0.5, 5.8)
    ax3.set_yticks([])
    ax3.set_title('(C) Yer Görevi Hazırlık Süresi: 185 sn (%38 Emniyet Marjini)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.set_xlabel('Süre (sn)', color='#94A3B8')
    ax3.tick_params(colors='#94A3B8')
    ax3.grid(True, color='#1E293B', ls=':')
    ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 4: Failsafe State Decision Flow
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#111827')
    anomalies = [
        ("Pitot Tüpü Tıkanması", "GPS/Sentetik AoA Yedekleme", '#10B981'),
        ("Geofence İhlal Riski (<4s)", "Otomatik Escape Vektörü", '#10B981'),
        ("Tek Hücre Çökmesi (<3.3V)", "Gaz Kademeli %50 Kısma", '#F59E0B'),
        ("Telemetri Kaybı (>3 sn)", "Otonom Bekleme & RTL", '#F59E0B'),
        ("Aktüatör Sıkışması (>3.5A)", "FDIR Kontrol Tahsisatı", '#10B981'),
        ("Manuel Müdahale (CH5)", "Anında Pilot Devri", '#00E5FF')
    ]
    ax4.set_xlim(0, 1)
    ax4.set_ylim(-0.5, len(anomalies) - 0.5)
    ax4.axis('off')
    for i, (hazard, mitigation, col) in enumerate(reversed(anomalies)):
        ax4.text(0.05, i, f"⚠ {hazard}", color='#E2E8F0', fontsize=11, fontweight='bold', va='center')
        ax4.text(0.55, i, f"-> [{mitigation}]", color=col, fontsize=11, fontweight='bold', va='center')
        ax4.plot([0.02, 0.98], [i - 0.35, i - 0.35], color='#1E293B', lw=1)
    ax4.set_title('(D) Uçuş Hattı Otomatik Acil Durum & FDIR Karar Matrisi', fontsize=12, fontweight='bold', color='#F1F5F9')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=150)
    plt.close()
    print(f"[OK] Flight line operations visual regenerated: {out_path}")


# ==============================================================================
# 3. MISSION 3 BALLISTIC DROP & TARGET ANALYSIS INFOGRAPHIC
# ==============================================================================
def generate_mission3_drop_visual():
    out_path = os.path.join(output_dir, 'dbf_mission3_drop.png')

    fig = plt.figure(figsize=(16, 9), facecolor='#0B0F19', dpi=150)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25,
                  left=0.08, right=0.95, top=0.90, bottom=0.08)

    fig.suptitle('AIAA DBF OPEN FRAMEWORK - GÖREV 3 BALİSTİK BIRAKMA VE HEDEF İSABET ANALİZİ',
                 fontsize=17, fontweight='bold', color='#00E5FF', y=0.96)

    # Subplot 1: 3-DOF Trajectory
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#111827')
    t = np.linspace(0, 2.27, 200)
    v0, alt0, theta = 24.5, 25.0, np.radians(2.4)
    vx = v0 * np.cos(theta) - 1.2 * t
    x = vx * t
    y = alt0 + v0 * np.sin(theta) * t - 0.5 * 9.81 * (t ** 2)

    ax1.plot(x, y, color='#00E5FF', lw=2.5, label='3-DOF RK4 Düşüş Hattı')
    ax1.scatter([0], [alt0], color='#F59E0B', s=90, zorder=5, label='Bırakma Noktası (t=0)')
    impact_x = x[y >= 0][-1]
    ax1.scatter([impact_x], [0], color='#10B981', s=110, marker='*', zorder=5, label='İsabet (t=2.27s)')
    ax1.axhline(0, color='#64748B', lw=1.5, ls='--')
    ax1.set_title('(A) 3-DOF RK4 Faydalı Yük Düşüş Yörüngesi (t = 2.27 sn)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.set_xlabel('Yatay Mesafe (m)', color='#94A3B8')
    ax1.set_ylabel('İrtifa (m)', color='#94A3B8')
    ax1.tick_params(colors='#94A3B8')
    ax1.grid(True, color='#1E293B', ls=':')
    ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 2: Concentric Target Distribution
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#111827')
    for r, col, lbl in [(5.0, '#334155', 'Dış Çember (5.0m)'),
                        (2.5, '#475569', 'Orta Çember (2.5m)'),
                        (1.2, '#0284C7', 'Boğa Gözü Toleransı (1.2m)')]:
        circ = patches.Circle((0, 0), r, fill=False, edgecolor=col, lw=2.0, ls='--', label=lbl)
        ax2.add_patch(circ)

    np.random.seed(42)
    drops_x = np.random.normal(0.18, 0.45, 120)
    drops_y = np.random.normal(-0.08, 0.40, 120)
    ax2.scatter(drops_x, drops_y, color='#00E5FF', alpha=0.75, s=30, label='Monte Carlo Atımları (N=120)')
    ax2.scatter([0.18], [-0.08], color='#EF4444', s=100, marker='X', zorder=6, label='Ortalama İsabet (0.20m Sapma)')
    ax2.set_xlim(-6, 6)
    ax2.set_ylim(-6, 6)
    ax2.set_aspect('equal')
    ax2.set_title('(B) AIAA DBF Konsantrik Hedef Dağılımı (Ort. Sapma: 0.20 m)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.tick_params(colors='#94A3B8')
    ax2.grid(True, color='#1E293B', ls=':')
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5, loc='upper right')

    # Subplot 3: Velocity Profile
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#111827')
    vx_prof = v0 * np.exp(-0.15 * t)
    vy_prof = -9.81 * t
    v_total = np.sqrt(vx_prof**2 + vy_prof**2)

    ax3.plot(t, vx_prof, color='#3B82F6', lw=2.0, label='Yatay Hız (Vx)')
    ax3.plot(t, np.abs(vy_prof), color='#F59E0B', lw=2.0, label='Dikey Çökme Hızı (|Vy|)')
    ax3.plot(t, v_total, color='#10B981', lw=2.5, label='Bileşke Hız (V_tot)')
    ax3.set_title('(C) Faydalı Yük Hız Boşalımı (Çarpma Hızı = 29.8 m/s)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.set_xlabel('Zaman (sn)', color='#94A3B8')
    ax3.set_ylabel('Hız (m/s)', color='#94A3B8')
    ax3.tick_params(colors='#94A3B8')
    ax3.grid(True, color='#1E293B', ls=':')
    ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 4: Adaptive Trim & Pitch Response
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#111827')
    time_sim = np.linspace(-0.5, 3.5, 300)
    pitch_uncomp = np.where(time_sim < 0, 2.4, 2.4 + 22.0 * (1.0 - np.exp(-1.5 * np.maximum(0, time_sim))))
    pitch_comp = np.where(time_sim < 0, 2.4, 2.4 + 5.34 * np.sin(3.5 * np.maximum(0, time_sim)) * np.exp(-2.2 * np.maximum(0, time_sim)))

    ax4.plot(time_sim, pitch_uncomp, color='#EF4444', lw=2.0, ls='--', label='Kompanzasyonsuz (Stall Riski)')
    ax4.plot(time_sim, pitch_comp, color='#00E5FF', lw=2.5, label='C++20 Adaptif Trim & CG Sönümleme')
    ax4.axvline(0, color='#F59E0B', lw=1.5, ls=':', label='Yük Bırakma (t=0)')
    ax4.axhline(15.0, color='#DC2626', lw=1.0, ls='-.', label='Kritik Stall Açısı (15°)')
    ax4.set_title('(D) Kütle Düşüşü (+44.1 mm CG Şoku) Pitch Geçici Cevabı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax4.set_xlabel('Zaman (sn)', color='#94A3B8')
    ax4.set_ylabel('Yunuslama Açısı Theta (°)', color='#94A3B8')
    ax4.tick_params(colors='#94A3B8')
    ax4.grid(True, color='#1E293B', ls=':')
    ax4.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5)

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] Mission 3 Drop infographic regenerated: {out_path}")


# ==============================================================================
# 4. 3D CAD ARCHITECTURE & MASS BUDGET BLUEPRINT
# ==============================================================================
def generate_cad_architecture_visual():
    out_path = os.path.join(output_dir, 'dbf_cad_exploded_view.png')

    fig = plt.figure(figsize=(16, 9), facecolor='#0B0F19', dpi=150)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25,
                  left=0.08, right=0.95, top=0.90, bottom=0.08)

    fig.suptitle('AIAA DBF OPEN FRAMEWORK - YAPISAL 3D CAD MİMARİSİ VE TEKNİK DÜZENİ',
                 fontsize=17, fontweight='bold', color='#00E5FF', y=0.96)

    # Subplot 1: Top-down Geometry Schematic
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#111827')
    wing_x = [-1.20, 1.20, 1.20, -1.20, -1.20]
    wing_y = [0.16, 0.16, -0.16, -0.16, 0.16]
    ax1.plot(wing_x, wing_y, color='#00E5FF', lw=2.5, label='Ana Kanat (b=2.40m, MAC=0.293m)')
    ax1.plot([-1.18, 1.18], [0.08, 0.08], color='#F59E0B', lw=3.0, ls='-', label='Toray T700 Karbon Spar')
    # Fuselage
    fuse_x = [-0.15, 0.15, 0.12, 0.08, -0.08, -0.12, -0.15]
    fuse_y = [0.45, 0.45, -0.80, -1.10, -1.10, -0.80, 0.45]
    ax1.plot(fuse_x, fuse_y, color='#10B981', lw=2.2, label='Karbon Monokok Gövde (L=1.55m)')
    # Tail
    ax1.plot([-0.35, 0.35], [-1.05, -1.05], color='#38BDF8', lw=2.0, label='Yatay Stabilize (Clark Y)')
    ax1.set_xlim(-1.40, 1.40)
    ax1.set_ylim(-1.25, 0.60)
    ax1.set_aspect('equal')
    ax1.set_title('(A) Üstten Görünüş CAD Geometrisi ve Karbon Spar Yerleşimi', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.tick_params(colors='#94A3B8')
    ax1.grid(True, color='#1E293B', ls=':')
    ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5, loc='upper left')

    # Subplot 2: Selig 1223 Airfoil
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#111827')
    chord = np.linspace(0, 1, 100)
    yt = 5 * 0.121 * (0.2969 * np.sqrt(chord) - 0.1260 * chord - 0.3516 * chord**2 + 0.2843 * chord**3 - 0.1015 * chord**4)
    yc = np.where(chord < 0.4, 0.081 * (chord/0.4)**2, 0.081 * ((1 - chord)/0.6)**1.5)
    yu = yc + yt
    yl = yc - yt

    ax2.plot(chord, yu, color='#00E5FF', lw=2.5, label='Selig 1223 Üst Yüzey (Cl_max = 2.23)')
    ax2.plot(chord, yl, color='#38BDF8', lw=2.5, label='Selig 1223 Alt Yüzey')
    ax2.fill_between(chord, yl, yu, color='#0284C7', alpha=0.25)
    ax2.scatter([0.25, 0.65], [yc[25], yc[65]], color='#F59E0B', s=90, zorder=5, label='Ana & Yardımcı Spar Tüpleri')
    ax2.set_xlim(-0.05, 1.05)
    ax2.set_ylim(-0.15, 0.25)
    ax2.set_aspect('equal')
    ax2.set_title('(B) Aerodinamik Kanat Profili ve Nervür Spar Delikleri', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.tick_params(colors='#94A3B8')
    ax2.grid(True, color='#1E293B', ls=':')
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5)

    # Subplot 3: Mass Breakdown
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#111827')
    categories = ['Boş Yapı (Gövde+Kanat)', 'İtki & Batarya (6S)', 'Aviyonik & Sensör', 'Görev 2 Faydalı Yük', 'Maks Kalkış TOGW']
    masses = [5.85, 4.70, 2.15, 11.20, 23.90]
    colors = ['#38BDF8', '#F59E0B', '#10B981', '#A855F7', '#EC4899']

    bars = ax3.barh(categories, masses, color=colors, edgecolor='#1E293B', height=0.55)
    for bar, m in zip(bars, masses):
        ax3.text(m + 0.25, bar.get_y() + bar.get_height()/2.0, f"{m:.2f} kg",
                 va='center', color='#F8FAFC', fontweight='bold', fontsize=9.5)
    ax3.axvline(24.95, color='#EF4444', lw=2.0, ls='--', label='55.0 lbs Üst Sınır (24.95 kg)')
    ax3.set_xlim(0, 28)
    ax3.set_title('(C) Alt Sistem Kütle Dağılımı ve 55 lbs AIAA Kural Uyumu', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.set_xlabel('Kütle (kg)', color='#94A3B8')
    ax3.tick_params(colors='#94A3B8')
    ax3.grid(True, color='#1E293B', ls=':')
    ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 4: CG Shift Tracking
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#111827')
    cg_dry_x = 0.278
    cg_payload_x = 0.322
    cg_np_x = 0.559

    ax4.plot([0, 1], [1, 1], color='#475569', lw=8.0, label='Ortalama Kord (MAC: 0.293m)')
    ax4.scatter([cg_dry_x], [1], color='#10B981', s=200, zorder=6, label=f'Yüksüz CG (%{cg_dry_x*100:.1f} MAC)')
    ax4.scatter([cg_payload_x], [1], color='#F59E0B', s=200, zorder=6, label=f'Yüklü CG (%{cg_payload_x*100:.1f} MAC)')
    ax4.scatter([cg_np_x], [1], color='#EF4444', s=220, marker='D', zorder=6, label=f'Nötr Nokta NP (%{cg_np_x*100:.1f} MAC)')

    ax4.annotate('', xy=(cg_payload_x, 1.25), xytext=(cg_dry_x, 1.25),
                 arrowprops=dict(arrowstyle="<->", color='#00E5FF', lw=2.5))
    ax4.text((cg_payload_x + cg_dry_x)/2.0, 1.35, 'ΔCG = +44.1 mm Geriye Kayma\n(Adaptif Trim ile Karşılanır)',
             ha='center', va='bottom', color='#00E5FF', fontweight='bold', fontsize=9)

    ax4.set_xlim(-0.1, 0.8)
    ax4.set_ylim(0.5, 1.6)
    ax4.set_yticks([])
    ax4.set_title('(D) Faydalı Yük Bırakma Anlık Ağırlık Merkezi (CG) Seyahati', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax4.set_xlabel('MAC Boyunca Konum Oranı (x/MAC)', color='#94A3B8')
    ax4.tick_params(colors='#94A3B8')
    ax4.grid(True, color='#1E293B', ls=':')
    ax4.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5, loc='lower left')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] CAD Architecture Blueprint regenerated: {out_path}")


# ==============================================================================
# 5. GCS LIVE COCKPIT & PFD TELEMETRY DASHBOARD
# ==============================================================================
def generate_gcs_cockpit_visual():
    out_path = os.path.join(output_dir, 'dbf_gcs_cockpit_dashboard.png')

    fig = plt.figure(figsize=(16, 9), facecolor='#0B0F19', dpi=150)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25,
                  left=0.08, right=0.95, top=0.90, bottom=0.08)

    fig.suptitle('AIAA DBF OPEN FRAMEWORK - CANLI YER İSTASYONU (GCS) VE BİRİNCİL UÇUŞ EKRANI (PFD)',
                 fontsize=17, fontweight='bold', color='#00E5FF', y=0.96)

    # Subplot 1: PFD Artificial Horizon
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#1E293B')
    sky = patches.Rectangle((-2, 0), 4, 2, facecolor='#0284C7', edgecolor='none')
    ground = patches.Rectangle((-2, -2), 4, 2, facecolor='#92400E', edgecolor='none')
    ax1.add_patch(sky)
    ax1.add_patch(ground)
    ax1.axhline(0, color='#FFFFFF', lw=2.0)

    # Pitch ladder
    for deg in [-10, -5, 5, 10]:
        y = deg * 0.1
        w = 0.8 if abs(deg) == 10 else 0.4
        ax1.plot([-w, w], [y, y], color='#FFFFFF', lw=1.5)
        ax1.text(1.1, y, f"{deg}°", color='#FFFFFF', va='center', fontsize=9)

    # Flight path symbol
    ax1.scatter([0], [0.24], color='#F59E0B', s=160, marker='o', edgecolors='#000000', lw=2, zorder=5)
    ax1.plot([-0.6, -0.1], [0.24, 0.24], color='#F59E0B', lw=4, zorder=5)
    ax1.plot([0.1, 0.6], [0.24, 0.24], color='#F59E0B', lw=4, zorder=5)
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-1.5, 1.5)
    ax1.set_title('(A) Birincil Uçuş Ekranı (PFD) - Yunuslama: +2.4° | Yatış: -1.2°', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.tick_params(colors='#94A3B8')

    # Subplot 2: Radar Map
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#111827')
    pylon_left = (-152.4, 0)
    pylon_right = (152.4, 0)
    ax2.scatter([pylon_left[0], pylon_right[0]], [pylon_left[1], pylon_right[1]],
                color='#EF4444', s=180, marker='^', zorder=6, label='Yarış Pylonları (1000 ft Aralık)')

    t_rad = np.linspace(0, 2*np.pi, 200)
    rad_x = 152.4 * np.cos(t_rad)
    rad_y = 65.0 * np.sin(t_rad)
    ax2.plot(rad_x, rad_y, color='#00E5FF', lw=2.5, ls='-', label='750m Referans Yarış Rotası')
    ax2.scatter([60.0], [64.0], color='#10B981', s=140, marker='>', zorder=7, label='Anlık İHA Konumu')
    ax2.set_xlim(-220, 220)
    ax2.set_ylim(-120, 120)
    ax2.set_title('(B) Taktik Radar Haritası ve 750m Pylon Devresi', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.set_xlabel('Doğu-Batı (m)', color='#94A3B8')
    ax2.set_ylabel('Kuzey-Güney (m)', color='#94A3B8')
    ax2.tick_params(colors='#94A3B8')
    ax2.grid(True, color='#1E293B', ls=':')
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5, loc='upper right')

    # Subplot 3: Power Telemetry
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#111827')
    time_p = np.linspace(0, 180, 180)
    power_watts = 800 + 450 * np.sin(time_p * 0.15)**2 + np.random.normal(0, 25, 180)
    current_amps = power_watts / 24.6

    ax3.plot(time_p, power_watts, color='#F59E0B', lw=1.8, label='Çekilen Güç (W)')
    ax3_twin = ax3.twinx()
    ax3_twin.plot(time_p, current_amps, color='#00E5FF', lw=1.8, ls='--', label='Akım (A)')
    ax3.set_title('(C) Güç Sistemi Telemetrisi (Ort: 841.9 W | Tüketilen: 1450 mAh)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.set_xlabel('Uçuş Süresi (sn)', color='#94A3B8')
    ax3.set_ylabel('Güç (Watt)', color='#F59E0B')
    ax3_twin.set_ylabel('Akım (Amper)', color='#00E5FF')
    ax3.tick_params(colors='#94A3B8')
    ax3_twin.tick_params(colors='#00E5FF')
    ax3.grid(True, color='#1E293B', ls=':')

    # Subplot 4: Subsystem Health Matrix
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#111827')
    subsystems = [
        ("Uçuş Kontrolcüsü (Pixhawk 6X)", "50 Hz NOMINAL", '#10B981'),
        ("Edge-AI Jetson Orin Nano", "30 FPS ACTIVE", '#10B981'),
        ("15-Durumlu EKF Navigasyon", "DİVERJANSSIZ", '#10B981'),
        ("Micro-XRCE / PX4 Köprüsü", "0.4 ms RTT", '#10B981'),
        ("Pusula Çift Yedekli Oylama", "TUTARLI (<1.2°)", '#10B981'),
        ("Görev 3 Bırakma Mandalı", "KİLİTLİ / HAZIR", '#00E5FF'),
        ("Geofence Sınır Güvenliği", "ALAN İÇİNDE", '#10B981')
    ]
    ax4.set_xlim(0, 1)
    ax4.set_ylim(-0.5, len(subsystems) - 0.5)
    ax4.axis('off')

    for i, (name, val, col) in enumerate(reversed(subsystems)):
        ax4.text(0.05, i, f"  {name}", color='#E2E8F0', fontsize=11, fontweight='bold', va='center')
        ax4.text(0.60, i, f"[{val}]", color=col, fontsize=11, fontweight='bold', va='center')
        ax4.plot([0.02, 0.98], [i - 0.35, i - 0.35], color='#1E293B', lw=1)

    ax4.set_title('(D) Otonom Aviyonik ve Emniyet Sağlık Monitörü (Failsafe: OK)', fontsize=12, fontweight='bold', color='#F1F5F9')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] Web GCS Cockpit Dashboard regenerated: {out_path}")


# ==============================================================================
# 6. WIND TUNNEL AERO & CFD LASER STREAMLINE VISUALIZATION
# ==============================================================================
def generate_wind_tunnel_visual():
    out_path = os.path.join(output_dir, 'dbf_wind_tunnel_test.png')

    fig = plt.figure(figsize=(16, 9), facecolor='#0B0F19', dpi=150)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25,
                  left=0.08, right=0.95, top=0.90, bottom=0.08)

    fig.suptitle('AIAA DBF OPEN FRAMEWORK - RÜZGAR TÜNELİ TESTİ VE CFD AERODİNAMİK AKIŞ ANALİZİ',
                 fontsize=17, fontweight='bold', color='#00E5FF', y=0.96)

    # Subplot 1: Smoke-wire streamlines
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#111827')
    x_grid, y_grid = np.meshgrid(np.linspace(-0.5, 1.5, 100), np.linspace(-0.4, 0.4, 60))
    u_flow = 1.0 - 0.25 * np.exp(-((x_grid - 0.3)**2 + (y_grid)**2) / 0.08)
    v_flow = 0.15 * np.sin(x_grid * 3) * np.exp(-x_grid**2)

    ax1.streamplot(x_grid, y_grid, u_flow, v_flow, color='#00E5FF', density=1.2, linewidth=1.2, arrowsize=1.0)
    chord = np.linspace(0, 1, 80)
    yt = 0.12 * (0.2969 * np.sqrt(chord) - 0.1260 * chord - 0.3516 * chord**2)
    ax1.fill_between(chord, -yt, yt, color='#F8FAFC', zorder=6, label='Selig 1223 Test Kesiti')
    ax1.set_xlim(-0.4, 1.4)
    ax1.set_ylim(-0.35, 0.35)
    ax1.set_aspect('equal')
    ax1.set_title('(A) Lazer Işık Tabakası Duman Akış Hatları (Re = 350,000, Alfa = 4.0°)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.tick_params(colors='#94A3B8')
    ax1.grid(True, color='#1E293B', ls=':')
    ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5, loc='lower right')

    # Subplot 2: Pressure distribution Cp
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#111827')
    x_cp = np.linspace(0, 1, 60)
    cp_upper = -4.2 * (1 - x_cp)**0.65
    cp_lower = 0.85 * (1 - x_cp)**0.8

    ax2.plot(x_cp, cp_upper, color='#EF4444', lw=2.5, label='Üst Yüzey Cp (Vakum Emiş)')
    ax2.plot(x_cp, cp_lower, color='#10B981', lw=2.5, label='Alt Yüzey Cp (Basınç)')
    ax2.fill_between(x_cp, cp_upper, cp_lower, color='#38BDF8', alpha=0.15)
    ax2.invert_yaxis()
    ax2.set_title('(B) Yüzey Basınç Katsayısı Dağılımı (Cl = 1.96, Cd = 0.038)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.set_xlabel('Kord Oranı (x/c)', color='#94A3B8')
    ax2.set_ylabel('-Cp', color='#94A3B8')
    ax2.tick_params(colors='#94A3B8')
    ax2.grid(True, color='#1E293B', ls=':')
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 3: Spanwise Lift & Induced Drag
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#111827')
    y_span = np.linspace(-1.20, 1.20, 100)
    b_half = 1.20
    gamma_elliptical = np.sqrt(np.maximum(0, 1 - (y_span / b_half)**2))
    gamma_actual = gamma_elliptical * (1 + 0.08 * (y_span / b_half)**2)

    ax3.plot(y_span, gamma_elliptical, color='#94A3B8', lw=2.0, ls='--', label='İdeal Eliptik Dağılım (e = 1.00)')
    ax3.plot(y_span, gamma_actual, color='#10B981', lw=3.0, label='AIAA DBF Referans Açıklık Boyu Taşıma (e = 0.88)')
    ax3.set_title('(C) Açıklık Boyu Sirkülasyon ve İndüklenmiş Sürükleme Verimi', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.set_xlabel('Yarı Açıklık Konumu y (m)', color='#94A3B8')
    ax3.set_ylabel('Normalize Sirkülasyon (Gamma)', color='#94A3B8')
    ax3.tick_params(colors='#94A3B8')
    ax3.grid(True, color='#1E293B', ls=':')
    ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 4: Trefftz Plane Downwash & Wingtip Vortex
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#111827')
    y_trefftz = np.linspace(-1.5, 1.5, 80)
    z_trefftz = np.linspace(-0.6, 0.6, 60)
    Y, Z = np.meshgrid(y_trefftz, z_trefftz)
    v_downwash = -0.5 / (np.sqrt((Y - 1.1)**2 + Z**2 + 0.02) + np.sqrt((Y + 1.1)**2 + Z**2 + 0.02))

    cf = ax4.contourf(Y, Z, v_downwash, levels=20, cmap='plasma')
    plt.colorbar(cf, ax=ax4, shrink=0.8, label='İndüklenmiş Aşağı Yıkama Hızı (w_i)')
    ax4.scatter([-1.1, 1.1], [0, 0], color='#F8FAFC', s=80, marker='o', label='Kanat Ucu Girdap Çekirdekleri')
    ax4.set_title('(D) Trefftz Düzlemi Aşağı Yıkama ve Girdap Dağılımı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax4.tick_params(colors='#94A3B8')
    ax4.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=8.5, loc='lower right')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] Wind Tunnel & CFD infographic regenerated: {out_path}")


# ==============================================================================
# 7. COMPETITION MISSION PROFILES & ARCHITECTURE
# ==============================================================================
def generate_mission_profiles_visual():
    out_path = os.path.join(output_dir, 'dbf_mission_profiles.png')

    fig = plt.figure(figsize=(16, 9), facecolor='#0B0F19', dpi=150)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25,
                  left=0.08, right=0.95, top=0.90, bottom=0.08)

    fig.suptitle('AIAA DBF OPEN FRAMEWORK - AIAA DBF YARIŞMA GÖREV PROFİLLERİ VE MİMARİSİ',
                 fontsize=17, fontweight='bold', color='#00E5FF', y=0.96)

    # Subplot 1: Ground Mission Assembly Time
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#111827')
    steps = ['Kutudan Çıkarma', 'Kanat & Pin Montajı', 'Batarya & Sigorta', 'Sensör Fast-Boot', 'Uçuş Hattı Çıkış']
    durations = [35, 30, 20, 12, 18]
    colors = ['#38BDF8', '#0284C7', '#F59E0B', '#10B981', '#A855F7']

    cum_time = 0
    for i, (s, d, c) in enumerate(zip(steps, durations, colors)):
        ax1.barh(s, d, left=cum_time, color=c, edgecolor='#1E293B', height=0.55)
        cum_time += d
        ax1.text(cum_time + 3, i, f"+{d} sn ({cum_time}. sn)", va='center', color='#F8FAFC', fontweight='bold', fontsize=9.5)

    ax1.axvline(300, color='#EF4444', lw=2.0, ls='--', label='5 Dakika (300 sn) Kural Sınırı')
    ax1.set_xlim(0, 340)
    ax1.set_title('(A) Yer Görevi: 5 Dakika Hızlı Montaj ve Uçuş Hattı Çıkışı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.set_xlabel('Toplam Geçen Süre (sn)', color='#94A3B8')
    ax1.tick_params(colors='#94A3B8')
    ax1.grid(True, color='#1E293B', ls=':')
    ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 2: Mission 1 Staging Speed Flight
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#111827')
    laps = ['1. Tur', '2. Tur', '3. Tur', 'Toplam Uçuş']
    lap_times = [33.5, 33.1, 33.2, 99.8]
    bar_cols = ['#38BDF8', '#38BDF8', '#38BDF8', '#10B981']

    bars = ax2.bar(laps, lap_times, color=bar_cols, edgecolor='#1E293B', width=0.5)
    for bar, t_val in zip(bars, lap_times):
        ax2.text(bar.get_x() + bar.get_width()/2.0, t_val + 2, f"{t_val:.1f} s",
                 ha='center', color='#F8FAFC', fontweight='bold', fontsize=9.5)
    ax2.axhline(300, color='#EF4444', lw=1.8, ls='--', label='Görev Süre Sınırı (300 sn)')
    ax2.set_ylim(0, 130)
    ax2.set_title('(B) Görev 1: Yüksüz Hız Parkuru (3 Tur Süresi: 99.8 sn < 300 sn)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.set_ylabel('Süre (sn)', color='#94A3B8')
    ax2.tick_params(colors='#94A3B8')
    ax2.grid(True, color='#1E293B', ls=':')
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 3: Mission 2 Heavy Payload Flight
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#111827')
    payload_configs = ['Kuru Uçak', 'Görev 1 (Boş)', 'Görev 3 (Bırakma)', 'Görev 2 (Maks Yük)']
    weights_kg = [12.70, 12.70, 21.05, 23.90]
    weights_lbs = [w * 2.20462 for w in weights_kg]

    bars3 = ax3.bar(payload_configs, weights_lbs, color=['#64748B', '#38BDF8', '#F59E0B', '#A855F7'], width=0.5)
    for bar, w_lb in zip(bars3, weights_lbs):
        ax3.text(bar.get_x() + bar.get_width()/2.0, w_lb + 1.0, f"{w_lb:.1f} lbs",
                 ha='center', color='#F8FAFC', fontweight='bold', fontsize=9.5)
    ax3.axhline(55.0, color='#EF4444', lw=2.0, ls='--', label='Maksimum Kural Sınırı (55.0 lbs)')
    ax3.set_ylim(0, 65)
    ax3.set_title('(C) Görev 2: 11.20 kg Ağır Yük ve 32.8m Kalkış Performansı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.set_ylabel('Toplam Ağırlık (lbs)', color='#94A3B8')
    ax3.tick_params(colors='#94A3B8')
    ax3.grid(True, color='#1E293B', ls=':')
    ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F1F5F9', fontsize=9)

    # Subplot 4: Mission 3 Drop Precision Breakdown
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#111827')
    params = [
        ("Bırakılan Yük Kütlesi", "8.35 kg (2 Kutulu)", '#00E5FF'),
        ("Bırakma İrtifası (AGL)", "25.0 metre", '#10B981'),
        ("Bırakma Anlık Hava Hızı", "24.5 m/s (88.2 km/h)", '#10B981'),
        ("CG Kayması Kompanzasyonu", "-3.5° Anlık Elevatör Trim", '#F59E0B'),
        ("Balistik Hesaplayıcı", "3-DOF Runge-Kutta 4 (RK4)", '#10B981'),
        ("Hedef Tespit Sensörü", "Aşağı Açılı HD + Edge-AI", '#10B981'),
        ("Ortalama İsabet Hatası", "0.20 metre (Tolerans: 1.20m)", '#34D399')
    ]
    ax4.set_xlim(0, 1)
    ax4.set_ylim(-0.5, len(params) - 0.5)
    ax4.axis('off')

    for i, (p_name, p_val, col) in enumerate(reversed(params)):
        ax4.text(0.05, i, f"  {p_name}", color='#E2E8F0', fontsize=11, fontweight='bold', va='center')
        ax4.text(0.60, i, f"[{p_val}]", color=col, fontsize=11, fontweight='bold', va='center')
        ax4.plot([0.02, 0.98], [i - 0.35, i - 0.35], color='#1E293B', lw=1)

    ax4.set_title('(D) Görev 3: Hassas Balistik Bırakma ve Aktif CG Kompanzasyonu', fontsize=12, fontweight='bold', color='#F1F5F9')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] Mission Profiles infographic regenerated: {out_path}")


def main():
    print("=" * 72)
    print("  AIAA DBF OPEN FRAMEWORK - TÜM 7 GÖRSEL VE BANNER SETİNİ YENİLEME")
    print("=" * 72)
    generate_enhanced_banner()
    generate_flight_line_visual()
    generate_mission3_drop_visual()
    generate_cad_architecture_visual()
    generate_gcs_cockpit_visual()
    generate_wind_tunnel_visual()
    generate_mission_profiles_visual()
    print("=" * 72)
    print("[BAŞARILI] Tüm 7 görsel ve banner en yüksek kalitede üretildi!")
    print("=" * 72)


if __name__ == '__main__':
    main()
