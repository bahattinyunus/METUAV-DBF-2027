# ⚡ AIAA DBF 2027 Elektrik İtki ve Güç Sistemleri Tasarım Raporu

Bu doküman, AIAA Design/Build/Fly 2027 yarışması isterlerine göre uçağın elektrik motoru, elektronik hız kontrolcüsü (ESC), batarya kimyası ve güç dağıtım mimarisinin mühendislik seçim kriterlerini belgeler.

---

## 1. Fırçasız Motor Seçim Matrisi

Maksimum kalkış ağırlığı olan $55\text{ lbs}$ ($24.85\text{ kg}$) konfigürasyonunda uçağın güvenli kalkış ve tırmanma yapabilmesi için minimum $1.8\text{ kW}$ sürekli güç ve $10\text{ kgf}$ statik itki gerekmektedir:

| Motor Modeli | $K_v$ (RPM/V) | Sürekli Güç | Maksimum Akım | Ağırlık | Statik İtki (6S) | Puan (10) | Karar |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Scorpion SII-4035-330** | **330** | **2400 W** | **95 A** | **465 g** | **12.5 kgf (19x12E)** | **9.6** | **SEÇİLDİ** |
| Hacker A50-16S V4 | 378 | 1950 W | 80 A | 435 g | 10.2 kgf (18x10E) | 8.4 | Yedek |
| T-Motor AT5230-25 | 300 | 2800 W | 105 A | 655 g | 13.8 kgf (20x10E) | 7.9 | Elendi (Aşırı ağır) |
| Dualsky GA2000.4 | 400 | 1800 W | 75 A | 410 g | 9.4 kgf (17x10E) | 7.2 | Elendi (İtki yetersiz) |

*   **Seçim Kararı:** Scorpion SII-4035-330KV motoru, yüksek tork katsayısı ($K_t \approx 0.0289\text{ N.m/A}$) sayesinde büyük çaplı ve yüksek hatveli 19x12E pervanesini 6S gerilim altında 6800 RPM'de rahatlıkla çevirebilmekte ve mükemmel güç/ağırlık oranı ($5.16\text{ W/g}$) sunmaktadır.

---

## 2. Batarya Kimyası ve Kapasite Seçimi (LiPo vs Li-Ion)

| Kriter | Lityum Polimer (LiPo 70C) | Lityum İyon (18650 / 21700 Molicel) |
| :--- | :--- | :--- |
| **Enerji Yoğunluğu** | $175\text{ Wh/kg}$ | **$250\text{ Wh/kg}$** |
| **Sürekli Boşalma Hızı (C-Rating)** | **70C Sürekli / 140C Pik** | 10C - 15C |
| **Kalkışta Gerilim Çökmesi (Voltage Sag)** | **Minimal (< 0.25V/hücre @ 85A)** | Yüksek (> 0.65V/hücre @ 85A) |
| **Termal Isınma** | Düşük ($R_{int} \approx 1.2\text{ m}\Omega/\text{hücre}$) | Yüksek ($R_{int} \approx 13\text{ m}\Omega/\text{hücre}$) |
| **DBF 5 Dakika Uçuşuna Uygunluk** | **MÜKEMMEL (Tercih Edildi)** | Yetersiz ani güç aktarımı |

*   **Nihai Batarya Paketi:** Gens Ace Tattu 6S1P 16000mAh 70C LiPo ($22.2\text{V}$, $355.2\text{Wh}$, Kütle: $2.15\text{ kg}$).

---

## 3. Güvenlik, Sigorta ve Telemetri Arayüzü

AIAA DBF güvenlik kurallarına tam uyum:
1.  **Fiziksel Emniyet Anahtarı (Arming Plug):** Dış gövde üzerinde yüksek akımlı (150A) çift kontaklı kırmızı emniyet soketi bulunmaktadır. Uçak piste çıkana kadar bu soket takılmaz ve motorlara fiziksel olarak enerji gidemez.
2.  **Akım Sınırlayıcı Sigorta (Main Fuse):** $120\text{ A}$ havacılık sınıfı ANL tipi eriyen sigorta, bataryanın hemen çıkışına seri olarak bağlanmıştır.
3.  **Güç Dağıtım Kartı (PDB) & Sensörler:** Hall-effect akım sensörü (Allegro ACS770, 0-200A) ve analog gerilim bölücü ile saniyede 10 kez telemetri paketine batarya verisi basılır.
