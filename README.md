# kapsam_bot

Haftalık iş geri bildirim Excel dosyasını okuyup SQLite veritabanına kaydeden, HPU (haftalık program uyumu) KPI değerlerini hesaplayan ve sonuçları bir Excel Output sayfasına yazan, Türkçe bir masaüstü aracıdır. İsteğe bağlı Streamlit arayüzü ile KPI’lar filtrelenerek dinamik bar / çizgi / dağılım grafiklerinde görselleştirilebilir.

**Hedef kitle:** İnternet erişimi ve paket yüklemesi kısıtlı olan imalat / işyeri bilgisayarları, teknik bilgisi düşük Ubuntu veya Windows kullanıcıları. Tüm bağımlılıklar paketlenmiş (offline/çevrimdışı) olarak dağıtılır.

---

## 📋 İçindekiler

1. [Hızlı Başlangıç](#hızlı-başlangıç)
2. [Kurulum (Linux / Ubuntu)](#kurulum-linux--ubuntu)
3. [Kurulum (Windows — çevrimdışı / offline)](#kurulum-windows--çevrimdışı-offline)
4. [Excel Dosyaları](#excel-dosyaları)
5. [Çalıştırma (Aşama 1 — veri aktarımı)](#çalıştırma-aşama-1--veri-aktarımı)
6. [Analiz Arayüzü (Aşama 2 — Streamlit dashboard)](#analiz-arayüzü-aşama-2--streamlit-dashboard)
7. [Hesaplanan Değerler](#hesaplanan-değerler)
8. [Veritabanı](#veritabanı)
9. [Paketli / Offline Kullanım](#paketli--offline-kullanım)
10. [Sistem Gereksinimleri](#sistem-gereksinimleri)
11. [Sorun Giderme](#sorun-giderme)

---

## Hızlı Başlangıç

Aşağıdaki komutları sırayla kopyalayıp terminale yapıştırın:

```bash
git clone https://github.com/sngzege/kapsam_bot.git
cd kapsam_bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Ardından `docs/` klasörüne Excel dosyalarını koyun ve:

```bash
python app/main.py
```

> Windows kullanıcıları isterslerse **çevrimdışı** kurulum için [bunu okuyun](#kurulum-windows--çevrimdışı-offline).

---

## Kurulum (Linux / Ubuntu)

### 1. Repository'yi indirin

```bash
git clone https://github.com/sngzege/kapsam_bot.git
```

> `git clone`, projeyi GitHub'dan bilgisayarınıza indiren bir komuttur. Linux'ta git kurulu olmalıdır
> (kurulu değilse: `sudo apt install git`).

### 2. Proje klasörüne geçin

```bash
cd kapsam_bot
```

### 3. Sanal ortam oluşturun

```bash
python3 -m venv .venv
```

> `python3 -m venv .venv` komutu, programın kendi kütüphanelerini sistemden ayıracak
> izole bir "sanal çalışma ortamı" (`.venv` klasörü) oluşturur.

### 4. Sanal ortamı etkinleştirin

```bash
source .venv/bin/activate
```

> Bu komuttan sonra komut satırının başında **`(.venv)`** yazısı belirir —
> yani artık bu klasördeki Python kullanılıyor demektir.
>
> **Yeni bir terminal açtığınızda** ortamı yeniden etkinleştirmeniz gerekir:
>
> ```bash
> cd ~/dil/kapsam_bot && source .venv/bin/activate
> ```
>
> Çalışma ortamından çıkmak için: `deactivate`

### 5. pip'yi güncelleyin

```bash
pip install --upgrade pip
```

> `pip`, Python paketlerini (kütüphane) indirip kurmak için kullanılan araçtır.

### 6. Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

> `requirements.txt` dosyasında programın ihtiyaç duyduğu tüm kütüphaneler listelenmiştir.

### 7. Excel dosyalarını yerleştirin

```bash
# docs/ klasörüne dosyalarınızı kopyalayın
cp ~/İndirilenler/Geri-BildirimPuantaj.xlsx docs/
cp ~/İndirilenler/HPU.xlsx docs/
```

---

## Kurulum (Windows — çevrimdışı / offline)

İşyeri bilgisayarınızda internet erişimi yoksa veya paket yükleme kısıtlıysa,
repository'deki `vendor/win/` klasöründeki **paketlenmiş wheel dosyalarını**
kullanarak hiçbir internet erişimi olmadan kurulum yapabilirsiniz.

### 1. Repository'yi indirin (USB / ağ paylaşımı ile)

GitHub'dan klonlayamayan bir bilgisayardaysanız, repository'yi ZIP olarak
indirip USB bellek ile kopyalayın. **ZIP içinde `vendor/win/` klasörü bulunur.**

### 2. Python 3.12 kurun (internet gerekmez)

1. <https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe>
   adresinden **`python-3.12.0-amd64-exe`** dosyasını bir internetli bilgisayarda
   indirin, USB ile taşıyın.

2. Dosyayı çalıştırın → **"Add python.exe to PATH"** kutusunu işaretleyin →
   **"Install Now"** butonuna tıklayın.

> Not: wheel paketleri Python 3.12 içindir (`cp312`). Python 3.10/3.11 kurarsanız
> paketler uyumsuz olur. Mutlaka 3.12 kurun.

### 3. Sanal ortamı oluşturun ve paketleri kurun (internet yok)

```bat
cd kapsam_bot
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip --no-index --find-links=vendor/win
pip install --no-index --find-links=vendor/win openpyxl streamlit pandas plotly
```

> --no-index : pip'in internetten arama yapmasını engeller.
> --find-links : wheel dosyalarını `vendor/win/` klasöründen bulur.

### 4. Kullanım

```bat
.venv\Scripts\activate
python app\main.py
```

---

## Excel Dosyaları

Kendi Excel dosyalarınızı `docs/` klasörüne **kendiniz manuel olarak** koymalısınız.
Bu dosyalar gizlilik gereği GitHub deposunda **değildir** (`.gitignore` ile korunur):

| Dosya | Rol |
|-------|-----|
| `docs/Geri-BildirimPuantaj.xlsx` | Veri kaynağı (yalnızca okunur) |
| `docs/HPU.xlsx` | Hedef dosya (veri buraya aktarılır + Output sonuçları yazılır) |

> Program bir dosyayı bulamazsa açık bir hata mesajı verir.

---

## Çalıştırma (Aşama 1 — veri aktarımı)

```bash
python app/main.py
```

Program şu adımları sırayla yapar:

1. Kaynak Excel okunur (`Geri-BildirimPuantaj.xlsx`, `Geri Bildirim` sayfası, 5. satırdan itibaren, AH sütununa kadar).
2. `HPU.xlsx` dosyasının `Geri Bildirim` sayfasına yalnızca değerler (values-only) yazılır. Yazmadan önce `HPU.xlsx` otomatik olarak `docs/backups/` klasörüne zaman damgasıyla yedeklenir.
3. Veriler SQLite veritabanına INSERT/UPDATE edilir (`ID-1` benzersiz anahtarıdır; programı tekrar çalıştırınca çift kayıt oluşmaz, mevcut kayıt güncellenir).
4. K / A / L / P grupları ve E sütunundaki işyeri kodu alt kümeleri hesaplanır.
5. Sonuçlar `Output` sayfasına yazılır.

---

## Analiz Arayüzü (Aşama 2 — Streamlit dashboard)

```bash
streamlit run app/dashboard.py
```

> Arayüz tarayıcınızda otomatik olarak açılır. Açılmazsa `http://localhost:8501` adresine gidin.

### Özellikler

- **Filtreler (sidebar):** Program Haftası, TUM/DİS kategori, Çalışma Yapan Disiplin, Teknik Birim, Rapor Tipi, Sorumlu Şef, tarih aralığı (Planlanan Başlangıç).
- **Pencere boyutu:** sidebar'daki radio menüden "Geniş" veya "Ortalanmış" seçin.
- **Grafik:** X ekseni (varsayılan: **İşyeri Kodu**), Y ekseni (**birden fazla seçilebilir**), toplulaştırma (Toplam/Ortalama/Adet), grafik tipi (Bar / Line / Scatter).
- **Çoklu değişken çizgi grafiği:** birden fazla Y ekseni seçerseniz aynı grafikte farklı renklerle çizilir.
- **HPU hızlı kartları:** Global HPU ve HPU Kapsam değerleri (DB'den hesaplındı).
- **CSV indirme:** filtrelenmiş ham veriyi (ilk 1000 satır) indirin.
- **Zaman damgası filtresi:** "Tarih aralığına göre filtrele" kutusunu işaretleyin → iki tarih seçin → SQL seviyesinde filtreniniz uygulanır.

> Dashboard `data/kapsam_bot.db` dosyasından okur; bu yüzden en az bir kez
> `python app/main.py` çalıştırmış olmanız gerekir.

---

## Hesaplanan Değerler

| Grup | Tanım |
|------|-------|
| **K** | Rapor Tipi "Programlı İş" **VE** Sahadan Gelen Bilgi "HD"/"Alt"/"Tamam" ile başlayan |
| **A** | Rapor Tipi "Acil İş" veya "Duruş İşi" |
| **L** | Rapor Tipi "İlave iş-2 (Saha)" |
| **P** | Rapor Tipi "Programlı İş" (K bu grubun alt kümesidir) |
| **K-1** | K grubunda (Top. Harcanan Süre − Kazanılan Süre) > 100 |

**Output sayfası satırları** (HPU.xlsx / Output):

- **TUM tablosu:** 8 (fazla mesai), 11 (program işgücü), 12 (kazanılan), 15 (acil), 17 (kapsam art.), 18 (ilave), 19 (HPU), 20 (HPU kapsam)
- **DIS tablosu:** 27, 30, 31, 34, 36, 37, 38, 39

**Formüller:**

- `HPU = K / (P − A − L + F)`  (F = fazla mesai, AE toplamı)
- `HPU Kapsam = (K + K1) / (P − A − L + F)`
- Sıfıra bölme durumunda 0 kullanılır.

---

## Veritabanı

- **Dosya:** `data/kapsam_bot.db` (otomatik oluşur; ilk çalıştırma için `python app/main.py`)
- **Tablo:** `geri_bildirim` (34 sütun, `id_1` PRIMARY KEY)
- **Güncel mekanizması:** `INSERT ... ON CONFLICT(id_1) DO UPDATE` → aynı `ID-1` tekrar geldiğinde güncellenir, duplicate yoktur.
- `program_haftasi` sütunu haftalık analizler için saklanır.
- Dashboard ile doğrudan sorgulanabilir.

---

## Paketli / Offline Kullanım

Repository, internet erişimi olmayan makinelerde de kurulabilmesi için
**Windows wheel'lerini** (`vendor/win/`) içerir:

| Dosya | Açıklama |
|-------|----------|
| `requirements.txt` | Linux/Ubuntu kurulumu için |
| `vendor/win/*.whl` | Windows Python 3.12 için 44 adet offline paket |
| `.gitignore` | `docs/*.xlsx`, `data/*.db`, `vendor/win/` hariç tutulmaz |

> `vendor/win/` paketleri GitHub'da **dahil edilmiştir** (90 MB),
> böylece çevrimdışı kurulum tek tıkla yapılabilir.

---

## Sistem Gereksinimleri

| Bileşen | Minimum | Tavsiye |
|---------|---------|---------|
| OS | Ubuntu 20.04+ / Windows 10+ | Ubuntu 22.04 LTS / Windows 11 |
| Python | **3.12** | 3.12 |
| RAM | 4 GB | 8 GB |
| Disk | 200 MB (program) + Excel dosyaları | 500 MB |
| Excel | LibreOffice veya Microsoft Excel (sadece dosya hazırlığı) | — |

> Python sadece 3.12 desteklenir: paketlenmiş Windows wheel'lari (`cp312`)
> başka sürümlerde çalışmaz. Python 3.12 kurulu değilse [buradan](https://www.python.org/downloads/release/python-3120/)
> (veya `sudo apt install python3.12 python3.12-venv`) temin edin.

---

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `python3 bulunamadı` (Linux) | `sudo apt update && sudo apt install python3.12 python3.12-venv python3.12-distutils` |
| `python bulunamadı` (Windows) | Python'ı https://python.org/downloads/ adresinden indirin. **Add to PATH** kutusu işaretli olmalı. |
| `Gerekli Excel dosyası bulunamadı` | `docs/` klasörüne `Geri-BildirimPuantaj.xlsx` ve `HPU.xlsx` dosyalarını koyun. |
| `Excel dosyası açık` | Excel/LibreOffice'te açık olan dosyayı kapatın, programı yeniden çalıştırın. |
| Dashboard boş / 0 kayıt | Önce `python app/main.py` çalıştırın (veritabanı oluşur). |
| `pip install` internet hatası | Windows kullanıcıysanız `vendor/win/` wheel'lerini --no-index --find-links ile kurun (yukarıda). |
| Streamlit tarayıcıda açılmaz | Tarayıcınızda <http://localhost:8501> adresine girin. |

---

## Notlar

- Hedef ortam **Linux/Ubuntu**'tur; Windows kurulumu için paketli (offline) yöntem önerilir.
- `app/dashboard.py` Streamlit arayüzü ile `app/main.py` pipeline'ı bağımsızdır;
  Aşama 2'yi çalıştırmak için Aşama 1'i tekrar çalıştırmanıza gerekmez
  (sadece `data/kapsam_bot.db` güncel olmalıdır).
- Her geliştirme adımından sonra test → commit → push workflow'u izlenir
  (commit mesajları Türkçe içerir: `feat:`, `fix:`, `docs:`).
