# 🛰️ Aviyonik ve Otonom Çalışma Alanı (ROS 2 Humble)

Bu dizin, **AIAA DBF 2027** uçağının uçuş kontrolü, hedef tespiti ve yer istasyonu telemetri haberleşmesini yürüten ana ROS 2 Humble çalışma alanıdır (workspace).

## 📦 Paket Mimarisi

*   **`ucus_kontrol` (C++20):**
    *   **Adaptif PID Kontrolcü (`adaptive_pid_controller`):** Dinamik basınca, tahmini hava aracı kütlesine ve anlık CG konumuna göre kontrol kazançlarını ölçekler. Görev 3'te yük bırakıldığı andaki kütle şokunu ve aerodinamik moment değişimini kompanze eden aktif trim ve kazanç sıçraması içerir.
    *   **Görev Yöneticisi (`mission_manager`):** Yer testi, kalkış, Görev 1 (Staging - 3 tur), Görev 2 (Faydalı yük), Görev 3 (Hassas hedef bırakma) durum makinelerini yönetir.
    *   **Hızlı Başlatma Kalibratörü (`fast_boot_calibrator`):** AIAA DBF 5 dakika montaj & uçuşa hazır olma kuralını sağlamak amacıyla sensör sıfır-kayıklık (zero-bias) kalibrasyonunu 20 saniyenin altında tamamlar.
*   **`edge_ai_vision` (Python 3.10+):**
    *   **Hedef Tespiti (`target_detector_node`):** Görev 3 hedef bölgesini (konsantrik dairesel hedef) kamera görüntüsü üzerinden derin öğrenme/bilgisayarlı görü ile tespit eder, kamera matrisi ve İHA açısal durumunu kullanarak yer koordinatlarına dönüştürür.
    *   **Bırakma Balistik Bilgisayarı (`drop_ballistics_computer`):** İHA'nın irtifası, yer hızı, hücum açısı ve rüzgar tahmin vektörünü entegre ederek yük bırakma anını hassas olarak hesaplar ve servo tetikleme komutu üretir.
*   **`telemetri` (Python 3.10+):**
    *   **MAVLink Köprüsü (`mavlink_bridge_node`):** Pixhawk uçuş kontrolcüsü ile ROS 2 düğümleri arasında MAVLink v2 protokolü ile çift yönlü haberleşme sağlar. GCS yer istasyonuna batarya, CG durumu, motor çekiş gücü ve görev telemetrisi gönderir.

## 🚀 Derleme ve Çalıştırma

```bash
cd aviyonik_ve_otonom
colcon build --symlink-install
source install/setup.bash

# Uçuş kontrolcüsünü başlatma
ros2 launch ucus_kontrol flight_control.launch.py

# Görev 3 hedefe bırakma vizyon boru hattını başlatma
ros2 launch edge_ai_vision vision_pipeline.launch.py
```
