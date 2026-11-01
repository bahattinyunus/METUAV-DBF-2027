# 💨 METU Rüzgar Tüneli Test Planı ve Doğrulama Protokolü

Bu protokol, ODTÜ Havacılık ve Uzay Mühendisliği Bölümü Rüzgar Tüneli tesislerinde METUAV DBF 2027 ölçekli kanat modelinin ve gövde-kanat entegrasyonunun aerodinamik karakteristiklerini doğrulamak için hazırlanmıştır.

---

## 1. Test Düzeneği ve Model Özellikleri

*   **Test Tesisi:** ODTÜ Rüzgar Tüneli (Kapalı çevrim, 1.0m x 1.0m test odası).
*   **Model Ölçeği:** 1:2 Yarı-Açıklık (Semi-span) Kanat Modeli (Açıklık: 1.20 m, Kord: 0.32 m).
*   **Ölçüm Ekipmanları:**
    *   6-Bileşenli Dahili Yük Hücresi (Strain-gauge balance)
    *   32-Kanallı Yüzey Basınç Tarama Modülü (Scanivalve / ESP)
    *   Pitot-Statik Tüp ve Sayısal Mikro-Manometreler
    *   Yüzey akış görselleştirme için iplikçikler (tufts) ve duman teli (smoke-wire)

---

## 2. Test Matrisi ve Adımları

| Test No | Hız ($V_\infty$) | Reynolds Sayısı ($Re$) | Hücum Açısı Aralığı ($\alpha$) | Ölçülen Parametreler |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | 15 m/s | $2.2 \times 10^5$ | -4° ile +14° (1° adımlarla) | $C_L, C_D, C_m$ |
| **T-02** | 22 m/s | $3.5 \times 10^5$ (Seyir Rejimi) | -4° ile +14° (0.5° adımlarla) | $C_L, C_D, C_m$, Stall Açısı |
| **T-03** | 28 m/s | $4.5 \times 10^5$ (Maks Hız) | -2° ile +10° | Sürükleme kutbu ($C_D$ vs $C_L^2$) |
| **T-04** | 22 m/s | $3.5 \times 10^5$ | +8°, +10°, +12° | Yüzey İplikçikleri ile Ayrılma Görselleştirmesi |

---

## 3. Kabul Kriterleri (Pass/Fail Criteria)

1.  Deneysel $C_{L_{max}}$ değeri, CFD analizinde öngörülen 1.96 değerinin $\% \pm 5$ bandı içinde kalmalıdır.
2.  Perdövites (stall) davranışı yumuşak ve aşamalı olmalı; kanat kökünden başlayıp kanat ucuna doğru ilerlemelidir (Aileron etkinliğini korumak için).
3.  Sürükleme kutbundan elde edilen indüklenmiş sürükleme faktörü $e \ge 0.80$ olmalıdır.
