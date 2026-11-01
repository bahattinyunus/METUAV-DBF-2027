# 🌐 Açık Kaynak Havacılık Repoları, DBF Araçları ve Kütüphaneler

Bu dizin, AIAA DBF, İHA tasarımı, çok disiplinli optimizasyon (MDO), hesaplamalı aerodinamik ve aviyonik alanında dünyadaki en prestijli açık kaynak kod depolarını ve mühendislik araçlarını listeler.

---

## 1. DBF Özelinde Üniversite Repoları ve Skorlama Araçları

*   **[UF-Design-Build-Fly / MultidisciplinaryDesignOptimization](https://github.com/UF-Design-Build-Fly)**
    *   *Geliştirici:* University of Florida DBF Takımı
    *   *Açıklama:* DBF yarışma kurallarını MATLAB matrislerine dökerek kanat alanı, kord dağılımı ve faydalı yük oranını optimize eden ön tasarım aracı.
*   **[Nightingale-LZH / DBF-Score-Optimization](https://github.com/Nightingale-LZH/DBF-Score-Optimization)**
    *   *Açıklama:* Jupyter Notebook ortamında DBF puan formülünün parametrik duyarlılık analizini ve Monte Carlo simülasyonunu yürüten açık kaynak kod tabanı.
*   **[RU-Airborne / QuickFoil-Project-Mithun-2023](https://github.com/RU-Airborne/QuickFoil-Project-Mithun-2023)**
    *   *Geliştirici:* Rutgers University DBF Takımı (*RU Airborne*)
    *   *Açıklama:* Düşük Reynolds sayılarında kanat profili seçimi ve polar eğrilerinin otomatik taranmasını sağlayan Python tabanlı aerodinamik betikler.
*   **[DerekZhang0000 / M3-Analysis-Tool](https://github.com/DerekZhang0000/M3-Analysis-Tool)**
    *   *Açıklama:* Görev 3 faydalı yük bırakma dinamiği ve hedef isabet analizini yürüten MATLAB aracı.
*   **[Bulnabi-SNU / Bulnabi_DBF2025_CustomFC_v1](https://github.com/Bulnabi-SNU/Bulnabi_DBF2025_CustomFC_v1)**
    *   *Geliştirici:* Seoul National University DBF Takımı (*Bulnabi*)
    *   *Açıklama:* PlatformIO/C++ tabanlı DBF aviyonik donanımı ve sensör okuma gömülü yazılımı.

---

## 2. Küresel Uçak Tasarım ve MDO Çatıları (Frameworks)

*   **[SUAVE (Stanford University Aerospace Vehicle Environment)](https://github.com/suavecode/SUAVE)**
    *   *Geliştirici:* Stanford University Aerospace Design Lab (ADL)
    *   *Özellikler:* Geleceğin elektrikli ve hibrit hava araçlarının kavramsal boyutlandırması, görev profili analizi ve aerodinamik-itki entegrasyonu için endüstri standardı açık kaynak MDO çatısı.
*   **[OpenVSP (Open Vehicle Sketch Pad)](https://github.com/OpenVSP/OpenVSP)**
    *   *Geliştirici:* NASA
    *   *Özellikler:* Parametrik 3D uçak geometrisi oluşturma, VSPAERO ile vorteks örgü (VLM) aerodinamik analizi ve kütle özellikleri çıkarma aracı.
*   **[AeroSandbox](https://github.com/peterdsharpe/AeroSandbox)**
    *   *Geliştirici:* Peter Sharpe (MIT)
    *   *Özellikler:* Otomatik türevlenebilir (Automatic Differentiation) uçak tasarım ve yörünge optimizasyon kütüphanesi. Gradyan tabanlı MDO'da saniyeler içinde binlerce tasarımı çözümler.
*   **[XFLR5 / XFOIL](https://www.xflr5.tech/)**
    *   *Geliştirici:* Mark Drela (MIT) & André Deperrois
    *   *Özellikler:* Düşük Reynolds rejiminde ($Re < 5 \times 10^5$) viskoz sınır katman analizi, geçiş balonu tahmini ve 3D kanat stabilite türevleri.

---

## 3. Otonomi, SITL Simülasyon ve Uçuş Kontrol Kütüphaneleri

*   **[PX4-Autopilot](https://github.com/PX4/PX4-Autopilot)**
    *   Açık kaynak endüstri standardı otopilot yazılımı. Sabit kanatlı uçaklarda Total Energy Control System (TECS) irtifa/hız kontrolü ve EKF3 durum tahmincisi.
*   **[ArduPilot](https://github.com/ArduPilot/ardupilot)**
    *   ArduPlane sabit kanat uçuş algoritması, otomatik termik yakalama ve rüzgar tahmin kütüphaneleri.
*   **[pymavlink & MAVROS](https://github.com/mavlink/mavros)**
    *   ROS / ROS 2 Humble ile Pixhawk uçuş kontrolcüsü arasında yüksek hızlı telemetri ve komut köprüsü.
*   **[Gazebo Simulation (gazebo_ros_pkgs)](https://github.com/ros-simulation/gazebo_ros_pkgs)**
    *   Fizik motorları (ODE, Bullet) ve rüzgar tüneli eklentileriyle donatılmış fotogerçekçi uçuş simülasyon ortamı.
