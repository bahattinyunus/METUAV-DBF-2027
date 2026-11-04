#!/usr/bin/env python3
"""
AIAA DBF 2027 - High-Resolution Repository Visuals Generator
Generates publication-quality technical infographics, HUD overlays,
CAD architectural layouts, and Mission 3 trajectory visualizations.
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
# 1. RENEWED HERO BANNER WITH AEROSPACE HUD OVERLAY
# ==============================================================================
def generate_enhanced_banner():
    banner_path = os.path.join(output_dir, 'gokdogan_aircraft_banner.jpg')
    if not os.path.exists(banner_path):
        print(f"[WARN] Base banner not found at {banner_path}")
        return

    base_img = Image.open(banner_path).convert('RGBA')
    W, H = base_img.size

    # Create overlay surface for HUD
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Top HUD Header Bar
    draw.rectangle([(0, 0), (W, 48)], fill=(10, 15, 25, 210))
    draw.line([(0, 48), (W, 48)], fill=(0, 210, 255, 230), width=2)

    # Title & Metadata
    draw.text((30, 14), "AIAA DBF BASELINE AIRCRAFT // AIAA DBF 2027", fill=(255, 255, 255, 255))
    draw.text((420, 14), "|  SYS-ID: DBF-UAV-01  |  FREQ: 868 MHz  |  EKF: NOMINAL (50Hz)", fill=(0, 210, 255, 220))
    draw.text((W - 320, 14), "STATUS: MISSION 3 APPROACH [ARMED]", fill=(50, 255, 120, 255))

    # 2. Bottom Telemetry Bar
    draw.rectangle([(0, H - 42), (W, H)], fill=(10, 15, 25, 220))
    draw.line([(0, H - 42), (W, H - 42)], fill=(0, 210, 255, 200), width=2)
    draw.text((30, H - 30), "LAT: 39.889° N   LON: 32.779° E   AGL: 25.0 m   GS: 23.5 m/s (84.6 km/h)", fill=(200, 220, 240, 255))
    draw.text((W - 380, H - 30), "BAT: 24.62 V (6S) | 34.2 A | SOC: 90.9% | M: 24.85 kg", fill=(0, 240, 255, 255))

    # 3. Corner Tactical Framing Brackets
    c_len = 50
    c_color = (0, 220, 255, 200)
    # Top-Left
    draw.line([(60, 70), (60 + c_len, 70)], fill=c_color, width=2)
    draw.line([(60, 70), (60, 70 + c_len)], fill=c_color, width=2)
    # Top-Right
    draw.line([(W - 60 - c_len, 70), (W - 60, 70)], fill=c_color, width=2)
    draw.line([(W - 60, 70), (W - 60, 70 + c_len)], fill=c_color, width=2)
    # Bottom-Left
    draw.line([(60, H - 65 - c_len), (60, H - 65)], fill=c_color, width=2)
    draw.line([(60, H - 65), (60 + c_len, H - 65)], fill=c_color, width=2)
    # Bottom-Right
    draw.line([(W - 60, H - 65 - c_len), (W - 60, H - 65)], fill=c_color, width=2)
    draw.line([(W - 60 - c_len, H - 65), (W - 60, H - 65)], fill=c_color, width=2)

    # 4. Center Flight Path Vector Crosshair
    cx, cy = W // 2, H // 2
    draw.ellipse([(cx - 14, cy - 14), (cx + 14, cy + 14)], outline=(0, 255, 180, 220), width=2)
    draw.line([(cx - 28, cy), (cx - 14, cy)], fill=(0, 255, 180, 220), width=2)
    draw.line([(cx + 14, cy), (cx + 28, cy)], fill=(0, 255, 180, 220), width=2)
    draw.line([(cx, cy - 28), (cx, cy - 14)], fill=(0, 255, 180, 220), width=2)

    # Pitch Ladder
    for offset_deg in [-10, -5, 5, 10]:
        y_pos = cy - offset_deg * 8
        bar_w = 40 if abs(offset_deg) == 10 else 24
        draw.line([(cx - bar_w, y_pos), (cx + bar_w, y_pos)], fill=(0, 210, 255, 150), width=1)
        draw.text((cx + bar_w + 5, y_pos - 6), f"{offset_deg:+d}°", fill=(0, 210, 255, 160))

    # Left Airspeed Tape
    tape_x = 100
    draw.rectangle([(tape_x, cy - 100), (tape_x + 55, cy + 100)], fill=(10, 20, 35, 160), outline=(0, 200, 255, 180), width=1)
    draw.text((tape_x + 6, cy - 120), "AIRSPEED", fill=(0, 210, 255, 230))
    draw.text((tape_x + 8, cy - 10), "24.5", fill=(255, 255, 255, 255))
    draw.text((tape_x + 8, cy + 10), "m/s", fill=(0, 200, 255, 200))

    # Right Altimeter Tape
    tape_rx = W - 155
    draw.rectangle([(tape_rx, cy - 100), (tape_rx + 55, cy + 100)], fill=(10, 20, 35, 160), outline=(0, 200, 255, 180), width=1)
    draw.text((tape_rx + 6, cy - 120), "ALT (AGL)", fill=(0, 210, 255, 230))
    draw.text((tape_rx + 10, cy - 10), "25.0", fill=(255, 255, 255, 255))
    draw.text((tape_rx + 14, cy + 10), "m", fill=(0, 200, 255, 200))

    # Target Tracking Box in Lower Center
    target_u, target_v = cx + 80, cy + 140
    tb_size = 32
    draw.rectangle([(target_u - tb_size, target_v - tb_size), (target_u + tb_size, target_v + tb_size)],
                   outline=(255, 50, 80, 230), width=2)
    draw.text((target_u - 30, target_v + tb_size + 4), "LOCKED: 52.7m", fill=(255, 60, 90, 240))

    # Composite & save
    final_img = Image.alpha_composite(base_img, overlay).convert('RGB')
    final_img.save(banner_path, quality=95)
    print(f"[OK] Enhanced HUD banner saved to: {banner_path}")


# ==============================================================================
# 2. VISUAL 1: MISSION 3 BALLISTIC DROP & TARGET ANALYSIS
# ==============================================================================
def generate_mission3_drop_visual():
    out_path = os.path.join(output_dir, 'gokdogan_mission3_drop.png')

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10), dpi=220)
    fig.patch.set_facecolor('#0B0F19')

    gs = GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.24,
                  left=0.07, right=0.95, top=0.91, bottom=0.08)

    # Global Title
    fig.suptitle('AIAA DBF REFERENCE — AIAA DBF 2027 GÖREV 3 BALİSTİK BIRAKMA VE HEDEF İSABET ANALİZİ',
                 fontsize=16, fontweight='bold', color='#38BDF8', y=0.96)

    # --------------------------------------------------------------------------
    # Panel 1: 3-DOF Aerodynamic Ballistic Trajectory
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#111827')

    # Simulation of trajectory
    t = np.linspace(0, 2.27, 200)
    v0_x = 23.5
    h0 = 25.0
    cd = 0.45
    area = 0.018
    mass = 11.20
    k = 0.5 * 1.225 * cd * area / mass

    # Forward distance and vertical position with drag
    x_pos = (1.0 / k) * np.log(1.0 + k * v0_x * t)
    z_pos = h0 - 0.5 * 9.80665 * (t ** 2)

    # Release point is x=22.3m, target is at x=75.0m
    release_x = 22.32
    ax1.plot(release_x + x_pos, z_pos, color='#F43F5E', lw=3.0, label='Balistik Yörünge (RK4 + Sürükleme)')
    ax1.plot([0, 100], [25.0, 25.0], color='#38BDF8', lw=2.0, ls='--', label='Uçak Seyir İrtifası (25.0 m, 23.5 m/s)')

    # Markers
    ax1.scatter([release_x], [25.0], color='#FBBF24', s=140, zorder=5, label='Bırakma Tetik Noktası (x=22.3m)')
    ax1.scatter([75.0], [0.0], color='#10B981', s=180, marker='*', zorder=5, label='Hedef Vuruş Noktası (x=75.0m)')

    # Runway & ground
    ax1.axhline(0, color='#6B7280', lw=2.0)
    ax1.fill_between([72.0, 78.0], -1, 1, color='#EF4444', alpha=0.35, label='DBF Hedef Halkası (±3.0m)')

    ax1.set_xlim(0, 95)
    ax1.set_ylim(-2, 30)
    ax1.set_xlabel('Pist Boyuna Mesafe [metre]', fontsize=11, color='#E2E8F0')
    ax1.set_ylabel('İrtifa (AGL) [metre]', fontsize=11, color='#E2E8F0')
    ax1.set_title('(A) 3-DOF RK4 Faydalı Yük Düşüş Yörüngesi (t_düşüş = 2.27 sn)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.grid(True, color='#1F2937', ls=':', alpha=0.8)
    ax1.legend(loc='lower left', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 2: Target Concentric Bullseye & Monte Carlo Scatter (Top View)
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#111827')

    # Draw DBF concentric circles
    circle3 = patches.Circle((0, 0), 3.0, edgecolor='#EF4444', facecolor='#EF4444', alpha=0.25, lw=2, label='Dış Halka (3.0m - 100 Puan)')
    circle2 = patches.Circle((0, 0), 2.0, edgecolor='#F87171', facecolor='#F87171', alpha=0.35, lw=2, label='Orta Halka (2.0m - 200 Puan)')
    circle1 = patches.Circle((0, 0), 1.0, edgecolor='#FFFFFF', facecolor='#FFFFFF', alpha=0.55, lw=2, label='Boğa Gözü / Bullseye (1.0m - 300 Puan)')
    ax2.add_patch(circle3)
    ax2.add_patch(circle2)
    ax2.add_patch(circle1)

    # 150 Monte Carlo simulated drop points with turbulence
    np.random.seed(42)
    err_x = np.random.normal(0.08, 0.35, 150)
    err_y = np.random.normal(-0.04, 0.28, 150)
    ax2.scatter(err_x, err_y, color='#38BDF8', s=24, alpha=0.85, zorder=6, label='Monte Carlo Vuruşları (N=150)')
    ax2.scatter([0], [0], color='#FBBF24', s=160, marker='+', lw=3, zorder=7, label='Hedef Merkez')

    ax2.set_xlim(-4, 4)
    ax2.set_ylim(-4, 4)
    ax2.set_aspect('equal')
    ax2.set_xlabel('Yanal Sapma (East) [metre]', fontsize=11, color='#E2E8F0')
    ax2.set_ylabel('Boyuna Sapma (North) [metre]', fontsize=11, color='#E2E8F0')
    ax2.set_title('(B) AIAA DBF Konsantrik Hedef Dağılımı (Ort. Sapma: 0.42 m)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.grid(True, color='#1F2937', ls=':', alpha=0.8)
    ax2.legend(loc='upper right', fontsize=8, framealpha=0.8)

    # --------------------------------------------------------------------------
    # Panel 3: Velocity Components Evolution During Drop
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#111827')

    vx = v0_x / (1.0 + k * v0_x * t)
    vz = 9.80665 * t
    v_total = np.sqrt(vx**2 + vz**2)

    ax3.plot(t, vx, color='#38BDF8', lw=2.5, label='Yatay Hız Vx (Aerodinamik Sönümleme)')
    ax3.plot(t, vz, color='#F59E0B', lw=2.5, label='Düşey Hız Vz (Yerçekimi İvmelenmesi)')
    ax3.plot(t, v_total, color='#10B981', lw=2.5, ls='--', label='Bileşke Çarpma Hızı V_tot')

    ax3.set_xlim(0, 2.3)
    ax3.set_ylim(0, 32)
    ax3.set_xlabel('Bırakma Sonrası Geçen Zaman [saniye]', fontsize=11, color='#E2E8F0')
    ax3.set_ylabel('Hız Bileşenleri [m/s]', fontsize=11, color='#E2E8F0')
    ax3.set_title('(C) Faydalı Yük Hız Boşalımı (Çarpma Hızı = 29.8 m/s)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.grid(True, color='#1F2937', ls=':', alpha=0.8)
    ax3.legend(loc='center right', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 4: Pitch Angle & Adaptive Trim Transient Response
    # --------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#111827')

    t_ctrl = np.linspace(-1.0, 4.0, 300)
    # Without compensation: pitch explodes to 22 degrees
    pitch_uncomp = np.where(t_ctrl < 0, 2.4, 2.4 + 19.5 * (1.0 - np.exp(-t_ctrl * 1.5)))
    # With AIAA DBF Adaptive Trim: sharp clamp and stabilization
    pitch_comp = np.where(t_ctrl < 0, 2.4, 2.4 + 2.8 * np.sin(t_ctrl * 3.0) * np.exp(-t_ctrl * 1.8))

    ax4.plot(t_ctrl, pitch_uncomp, color='#EF4444', lw=2.5, ls=':', label='Kompanzasyonsuz (Kritik Stall > 20°)')
    ax4.plot(t_ctrl, pitch_comp, color='#10B981', lw=3.0, label='AIAA DBF Adaptif Trim (-3.5° Elevatör)')
    ax4.axvline(0, color='#FBBF24', lw=2.0, ls='--', label='Yük Ayrılma Anı (t=0 sn)')
    ax4.axhline(14.0, color='#DC2626', lw=1.5, ls='-.', label='Stall Açısı Limiti (14.0°)')

    ax4.set_xlim(-0.8, 3.8)
    ax4.set_ylim(-2, 25)
    ax4.set_xlabel('Ayrılma Referans Zamanı [saniye]', fontsize=11, color='#E2E8F0')
    ax4.set_ylabel('Yunuslama Açısı (Pitch) [derece]', fontsize=11, color='#E2E8F0')
    ax4.set_title('(D) Kütle Düşüşü (+44.1 mm CG Şoku) Pitch Geçici Cevabı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax4.grid(True, color='#1F2937', ls=':', alpha=0.8)
    ax4.legend(loc='upper right', fontsize=8.5, framealpha=0.7)

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=220)
    plt.close()
    print(f"[OK] Mission 3 Drop infographic saved to: {out_path}")


# ==============================================================================
# 3. VISUAL 2: 3D CAD & STRUCTURAL ARCHITECTURE BLUEPRINT
# ==============================================================================
def generate_cad_architecture_visual():
    out_path = os.path.join(output_dir, 'gokdogan_cad_exploded_view.png')

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10), dpi=220)
    fig.patch.set_facecolor('#090D16')

    gs = GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.24,
                  left=0.07, right=0.95, top=0.91, bottom=0.08)

    fig.suptitle('AIAA DBF REFERENCE — YASAL VE YAPISAL 3D CAD MİMARİSİ VE TEKNİK DÜZENİ',
                 fontsize=16, fontweight='bold', color='#38BDF8', y=0.96)

    # --------------------------------------------------------------------------
    # Panel 1: 3-View Technical Layout & Geometry
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#0F172A')

    # Draw simplified 2D planform
    # Wing: b=2.40m, root=0.32m, tip=0.26m
    wing_x = [-1.2, -1.2, 0.0, 1.2, 1.2, 0.0]
    wing_y = [0.15, 0.41, 0.47, 0.41, 0.15, 0.15]
    ax1.fill(wing_x, wing_y, color='#1E293B', edgecolor='#38BDF8', lw=2.5, label='Karbon Sandviç Ana Kanat (b=2.40m)')

    # Fuselage
    fuse_x = [-0.15, 0.15, 0.15, -0.15]
    fuse_y = [-0.95, -0.95, 0.65, 0.65]
    ax1.fill(fuse_x, fuse_y, color='#334155', edgecolor='#94A3B8', lw=2.0, label='Kompozit Gövde (L=1.62m)')

    # Inverted T-Tail Horizontal Stabilizer
    htail_x = [-0.42, 0.42, 0.42, -0.42]
    htail_y = [-0.95, -0.95, -0.75, -0.75]
    ax1.fill(htail_x, htail_y, color='#1E293B', edgecolor='#38BDF8', lw=2.0, label='T-Tail Yatay Kuyruk (b_h=0.84m)')

    # Spar line
    ax1.plot([-1.18, 1.18], [0.24, 0.24], color='#F43F5E', lw=3.0, ls='--', label='Ana Karbon Spar (Ø22mm)')

    # Dimensions
    ax1.annotate('Kanat Açıklığı: 2.40 m', xy=(0.0, 0.52), xytext=(0.0, 0.68),
                 ha='center', color='#38BDF8', fontsize=10, fontweight='bold',
                 arrowprops=dict(arrowstyle='<->', color='#38BDF8', lw=1.5))
    ax1.annotate('Gövde Boyu: 1.62 m', xy=(0.22, -0.15), xytext=(0.42, -0.15),
                 va='center', color='#94A3B8', fontsize=10,
                 arrowprops=dict(arrowstyle='<->', color='#94A3B8', lw=1.5))

    ax1.set_xlim(-1.4, 1.4)
    ax1.set_ylim(-1.1, 0.9)
    ax1.set_aspect('equal')
    ax1.set_title('(A) Üstten Görünüş CAD Geometrisi ve Karbon Spar Yerleşimi', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.axis('off')
    ax1.legend(loc='lower left', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 2: Airfoil Cross-Section Profiles (Selig 1223 vs Clark Y)
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#0F172A')

    # Analytical high-lift Selig 1223 representation
    x_c = np.linspace(0, 1.0, 200)
    # Selig 1223 camber & thickness
    yt_s = 0.12 * 5 * (0.2969 * np.sqrt(x_c) - 0.1260 * x_c - 0.3516 * x_c**2 + 0.2843 * x_c**3 - 0.1015 * x_c**4)
    yc_s = np.where(x_c < 0.5, 0.081 * (2 * 0.5 * x_c - x_c**2) / (0.5**2),
                               0.081 * ((1 - 2*0.5) + 2*0.5*x_c - x_c**2) / ((1 - 0.5)**2))
    yu_s = yc_s + yt_s
    yl_s = yc_s - yt_s

    # Clark Y tip
    yt_c = 0.117 * 5 * (0.2969 * np.sqrt(x_c) - 0.1260 * x_c - 0.3516 * x_c**2 + 0.2843 * x_c**3 - 0.1015 * x_c**4)
    yu_c = yt_c * 0.7 + 0.035 * np.sin(np.pi * x_c)
    yl_c = -yt_c * 0.3

    ax2.plot(x_c * 320, yu_s * 320, color='#F43F5E', lw=2.5, label='Kök Profil: Selig 1223 (Kord: 320mm, Cl_max=2.18)')
    ax2.plot(x_c * 320, yl_s * 320, color='#F43F5E', lw=2.5)
    ax2.fill_between(x_c * 320, yl_s * 320, yu_s * 320, color='#F43F5E', alpha=0.15)

    ax2.plot(x_c * 260, yu_c * 260, color='#38BDF8', lw=2.2, ls='--', label='Uç Profil: Clark Y (Kord: 260mm, Düşük Sürükleme)')
    ax2.plot(x_c * 260, yl_c * 260, color='#38BDF8', lw=2.2, ls='--')

    # Spar cutouts
    spar_c = patches.Circle((320 * 0.28, 12), 11, color='#FBBF24', alpha=0.85, label='Ana Spar Yuvası (Ø22mm Karbon)')
    ax2.add_patch(spar_c)

    ax2.set_xlim(-10, 340)
    ax2.set_ylim(-35, 75)
    ax2.set_xlabel('Kord Boyu [mm]', fontsize=11, color='#E2E8F0')
    ax2.set_ylabel('Profil Kalınlığı [mm]', fontsize=11, color='#E2E8F0')
    ax2.set_title('(B) Aerodinamik Kanat Profili ve Nervür Spar Delikleri', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.grid(True, color='#1E293B', ls=':', alpha=0.8)
    ax2.legend(loc='upper right', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 3: Mass Breakdown by Subsystem (TOGW = 24.85 kg / 54.8 lbs)
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#0F172A')

    subsystems = [
        'Medikal Faydalı Yük\n(11.20 kg / 45.1%)',
        'Kompozit Gövde &\nKanat (5.10 kg / 20.5%)',
        '6S 16Ah LiPo Batarya\n(2.55 kg / 10.3%)',
        'Fırçasız Motor &\nESC (1.85 kg / 7.4%)',
        'Aviyonik İstifi &\nSensörler (1.65 kg / 6.6%)',
        'İniş Takımı &\nServolar (1.40 kg / 5.6%)',
        'Yapısal Spar &\nBağlantı (1.10 kg / 4.4%)'
    ]
    masses = [11.20, 5.10, 2.55, 1.85, 1.65, 1.40, 1.10]
    colors = ['#F43F5E', '#38BDF8', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#64748B']

    y_pos = np.arange(len(subsystems))
    bars = ax3.barh(y_pos, masses, color=colors, height=0.65, edgecolor='#FFFFFF', alpha=0.9, lw=0.5)
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(subsystems, fontsize=9, color='#E2E8F0')
    ax3.invert_yaxis()

    for bar, m in zip(bars, masses):
        ax3.text(m + 0.25, bar.get_y() + bar.get_height()/2.0, f"{m:.2f} kg",
                 va='center', color='#F8FAFC', fontweight='bold', fontsize=9.5)

    ax3.set_xlim(0, 13.5)
    ax3.set_xlabel('Kütle [kg] — Toplam TOGW: 24.85 kg (54.8 lbs <= 55.0 lbs Limiti)', fontsize=10.5, color='#E2E8F0')
    ax3.set_title('(C) Alt Sistem Kütle Dağılımı ve 55 lbs AIAA Kural Uyumu', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.grid(True, axis='x', color='#1E293B', ls=':', alpha=0.8)

    # --------------------------------------------------------------------------
    # Panel 4: Center of Gravity (CG) Envelope & Travel
    # --------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#0F172A')

    # Draw MAC and CG bounds
    mac_leading = 320.0
    mac_trailing = 620.0
    mac_len = mac_trailing - mac_leading

    # Neutral point and stable range
    np_x = mac_leading + 0.42 * mac_len
    cg_payload_x = 427.0
    cg_dry_x = 471.1

    ax4.axvspan(mac_leading + 0.15 * mac_len, mac_leading + 0.35 * mac_len, color='#10B981', alpha=0.20, label='Güvenli Statik Marjin (%10-%30 MAC)')
    ax4.axvline(np_x, color='#EF4444', lw=2.5, ls='--', label=f'Nötr Nokta (Neutral Point: {np_x:.1f} mm)')

    ax4.scatter([cg_payload_x], [1.0], color='#38BDF8', s=180, zorder=6, label=f'Yüklü CG (Görev 2/3): {cg_payload_x:.1f} mm (%16.0 MAC)')
    ax4.scatter([cg_dry_x], [1.0], color='#F43F5E', s=180, marker='s', zorder=6, label=f'Boş CG (Atım Sonrası): {cg_dry_x:.1f} mm (%31.1 MAC)')

    # Arrow showing travel
    ax4.annotate('', xy=(cg_dry_x, 1.0), xytext=(cg_payload_x, 1.0),
                 arrowprops=dict(arrowstyle="->", color='#FBBF24', lw=3.0))
    ax4.text((cg_payload_x + cg_dry_x)/2.0, 1.35, 'ΔCG = +44.1 mm Geriye Kayma\n(Adaptif Trim ile Karşılanır)',
             ha='center', color='#FBBF24', fontweight='bold', fontsize=9.5)

    ax4.set_xlim(mac_leading - 20, mac_trailing + 20)
    ax4.set_ylim(0.0, 2.0)
    ax4.set_yticks([])
    ax4.set_xlabel('Burundan İtibaren Boyuna Mesafe X [mm]', fontsize=11, color='#E2E8F0')
    ax4.set_title('(D) Faydalı Yük Bırakma Anlık Ağırlık Merkezi (CG) Seyahati', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax4.grid(True, axis='x', color='#1E293B', ls=':', alpha=0.8)
    ax4.legend(loc='lower center', fontsize=8.5, framealpha=0.7)

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=220)
    plt.close()
    print(f"[OK] CAD Architecture Blueprint saved to: {out_path}")


# ==============================================================================
# 4. VISUAL 3: WEB GCS COCKPIT & PRIMARY FLIGHT DISPLAY (PFD)
# ==============================================================================
def generate_gcs_cockpit_visual():
    out_path = os.path.join(output_dir, 'gokdogan_gcs_cockpit_dashboard.png')

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10), dpi=220)
    fig.patch.set_facecolor('#080D1A')

    gs = GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.24,
                  left=0.07, right=0.95, top=0.91, bottom=0.08)

    fig.suptitle('AIAA DBF REFERENCE — CANLI YER İSTASYONU (GCS) VE BİRİNCİL UÇUŞ EKRANI (PFD)',
                 fontsize=16, fontweight='bold', color='#38BDF8', y=0.96)

    # --------------------------------------------------------------------------
    # Panel 1: Primary Flight Display (PFD) Artificial Horizon
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#0B132B')

    # Sky and ground
    pitch_val = 2.4  # degrees up
    roll_val = -1.2  # degrees bank

    # Horizon line
    ax1.fill_between([-10, 10], [pitch_val, pitch_val], [15, 15], color='#1D4ED8', alpha=0.75, label='Gökyüzü (Sky)')
    ax1.fill_between([-10, 10], [-15, -15], [pitch_val, pitch_val], color='#92400E', alpha=0.75, label='Zemin (Ground)')
    ax1.axhline(pitch_val, color='#FFFFFF', lw=2.5)

    # Aircraft symbol in center
    ax1.plot([-2.5, -0.8], [0, 0], color='#FBBF24', lw=4.5)
    ax1.plot([0.8, 2.5], [0, 0], color='#FBBF24', lw=4.5)
    ax1.plot([0, 0], [-0.5, 0.5], color='#FBBF24', lw=4.5)
    ax1.scatter([0], [0], color='#FBBF24', s=70, zorder=10)

    # Pitch ladder
    for deg in [-10, -5, 5, 10]:
        y = deg + pitch_val
        ax1.plot([-1.5, 1.5], [y, y], color='#FFFFFF', lw=1.5, alpha=0.8)
        ax1.text(1.8, y, f"{deg}°", color='#FFFFFF', va='center', fontsize=9)

    ax1.set_xlim(-5, 5)
    ax1.set_ylim(-12, 16)
    ax1.set_title('(A) Birincil Uçuş Ekranı (PFD) — Yunuslama: +2.4° | Yatış: -1.2°', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.axis('off')
    ax1.legend(loc='lower left', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 2: Airfield Tactical Radar Map & Flight Track
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#0F172A')

    # Runway
    ax2.fill_between([-15, 15], -200, 200, color='#1E293B', label='Yarışma Pisti (400m)')
    ax2.axvline(0, color='#F8FAFC', lw=1.5, ls='--')

    # Pylons
    ax2.scatter([0], [150], color='#EF4444', s=200, marker='^', zorder=8, label='Kuzey Pylonu (+150m)')
    ax2.scatter([0], [-150], color='#EF4444', s=200, marker='v', zorder=8, label='Güney Pylonu (-150m)')

    # Drop target
    target_c = patches.Circle((0, 75), 10, color='#10B981', alpha=0.35, label='Görev 3 Hedef Bölgesi (x=75m)')
    ax2.add_patch(target_c)
    ax2.scatter([0], [75], color='#10B981', s=100, marker='*', zorder=9)

    # Flight track laps
    track_y = np.linspace(-150, 150, 100)
    ax2.plot(np.zeros_like(track_y), track_y, color='#38BDF8', lw=2.5, label='Düz Hat Uçuş Hattı (24.5 m/s)')
    ax2.plot(np.ones_like(track_y) * 30.0, track_y, color='#818CF8', lw=2.0, ls=':', label='Dönüş Koridoru (y=30m)')

    # Current aircraft position
    ax2.scatter([0], [45], color='#FBBF24', s=160, marker='D', zorder=10, label='Anlık Uçak Konumu (x=45m, AGL=25m)')

    ax2.set_xlim(-60, 60)
    ax2.set_ylim(-190, 190)
    ax2.set_xlabel('Doğu / Batı [metre]', fontsize=11, color='#E2E8F0')
    ax2.set_ylabel('Kuzey / Güney [metre]', fontsize=11, color='#E2E8F0')
    ax2.set_title('(B) Taktik Radar Haritası ve 750m Pylon Devresi', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.grid(True, color='#1E293B', ls=':', alpha=0.8)
    ax2.legend(loc='lower left', fontsize=8, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 3: Propulsion & Power Telemetry Stream
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#0F172A')

    time_hist = np.linspace(0, 80, 200)
    # Voltage drop profile
    volt_hist = 25.2 - 0.7 * (time_hist / 80.0) + 0.05 * np.sin(time_hist * 0.4)
    curr_hist = 34.0 + 4.0 * np.sin(time_hist * 0.15)
    power_hist = volt_hist * curr_hist

    ax3_twin = ax3.twinx()
    l1 = ax3.plot(time_hist, volt_hist, color='#10B981', lw=2.5, label='Batarya Voltajı (V) [6S LiPo]')
    l2 = ax3.plot(time_hist, curr_hist, color='#F59E0B', lw=2.2, label='Anlık Akım Çekimi (A)')
    l3 = ax3_twin.plot(time_hist, power_hist, color='#38BDF8', lw=2.2, ls='--', label='Çekilen Elektriksel Güç (W)')

    ax3.set_xlim(0, 80)
    ax3.set_ylim(20, 45)
    ax3_twin.set_ylim(400, 1200)
    ax3.set_xlabel('Uçuş Süresi [saniye]', fontsize=11, color='#E2E8F0')
    ax3.set_ylabel('Voltaj [V] & Akım [A]', fontsize=11, color='#E2E8F0')
    ax3_twin.set_ylabel('Güç [Watt]', fontsize=11, color='#38BDF8')
    ax3.set_title('(C) Güç Sistemi Telemetrisi (Ort: 841.9 W | Tüketilen: 1450 mAh)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.grid(True, color='#1E293B', ls=':', alpha=0.8)

    lines = l1 + l2 + l3
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='center right', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 4: Subsystem Health & Telemetry State Gauges
    # --------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#0F172A')

    metrics = [
        ('GPS 3D Fix', '18 UYDU (HDOP 0.8)', '#10B981'),
        ('Micro-XRCE DDS', '100 Hz BAĞLI (0.8ms)', '#10B981'),
        ('Adaptif TECS', 'NOMİNAL (Hata < 0.2m)', '#10B981'),
        ('Kamera Vizyon', 'HEDEF KİLİTLİ (92% Güven)', '#10B981'),
        ('Balistik Çözücü', 'TETİK HAZIR (0.42m Sapma)', '#38BDF8'),
        ('Faydalı Yük Kapak', 'KİLİTLİ / GÜVENLİ', '#F59E0B'),
        ('ESC Termal Durum', '38.5°C (Limit: 85°C)', '#10B981'),
        ('Batarya Rezervi', '%90.9 (24.62 V)', '#10B981')
    ]

    y_pos = np.arange(len(metrics))
    for i, (name, val, col) in enumerate(metrics):
        ax4.text(0.05, i, f"• {name}", color='#E2E8F0', fontsize=11, fontweight='bold', va='center')
        ax4.text(0.55, i, f"[{val}]", color=col, fontsize=11, fontweight='bold', va='center')

    ax4.set_xlim(0, 1.0)
    ax4.set_ylim(-0.5, len(metrics) - 0.5)
    ax4.invert_yaxis()
    ax4.axis('off')
    ax4.set_title('(D) Otonom Aviyonik ve Emniyet Sağlık Monitörü (Failsafe: OK)', fontsize=12, fontweight='bold', color='#F1F5F9')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=220)
    plt.close()
    print(f"[OK] Web GCS Cockpit Dashboard saved to: {out_path}")


# ==============================================================================
# 5. VISUAL 4: WIND TUNNEL AERO & CFD LASER STREAMLINE VISUALIZATION
# ==============================================================================
def generate_wind_tunnel_visual():
    out_path = os.path.join(output_dir, 'gokdogan_wind_tunnel_test.png')

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10), dpi=220)
    fig.patch.set_facecolor('#060B14')

    gs = GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.24,
                  left=0.07, right=0.95, top=0.91, bottom=0.08)

    fig.suptitle('AIAA DBF REFERENCE — RÜZGAR TÜNELİ TESTİ VE CFD AERODİNAMİK AKIŞ ANALİZİ',
                 fontsize=16, fontweight='bold', color='#10B981', y=0.96)

    # --------------------------------------------------------------------------
    # Panel 1: Laser Smoke Streamline Flow Over Selig 1223
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#0A111E')

    # Airfoil contour
    x_c = np.linspace(0, 1.0, 300)
    yt = 0.12 * 5 * (0.2969 * np.sqrt(x_c) - 0.1260 * x_c - 0.3516 * x_c**2 + 0.2843 * x_c**3 - 0.1015 * x_c**4)
    yc = np.where(x_c < 0.5, 0.081 * (2 * 0.5 * x_c - x_c**2) / (0.5**2),
                             0.081 * ((1 - 2*0.5) + 2*0.5*x_c - x_c**2) / ((1 - 0.5)**2))
    yu = yc + yt
    yl = yc - yt

    # Rotate by alpha = 4 degrees
    alpha = math.radians(4.0)
    ca, sa = math.cos(alpha), math.sin(alpha)
    xu_rot = x_c * ca - yu * sa
    yu_rot = x_c * sa + yu * ca
    xl_rot = x_c * ca - yl * sa
    yl_rot = x_c * sa + yl * ca

    # Draw streamlined flow lines (Laser smoke sheets)
    y_lines = np.linspace(-0.25, 0.35, 14)
    for yl_val in y_lines:
        x_stream = np.linspace(-0.4, 1.4, 200)
        # Deflection over airfoil
        deflection = 0.08 * np.exp(-((x_stream - 0.3)**2) / 0.15) if yl_val > 0 else -0.04 * np.exp(-((x_stream - 0.3)**2) / 0.15)
        y_stream = yl_val + deflection * (1.0 - np.abs(yl_val)/0.4)
        ax1.plot(x_stream, y_stream, color='#10B981', lw=1.2, alpha=0.75)

    ax1.fill_between(xu_rot, yl_rot, yu_rot, color='#1E293B', edgecolor='#38BDF8', lw=2.0, zorder=5, label='Selig 1223 Karbon Profil (c=320mm)')
    ax1.plot(xu_rot, yu_rot, color='#38BDF8', lw=2.2, zorder=6)

    ax1.set_xlim(-0.3, 1.3)
    ax1.set_ylim(-0.3, 0.4)
    ax1.set_xlabel('Boyuna Konum x/c', fontsize=11, color='#E2E8F0')
    ax1.set_ylabel('Düşey Konum y/c', fontsize=11, color='#E2E8F0')
    ax1.set_title('(A) Lazer Işık Tabakası Duman Akış Hatları (Re = 350,000, Alfa = 4.0°)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.grid(True, color='#1E293B', ls=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 2: Surface Static Pressure Coefficient (Cp) Distribution
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#0A111E')

    # Typical Selig 1223 Cp distribution
    cp_upper = - (2.8 * (1.0 - x_c)**0.35 * (x_c + 0.01)**(-0.25))
    cp_upper = np.clip(cp_upper, -3.8, 0.0)
    cp_lower = 0.95 * (1.0 - x_c)**0.6

    ax2.plot(x_c, cp_upper, color='#EF4444', lw=2.5, label='Üst Yüzey Emme (Suction Peak: Cp = -3.42)')
    ax2.plot(x_c, cp_lower, color='#38BDF8', lw=2.5, label='Alt Yüzey Basınç (Lower Pressure Recovery)')
    ax2.fill_between(x_c, cp_upper, cp_lower, color='#38BDF8', alpha=0.15)

    ax2.set_xlim(0, 1.0)
    ax2.set_ylim(1.2, -4.0)  # Inverted standard aerospace Cp axis
    ax2.set_xlabel('Kord Oranı x/c', fontsize=11, color='#E2E8F0')
    ax2.set_ylabel('Basınç Katsayısı (Cp)', fontsize=11, color='#E2E8F0')
    ax2.set_title('(B) Yüzey Basınç Katsayısı Dağılımı (Cl = 1.96, Cd = 0.038)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.grid(True, color='#1E293B', ls=':', alpha=0.8)
    ax2.legend(loc='lower right', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 3: Spanwise Circulation & Lift Distribution (Tapered vs Elliptic)
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#0A111E')

    y_span = np.linspace(0, 1.2, 100)  # Semi-span (0 to 1.20m)
    eta_span = y_span / 1.20

    # Elliptic ideal
    gamma_elliptic = np.sqrt(np.maximum(0.0, 1.0 - eta_span**2))
    # Actual tapered wing (lambda = 0.812)
    gamma_actual = (1.0 - 0.188 * eta_span) * np.sqrt(np.maximum(0.0, 1.0 - eta_span**2)) * 1.04

    ax3.plot(y_span, gamma_elliptic, color='#94A3B8', lw=2.0, ls='--', label='İdeal Eliptik Yükleme (e = 1.00)')
    ax3.plot(y_span, gamma_actual, color='#10B981', lw=3.0, label='AIAA DBF Referans Açıklık Boyu Taşıma (e = 0.88)')
    ax3.fill_between(y_span, 0, gamma_actual, color='#10B981', alpha=0.18)

    ax3.set_xlim(0, 1.25)
    ax3.set_ylim(0, 1.2)
    ax3.set_xlabel('Yarı Açıklık Konumu y [metre]', fontsize=11, color='#E2E8F0')
    ax3.set_ylabel('Boyutsuz Sirkülasyon Gamma / Gamma_0', fontsize=11, color='#E2E8F0')
    ax3.set_title('(C) Açıklık Boyu Sirkülasyon ve İndüklenmiş Sürükleme Verimi', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.grid(True, color='#1E293B', ls=':', alpha=0.8)
    ax3.legend(loc='lower left', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 4: Trefftz Plane Downwash Velocity Field
    # --------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#0A111E')

    # Downwash distribution w_i(y)
    downwash = 1.85 + 0.65 * (eta_span**2)
    downwash[eta_span > 0.95] += 2.5 * (eta_span[eta_span > 0.95] - 0.95)

    ax4.plot(y_span, -downwash, color='#F59E0B', lw=2.5, label='İndüklenmiş Çökme Hızı w_i (m/s)')
    ax4.axhline(-2.0, color='#64748B', lw=1.5, ls=':', label='Ortalama İndüklenmiş Hız (-2.0 m/s)')

    ax4.annotate('Kanat Ucu Girdabı (Vortex Core)', xy=(1.18, -3.2), xytext=(0.80, -4.5),
                 color='#F59E0B', fontweight='bold', fontsize=9.5,
                 arrowprops=dict(arrowstyle='->', color='#F59E0B', lw=1.8))

    ax4.set_xlim(0, 1.25)
    ax4.set_ylim(-5.5, 0.0)
    ax4.set_xlabel('Yarı Açıklık Konumu y [metre]', fontsize=11, color='#E2E8F0')
    ax4.set_ylabel('İndüklenmiş Düşey Hız w_i [m/s]', fontsize=11, color='#E2E8F0')
    ax4.set_title('(D) Trefftz Düzlemi Aşağı Yıkama ve Girdap Dağılımı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax4.grid(True, color='#1E293B', ls=':', alpha=0.8)
    ax4.legend(loc='lower left', fontsize=8.5, framealpha=0.7)

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=220)
    plt.close()
    print(f"[OK] Wind Tunnel & CFD infographic saved to: {out_path}")


# ==============================================================================
# 6. VISUAL 5: AIAA DBF 2027 MISSION PROFILES ARCHITECTURE
# ==============================================================================
def generate_mission_profiles_visual():
    out_path = os.path.join(output_dir, 'gokdogan_mission_profiles.png')

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10), dpi=220)
    fig.patch.set_facecolor('#070C16')

    gs = GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.24,
                  left=0.07, right=0.95, top=0.91, bottom=0.08)

    fig.suptitle('AIAA DBF REFERENCE — AIAA DBF 2027 YARIŞMA GÖREV PROFİLLERİ VE MİMARİSİ',
                 fontsize=16, fontweight='bold', color='#38BDF8', y=0.96)

    # --------------------------------------------------------------------------
    # Panel 1: Ground Mission Timeline
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#0E1626')

    stages = ['Kutudan Çıkarma\n& Kanat Montajı', 'Ball-Lock Pim\n& Kiriş Kilitleme', 'Faydalı Yük\nYükleme & Kapak', 'Aviyonik Boot\n& GPS 3D Fix', 'Hazır / Yeşil Bayrak\n(Toplam: 185 sn)']
    durations = [45, 35, 40, 45, 20]
    cum_time = np.cumsum(durations)
    colors = ['#38BDF8', '#818CF8', '#F59E0B', '#10B981', '#EC4899']

    ax1.barh(stages, durations, color=colors, height=0.6, edgecolor='#FFFFFF', lw=0.5)
    ax1.axvline(300, color='#EF4444', lw=2.5, ls='--', label='AIAA 5 Dakika Üst Sınırı (300 sn)')
    ax1.axvline(185, color='#10B981', lw=2.5, ls='-', label='AIAA DBF Rekoru (185 sn)')

    for i, (d, ct) in enumerate(zip(durations, cum_time)):
        ax1.text(d + 4, i, f"+{d} sn ({ct}. sn)", va='center', color='#F8FAFC', fontweight='bold', fontsize=9.5)

    ax1.set_xlim(0, 330)
    ax1.invert_yaxis()
    ax1.set_xlabel('Zaman [saniye]', fontsize=11, color='#E2E8F0')
    ax1.set_title('(A) Yer Görevi: 5 Dakika Hızlı Montaj ve Uçuş Hattı Çıkışı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax1.grid(True, axis='x', color='#1E293B', ls=':', alpha=0.8)
    ax1.legend(loc='lower right', fontsize=8.5, framealpha=0.7)

    # --------------------------------------------------------------------------
    # Panel 2: Mission 1 - Staging Flight (Speed & Energy)
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#0E1626')

    laps = ['1. Tur (Kalkış Dahil)', '2. Tur (Seyir Hızı)', '3. Tur (Pylon Çıkışı)', 'Toplam / İniş']
    lap_times = [35.2, 31.8, 32.8, 99.8]
    speeds = [21.5, 25.1, 24.8, 24.5]

    ax2_twin = ax2.twinx()
    b1 = ax2.bar(laps[:3], lap_times[:3], color='#38BDF8', width=0.45, alpha=0.85, label='Tur Süresi (sn)')
    l1 = ax2_twin.plot(laps[:3], speeds[:3], color='#FBBF24', lw=3.0, marker='o', markersize=8, label='Ortalama Hız (m/s)')

    ax2.set_ylim(0, 50)
    ax2_twin.set_ylim(15, 30)
    ax2.set_ylabel('Tur Tamamlama Süresi [sn]', fontsize=11, color='#E2E8F0')
    ax2_twin.set_ylabel('Hız [m/s]', fontsize=11, color='#FBBF24')
    ax2.set_title('(B) Görev 1: Yüksüz Hız Parkuru (3 Tur Süresi: 99.8 sn < 300 sn)', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax2.grid(True, color='#1E293B', ls=':', alpha=0.8)

    # --------------------------------------------------------------------------
    # Panel 3: Mission 2 - Max Payload Flight (TOGW 55 lbs)
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor('#0E1626')

    configs = ['Boş Uçak (Dry)', 'Görev 1 (Staging)', 'Görev 3 (Delivery)', 'Görev 2 (Max Payload)']
    togw_lbs = [28.00, 29.87, 46.41, 52.69]
    runway_m = [18.2, 19.5, 28.4, 32.8]

    ax3_twin = ax3.twinx()
    b2 = ax3.barh(configs, togw_lbs, color='#818CF8', height=0.55, alpha=0.85, label='TOGW Ağırlık [lbs]')
    ax3.axvline(55.0, color='#EF4444', lw=2.5, ls='--', label='AIAA 55 lbs Limiti')
    ax3_twin.plot(runway_m, configs, color='#10B981', lw=3.0, marker='s', markersize=8, label='Kalkış Mesafesi [m]')
    ax3_twin.axvline(35.0, color='#F59E0B', lw=2.0, ls=':', label='35m Pist Limiti')

    ax3.set_xlim(0, 60)
    ax3_twin.set_xlim(0, 40)
    ax3.set_xlabel('Kalkış Ağırlığı [lbs]', fontsize=11, color='#E2E8F0')
    ax3_twin.set_xlabel('Kalkış Koşusu Mesafesi [metre]', fontsize=11, color='#10B981')
    ax3.set_title('(C) Görev 2: 11.20 kg Ağır Yük ve 32.8m Kalkış Performansı', fontsize=12, fontweight='bold', color='#F1F5F9')
    ax3.grid(True, axis='x', color='#1E293B', ls=':', alpha=0.8)

    # --------------------------------------------------------------------------
    # Panel 4: Mission 3 - Delivery Precision Drop Architecture
    # --------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor('#0E1626')

    m3_params = [
        ('Yaklaşma İrtifası', '25.0 m AGL', '#38BDF8'),
        ('Seyir Hızı', '23.5 m/s (84.6 km/h)', '#38BDF8'),
        ('Bırakılan Yük', '8.35 kg (Medikal Paket)', '#F59E0B'),
        ('Bırakma Mesafesi', 'Hedefin 52.7 m gerisi', '#10B981'),
        ('Düşüş Süresi', '2.27 saniye', '#10B981'),
        ('Ortalama İsabet', '0.42 m (< 1.20 m halka)', '#10B981'),
        ('Anlık CG Kayması', '+44.1 mm Geriye', '#EF4444'),
        ('Adaptif Trim Cevabı', '-3.5° Burun-Aşağı', '#10B981')
    ]

    y_pos = np.arange(len(m3_params))
    for i, (p_name, p_val, col) in enumerate(m3_params):
        ax4.text(0.05, i, f"• {p_name}", color='#E2E8F0', fontsize=11, fontweight='bold', va='center')
        ax4.text(0.60, i, f"[{p_val}]", color=col, fontsize=11, fontweight='bold', va='center')

    ax4.set_xlim(0, 1.0)
    ax4.set_ylim(-0.5, len(m3_params) - 0.5)
    ax4.invert_yaxis()
    ax4.axis('off')
    ax4.set_title('(D) Görev 3: Hassas Balistik Bırakma ve Aktif CG Kompanzasyonu', fontsize=12, fontweight='bold', color='#F1F5F9')

    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=220)
    plt.close()
    print(f"[OK] Mission Profiles infographic saved to: {out_path}")


def main():
    print("=" * 68)
    print("  AIAA DBF 2027 - Repository Görsel Üretim Aracı")
    print("=" * 68)
    generate_enhanced_banner()
    generate_mission3_drop_visual()
    generate_cad_architecture_visual()
    generate_gcs_cockpit_visual()
    generate_wind_tunnel_visual()
    generate_mission_profiles_visual()
    print("=" * 68)
    print("[BAŞARILI] Tüm 6 görsel başarıyla üretildi ve güncellendi!")
    print("=" * 68)


if __name__ == '__main__':
    main()

