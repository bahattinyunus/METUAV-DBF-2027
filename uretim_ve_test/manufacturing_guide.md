# 🏭 AIAA DBF 2027 Kompozit Üretim ve İmalat Kılavuzu

Bu kılavuz, AIAA DBF 2027 uçağının gövde, kanat ve faydalı yük bileşenlerinin hafif, rijit ve tekrarlanabilir kalitede üretilmesi için Kompozit atölyesinde uygulanan imalat prosedürlerini tanımlar.

---

## 1. Kompozit Vakum İnfüzyon Prosedürü (Gövde Kabuğu)

*   **Kalıp Hazırlığı:**
    1.  Kalıp yüzeyi 2000 kuma kadar zımparalanır, pasta-cila uygulanır.
    2.  Kalıp ayırıcı cila (Frekote 700-NC) 4 kat halinde, katlar arası 20 dakika kuruma süresi bırakılarak uygulanır.
*   **Katman Dizilimi (Layup Schedule):**
    *   Kat 1: 100 g/m² 3K Karbon Kumaş (Twill 2x2 - Yüzey finişi için)
    *   Kat 2: 200 g/m² Biaxial (±45°) Karbon Kumaş (Burulma rijitliği için)
    *   Çekirdek (Core): 2.0 mm Rohacell 51 IG-F köpük (Ağırlık tasarrufu ve bükülme direnci)
    *   Kat 3: 100 g/m² 3K Karbon Kumaş (Twill 2x2)
*   **İnfüzyon Reçinesi ve Kürleme:**
    *   Epoksi: Hexion MGS RIMR 135 / RIMH 1366 (Düşük viskoziteli infüzyon reçinesi).
    *   Vakum Basıncı: -0.95 bar (Sızdırmazlık testi süresi 30 dakika).
    *   Oda sıcaklığında 24 saat ön kürleme, ardından 60°C'de 8 saat fırınlama (post-cure).

---

## 2. CNC Lazer Kesim Parametreleri (Nervürler ve Gövde Postaları)

*   **Makine:** 80W CO2 CNC Lazer Kesici
*   **Malzemeler:**
    *   3.0 mm Havacılık Huş Kontrplağı (Birch Plywood - Ana spar yuvalı taşıyıcı nervürler)
    *   2.5 mm Balsa Ağacı (Hafif kanat profil nervürleri)
*   **Parametre Tablosu:**
    | Malzeme | Hız (Speed) | Güç (Power) | Frekans | Odak Uzaklığı |
    | :--- | :--- | :--- | :--- | :--- |
    | 3.0 mm Huş Kontrası | 18 mm/sn | %72 | 1000 Hz | 50.8 mm |
    | 2.5 mm Balsa | 35 mm/sn | %45 | 800 Hz | 50.8 mm |
    | 1.5 mm Cam-Epoksi (FR4) | 8 mm/sn (Çift paso) | %85 | 1200 Hz | 50.8 mm |

---

## 3. Eklemeli İmalat (3D Baskı) Standartları

Uçuş emniyetini etkileyen kritik servo yatakları, pitot tutucular ve faydalı yük mandalları için FDM / SLS parametreleri:

*   **Filament Malzemesi:** Karbon Elyaf Takviyeli Poliamid / Naylon (PA12-CF) veya PETG-CF.
*   **Nozzle Sıcaklığı:** 275°C (Sertleştirilmiş çelik nozzle, 0.4 mm).
*   **Yatak Sıcaklığı:** 90°C.
*   **Dolgu Tipi ve Yoğunluğu:** %40 Gyroid (İzotropik gerilme dağılımı).
*   **Duvar Sayısı:** Minimum 4 katman (Perimeter).
