# ⏱️ AIAA DBF 2027 5 Dakika Hızlı Montaj ve Uçuşa Hazırlık Kılavuzu

AIAA DBF yarışma kuralı: *"Uçağın taşıma kutusundan çıkarılıp uçuş hattına hazır hale gelmesi ve tüm aviyonik kalibrasyonların tamamlanması maksimum 5 dakika (300 saniye) sürmelidir."*

DBF mühendislik ekibi, bu ister doğrultusunda **Aletsiz Hızlı Kilit (Tool-less Quick-Lock)** ve **Kör-Geçme Çok Kutuplu Konektör (Blind-Mate Multi-Pin Connectors)** mimarilerini tasarlamıştır.

---

## 1. Montaj Zaman Çizelgesi (Assembly Timeline Budget)

| Adım | İşlem | Hedef Süre | Birikimli Süre | Sorumlu Ekip Üyesi |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Taşıma kutusu mandallarının açılması, ana gövdenin montaj sehpasına yerleştirilmesi | 25 sn | 0:25 | Üye 1 & 2 |
| **2** | Sol ve sağ kanat panellerinin karbon I-spar yuvalarına sürülmesi ve kilit pimlerinin takılması | 45 sn | 1:10 | Üye 1 & 2 |
| **3** | Yatay ve düşey kuyruk panellerinin 1/4 tur bayonet kilit ile sabitlenmesi | 30 sn | 1:40 | Üye 1 |
| **4** | Faydalı yükün (Görev 2/3 medikal yükler) gövde içi raylı yuvaya sürülmesi ve servo kilit mandalının oturması | 25 sn | 2:05 | Üye 2 |
| **5** | Uçuş bataryasının (6S LiPo) takılması ve emniyet anahtarının (Arming Plug) sokulması | 15 sn | 2:20 | Üye 1 |
| **6** | Aviyonik sistemlerin boot etmesi (`fast_boot_calibrator` IMU sıfır kayıklık ve GPS 3D fix) | 25 sn | 2:45 | Yazılım / Otonom |
| **7** | Kontrol yüzeyleri (Aileron, Elevator, Rudder, Flap) ön kontrol testi ve kalkış onay bayrağı | 20 sn | **3:05** | Pilot & Takım Lideri |

> **Sonuç:** Toplam montaj ve hazır olma süresi **3 dakika 5 saniye** olarak gerçekleşmekte, 5 dakikalık (300 sn) yarışma sınırının \%38 altında emniyetli marjinle tamamlanmaktadır.

---

## 2. Mekanik Hızlı Bağlantı Çözümleri

### 2.1 Kanat Kökü - Gövde Bağlantısı
*   **Ana Taşıyıcı Karbon Spar:** 25 mm çapında içi boş pultrüzyon karbon boru, gövde içindeki duralumin kılavuz kovanına oturur.
*   **Hızlı Kilit Pimi (Quick-Release Ball Lock Pin):** Kanat paneli yerine oturduğunda yaylı bilyeli paslanmaz pim kendiliğinden kilitlenir; tornavida veya alyan anahtarı gerektirmez.
*   **Otomatik Elektriksel Bağlantı (Blind-Mate Connector):** Kanat kök profiline gömülü altın kaplama PCB konektörleri, kanat gövdeye itildiğinde aileron servo sinyallerini ve telemetri veri hatlarını aletsiz birleştirir.

### 2.2 Faydalı Yük Hızlı Yükleme Mekanizması
*   Gövde altındaki karbon kapak çift yaylı mıknatıslı mandal sistemi ile tek elle açılır.
*   Faydalı yük kutusu teflon raylar üzerinde kayarak yerine oturur ve yüksek torklu micro servo pimi ile kilitlenir.

---

## 3. Yazılımsal Hızlı Başlatma (Fast-Boot Architecture)

*   Jetson ve Pixhawk otopilot sistemi, Linux kernel ve ROS2 başlangıç servisleri `systemd` seviyesinde optimize edilmiş, gereksiz arka plan servisleri devre dışı bırakılmıştır.
*   `ucus_kontrol/src/fast_boot_calibrator.cpp` algoritması:
    *   100 adet IMU verisini 2 saniyede örnekleyerek gyro ve ivmeölçer sıfır kayıklıklarını (zero-bias) anında hesaplar.
    *   Uçağın kalkış koordinatını kilitler ve 20 saniye içinde `SYSTEM_READY` bayrağını yer istasyonuna iletir.
