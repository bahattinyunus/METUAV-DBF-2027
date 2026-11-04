# 🌪️ AIAA DBF 2027 Aerodinamik Tasarım ve CFD Analiz Raporu (Referans Platform)

Bu doküman, AIAA Design/Build/Fly 2027 yarışması kuralları ve tasarım raporu (Design Report) isterlerine uygun olarak hazırlanmış aerodinamik analiz bulgularını içerir.

---

## 1. Aerodinamik Tasarım Hedefleri ve İsterler

AIAA DBF 2027 yarışma isterlerine göre aerodinamik tasarım aşağıdaki kritik hedefleri karşılamak zorundadır:

1.  **Ağır Faydalı Yük Taşıma (Görev 2 & Görev 3):** Maksimum kalkış ağırlığı olan 55 lbs (24.85 kg) sınırında kısa kalkış mesafesi ($S_{TO} \le 35\text{ m}$) elde etmek için yüksek maksimum taşıma katsayısı ($C_{L_{max}} \ge 1.9$).
2.  **Düşük İndüklenmiş Sürükleme (Görev 1):** Yüksüz 3 tam tur uçuşunda 5 dakikalık süre içinde yüksek ortalama hız ($V \ge 28\text{ m/s}$) ve yüksek batarya verimliliği için optimize edilmiş narinlik oranı ($AR = 8.19$).
3.  **Yük Bırakma Kararlılığı (Görev 3):** Gövde altı kapağından 11.2 kg faydalı yükün bırakıldığı andaki ani aerodinamik moment değişiminde kontrol otoritesini kaybetmeyecek boyuna statik marjin ($\text{Static Margin} \ge 12\% \text{ MAC}$).

---

## 2. Kanat Profili (Airfoil) Seçim Matrisi

Farklı hücum açılarında ve $Re = 3.5 \times 10^5$ akış rejiminde aday profiller XFLR5 ve ANSYS Fluent ile karşılaştırılmıştır:

| Profil | $C_{l_{max}}$ (2D) | $(C_l/C_d)_{max}$ | $\alpha_{stall}$ | Üretim Kolaylığı | Değerlendirme Puanı | Karar |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Selig 1223** | **2.23** | **68.4** | **11.0°** | Orta (İnce firar kenarı) | **9.4 / 10** | **SEÇİLDİ (Ana Kanat)** |
| Eppler 423 | 1.95 | 61.2 | 12.5° | İyi | 8.2 / 10 | Yedek |
| NACA 4412 | 1.48 | 54.0 | 14.0° | Çok İyi | 6.8 / 10 | Elendi (Taşıma yetersiz) |
| Clark Y | 1.35 | 48.0 | 13.0° | Mükemmel | 7.5 / 10 | **Yatay Kuyruk Profili** |

*   **Ana Kanat:** Maksimum taşıma önceliği nedeniyle kamberli yüksek taşıyıcı **Selig 1223** seçilmiştir.
*   **Yatay ve Düşey Kuyruk:** Simetrik ve düşük momentli davranış sergileyen düz alt yüzeyli **Clark Y / NACA 0009** profili seçilmiştir.

---

## 3. Kanat Geometrisi ve 3 Boyutlu Planform

*   **Kanat Açıklığı ($b$):** 2.40 m
*   **Kanat Alanı ($S$):** 0.7032 m²
*   **Narinlik Oranı ($AR$):** 8.19
*   **Ortalama Aerodinamik Kord ($\text{MAC}$):** 0.293 m
*   **Kök Kordu ($c_{root}$):** 0.320 m
*   **Uç Kordu ($c_{tip}$):** 0.260 m
*   **Sivrilme Oranı ($\lambda$):** 0.812 (Eliptik yüke yakın indüklenmiş sürükleme optimizasyonu)
*   **Dihedral Açısı:** +2.0° (Yanal spiral stabilite katkısı)
*   **Ok Açısı ($\Lambda_{LE}$):** 1.5°

---

## 4. Sayısal Hesaplamalı Akışkanlar Dinamiği (CFD) Analizi

### 4.1 Hesaplama Ağı ve Sınır Şartları
*   **Yazılım:** ANSYS Fluent 2024 / OpenFOAM v2312
*   **Türbülans Modeli:** $k-\omega\text{ SST}$ (Transitional Low-Reynolds $y^+ < 1$ sınır katman prizmatik şişirme katmanları, 18 katman, 1.15 büyüme oranı).
*   **Hücre Sayısı:** 7.85 Milyon polihedral hücre (Ağ bağımsızlık çalışması ile doğrulanmıştır).
*   **Giriş Sınır Şartı (Velocity Inlet):** $V_\infty = 24.0\text{ m/s}$, Türbülans şiddeti $\%0.5$.
*   **Çıkış Sınır Şartı (Pressure Outlet):** $P_{gauge} = 0\text{ Pa}$.

### 4.2 Analiz Sonuçları ve Aerodinamik Katsayılar

| Hücum Açısı ($\alpha$) | $C_L$ (3D) | $C_D$ (3D) | $L/D$ (3D) | $C_m$ ($0.25 \text{MAC}$) |
| :--- | :--- | :--- | :--- | :--- |
| **0.0°** | 0.62 | 0.038 | 16.32 | -0.165 |
| **2.0°** | 0.84 | 0.045 | 18.67 | -0.168 |
| **4.0°** | 1.12 | 0.058 | 19.31 | -0.170 |
| **6.0°** | **1.38** | **0.076** | **18.15** | **-0.169** |
| **8.0°** | 1.62 | 0.101 | 16.04 | -0.164 |
| **10.0°** | 1.84 | 0.138 | 13.33 | -0.155 |
| **11.5° (Stall)** | **1.96** | **0.185** | **10.59** | **-0.138** |

---

## 5. Uçuş Dinamiği ve Kararlılık Türevleri

Uçağın boyuna ve yanal kararlılık katsayıları Roskam ve DATCOM yöntemleriyle hesaplanmıştır:

*   **Boyuna Kararlılık:** $C_{m_\alpha} = -0.024\text{ rad}^{-1} < 0$ (Doğal boyuna kararlılık sağlanmıştır).
*   **Yanal Yuvarlanma Kararlılığı:** $C_{l_\beta} = -0.068\text{ rad}^{-1} < 0$ (+2° dihedral ile güçlü dihedral etkisi).
*   **Düşey Doğrultu Kararlılığı (Weathercock):** $C_{n_\beta} = +0.082\text{ rad}^{-1} > 0$ (Geniş düşey fin sayesinde mükemmel doğrultu tutuşu).
*   **Elevatör Etkinliği:** $C_{m_{\delta_e}} = -0.032\text{ deg}^{-1}$.

Bu aerodinamik türevler, `aviyonik_ve_otonom/src/ucus_kontrol` paketindeki adaptif PID kontrolcüsüne doğrudan aktarılmış ve simülasyonda doğrulanmıştır.
