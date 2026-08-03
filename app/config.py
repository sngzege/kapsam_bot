"""Merkezi yapılandırma: dosya yolları, sütun ve hücre eşlemeleri.

Belirsiz/çelişkili hücre adresleri burada tek noktada tutulur.
Output şablonu (docs/HPU.xlsx -> Output) incelenerek doğrulanmıştır:
  TUM tablosu başlık satırı 5, veri satırları 6-20
  DIS tablosu başlık satırı 24, veri satırları 25-39
  Sütunlar: D=METAL, E=INSAAT, F=ISKELE, G=IZOLE, H=ELK-ENS, I=TOPLAM
"""

from pathlib import Path

# --- Dizinler ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DOCS_DIR / "backups"

SOURCE_XLSX = DOCS_DIR / "Geri-BildirimPuantaj.xlsx"
TARGET_XLSX = DOCS_DIR / "HPU.xlsx"
DB_PATH = DATA_DIR / "kapsam_bot.db"

# --- Worksheet isimleri -----------------------------------------------------
SOURCE_SHEET = "Geri Bildirim"
TARGET_SHEET = "Geri Bildirim"
OUTPUT_SHEET = "Output"

# --- Veri aralığı -----------------------------------------------------------
DATA_START_ROW = 5          # veri 5. satırdan başlar
HEADER_ROW = 3              # ana başlık satırı
LAST_COL = 34               # AH sütunu dahil (A=1 ... AH=34)

# --- Kaynak sütun indeksleri (1-tabanlı) ------------------------------------
COL_ID = 1        # A  ID-1
COL_HAFTA = 2     # B  Program Haftası
COL_TUMGBY = 4    # D  TUM/GBY
COL_DISIPLIN = 5  # E  Çalışma Yapan Disiplin
COL_RAPOR = 16    # P  Rapor Tipi
COL_GERI = 17     # Q  GeriBildirim - Sahadan Gelen Bilgi
COL_AC = 29       # AC Planlanan Süre (dk)
COL_AD = 30       # AD Normal Mesai (dk)
COL_AE = 31       # AE Fazla Mesai (dk)
COL_AF = 32       # AF Toplam Harcanan Süre (dk)
COL_AG = 33       # AG Kazanılan Süre (dk)

# --- SQLite tablo şeması ----------------------------------------------------
DB_TABLE = "geri_bildirim"

# (excel_kolon_index, sql_kolon_adi, sql_tipi)  -- sıra korunur
DB_COLUMNS = [
    (1,  "id_1",                             "TEXT"),
    (2,  "program_haftasi",                  "TEXT"),
    (3,  "sorumlu_isyeri_tpy_disiplin",      "TEXT"),
    (4,  "tum_gby",                          "TEXT"),
    (5,  "calisma_yapan_disiplin",           "TEXT"),
    (6,  "siparis",                          "TEXT"),
    (7,  "bildirim",                         "TEXT"),
    (8,  "islem_no_aktivite_id",             "TEXT"),
    (9,  "siparis_tpy_tanimi",               "TEXT"),
    (10, "teknik_birim",                     "TEXT"),
    (11, "planlanan_baslangic_tarihi",       "TEXT"),
    (12, "planlanan_bitis_tarihi",           "TEXT"),
    (13, "gerceklesen_baslangic_tarihi",     "TEXT"),
    (14, "gerceklesen_bitis_tarihi",         "TEXT"),
    (15, "islem_kisa_metni_aktivite_tanimi", "TEXT"),
    (16, "rapor_tipi",                       "TEXT"),
    (17, "geribildirim_sahadan_gelen_bilgi", "TEXT"),
    (18, "geribildirim_notlar",              "TEXT"),
    (19, "geribildirim_ilerleme",            "REAL"),
    (20, "metraj1_birim",                    "TEXT"),
    (21, "metraj1_miktar",                   "REAL"),
    (22, "metraj1_aciklamalar",              "TEXT"),
    (23, "metraj2_birim",                    "TEXT"),
    (24, "metraj2_miktar",                   "REAL"),
    (25, "metraj2_aciklamalar",              "TEXT"),
    (26, "planlanan_metraj_kod",             "TEXT"),
    (27, "planlanan_metraj_birim",           "TEXT"),
    (28, "planlanan_metraj",                 "TEXT"),
    (29, "planlanan_sure_dk",                "REAL"),
    (30, "normal_mesai_dk",                  "REAL"),
    (31, "fazla_mesai_dk",                   "REAL"),
    (32, "top_harcanan_sure_dk",             "REAL"),
    (33, "kazanilan_sure_dk",                "REAL"),
    (34, "sorumlu_sef",                      "TEXT"),
]

# --- İşyeri kodları ---------------------------------------------------------
# kod -> (kısa isim, kategori)
ISYERI_KODLARI = {
    "INS-DIS": ("insaat",       "dis"),
    "MET-DIS": ("metal",        "dis"),
    "ISK-DIS": ("iskele",       "dis"),
    "IZO-DIS": ("izole",        "dis"),
    "TUM-INS": ("tuminsaat",    "tum"),
    "TUM-MTL": ("tummetal",     "tum"),
    "TUM-ISK": ("tumiskele",    "tum"),
    "TUM-IZO": ("tumizole",     "tum"),
    "TUM-ELK": ("tumelektrik",  "tum"),
    "TUM-ENS": ("tumenstruman", "tum"),
}

# --- Output tablo yerleşimi -------------------------------------------------
# Output sayfası sütunları: her tablo sütunu hangi işyeri kodlarını toplar
OUTPUT_COLUMNS = {
    "tum": {
        "D": ["TUM-MTL"],
        "E": ["TUM-INS"],
        "F": ["TUM-ISK"],
        "G": ["TUM-IZO"],
        "H": ["TUM-ELK", "TUM-ENS"],
    },
    "dis": {
        "D": ["MET-DIS"],
        "E": ["INS-DIS"],
        "F": ["ISK-DIS"],
        "G": ["IZO-DIS"],
        "H": [],  # DIS tarafında ELK/ENS dış hizmet kodu bulunmuyor
    },
}
TOTAL_COL = "I"  # D..H toplamı

# Metrik -> {kategori: satır}
# HPU.xlsx Output şablonu incelenerek doğrulandı.
OUTPUT_ROWS = {
    "fazla_mesai":      {"tum": 8,  "dis": 27},  # AE toplamı (F grubu)
    "program_isgucu":   {"tum": 11, "dis": 30},  # AC toplamı (P grubu)
    "kazanilan_sure":   {"tum": 12, "dis": 31},  # AG toplamı (K grubu)
    "acil_harcanan":    {"tum": 15, "dis": 34},  # AF toplamı (A grubu)
    "kapsam_artisi":    {"tum": 17, "dis": 36},  # K-1: (AF-AG) toplamı
    "ilave_harcanan":   {"tum": 18, "dis": 37},  # AF toplamı (L grubu)
    "hpu":              {"tum": 19, "dis": 38},  # K / (P - A - L + F)
    "hpu_kapsam":       {"tum": 20, "dis": 39},  # (K + K1) / (P - A - L + F)
}

# Şablon doğrulaması için beklenen satır etiketleri (B sütunu ile eşleşmeli)
OUTPUT_ROW_LABELS = {
    8:  "Fazla Mesai",
    11: "Haftalık Program İşgücü",
    12: "Tamamlanan",
    15: "Acil",
    17: "Kapsam Artışı",
    18: "İlave",
    19: "HPU",
    20: "Kapsam",
}

# K-1 eşiği: (AF - AG) > 100
KAPSAM_ARTIS_ESIK = 100
