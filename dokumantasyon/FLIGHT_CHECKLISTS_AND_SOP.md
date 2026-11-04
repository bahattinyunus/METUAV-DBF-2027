# 📋 AIAA DBF 2027 Uçuş Kontrol Listeleri ve Standart Operasyon Prosedürleri (SOP)

Bu doküman, yarışma sahasında ve antrenman uçuşlarında uçuş emniyetini en üst seviyede tutmak için pilot, yer kontrol operatörü ve mekanik ekibin harfiyen uygulayacağı resmî kontrol listelerini içerir.

---

## 1. Uçuş Öncesi Hangart Test Listesi (Pre-Flight Hangar Checklist)

- [ ] **Yapısal Kontrol:** Kanat hücum kenarları, karbon spar kilit pimleri ve kontrol yüzey menteşeleri (Aileron, Elevator, Rudder) mekanik boşluksuz.
- [ ] **Bağlantı Elemanları:** Motor montaj vidaları (M4 Loctite kontrolü), iniş takımı bacak cıvataları torklanmış.
- [ ] **Pervane Muayenesi:** 19x12E karbon pervane üzerinde kılcal çatlak, çentik veya balanssızlık yok.
- [ ] **Faydalı Yük Mandalı:** Kilit pimi manuel olarak serbest bırakılıp kurulabiliyor; yük kızak içinde takılmadan serbestçe kayıyor.
- [ ] **Pitot Tüpü:** Hava giriş ve statik delikleri açık, tıkanıklık yok.

---

## 2. 5 Dakika Uçuş Hattı Montaj Geri Sayımı (5-Minute Flight-Line Countdown)

*Hakem kronometreyi başlattığı andan itibaren:*

1.  **[00:00 - 00:25] Kutu Açılışı:** Taşıma sandığı açılır, gövde montaj sehpasına konur.
2.  **[00:25 - 01:10] Kanat Montajı:** Sol ve sağ kanat panelleri karbon borulara itilir; ball-lock pimleri "klik" sesiyle kilitlenir; blind-mate aviyonik konektörlerin oturduğu teyit edilir.
3.  **[01:10 - 01:40] Kuyruk Montajı:** Yatay ve düşey stabilize panelleri süngü kilit ile sabitlenir.
4.  **[01:40 - 02:05] Faydalı Yük:** Medikal kutu / faydalı yük hazneye sürülür; servo mandalı kilit konumuna alınır.
5.  **[02:05 - 02:20] Batarya Bağlantısı:** 6S LiPo cırt bantla sabitlenir, ana güç XT90 soketi ve gövde dışı kırmızı Arming Plug takılır.
6.  **[02:20 - 02:45] Sistem Boot & Kalibrasyon:** Jetson & Pixhawk ayağa kalkar; `fast_boot_calibrator` sensör sıfır kayıklıklarını alır; GPS 3D Fix (HDOP < 1.2) kilitlenir.
7.  **[02:45 - 03:05] Yüzey Testi:** Kontrol yüzeyleri tam sapma kontrolü (Sağ aileron yukarı, sol aşağı; elevatör yukarı/aşağı; rudder sağ/sol).
8.  **[03:05] Onay:** Takım lideri hakeme yeşil uçuş bayrağını kaldırır.

---

## 3. Acil Durum ve Failsafe Prosedürleri (In-Flight Emergency Protocols)

### 3.1 Telemetri veya RC Verici Bağlantı Kopması (Loss of Link)
1.  Otopilot 1.5 saniye içinde sinyal kaybını algılar (`FAILSAFE_HOLD`).
2.  Uçak o anki irtifasını koruyarak pist merkezli güvenli loiter çemberine girer.
3.  Bağlantı 15 saniye içinde geri gelmezse Return-To-Land (RTL) moduna geçer ve pist eşiğine doğru otonom yaklaşma başlatır.

### 3.2 Kritik Batarya Düşüşü (< 3.55V / Hücre)
1.  GCS ekranında kırmızı sesli alarm çalar (`CRITICAL_RTL_BATTERY`).
2.  Uçuş yöneticisi derhal mevcut görevi sonlandırır ve uçağı iniş paternine yönlendirir.

### 3.3 Görev 3 Ani Yük Bırakma Şoku
1.  Yük bırakıldığı anda elevatöre uygulanan otomatik $-3.5^\circ$ trim sayesinde uçak yunuslama yapmadan yatay seyrini sürdürür.
2.  Pilot uçağın tepkisini izler; gerekirse manuel müdahale ile gazı hafifçe keserek hızlanmayı dengeler.
