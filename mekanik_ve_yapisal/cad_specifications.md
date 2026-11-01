# 🛠️ METUAV DBF 2027 Mekanik ve Yapısal Tasarım Özellikleri

## 1. Malzeme ve Üretim Yöntemleri

*   **Ana Taşıyıcı Gövde:** Karbon-elyaf / Rohacell köpük sandviç laminat (Vakum infüzyon yöntemi ile üretilmiştir).
*   **Kanat Yapısı:** CNC kesim balsa ve havacılık huş kontrası nervürler, pultrüzyon karbon I-beam spar, 0.4 mm mikro-balon takviyeli cam elyaf / karbon kaplama.
*   **İniş Takımı:** 4 mm kalınlığında yay çeliği destekli otoklav kürlü tek parça karbon bacaklar, 110 mm hafif sünger çekirdekli rulmanlı tekerlekler.
*   **Servo Yatakları ve Montaj Braketleri:** Karbon takviyeli PETG / Nylon (PA-CF) filament ile FDM 3D baskı (%40 gyroid dolgu).

## 2. Bağlantı Elemanları ve Tork Değerleri

| Bölge | Bağlantı Tipi | Standart | Sıkma Torku | Emniyet Önlemi |
| :--- | :--- | :--- | :--- | :--- |
| Motor Bağlantısı | M4x12 Titanyum Civata | DIN 912 | 3.2 N.m | Loctite 243 (Mavi) |
| Ana İniş Takımı | M5x16 Paslanmaz A4 | DIN 7991 | 5.5 N.m | Naylon Fiberli Kilit Somun |
| Servo Kolları | M2.5x8 Çelik | ISO 7380 | 0.8 N.m | Yaylı Pul + Loctite 222 |
| Kanat Kilit Pimleri | 8mm Ball Lock Pin | NAS 1334 | Aletsiz Geçme | Bilyeli Emniyet Kilidi |

## 3. SolidWorks CAD Klasör Hiyerarşisi

```text
mekanik_ve_yapisal/
├── cad/
│   ├── asm/                 # Ana Uçak Montajı (Top-Level Assembly)
│   ├── parts/               # Parça dataları (Fuselage, Wing, Tail, Mounts)
│   └── drawings/            # 2D Teknik Resimler ve Toleranslar
├── scripts/                 # Kütle/CG ve Spar FEA hesaplama araçları
├── ASSEMBLY_5MIN_GUIDE.md   # 5 Dakika montaj talimatnamesi
└── cad_specifications.md    # Malzeme ve CAD standartları
```
