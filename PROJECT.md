# KAPSAM BOT — HERMES AGENT PROJE UYGULAMA PROMPTU

Sen bu projede **uçtan uca çalışan bir coding agent** olarak görev yapacaksın. Projeyi analiz et, gerekli dosya ve klasörleri oluştur, Python uygulamasını geliştir, SQLite veritabanını kur, Excel veri işleme ve filtreleme mantığını uygula, çıktıları `Output` worksheet'ine yaz ve test ederek çalışan bir sistem teslim et.

Kullanıcıdan gereksiz onay isteme. Projeyi doğrudan başlat ve tamamla.

---

## 1. PROJE DİZİNİ

Ana proje dizini:

```text
~/dil/kapsam_bot
```

Excel dosyalarının bulunduğu dizin:

```text
~/dil/kapsam_bot/docs
```

Kaynak Excel:

```text
~/dil/kapsam_bot/docs/Geri-BildirimPuantaj.xlsx
```

Hedef Excel:

```text
~/dil/kapsam_bot/docs/HPU.xlsx
```

---

# 2. PROJENİN AMACI

Bu proje, `Geri-BildirimPuantaj.xlsx` içerisindeki verileri okuyacak, gerekli verileri `HPU.xlsx` dosyasına taşıyacak, verileri belirlenen kurallara göre filtreleyip gruplandıracak, hesaplamaları yapacak ve sonuçları `HPU.xlsx` dosyasındaki `Output` worksheet'ine belirlenen hücrelere yazacaktır.

Ayrıca veri taşıma aşamasında alınan veriler SQLite veritabanında saklanacaktır.

Program her çalıştırıldığında aynı verilerin tekrar tekrar eklenmesi engellenmelidir.

---

# 3. TEKNOLOJİ

Ana programlama dili:

```text
Python
```

Gerekirse destekleyici olarak kullanılabilir:

```text
HTML
YAML
Config dosyaları
```

Excel işlemleri için uygun ve güvenilir bir Python kütüphanesi kullan.

SQLite için Python'ın SQLite desteğini kullanabilirsin.

Proje mümkün olduğunca sade, modüler ve sürdürülebilir olsun.

---

# 4. VERİ İŞLEME KATMANI

## 4.1 Veri Kaynağı

Veriyi şu Excel dosyasından oku:

```text
~/dil/kapsam_bot/docs/Geri-BildirimPuantaj.xlsx
```

Kaynak worksheet:

```text
Geri Bildirim
```

Veri işlemlerinde başlangıç satırı:

```text
5
```

Yani filtreleme ve hesaplamalarda satır 5'ten itibaren bulunan veri dikkate alınacaktır.

---

# 5. AŞAMA 1 — EXCEL VERİ TAŞIMA

Kaynak dosya:

```text
~/dil/kapsam_bot/docs/Geri-BildirimPuantaj.xlsx
```

Kaynak worksheet:

```text
Geri Bildirim
```

Kaynak verinin:

```text
5. satırdan
AH sütununa kadar
AH dahil
```

olan kısmını al.

Veriyi **values-only** olarak kopyala.

Hedef dosya:

```text
~/dil/kapsam_bot/docs/HPU.xlsx
```

Hedef worksheet:

```text
Geri Bildirim
```

Hedefte:

```text
5. satırdan itibaren
```

yaz.

Formülleri veya Excel formül bağlantılarını taşımaya çalışma. Sadece hücre değerlerini taşı.

Program tekrar çalıştırıldığında eski veri ile yeni veri arasında gereksiz duplicate oluşmasını engelle.

---

# 6. VERİ FİLTRELEME

Tüm filtreleme sonuçlarında:

```text
5. satırdan itibaren
```

olan verileri dikkate al.

Filtreleme yaparken mümkün olduğunca `exact match` kullanma.

Genel kural:

```text
contains / startswith
```

mantığını kullan.

Özellikle Türkçe karakterlerde encoding kaynaklı problemlere karşı dayanıklı bir normalizasyon yaklaşımı uygula.

Örneğin:

```text
HD DEVAM (Haftaya Devam eden uzun iş)
```

için hücre:

```text
HD
```

ile başlıyorsa eşleşsin.

Benzer şekilde:

```text
Alt İŞ ADIMI TAMAM
```

için:

```text
Alt
```

ile başlayanlar eşleşsin.

```text
TAMAM (Ana İş Tamam)
```

için:

```text
Tamam
```

ile başlayanlar eşleşsin.

Filtreleme mantığında büyük/küçük harf ve Türkçe karakter farklılıklarını mümkün olduğunca normalize et.

---

# 7. ANA GRUPLAR

## GRUP K

`HPU.xlsx` içindeki:

```text
P sütunu = Programlı İş
```

olan satırlar içerisinden Q sütunu aşağıdaki durumlardan birine uyanları K grubuna dahil et:

```text
HD ile başlayan
Alt ile başlayan
Tamam ile başlayan
```

Yani K grubu mantıksal olarak:

```text
P contains "Programlı İş"
AND
(
    Q startswith "HD"
    OR
    Q startswith "Alt"
    OR
    Q startswith "Tamam"
)
```

---

## GRUP A

P sütununda aşağıdakilerden biri bulunanları A grubuna dahil et:

```text
Acil İş
Duruş İşi
```

`contains` mantığını kullan.

---

## GRUP L

P sütununda:

```text
İlave iş-2 (Saha)
```

bulunanları L grubuna dahil et.

`contains` mantığını kullan.

---

## GRUP P

P sütununda:

```text
Programlı İş
```

bulunan tüm satırlardır.

K grubu, P grubunun bir alt kümesidir.

---

# 8. ALT KÜMELER

E sütunundaki işyeri kodlarına göre alt kümeler oluştur.

Kullanılacak kodlar:

```text
INS-DIS
MET-DIS
TUM-INS
TUM-MTL
ISK-DIS
TUM-ISK
TUM-IZO
IZO-DIS
TUM-ELK
TUM-ENS
```

Örneğin:

```text
F-insaat
```

şu anlama gelir:

```text
F grubundaki
E sütunu contains "INS-DIS" olan satırlar
```

Aynı mantık tüm gruplarda uygulanacaktır.

---

## K ALT KÜMELERİ

```text
K-insaat       = K + E contains "INS-DIS"
K-metal        = K + E contains "MET-DIS"
K-tuminsaat    = K + E contains "TUM-INS"
K-tummetal     = K + E contains "TUM-MTL"
K-iskele       = K + E contains "ISK-DIS"
K-izole        = K + E contains "IZO-DIS"
K-tumelektrik  = K + E contains "TUM-ELK"
K-tumenstruman = K + E contains "TUM-ENS"
K-tumiskele    = K + E contains "TUM-ISK"
K-tumizole     = K + E contains "TUM-IZO"
```

---

## A VE L ALT KÜMELERİ

A ve L grupları için K grubunda kullanılan aynı E sütunu kodlarını kullan.

Örnek:

```text
L-tummetal = L grubu + E contains "TUM-MTL"

A-metal = A grubu + E contains "MET-DIS"
```

Aynı mantıkla bütün kombinasyonları oluştur.

---

# 9. GRUP K-1

K grubundaki satırlar içerisinde:

```text
AF - AG > 100
```

olanları K-1 grubuna dahil et.

Her satır için:

```text
AF değerinden AG değerini çıkar.
```

Sonuç:

```text
100'den büyükse
```

K-1 grubuna dahil et.

---

# 10. İŞYERİ KODLARI

E sütunundaki kodların anlamları:

```text
INS-DIS  = insaat
MET-DIS  = metal
ISK-DIS  = iskele
IZO-DIS  = izole
TUM-IZO  = tumizole
TUM-ELK  = tumelektrik
TUM-ENS  = tumenstruman
TUM-ISK  = tumiskele
TUM-INS  = tuminsaat
TUM-MTL  = tummetal
```

Kod isimlerini output değişkenlerinde kullan.

---

# 11. TUM VE DIS AYRIMI

Her output için iki ayrı kategori bulunacaktır:

```text
tum
dis
```

`TUM-*` kodları `tum` tablosuna/kategorisine aittir.

`*-DIS` kodları `dis` tablosuna/kategorisine aittir.

Bu ayrım tüm hesaplamalarda aynı şekilde uygulanmalıdır.

Örneğin:

```text
TUM-MTL -> tum
TUM-INS -> tum
TUM-ISK -> tum
TUM-IZO -> tum
TUM-ELK -> tum
TUM-ENS -> tum

MET-DIS -> dis
INS-DIS -> dis
ISK-DIS -> dis
IZO-DIS -> dis
```

---

# 12. OUTPUT HESAPLAMALARI

Sonuçları:

```text
HPU.xlsx
```

içindeki:

```text
Output
```

worksheet'ine yaz.

Aşağıdaki hücre konumlarını aynen kullan.

---

## 12.1 FAZLA MESAİ

Her F alt kümesi için:

```text
AE sütunundaki değerlerin toplamını hesapla.
```

Örnek:

```text
F-insaat -> AE toplamı
F-iskele -> AE toplamı
```

### TUM — Satır 8

```text
D8 = fazla_mesai-tum-mtl
E8 = fazla_mesai-tum-ins
F8 = fazla_mesai-tum-isk
G8 = fazla_mesai-tum-izo
H8 = fazla_mesai-tum-elk + fazla_mesai-tum-ens
I8 = D8 + E8 + F8 + G8 + H8
```

### DIS — Satır 27

```text
D27 = fazla_mesai-met-dis
E27 = fazla_mesai-ins-dis
F27 = fazla_mesai-isk-dis
G27 = fazla_mesai-izo-dis
H27 = ilgili ELK + ENS toplamı
I27 = D27 + E27 + F27 + G27 + H27
```

---

## 12.2 PROGRAM İŞGÜCÜ / PLANLANAN SÜRE

Her işyeri kodu için:

```text
AC sütunundaki değerlerin toplamını hesapla.
```

Output isimlendirme mantığı:

```text
planlanan_sure-<kod>
```

### TUM — Satır 11

```text
D11 = program_isgucu-tum-mtl
E11 = program_isgucu-tum-ins
F11 = program_isgucu-tum-isk
G11 = program_isgucu-tum-izo
H11 = program_isgucu-tum-elk + program_isgucu-tum-ens
I11 = D11 + E11 + F11 + G11 + H11
```

### DIS — Satır 30

```text
D30 = program_isgucu-met-dis
E30 = program_isgucu-ins-dis
F30 = program_isgucu-isk-dis
G30 = program_isgucu-izo-dis
H30 = ilgili ELK + ENS toplamı
I30 = D30 + E30 + F30 + G30 + H30
```

Not: Kaynak dokümanda bazı DIS hücreleri `D27`, `E27` vb. olarak yazılmıştır ancak bölüm başlığı `row=30` demektedir. Uygulama sırasında `Output` worksheet'inin gerçek şablonunu incele. Şablondaki yapı ile dokümandaki tanım çelişiyorsa bunu otomatik olarak kontrol et ve doğru satırı belirle. Rastgele varsayım yapma.

---

## 12.3 KAZANILAN SÜRE

K grubunun tüm alt kümeleri için:

```text
AG sütunundaki değerlerin toplamını hesapla.
```

### TUM

```text
Satır 12
```

### DIS

```text
Satır 31
```

Her işyeri kodu için ilgili K alt kümesinin AG toplamını yaz.

---

## 12.4 ACİL HARCANAN SÜRE

A grubunun tüm alt kümeleri için:

```text
AF sütunundaki değerlerin toplamını hesapla.
```

### TUM

```text
Satır 15
```

### DIS

```text
Satır 34
```

Her işyeri kodu için ilgili A alt kümesinin AF toplamını yaz.

---

## 12.5 İLAVE HARCANAN SÜRE

L grubunun tüm alt kümeleri için:

```text
AF sütunundaki değerlerin toplamını hesapla.
```

### TUM

```text
Satır 18
```

### DIS

```text
Satır 37
```

Her işyeri kodu için ilgili L alt kümesinin AF toplamını yaz.

---

## 12.6 KAPSAM ARTIŞI

K-1 grubunu kullan.

K-1 şartı:

```text
AF - AG > 100
```

Her K-1 satırı için:

```text
AF - AG
```

değerini hesapla.

Tüm K-1 satırlarının bu değerlerini topla.

### TUM

```text
Satır 17
```

### DIS

```text
Satır 36
```

İlgili TUM ve DIS işyeri kodlarına göre değerleri hesapla.

---

## 12.7 HPU KAPSAM

Formül:

```text
hpu_kapsam =
(planlanan_sure + kapsam_artis)
/
(
    planlanan_sure
    - acil_harcanan_sure
    - ilave_harcanan_sure
    + fazla_mesai
)
```

### TUM

```text
Satır 20
```

### DIS

```text
Satır 39
```

Her işyeri kodu için formülü uygula.

Sıfıra bölme durumlarını güvenli şekilde ele al.

---

## 12.8 HPU

Formül:

```text
hpu =
planlanan_sure
/
(
    planlanan_sure
    - acil_harcanan_sure
    - ilave_harcanan_sure
    + fazla_mesai
)
```

### TUM

```text
Satır 19
```

### DIS

```text
Satır 38
```

Sıfıra bölme durumlarını güvenli şekilde ele al.

---

# 13. SQLITE DATABASE

Aşama 1 veri taşıma sırasında alınan verileri SQLite veritabanına kaydet.

Veritabanında bir tablo oluştur:

```text
Geri-Bildirim
```

Ancak SQLite tablo ve sütun isimleri için güvenli SQL identifier kullan.

Kaynak Excel'deki sütun isimlerini SQLite'a aktar.

Sütun isimleri:

* Küçük/büyük harf farklılıklarını normalize et.
* Türkçe karakterleri ASCII/universal karakterlere dönüştür.
* SQL açısından güvenli isimler oluştur.
* Sütun sırasını koru.

---

# 14. SQLITE TABLO ŞEMASI

Excel sütunları ve karşılıkları:

```text
A  = ID-1
B  = Program Haftası
C  = Sorumlu İşyeri/ TPY Disiplin
D  = TUM/GBY
E  = Çalışma Yapan Disiplin
F  = Sipariş
G  = Bildirim
H  = İşlem No/Aktivite ID
I  = Sipariş / TPY Tanımı
J  = Teknik Birim
K  = Planlanan Başlangıç Tarihi
L  = Planlanan Bitiş Tarihi
M  = Gerçekleşen Başlangıç Tarihi
N  = Gerçekleşen Bitiş Tarihi
O  = İşlem Kısa Metni / Aktivite Tanımı
P  = Rapor Tipi
Q  = GeriBildirim-Sahadan Gelen Bilgi
R  = GeriBildirim-Notlar
S  = GeriBildirim-İlerleme
T  = METRAJ1-Birim
U  = METRAJ1-Miktar
V  = METRAJ1-Açıklamalar
W  = METRAJ2-Birim
X  = METRAJ2-Miktar
Y  = METRAJ2-Açıklamalar
Z  = Planlanan Metraj-KOD & Kaynak x Birim Süre
AA = Planlanan-Metraj-Birim
AB = Planlanan-Metraj
AC = Planlanan Süre (dk)
```

SQL tablo kolonlarını bu sırayı koruyarak oluştur.

---

# 15. DATABASE UNIQUE KURALI

A sütunu:

```text
ID-1
```

benzersiz anahtar olarak kullanılacaktır.

SQL'de duplicate `ID-1` bulunmamalıdır.

Program arka arkaya çalıştırıldığında:

```text
aynı ID-1 varsa yeni kayıt ekleme,
mevcut kaydı yeni gelen veriyle güncelle.
```

Yani davranış:

```text
ID-1 yoksa -> INSERT
ID-1 varsa -> UPDATE
```

Son veri, eski verinin üzerine yazılmalıdır.

B sütunu:

```text
Program Haftası
```

ileride haftalık analizler yapılacağı için korunmalıdır.

İleride bu sütuna göre:

```text
haftalık artış
haftalık değişim
haftalık karşılaştırma
```

gibi analizler yapılabilmesi için veri yapısını buna uygun tasarla.

---

# 16. UYGULAMA MİMARİSİ

Projeyi gereksiz karmaşıklaştırma.

Basit ve anlaşılır bir yapı kur.

Önerilen yapı:

```text
~/dil/kapsam_bot/
├── docs/
│   ├── Geri-BildirimPuantaj.xlsx
│   └── HPU.xlsx
├── app/
│   ├── main.py
│   ├── excel_processor.py
│   ├── filters.py
│   ├── calculations.py
│   └── database.py
├── data/
│   └── kapsam_bot.db
├── requirements.txt
├── README.md
└── ...
```

Gerekli değilse ekstra dosya oluşturma.

Kodları modüler tut ancak overengineering yapma.

---

# 17. UYGULAMA AKIŞI

Program çalıştırıldığında aşağıdaki sırayı izle:

```text
1. Kaynak Excel'i aç.
2. Kaynak "Geri Bildirim" worksheet'ini oku.
3. 5. satırdan AH sütununa kadar olan verileri al.
4. Values-only veriyi HPU.xlsx -> Geri Bildirim worksheet'ine 5. satırdan yaz.
5. Aynı verileri SQLite'a INSERT/UPDATE ile kaydet.
6. HPU.xlsx verilerini satır 5'ten itibaren oku.
7. K, A, L ve P ana gruplarını oluştur.
8. E sütununa göre alt kümeleri oluştur.
9. K-1 grubunu oluştur.
10. TUM/DIS ayrımını uygula.
11. AE, AC, AG ve AF sütunları üzerinden gerekli toplamları hesapla.
12. Kapsam artışı hesapla.
13. HPU ve HPU Kapsam formüllerini hesapla.
14. Sonuçları HPU.xlsx -> Output worksheet'inde doğru hücrelere yaz.
15. Excel dosyasını kaydet.
16. İşlem sonucunu terminalde anlaşılır şekilde raporla.
```

---

# 18. VERİ TİPLERİ VE HATA YÖNETİMİ

Excel'deki sayısal sütunlarda:

```text
AE
AF
AG
AC
```

boş hücre veya sayısal olmayan değerler olabilir.

Bunları güvenli şekilde işle.

Gerekirse:

```text
boş -> 0
```

olarak değerlendir.

Ancak veri kaybına neden olacak şekilde orijinal Excel verisini değiştirme.

`AF - AG` hesaplamasında her iki değeri güvenli şekilde sayıya dönüştür.

Sıfıra bölme durumlarında program çökmemeli.

Eksik worksheet veya dosya varsa anlaşılır hata mesajı üret.

---

# 19. ÇELİŞKİLİ / BELİRSİZ TANIMLAR

Kaynak gereksinimlerde bazı hücre adresleri ile bölüm satırları arasında çelişki olabilir.

Örneğin:

```text
program_isgucu
```

bölümü:

```text
DIS row=30
```

derken bazı hücreler:

```text
D27
E27
F27
G27
H27
I27
```

olarak verilmiştir.

Bu tür durumlarda:

1. `HPU.xlsx` dosyasındaki `Output` worksheet'ini incele.
2. Hücrelerin çevresindeki başlıkları ve tablo yapısını kontrol et.
3. `TUM` ve `DIS` tablolarının gerçek satırlarını belirle.
4. Gereksinimdeki satır tanımı ile Excel şablonu arasında uyuşmazlık varsa Excel şablonunu esas al.
5. Kod içerisinde bu hücreleri merkezi bir mapping/config yapısında tut.
6. Rastgele veya sessizce yanlış hücreye yazma.

Benzer çelişkileri diğer outputlar için de kontrol et.

---

# 20. TEST

Uygulama tamamlandıktan sonra mutlaka test et.

En azından:

```text
- Excel dosyası açılıyor mu?
- Kaynak worksheet mevcut mu?
- Hedef worksheet mevcut mu?
- Veri 5. satırdan taşınıyor mu?
- AH sütununa kadar veri taşınıyor mu?
- Values-only aktarım çalışıyor mu?
- SQLite oluşturuluyor mu?
- ID-1 unique çalışıyor mu?
- Aynı ID tekrar çalıştırıldığında UPDATE oluyor mu?
- K grubu doğru oluşuyor mu?
- A grubu doğru oluşuyor mu?
- L grubu doğru oluşuyor mu?
- P grubu doğru oluşuyor mu?
- E alt kümeleri doğru oluşuyor mu?
- K-1 filtresi doğru çalışıyor mu?
- TUM/DIS ayrımı doğru mu?
- AE toplamları doğru mu?
- AC toplamları doğru mu?
- AG toplamları doğru mu?
- AF toplamları doğru mu?
- HPU formülü doğru mu?
- HPU kapsam formülü doğru mu?
- Output hücrelerine doğru değerler yazılıyor mu?
- Sıfıra bölme durumunda program çökmüyor mu?
```

Test için mümkünse küçük bir örnek veri seti veya mevcut Excel verisi üzerinden doğrulama yap.

---

# 21. ÇALIŞTIRMA

Projeyi tamamladıktan sonra kullanıcı tarafından kolayca çalıştırılabilir hale getir.

Örneğin:

```bash
cd ~/dil/kapsam_bot
python3 app/main.py
```

şeklinde çalışabilsin.

Gerekli Python bağımlılıklarını:

```text
requirements.txt
```

içerisinde belirt.

README dosyasında:

```text
Kurulum
Bağımlılıkların kurulması
Çalıştırma
Dosya yolları
SQLite veritabanı
Programın yaptığı işlemler
```

kısa ve anlaşılır şekilde açıklansın.

---

# 22. ÖNEMLİ ÇALIŞMA KURALLARI

* Projeyi sadece açıklama seviyesinde bırakma.
* Dosyaları gerçekten oluştur.
* Kodları gerçekten yaz.
* Mevcut Excel dosyalarını incele.
* `Output` worksheet'inin gerçek yapısını kontrol et.
* Uygulamayı çalıştır.
* Hataları düzelt.
* Mümkün olan testleri gerçekleştir.
* Gereksiz framework veya mimari ekleme.
* Gereksiz karmaşıklaştırma yapma.
* Kullanıcının verdiği filtre ve hesaplama kurallarını değiştirme.
* Belirsiz hücre adreslerini Excel şablonunu inceleyerek çöz.
* Veri aktarımında values-only kullan.
* SQLite'ta `ID-1` duplicate oluşmasına izin verme.
* Aynı `ID-1` tekrar geldiğinde yeni veriyle güncelle.
* Program birden fazla kez çalıştırıldığında güvenli ve idempotent davran.
* İşlem sonunda terminalde kısa bir özet göster:

  * kaç satır okundu
  * kaç satır Excel'e aktarıldı
  * kaç kayıt SQLite'a eklendi
  * kaç kayıt güncellendi
  * kaç satır K/A/L/P grubuna girdi
  * Output işlemi tamamlandı mı
  * hata varsa ne olduğu

Proje tamamlanmadan görevi bitmiş kabul etme.

Önce mevcut proje dizinini ve Excel dosyalarını incele, sonra implementasyona geç.
# 23. GITHUB VE VERSION CONTROL

Proje Git repository olarak yönetilecektir.

GitHub repository:

```text
https://github.com/sngzege/kapsam_bot
```

Her anlamlı geliştirme veya güncelleme tamamlandığında:

1. Kodun çalıştığını kontrol et.
2. Testleri çalıştır.
3. Hataları düzelt.
4. Değişiklikleri Git'e commit et.
5. Commit'i GitHub repository'sine push et.

Her tamamlanan geliştirme adımı için anlamlı commit mesajları kullan.

Örnek:

```text
feat: implement Excel data transfer
feat: add SQLite upsert logic
feat: implement group filtering
feat: add Output calculations
fix: correct output cell mapping
docs: improve installation instructions
feat: add interactive analytics dashboard
```

Commit ve push işlemlerini sadece çalışan ve doğrulanmış değişikliklerden sonra yap.

Bir geliştirme tamamlanmadan yarım veya kırık kodu commit edip pushlama.

Her güncelleme sonunda repository'nin güncel ve çalışır durumda olması hedeflenmelidir.

GitHub'a push yapılmadan önce:

```text
git status
```

ile değişiklikleri kontrol et.

Yanlışlıkla Excel dosyalarını veya hassas kullanıcı verilerini commit etme.

---

# 24. EXCEL DOSYALARININ GIT'TEN DIŞLANMASI

`docs` klasörü içerisindeki Excel dosyaları Git repository'ye gönderilmeyecektir.

`.gitignore` dosyası oluştur veya mevcut `.gitignore` dosyasını güncelle.

Aşağıdaki dosya türlerini `docs` içerisinde ignore et:

```text
docs/*.xlsx
docs/*.xls
docs/*.xlsm
docs/*.xlsb
```

Gerekirse geçici Excel dosyalarını da ignore et:

```text
docs/~$*
```

Kullanıcının kendi Excel dosyaları GitHub'a pushlanmamalıdır.

Ancak proje çalışabilmesi için `docs` klasörünün kendisi repository içerisinde bulunabilir.

Gerekirse:

```text
docs/.gitkeep
```

kullan.

---

# 25. README — KULLANICININ EXCEL DOSYALARINI YERLEŞTİRMESİ

Kullanıcı Excel dosyalarını kendisi `docs` klasörüne koyacaktır.

README.md içerisinde bu durum açıkça belirtilmelidir.

README içerisinde aşağıdaki gibi net bir bölüm bulunmalıdır:

```text
## Excel Dosyaları

Projeyi çalıştırmadan önce gerekli Excel dosyalarını `docs` klasörüne kendiniz yerleştirin.

Gerekli dosyalar:

docs/
├── Geri-BildirimPuantaj.xlsx
└── HPU.xlsx
```

Açıklama:

```text
Geri-BildirimPuantaj.xlsx
→ Veri kaynağı olarak kullanılır.

HPU.xlsx
→ Verilerin aktarıldığı ve Output sonuçlarının yazıldığı hedef Excel dosyasıdır.
```

Excel dosyaları GitHub repository'sinde bulunmaz.

Kullanıcı repository'yi clone ettikten sonra Excel dosyalarını manuel olarak:

```text
~/dil/kapsam_bot/docs/
```

klasörüne koymalıdır.

Program gerekli Excel dosyaları bulunmuyorsa anlaşılır bir hata mesajı vermelidir.

Örneğin:

```text
Gerekli Excel dosyası bulunamadı:

docs/Geri-BildirimPuantaj.xlsx

Lütfen Excel dosyasını docs klasörüne yerleştirin ve programı tekrar çalıştırın.
```

---

# 26. PYTHON VENV VE KURULUM

Python sanal ortamı düzgün şekilde yapılandırılmalıdır.

Repository içerisinde `.venv` veya `venv` klasörü Git'e gönderilmemelidir.

`.gitignore` içerisine ekle:

```text
.venv/
venv/
__pycache__/
*.py[cod]
```

Python bağımlılıklarını:

```text
requirements.txt
```

dosyasında tanımla.

README içerisinde kurulum talimatlarını, Linux/Ubuntu kullanıcısının **Python, CLI veya virtual environment konusunda hiçbir bilgisi olmadığını varsayarak** yaz.

Kullanıcı yalnızca kopyala-yapıştır yaparak sistemi kurabilmelidir.

README'deki kurulum bölümü aşağıdaki mantıkta olmalıdır:

```text
## Kurulum

### 1. Repository'yi indirin

Terminali açın ve aşağıdaki komutu çalıştırın:

git clone https://github.com/sngze/kapsam_bot.git

### 2. Proje klasörüne girin

cd kapsam_bot

### 3. Python sanal ortamını oluşturun

python3 -m venv .venv

### 4. Sanal ortamı aktif edin

source .venv/bin/activate

### 5. Gerekli paketleri yükleyin

pip install --upgrade pip
pip install -r requirements.txt

### 6. Excel dosyalarını docs klasörüne koyun

Gerekli Excel dosyalarını docs klasörüne kopyalayın.

### 7. Programı çalıştırın

python app/main.py
```

README'de her komutun ne yaptığı kısa ve basit şekilde açıklanmalıdır.

Windows ve Linux arasında farklılık varsa kullanıcıya ayrıca açıkça belirt.

Projenin hedef ortamı Linux/Ubuntu ise öncelik Linux/Ubuntu kurulumuna ver.

Kullanıcı `venv` nedir, terminal nedir veya `pip` nedir bilmiyor olsa bile README'yi takip ederek projeyi çalıştırabilmelidir.

---

# 27. VENV AKTİVASYONU

README'de sanal ortam aktif edildiğinde terminal satırının başında örneğin:

```text
(.venv)
```

görüneceğini belirt.

Kullanıcı yeni bir terminal açarsa sanal ortamın tekrar aktif edilmesi gerektiğini açıkla:

```bash
cd ~/dil/kapsam_bot
source .venv/bin/activate
```

Programı çalıştırma:

```bash
python app/main.py
```

Sanal ortamdan çıkmak için:

```bash
deactivate
```

komutunu README'de açıkla.

Kullanıcıya gereksiz CLI komutları öğretme. Sadece gerekli komutları ver.

---

# 28. README KURULUM AKIŞI

README'nin başında mümkün olduğunca basit bir "Hızlı Başlangıç" bölümü oluştur.

Kullanıcı için ideal akış:

```text
1. GitHub repository'yi clone et.
2. Proje klasörüne gir.
3. Venv oluştur.
4. Venv'i aktif et.
5. Requirements'ları yükle.
6. Excel dosyalarını docs klasörüne koy.
7. Programı çalıştır.
```

Her adım için doğrudan kopyalanabilir CLI komutları ver.

Örneğin kullanıcı tüm temel kurulum için aşağıdaki komutları sırayla kopyalayıp çalıştırabilsin:

```bash
git clone https://github.com/sngze/kapsam_bot.git
cd kapsam_bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Daha sonra Excel dosyalarını:

```text
docs/
```

klasörüne koyması gerektiğini belirt.

Ardından:

```bash
python app/main.py
```

ile programı çalıştırabilsin.

---

# 29. PROJE AŞAMALARI

Projeyi iki ana aşama halinde geliştir.

## AŞAMA 1 — VERİ İŞLEME VE EXCEL ÇIKTISI

Aşama 1 kapsamında:

```text
Excel -> Python -> SQLite
              |
              +-> HPU.xlsx
              |
              +-> Output worksheet
```

akışı çalışır hale getir.

Aşama 1 tamamlandığında:

* Excel verileri alınmalı.
* SQLite'a kaydedilmeli.
* Duplicate kayıtlar engellenmeli.
* Gruplar ve alt gruplar hesaplanmalı.
* Output sonuçları oluşturulmalı.
* HPU.xlsx güncellenmeli.
* Testler yapılmalı.
* Git commit oluşturulmalı.
* GitHub'a push yapılmalı.

Aşama 1 tamamen çalışan ve doğrulanmış hale gelmeden Aşama 2'ye geçme.

---

# 30. AŞAMA 2 — DİNAMİK VERİ ANALİZİ VE GRAFİK ARAYÜZÜ

Aşama 1 tamamlandıktan sonra proje için ikinci aşama olarak opsiyonel bir dinamik grafik ve veri analiz arayüzü oluştur.

Bu özellik mümkünse ayrı bir modül veya ayrı bir uygulama olarak tasarlanabilir.

Amaç:

```text
SQLite Database
       ↓
Data Analysis Interface
       ↓
Dynamic Filters
       ↓
Interactive Charts
```

Kullanıcı SQLite veritabanındaki verileri grafiksel olarak inceleyebilmelidir.

---

# 31. AŞAMA 2 — DİNAMİK FİLTRELEME

Grafik arayüzünde kullanıcı mümkün olduğunca fazla anlamlı filtreleme seçeneğine sahip olmalıdır.

Örneğin:

```text
Program Haftası
Tarih
TUM / DIS
Çalışma Yapan Disiplin
Teknik Birim
Rapor Tipi
İşyeri Kodu
Program Tipi
```

gibi veritabanında gerçekten mevcut olan alanlar filtre olarak sunulabilir.

Filtreler dinamik çalışmalıdır.

Kullanıcı:

```text
Belirli bir tarih
Tarih aralığı
Belirli bir program haftası
Belirli bir işyeri
Belirli bir disiplin
```

gibi seçimler yapabilmelidir.

Filtre seçenekleri doğrudan SQLite verisinden üretilebilir.

Veritabanında olmayan veya anlamsız filtreleri sırf arayüzü büyütmek için ekleme.

---

# 32. AŞAMA 2 — DİNAMİK X VE Y EKSENİ

Kullanıcı grafik oluştururken:

```text
X Ekseni
Y Ekseni
```

seçebilmelidir.

Kullanıcı istediği iki sütunu karşılaştırabilmelidir.

Örneğin:

```text
X = Program Haftası
Y = Planlanan Süre
```

veya:

```text
X = Tarih
Y = Gerçekleşen Süre
```

veya:

```text
X = İşyeri Kodu
Y = Fazla Mesai
```

gibi grafikler oluşturulabilmelidir.

X ve Y ekseni seçenekleri SQLite'daki uygun veri alanlarından dinamik olarak oluşturulmalıdır.

Sayısal olmayan alanlar Y ekseni için varsayılan olarak gösterilmeyebilir.

---

# 33. DEFAULT GRAFİK

Grafik arayüzü ilk açıldığında varsayılan grafik olarak:

```text
X Ekseni = İşyeri Kodlamaları
Y Ekseni = Kullanıcının seçebileceği sayısal bir metrik
```

kullanılmalıdır.

İşyeri kodlamaları, projede kullanılan:

```text
INS-DIS
MET-DIS
TUM-INS
TUM-MTL
ISK-DIS
TUM-ISK
TUM-IZO
IZO-DIS
TUM-ELK
TUM-ENS
```

gibi işyeri kodlarıdır.

Varsayılan grafik, mevcut veri yapısına göre en anlamlı sayısal metriği göstermelidir.

Ancak kullanıcı X ve Y eksenlerini değiştirebilmelidir.

---

# 34. GRAFİK DEĞİŞKENLERİ

Kullanıcı aşağıdaki seçenekleri arayüz üzerinden değiştirebilmelidir:

```text
X ekseni
Y ekseni
Filtreler
Tarih / tarih aralığı
Program haftası
İşyeri kodu
Grup
Alt grup
Grafik tipi
```

En azından aşağıdaki grafik tiplerinden uygun olanları destekle:

```text
Bar Chart
Line Chart
Scatter Plot
```

Grafik tipi seçimi opsiyonel olabilir ancak kullanıcı deneyimini iyileştirecek şekilde tasarlanmalıdır.

Grafik, kullanıcı seçimlerini değiştirdiğinde yeniden oluşturulmalıdır.

---

# 35. GRAFİK ARAYÜZÜ İÇİN TEKNOLOJİ

Aşama 2 için Python tabanlı, kurulumu kolay bir çözüm tercih et.

Örneğin uygun görürsen:

```text
Streamlit
Plotly
```

kullanabilirsin.

Amaç:

```text
SQLite -> Python -> Interactive Web UI
```

oluşturmaktır.

Kullanıcı mümkün olduğunca az CLI komutu kullanarak arayüzü çalıştırabilmelidir.

README'ye örneğin:

```bash
streamlit run app/dashboard.py
```

gibi doğrudan çalıştırılabilir komutu ekle.

Arayüzün nasıl açılacağını ve tarayıcıdan nasıl erişileceğini README'de açıkça anlat.

---

# 36. AŞAMA 2 OPSİYONEL ÇALIŞMA

Aşama 2, Aşama 1'in çalışmasını bozmamalıdır.

Aşama 1:

```text
python app/main.py
```

ile çalışmaya devam etmelidir.

Aşama 2:

```text
streamlit run app/dashboard.py
```

gibi ayrı bir komutla çalıştırılabilir.

Aşama 2 arayüzü doğrudan:

```text
data/kapsam_bot.db
```

SQLite veritabanını okuyabilir.

Aşama 1 çalıştırıldığında SQLite güncellendiğinde, Aşama 2 arayüzü en güncel verileri okuyabilmelidir.

---

# 37. AŞAMA 2 GÜVENLİK VE PERFORMANS

SQL sorgularında kullanıcı tarafından girilen değerleri doğrudan SQL string'ine ekleme.

Parametreli sorgular kullan.

Kullanıcının X/Y ekseni olarak seçebileceği sütunları whitelist üzerinden kontrol et.

Veritabanı kolon adlarını doğrudan kullanıcı girdisi olarak SQL'e gönderme.

Büyük veri setlerinde gereksiz yere tüm veriyi her işlemde tekrar tekrar yükleme.

Filtreleri mümkün olduğunca SQL seviyesinde uygula.

---

# 38. AŞAMA 2 TEST VE GITHUB WORKFLOW

Aşama 2 tamamlandığında:

1. Dashboard'ı çalıştır.
2. SQLite verisini okuyabildiğini doğrula.
3. Filtrelerin çalıştığını doğrula.
4. X ekseni seçiminin çalıştığını doğrula.
5. Y ekseni seçiminin çalıştığını doğrula.
6. En az birkaç farklı grafik oluştur.
7. Tarih/tarih aralığı filtresini test et.
8. İşyeri kodu filtresini test et.
9. Uygulama hata veriyorsa düzelt.
10. README'yi güncelle.
11. Testleri tekrar çalıştır.
12. Git commit oluştur.
13. GitHub'a push et.

Örnek commit:

```text
feat: add interactive SQLite analytics dashboard
```

---

# 39. SON TESLİM KRİTERLERİ

Proje tamamlandığında aşağıdaki yapı çalışır durumda olmalıdır:

```text
GitHub Repository
        │
        ├── app/
        │   ├── main.py
        │   ├── excel_processor.py
        │   ├── filters.py
        │   ├── calculations.py
        │   ├── database.py
        │   └── dashboard.py
        │
        ├── docs/
        │   └── .gitkeep
        │
        ├── data/
        │   └── kapsam_bot.db
        │
        ├── requirements.txt
        ├── .gitignore
        └── README.md
```

Kullanıcı:

1. Repository'yi clone eder.
2. Venv oluşturur.
3. Requirements'ları yükler.
4. Excel dosyalarını `docs` klasörüne koyar.
5. `python app/main.py` çalıştırır.
6. Excel verileri SQLite'a aktarılır.
7. HPU.xlsx güncellenir.
8. Output sonuçları oluşturulur.
9. İsterse dashboard'ı çalıştırır.
10. SQLite verilerini filtreleyerek dinamik grafikler oluşturur.

Tüm süreç README'de teknik bilgisi olmayan bir kullanıcının takip edebileceği şekilde anlatılmalıdır.

Her anlamlı geliştirme tamamlandığında:

```text
Test
↓
Commit
↓
Push
```

workflow'unu uygula.

Projeyi yarım bırakma. Aşama 1'i tamamen tamamla, doğrula ve pushla. Ardından Aşama 2'yi geliştir, doğrula ve pushla.
