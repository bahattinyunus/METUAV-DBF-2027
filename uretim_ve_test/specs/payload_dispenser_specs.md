# 📦 Görev 3 Faydalı Yük Bırakma Sistemi Teknik Şartnamesi

Bu mekanizma, AIAA DBF 2027 Görev 3 isterleri doğrultusunda uçuş esnasında hedef bölge üzerine hassas ve takılmasız faydalı yük bırakmayı sağlar.

## 1. Mekanizma Bileşenleri

*   **Tetikleyici Aktüatör:** KST DS589MG Çelik Dişli Dijital Servo (Tork: 9.2 kg.cm @ 7.4V, Tepki Süresi: 0.08 sn/60°).
*   **Mandal Mekanizması:** 7075-T6 Havacılık Alüminyumundan CNC frezelenmiş çift tırnaklı yay destekli kilit.
*   **Ray Sistemi:** PTFE (Teflon) kaplı ultra düşük sürtünmeli kızak. Yük serbest bırakıldığı anda yerçekimi ve hava akımı ile 0.12 saniye içinde gövdeyi terk eder.

## 2. Elektriksel ve Sinyal Arayüzü

*   **Giriş Sinyali:** ROS 2 `/metuav/payload_drop_trigger` konusundan tetiklenen PWM darbesi (1000 µs kilitli -> 2000 µs serbest).
*   **Güvenlik Kilidi (Hardware Arming Interlock):** Görev 3 moduna geçilmeden ve uçağın irtifası 15 metrenin üzerine çıkmadan mekanizmaya enerji gitmesini engelleyen optokuplörlü fiziksel emniyet devresi.
