# 🎥 AIAA DBF Video Arşivi, Uçuş Hattı Analizleri ve Ders Çıkarılan Hatalar

Bu doküman, geçmiş AIAA DBF yarışmalarının resmî uçuş hattı video kayıtlarını, şampiyon takımların test uçuşu videolarını ve yarışma anında rakiplerin yaşadığı kaza/kırım senaryolarından çıkarılan kritik dersleri içerir.

---

## 1. Resmî AIAA Yarışma ve Uçuş Hattı Kayıtları

*   **AIAA Design/Build/Fly Official YouTube Channel & Livestreams:**
    *   *2025 Tucson Fly-Off Highlights:* X-1 planörünün ana uçaktan ayrılma anı, planörün otonom uçuşa geçişi ve ana uçağın iniş paterni.
    *   *2024 Wichita Fly-Off Highlights:* Sert Kansas rüzgarlarında ($25-35\text{ knot}$) takımların kalkış ve yan rüzgar (crosswind) iniş yaklaşımları.
    *   *2023 Tucson Fly-Off Stream:* Kanat ucu radar podu taşıyan uçakların dönüşlerdeki kanat burulması ve aileron ters dönmesi (aileron reversal) etkileri.
    *   *2022 Wichita Humanitarian Fly-Off:* Şırınga ve faydalı yüklerin hedef çemberine serbest bırakılış anları ve isabet oranları.
*   **Embry-Riddle DBF YouTube Arşivi:**
    *   ERAU Daytona Beach ekibinin rüzgar tüneli testleri, tam ölçekli statik kanat kırma testleri ve 5 dakikalık montaj kutusu prova kayıtları.
*   **FH Joanneum & University of Ljubljana Test Videoları:**
    *   Vakum infüzyon kompozit gövde kalıptan çıkarma süreçleri, F3A pilotaj teknikleri ve kalkış teker kesme (rotation) dinamikleri.

---

## 2. Rakiplerin Uçuş Sırasında Yaşadığı Başarısızlıklar ve Alınan Dersler (Failure Modes)

Videolardan yapılan kare kare incelemeler sonucunda rakiplerin en sık elenme veya kaza yapma nedenleri 5 temel başlıkta toplanmıştır:

### ⚠️ 1. Dönüşlerde Kanat Ucu Perdövitesi (Tip Stall) ve Viril
*   *Gözlenen Hata:* Yüksek kanat açıklığına sahip ($b > 2.5\text{ m}$) takımlar pylon etrafında sert dönüş ($>45^\circ$ bank angle) yaparken kanat ucundaki akış ayrılmış ve uçak aniden virile girerek piste çakılmıştır.
*   *AIAA DBF Önlemi:* Kanat ucuna doğru $-2.0^\circ$ geometrik burulma (aerodynamic washout) uygulanmış ve aileronlar kanat ucundan $\%15$ iç kısma ötelenerek firar kenarı akışı korunmuştur.

### ⚠️ 2. Görev 3 Ani Yük Bırakmada Yunuslama ve Stall
*   *Gözlenen Hata:* Faydalı yük serbest bırakıldığı anda ağırlık merkezinin hızla geriye kayması sebebiyle uçak burnunu aniden yukarı dikmiş (pitch-up), elevatör ters momenti yetişememiş ve uçak havada tutunamayarak düşmüştür.
*   *AIAA DBF Önlemi:* `ucus_kontrol` paketimizdeki `adaptive_pid_controller.cpp` servoya bırakma darbesi gittiği milisaniyede elevatöre $-3.5^\circ$ burun-aşağı trim uygulamakta ve integrali $\%75$ kırparak aşırı salınımı önlemektedir.

### ⚠️ 3. 55 lbs Sınırında İniş Takımı Kırılması
*   *Gözlenen Hata:* 55 lbs maksimum ağırlıkta sert iniş yapan birçok takımın alüminyum veya 3D baskı iniş takımları bükülmüş veya gövdeyi yırtarak pervaneyi yere vurmuştur (Prop Strike DQ).
*   *AIAA DBF Önlemi:* Yay çeliği takviyeli tek parça otoklav kürlü 4 mm karbon iniş takımı bacakları ve $110\text{ mm}$ sünger çekirdekli rulmanlı tekerlekler kullanılmıştır.

### ⚠️ 4. 5 Dakika Kuralında Zaman Aşımı
*   *Gözlenen Hata:* Kanat bağlantılarını alyan civatalarla vidalamaya çalışan takımlar soğukta veya el titremesiyle civatayı yuvaya oturtamamış ve 5 dakikalık süreyi aşarak uçuş hakkını kaybetmiştir.
*   *AIAA DBF Önlemi:* Aletsiz bilyeli kilit pimleri (quick-release ball lock pin) ve kör-geçme konektörlerle montaj süresi **3 dakika 5 saniyeye** indirilmiştir.

---

## 3. Mühendislik Eğitimi ve Ders Videoları

*   **Prof. Mark Drela (MIT) - Düşük Hız Aerodinamiği ve XFOIL Dersleri:** Düşük Reynolds rejiminde laminar ayrılma balonunun yönetimi.
*   **NASA Armstrong Uçuş Araştırma Merkezi:** Model uçak uçuş test teknikleri ve telemetri kalibrasyonu.
*   **Easy Composites Ltd Video Kütüphanesi:** Karbon kumaş vakum infüzyonu, epoksi gaz giderme ve kalıp ayırıcı uygulama protokolleri.
