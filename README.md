# kapsam_bot

Haftalık iş geri bildirim Excel dosyasını okuyup SQLite veritabanına kaydeden, HPU (haftalık program uyumu) KPI değerlerini hesaplayan ve sonuçları bir Excel Output sayfasına yazan Türkçe bir araçtır. İsteğe bağlı Streamlit arayüzü ile hesaplanan değerler tarayıcıda görselleştirilebilir.

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

Excel dosyalarını `docs/` klasörüne koyun.

```bash
python app/main.py
```

## Kurulum

1. `git clone https://github.com/sngzege/kapsam_bot.git`
   Projeyi bilgisayarınıza indirir.
2. `cd kapsam_bot`
   İndirilen proje klasörüne geçer.
3. `python3 -m venv .venv`
   Proje için ayrı bir çalışma ortamı (venv) oluşturur; bu, programın kendi bağımlılıklarını sistemden ayırır.
4. `source .venv/bin/activate`
   Oluşturulan çalışma ortamını açar. Bundan sonra komut satırının başında `(.venv)` yazısı görünür.
5. `pip install --upgrade pip`
   Paket yükleyicisini (pip) günceller; bu, programın bileşenlerini indiren araçtır.
6. `pip install -r requirements.txt`
   Programın ihtiyaç duyduğu tüm bileşenleri yükler.
7. `python app/main.py`
   Programı çalıştırır.

Yeni bir terminal penceresi açtığınızda ortamı tekrar etkinleştirmeniz gerekir:

```bash
cd ~/dil/kapsam_bot && source .venv/bin/activate
```

Çalışma ortamından çıkmak için `deactivate` yazın.

## Excel Dosyaları

Kendi Excel dosyalarınızı `docs/` klasörüne kendiniz koymalısınız; bu dosyalar gizlilik gereği GitHub deposunda yer almaz (gitignore ile korunur). Gerekli dosyalar:

- `docs/Geri-BildirimPuantaj.xlsx` → veri kaynağı (yalnızca okunur)
- `docs/HPU.xlsx` → hedef dosya (veri buraya aktarılır ve Output sonuçları buraya yazılır)

Bir dosya eksikse program açık bir hata mesajı verir.

## Çalıştırma (Aşama 1)

```bash
python app/main.py
```

Program şu adımları sırayla yapar:

1. Kaynak Excel okunur (`Geri BildirimPuantaj.xlsx`, Geri Bildirim sayfası, 5. satırdan itibaren, AH sütununa kadar).
2. `HPU.xlsx` dosyasının `Geri Bildirim` sayfasına yalnızca değerler (values-only) yazılır. Yazmadan önce `HPU.xlsx` otomatik olarak `docs/backups/` klasörüne yedeklenir.
3. Veriler SQLite veritabanına INSERT/UPDATE edilir (`ID-1` benzersiz anahtarıdır; programı tekrar çalıştırınca çift kayıt oluşmaz, mevcut kayıt güncellenir).
4. K/A/L/P grupları ve E sütunundaki işyeri kodu alt kümeleri hesaplanır.
5. Sonuçlar `Output` sayfasına yazılır.

## Analiz Arayüzü (Aşama 2)

```bash
streamlit run app/dashboard.py
```

Arayüz tarayıcıda otomatik olarak açılır. Açılmazsa `http://localhost:8501` adresine gidin. Filtreler, X/Y ekseni seçimi ve bar/line/scatter grafik tipleri mevcuttur. Kapatmak için terminalde `Ctrl+C` tuşlarına basın.

Arayüz `data/kapsam_bot.db` dosyasından veri okur; bu nedenle en az bir kez `python app/main.py` çalıştırılmış olmalıdır.

## Hesaplanan Değerler

| Grup | Tanım |
|------|-------|
| Grup K | Rapor Tipi "Programlı İş" VE Sahadan Gelen Bilgi "HD"/"Alt"/"Tamam" ile başlayan |
| Grup A | Rapor Tipi "Acil İş" veya "Duruş İşi" |
| Grup L | Rapor Tipi "İlave iş-2 (Saha)" |
| Grup P | Rapor Tipi "Programlı İş" |
| Grup K-1 | K grubunda (Top. Harcanan Süre - Kazanılan Süre) > 100 olanlar |

Output sayfasına yazılan satırlar:

- **TUM tablosu:** satır 8 / 11 / 12 / 15 / 17 / 18 / 19 / 20
- **DIS tablosu:** satır 27 / 30 / 31 / 34 / 36 / 37 / 38 / 39

Hesaplama formülleri:

- `HPU = K / (P - A - L + F)`
- `HPU Kapsam = (K + K1) / (P - A - L + F)`  (F = fazla mesai)

## Veritabanı

Veriler `data/kapsam_bot.db` dosyasında `geri_bildirim` adlı tabloda saklanır. `ID-1` benzersiz anahtardır. Haftalık analizler için `program_haftasi` sütunu tutulur. Veritabanını Aşama 2 arayüzü üzerinden inceleyebilirsiniz.

## Sorun Giderme

- **`python3 bulunamadı`** → `sudo apt install python3 python3-venv` komutunu çalıştırın.
- **`Gerekli Excel dosyası bulunamadı`** → `docs/` klasörünü kontrol edin, dosyaların doğru isimle yer aldığından emin olun.
- **`Excel dosyası açık`** → Dosyayı LibreOffice/Excel'de kapatın ve programı tekrar çalıştırın.
- **Dashboard boş** → Önce `python app/main.py` komutunu çalıştırın.

## Notlar

Hedef ortam Linux/Ubuntu'dur. Windows kullanıcıları çalışma ortamını `.venv\Scripts\activate` komutu ile etkinleştirir.
