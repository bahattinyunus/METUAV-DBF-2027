# 🦅 METUAV-DBF-2027 | AIAA Design/Build/Fly İHA Geliştirme Reposu

[![Standart: C++20](https://img.shields.io/badge/C++-20-blue.svg)](https://isocpp.org/)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework: ROS2](https://img.shields.io/badge/ROS2-Humble-22314E.svg)](https://docs.ros.org/en/humble/index.html)
[![AIAA DBF: 2027](https://img.shields.io/badge/AIAA_DBF-2027-red.svg)](https://www.aiaa.org/dbf)
[![CI: Passing](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](https://github.com/bahattinyunus/METUAV-DBF-2027/actions)
[![Takım: METU MECH](https://img.shields.io/badge/Team-METU_MECH-red.svg)](https://mech.metu.edu.tr/)

## 📌 Proje Hakkında
Bu depo, **METU MECH** bünyesinde faaliyet gösteren **METUAV** takımının AIAA Design/Build/Fly (DBF) 2027 yarışması için geliştirdiği İnsansız Hava Aracı (İHA) sistemlerinin tüm donanım, aerodinamik, itki, yapısal ve yazılım altyapısını barındırır. 

Amacımız; yalnızca aerodinamik olarak mükemmel bir uçak tasarlamak değil, aynı zamanda uçuş sırasında yaşanabilecek anlık ağırlık merkezi (CG) değişimlerini ve görev gereksinimlerini **Edge-AI destekli adaptif ROS2 mimarisi** ve **MDO optimizasyon motoru** ile otonom olarak yönetebilen şampiyonluk adayı bir sistem ortaya koymaktır. 

---

## ⚖️ AIAA DBF 2027 Yarışma Kuralları ve Geliştirme İsterleri

Uçağımızın tasarımı ve yazılım mimarisi, resmi yarışma kuralları referans alınarak şu kısıtlamalara göre geliştirilmektedir:

*   **Maksimum Kalkış Ağırlığı (TOGW):** Uçak, taşıdığı tüm faydalı yüklerle birlikte 55 lbs (yaklaşık 24.95 kg) sınırını kesinlikle geçmemelidir.
*   **İtki Sistemi:** Sistem tamamen elektrik motorlu olmalı, güç dağıtımı ve telemetri verileri anlık olarak yer istasyonuna (GCS) aktarılmalıdır.
*   **Montaj Süresi (5 Dakika Kuralı):** Uçağın kutudan çıkarılıp uçuşa hazır hale gelmesi ve ROS2/Aviyonik sistemlerin boot edilerek sensör kalibrasyonlarını tamamlaması maksimum **5 dakika** sürmelidir. Geliştirilen yazılım, hızlı başlatma (`fast_boot_calibrator`) prensiplerine göre optimize edilmiş olup **3 dakika 5 saniyede** uçuşa hazır hale gelmektedir.
*   **Tasarım Raporu:** Mekanik ve yazılımsal tüm mimari kararlar, maksimum 60 sayfalık yarışma tasarım raporuna ([AIAA_DBF_2027_DESIGN_REPORT.md](dokumantasyon/AIAA_DBF_2027_DESIGN_REPORT.md)) aktarılmıştır.

---

## 🎯 DBF 2027 Uçuş Görevleri (Mission Profiles)

Sistemimiz aşağıdaki görevleri en yüksek hız ve stabilite ile tamamlamak üzere tasarlanmıştır:

1.  **Yer Görevi (Ground Mission):** Uçağın yapısal bütünlüğünün (kanat ucu +3.5g statik yükleme) ve sistem entegrasyonunun testi.
2.  **Görev 1 (Staging Flight):** Yüksüz konfigürasyonda, maksimum hızda 5 dakika içerisinde 3 tam turun otonom/manuel hibrit uçuşla tamamlanması (Hedeflenen süre: 99.8 sn).
3.  **Görev 2 (Payload Flight):** Belirlenen faydalı yükler (11.2 kg medikal yük) uçağa yüklenir. Hedef, taşıma kapasitesi ile tur süresi arasındaki en iyi aerodinamik ve elektriksel verimliliği sağlamaktır.
4.  **Görev 3 (Delivery/Launch):** Uçuş sırasında faydalı yükün hedef bölgeye bırakılması. Yazılım ekibi, yük bırakıldığı andaki ani ağırlık azalımını ve 44 mm CG kaymasını kompanze edecek adaptif PID güncellemelerini anlık olarak hesaplamaktadır.

---

## 📂 Depo Mimarisi ve Klasör Yapısı

Proje, disiplinler arası çalışmayı kolaylaştırmak ve takım içi çakışmaları önlemek adına modüler olarak kurgulanmıştır:

```text
METUAV-DBF-2027/
│
├── 📁 aerodinamik/              # XFLR5, OpenVSP tasarımları, polar analizleri ve CFD analiz raporu
│   ├── data/                   # Selig 1223 ve Clark Y polar veri setleri (.csv)
│   ├── scripts/                # 3D kanat dönüşümü, L/D ve TOGW analiz araçları
│   └── CFD_ANALYSIS_REPORT.md  # Kapsamlı AIAA DBF formatında aerodinamik rapor
├── 📁 mekanik_ve_yapisal/       # SolidWorks CAD dataları, kompozit katman analizleri (FEA)
│   ├── scripts/                # Kütle/CG bütçesi ve karbon spar gerilme hesaplayıcı
│   ├── ASSEMBLY_5MIN_GUIDE.md  # 5 Dakika montaj ve hızlı kilit yönergesi
│   └── cad_specifications.md   # Malzeme, bağlantı ve CAD standartları
├── 📁 itki_ve_guc_sistemleri/   # Elektrik itki motoru, pervane ve batarya analizleri
│   ├── scripts/                # BEMT pervane optimizasyonu ve motor/batarya termal simülatörü
│   └── propulsion_trade_study.md # Motor ve LiPo batarya seçim takas raporu
├── 📁 optimizasyon_ve_mdo/      # Çok Disiplinli Tasarım Optimizasyonu (MDO) & Skorlama
│   ├── scripts/                # dbf_scoring_mdo.py (Duyarlılık & Monte Carlo simülasyonu)
│   └── test/                   # MDO skorlama birim testleri
├── 📁 aviyonik_ve_otonom/       # Ana ROS2 Humble Workspace
│   ├── src/
│   │   ├── ucus_kontrol/       # C++20 adaptif PID, Genişletilmiş Kalman Filtresi (EKF), Enerji Yöneticisi
│   │   ├── edge_ai_vision/     # Python tabanlı (PyTorch/OpenCV) hedef tespiti ve balistik bilgisayarı
│   │   └── telemetri/          # MAVLink köprüsü ve Canlı GCS Telemetri Paneli (gcs_dashboard.py)
│   └── setup_workspace.sh      # ROS2 çalışma alanı otomatik kurulum betiği
├── 📁 simulasyon/               # Gazebo ve PX4 SITL test senaryoları, dünya (world) modelleri
│   ├── models/dbf_aircraft/    # Ayrılabilir faydalı yüke sahip DBF uçak modeli (.sdf)
│   ├── worlds/dbf_airfield.world # DBF yarışma pisti, pylonlar ve hedef alanı
│   ├── launch/                 # dbf_mission3_sitl.launch.py
│   └── scripts/                # simulate_flight_test.py (3-DOF uçuş doğrulama)
├── 📁 uretim_ve_test/           # Lazer kesim vektörleri, 3D baskı (STL/G-code) ve rüzgar tüneli verileri
│   ├── dxf_outputs/            # CNC lazer kesim kanat nervür vektörleri (selig1223_root_rib_320mm.dxf)
│   ├── scripts/                # generate_wing_rib_dxf.py (Parametrik DXF üretici)
│   ├── specs/                  # Görev 3 faydalı yük bırakıcı mekanik şartnamesi
│   ├── manufacturing_guide.md  # Kompozit vakum infüzyon ve CNC lazer üretim kılavuzu
│   └── WIND_TUNNEL_TEST_PLAN.md # ODTÜ Rüzgar Tüneli test protokolü
├── 📁 dokumantasyon/            # Resmî tasarım raporları ve standart operasyon listeleri
│   ├── AIAA_DBF_2027_DESIGN_REPORT.md # 60 Sayfalık AIAA resmî tasarım raporu
│   └── FLIGHT_CHECKLISTS_AND_SOP.md   # Uçuş öncesi, hat montajı ve acil durum prosedürleri
├── 📁 rakip_analizi_ve_benchmark/ # Dünya şampiyonları, açık kaynak repolar, makaleler ve video analizi
│   ├── SAMPIYONLAR_VE_RAKIP_TAKIMLAR.md # FH Joanneum, ERAU, RWTH Aachen, Georgia Tech, Ljubljana analizi
│   ├── ACIK_KAYNAK_REPOLAR_VE_ARACLAR.md # DBF, MDO, aerodinamik ve aviyonik açık kaynak repoları
│   ├── AKADEMIK_MAKALELER_VE_LITERATUR.md # Düşük-Re aerodinamiği, kütle şoku ve kompozit makaleleri
│   ├── VIDEO_ARSIVI_VE_ANALIZLER.md   # Uçuş hattı videoları ve rakiplerin kaza/kırım kök neden analizleri
│   └── scripts/competitor_benchmark_matrix.py # Karşılaştırmalı benchmark matrisi ve gap analizi
└── 📄 README.md                 # Proje ana dokümantasyonu
```

---

## 🛠️ Teknoloji Yığını (Tech Stack)

Ağır yük altında stabil uçuş, minimum gecikme (low-latency) ve yüksek reaksiyon süreleri elde etmek için aşağıdaki teknolojiler kullanılmaktadır:

*   **Otonomi ve Yazılım:** C++ (20), Python (3.10+), ROS2 (Humble), MAVLink protokolü, PX4 otopilot mimarisi.
*   **Yapay Zeka ve Veri İşleme:** PyTorch, OpenCV, Edge-AI optimizasyonları (hedef tespiti ve balistik bırakma).
*   **Tasarım ve Simülasyon:** SolidWorks, ANSYS (CFD/FEA), XFLR5, OpenVSP, Gazebo.
*   **İtki & Güç:** Scorpion SII-4035-330KV Motor, 19x12E Pervane, 6S 16000mAh 70C LiPo batarya.
*   **Donanım Altyapısı:** Pixhawk 6X (Ana uçuş kontrolcüsü), Nvidia Jetson Orin Nano (Edge hesaplamalar ve görüntü işleme kartı), telemetry alıcı-verici modülleri.

---

## 🚀 Kurulum ve Geliştirme Ortamı (Yazılım Ekibi İçin)

Yazılım geliştiricilerin projeye katkı verebilmesi için **Ubuntu Linux** (tercihen 22.04 LTS) kullanması ve aşağıdaki adımları sırasıyla uygulaması önerilir:

### 1. Depoyu Klonlama ve Çalışma Alanı

```bash
git clone https://github.com/bahattinyunus/METUAV-DBF-2027.git
cd METUAV-DBF-2027/aviyonik_ve_otonom
```

### 2. ROS2 ve Python Bağımlılıklarının Kurulumu

```bash
# ROS2 kütüphaneleri
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Edge-AI ve Telemetri gereksinimleri
pip install -r src/edge_ai_vision/requirements.txt
pip install -r src/telemetri/requirements.txt
```

### 3. Paketleri Derleme

C++ ve Python tabanlı ROS2 düğümlerini derlemek için:

```bash
colcon build --symlink-install
source install/setup.bash
```

---

## 🧪 Simülasyon, Analiz ve Doğrulama Testleri

### MDO Skorlama ve Duyarlılık Analizi
```bash
python optimizasyon_ve_mdo/scripts/dbf_scoring_mdo.py
```

### BEMT Pervane Verimliliği ve Motor Termal Analizi
```bash
python itki_ve_guc_sistemleri/scripts/bemt_propeller_optimizer.py
python itki_ve_guc_sistemleri/scripts/motor_thermal_simulator.py
```

### CNC Lazer Kesim DXF Vektör Üretimi
```bash
python uretim_ve_test/scripts/generate_wing_rib_dxf.py
```

### Bağımsız 3-DOF Uçuş ve Görev 3 Doğrulama Testi
```bash
python simulasyon/scripts/simulate_flight_test.py
```

### Yer İstasyonu (GCS) Telemetri Paneli
```bash
python aviyonik_ve_otonom/src/telemetri/telemetri/gcs_dashboard.py
# Web arayüzü sunucusu için:
python aviyonik_ve_otonom/src/telemetri/telemetri/gcs_dashboard.py --server
```

### Rakip Analizi ve Uluslararası Şampiyonlar Benchmark Matrisi
```bash
python rakip_analizi_ve_benchmark/scripts/competitor_benchmark_matrix.py
```

### Otomatik Birim Testleri
```bash
python -m pytest aviyonik_ve_otonom/src/edge_ai_vision/test/test_ballistics.py
python -m pytest aviyonik_ve_otonom/src/telemetri/test/test_telemetry.py
python -m pytest aviyonik_ve_otonom/src/ucus_kontrol/test/test_control_logic.py
python -m pytest optimizasyon_ve_mdo/test/test_mdo.py -o "pythonpath=."
python -m pytest rakip_analizi_ve_benchmark/test/test_benchmark.py -o "pythonpath=."
```

---

## 🤝 Katkıda Bulunma Kuralları (Contribution Guidelines)

Bu repo tüm METU MECH alt ekiplerinin ortak alanıdır. Sistemin sorunsuz işlemesi için aşağıdaki kurallar esastır:

1.  **Branch İsimlendirmesi:** Ana (`main`) dal üzerinde doğrudan çalışmak yasaktır.
    *   Özellik eklerken: `feat/otonom-inis`, `feat/edge-ai-hizalama`
    *   Hata çözerken: `bugfix/mavlink-kopmasi`
    *   Tasarım güncellerken: `cad/yeni-govde-v2`
2.  **Pull Request (PR) Açıklamaları:** Açtığınız PR'da donanımsal bir ekleme varsa **ağırlık artışını (gram cinsinden)**, yazılımsal bir kod ekliyorsanız **işlemci/RAM yükünü** mutlaka belirtin. DBF'de uçağın donanımına veya işlemcisine binen her ekstra yük kritik önem taşır.
3.  **Code Review:** Her kod parçası veya mekanik tasarım, birleştirilmeden önce mutlaka takım liderleri veya ilgili sorumlular tarafından (GitHub üzerinden `Approve` alarak) onaylanmalıdır.

---

## 📞 İletişim

Geliştirme süreci, yetkilendirme veya repodaki görev dağılımları hakkında destek almak için GitHub üzerinden `@arch-yunus` ile iletişime geçebilir ya da doğrudan METU MECH Discord/WhatsApp kanallarını kullanabilirsiniz.

**Uçuş hattında görüşmek üzere, başarılar METUAV!** 🌪️
