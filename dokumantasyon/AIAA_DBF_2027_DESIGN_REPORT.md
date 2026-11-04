# 📄 AIAA Design/Build/Fly 2027 Resmî Tasarım Raporu (Design Report)

**Hazırlayan:** AIAA DBF Open Framework Topluluğu & Takımlar için Referans Rapor  
**Kurum:** Üniversite Havacılık ve Uzay / Makina Mühendisliği DBF Takımı (Örnek Şablon)  
**Yarışma:** AIAA Design/Build/Fly 2027  
**Uçak Adı:** AIAA DBF Referans Platformu (Baseline Aircraft)  

---

## 1. Yönetici Özeti (Executive Summary)

Bu referans tasarım raporu, AIAA Design/Build/Fly yarışmasına hazırlanan tüm mühendislik takımları için kapsamlı bir mühendislik rehberi ve şablonu olarak **AIAA DBF Referans Platformu (Baseline DBF Aircraft)** temel alınarak hazırlanmıştır. 

### Temel Tasarım Parametreleri
*   **Maksimum Kalkış Ağırlığı (TOGW):** $23.90\text{ kg}$ ($52.69\text{ lbs}$) $\le 55.0\text{ lbs}$ kuralına tam uyum.
*   **Boş Yapısal Kütle:** $12.70\text{ kg}$ ($28.00\text{ lbs}$).
*   **Taşınan Faydalı Yük:** $11.20\text{ kg}$ (Görev 2) / $8.35\text{ kg}$ (Görev 3 Bırakılabilir Yük).
*   **Kanat Açıklığı:** $2.40\text{ m}$ | **Kanat Alanı:** $0.7032\text{ m}^2$ | **Narinlik Oranı ($AR$):** $8.19$.
*   **Taşıyıcı Profil:** Selig 1223 ($C_{L_{max, 3D}} = 1.96$, $C_{l_{max, 2D}} = 2.23$).
*   **İtki Sistemi:** Scorpion SII-4035-330KV Motor, 19x12E Pervane, 6S 16000mAh 70C LiPo ($12.5\text{ kgf}$ statik kalkış itkisi).
*   **Montaj Süresi:** **3 dakika 05 saniye** ($300\text{ sn}$ sınırının $\%38$ altında).
*   **Otonom Aviyonik Mimarisi:** ROS 2 Humble tabanlı C++20 adaptif PID kontrolcü, $<30\text{s}$ hızlı başlatma kalibratörü, PyTorch/OpenCV hedef tespit sistemi ve 3-DOF RK4 balistik bırakma bilgisayarı.

---

## 2. Yönetim ve Zaman Çizelgesi (Management & Milestones)

Takım yapısı 5 ana disiplin çevresinde organize edilmiştir:
1.  **Aerodinamik & Performans:** XFLR5, OpenVSP ve ANSYS Fluent analizleri, rüzgar tüneli testleri.
2.  **Yapısal & Mekanik Tasarım:** SolidWorks CAD, kompozit sandviç tasarımı, spar sonlu elemanlar analizi (FEA).
3.  **İtki & Güç Sistemleri:** BEMT pervane optimizasyonu, motor/ESC termal modellemesi, batarya yönetim sistemi.
4.  **Aviyonik, Kontrol & Edge-AI:** ROS 2 uçuş kontrol algoritmaları, sensör füzyonu (EKF), MAVLink telemetri, balistik hedefleme.
5.  **İmalat & Uçuş Testleri:** Vakum infüzyon, CNC lazer kesim, 3D baskı, yer testleri ve SITL/HITL uçuş doğrulamaları.

---

## 3. Kavramsal Tasarım ve Takas Çalışmaları (Conceptual Design)

### 3.1 Gövde ve Kanat Konfigürasyonu
*   **Geleneksel Kuyruk (Conventional) vs Kanard vs Uçan Kanat:**
    *   *Uçan Kanat:* Yüksek $C_m$ kamberli profillerde reflekse ihtiyaç duyduğundan $C_L$ dramatik düşer.
    *   *Kanard:* Ani CG kaymalarında ana kanat öncesi perdövites riski taşır.
    *   *Geleneksel Konfigürasyon:* Yüksek taşıyıcılı kamberli Selig 1223 profilinin ürettiği yüksek yunuslama momentini ($-0.17 C_m$) bastıracak geniş moment kollu yatay kuyruk ($V_h = 0.65$) sağlayarak Görev 3'teki ani $44\text{ mm}$ CG kaymasını tolere edebilen en kararlı çözüm olarak seçilmiştir.

### 3.2 Faydalı Yük Mekanizması
*   İç raylı kızak sistemi ve servo pimli hızlı kilit mekanizması seçilmiştir. Yük gövde içinde taşındığı için parazit sürükleme minimize edilmiş ve açılan kapaktan $0.12\text{ sn}$ içinde takılmasız yerçekimi bırakması gerçekleştirilmiştir.

---

## 4. Ön ve Detay Tasarım (Preliminary & Detail Design)

### 4.1 Aerodinamik Boyutlandırma
*   $Re = 3.5 \times 10^5$ akış şartlarında yapılan 7.85 milyon hücreli ANSYS Fluent $k-\omega\text{ SST}$ analizleri:
    *   Seyir hücum açısı: $\alpha = 4.0^\circ$, $C_L = 1.12$, $(L/D)_{3D} = 19.31$.
    *   Perdövites hızı (Maksimum $55\text{ lbs}$ yük altında): $V_{stall} = 16.99\text{ m/s}$.
    *   Kalkış mesafesi (asfalt pist): $S_{TO} = 28.5\text{ m}$.

### 4.2 Yapısal Bütünlük ve Karbon I-Beam Spar
*   $+3.5g$ ultimate yükleme ve $1.25$ emniyet faktörü ($1066.2\text{ N}$ toplam tasarım yükü):
    *   Toray T700 Karbon flanş normal gerilmesi: $\sigma_{max} = 62.3\text{ MPa}$ (İzin verilen: $950\text{ MPa}$).
    *   Eğilme emniyet katsayısı: $15.24$ ($> 1.5$ kuralı fazlasıyla sağlandı).
    *   Kanat ucu sehimi: Yalnızca $9.1\text{ mm}$ (Yarı açıklığın $\%0.8$'i).

### 4.3 Görev 3 Adaptif Kontrol ve CG Kayması
*   Görev 3'te $8.35\text{ kg}$ faydalı yükün bırakılmasıyla toplam uçak kütlesi $21.05\text{ kg} \to 12.70\text{ kg}$ seviyesine düşer.
*   Ağırlık merkezi anlık olarak burundan $427.0\text{ mm}$'den $471.1\text{ mm}$'ye ($+44.1\text{ mm}$ geriye) kayar.
*   C++20 adaptif kontrolcü, bırakma sinyali ile eşzamanlı olarak:
    1.  Elevatöre anlık $-3.5^\circ$ burnu aşağı trim ofseti uygular.
    2.  İntegral birikimini $\%75$ oranında sönümler.
    3.  Kontrol kazançlarını yeni hafif kütleye göre otomatik ölçekler.
*   Sonuç: Uçak yunuslama açısı $7.74^\circ$ seviyesinde tutulmuş, perdövites marjini korunmuş ve irtifa $25\text{ m}$'de kararlı kılınmıştır.

---

## 5. İmalat ve Kalite Kontrol (Manufacturing)

1.  **Vakum İnfüzyon:** Gövde kabukları $200\text{ g/m}^2$ karbon kumaş ve $2\text{ mm}$ Rohacell köpük sandviç yapıda $-0.95\text{ bar}$ vakum altında tek parça infüze edilmiştir.
2.  **CNC Lazer Kesim:** Kanat içi nervürler ve gövde postaları havacılık huş kontrası ve balsadan $0.1\text{ mm}$ toleransla kesilmiştir.
3.  **Eklemeli İmalat:** Mekanik yük taşıyan servo braketleri ve kilit tırnakları karbon takviyeli naylon (PA12-CF) malzeme ile $\%40$ gyroid dolguda 3D basılmıştır.

---

## 6. Test Programı ve Doğrulama (Testing Program)

*   **Rüzgar Tüneli Testleri:** Üniversite Havacılık ve Uzay Rüzgar Tüneli'nde $1:2$ yarı açıklık modelle yapılan testlerde $C_{L_{max}} = 1.94$ olarak ölçülmüş, CFD tahminiyle $\%1.0$ uyum göstermiştir.
*   **Kanat Ucu Yükleme Testi:** Gövde sabitlenerek kanat uçlarına kademeli kum torbaları yerleştirilmiş; $3.5g$ eşdeğeri yük altında sıfır kalıcı deformasyon gözlenmiştir.
*   **Balistik Bırakma Testleri:** 3-DOF RK4 bilgisayarı ile yapılan 10 uçuş testinde ortalama hedef sapması $0.42\text{ m}$ olarak ölçülmüştür.

---

## 7. Görev Puanı Tahminleri ve MDO Çıktıları

Çok disiplinli optimizasyon motorunun çıktılarına göre:
*   **Yer Görevi:** $1.00$
*   **Görev 1 (Staging):** $1.00$ ($99.8\text{ sn}$ ile 3 tam tur)
*   **Görev 2 (Payload):** $3.08$ ($11.2\text{ kg}$ yük ile maksimum verimlilik)
*   **Görev 3 (Delivery):** $4.51$ ($0.42\text{ m}$ hedef hassasiyeti)
*   **Rapor Çarpanı:** $\%94.5$
*   **Toplam Tahmini Skor:** **$9.06 / 10.0$** (Şampiyonluk hedefi).
