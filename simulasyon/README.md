# 🛫 METUAV DBF 2027 Simülasyon ve SITL Paketi

Bu dizin, Gazebo ve PX4 SITL (Software-In-The-Loop) tabanlı simülasyon dünyasını, İHA modelini ve uçuş test senaryolarını içerir.

## 📁 Dizin İçeriği

*   **`models/dbf_aircraft/`**:
    *   2.40 metre kanat açıklığı, çift kademeli taşıyıcı profil ve ayrılabilir iç faydalı yük (payload link) barındıran SDF uçak modeli.
    *   Hedefe kilitlenen aşağı açılı kamera sensörü (`camera_link`).
*   **`worlds/dbf_airfield.world`**:
    *   AIAA DBF kurallarına uygun 200m x 25m pist, Mission 1 dönüş pylonları (+150m, -150m) ve Mission 3 konsantrik hedef dairesi.
*   **`launch/dbf_mission3_sitl.launch.py`**:
    *   Gazebo, PX4 SITL, uçuş kontrolcüsü, vizyon tespiti ve telemetri köprüsünü tek komutla başlatan ROS 2 launch dosyası.
*   **`scripts/simulate_flight_test.py`**:
    *   Gazebo grafik arayüzüne ihtiyaç duymadan aerodinamik tepkileri ve faydalı yük bırakma anındaki ani CG değişimini doğrulayan 3-DOF simülasyon ve doğrulama aracı.

## 🚀 Çalıştırma

### Bağımsız Uçuş Testi (Hızlı Doğrulama)
```bash
python simulasyon/scripts/simulate_flight_test.py
```

### ROS 2 ve Gazebo SITL Ortamı
```bash
ros2 launch metuav_simulation dbf_mission3_sitl.launch.py
```
*(Not: `README.md` içerisindeki yazım uyumluluğu için `metuvav_simulation` ve `metuav_simulation` paket tanımları desteklenmektedir).*
