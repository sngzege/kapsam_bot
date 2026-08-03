"""Grup filtreleme ve Türkçe karakter normalizasyonu.

Filtrelemede exact match kullanılmaz; contains/startswith mantığı
Türkçe karakter ve büyük/küçük harf farklarına dayanıklı şekilde uygulanır.
"""

import unicodedata

from config import COL_AF, COL_AG, COL_DISIPLIN, COL_GERI, COL_RAPOR, ISYERI_KODLARI, KAPSAM_ARTIS_ESIK

# Türkçe -> ASCII eşlemesi. Sadece unicodedata'ya güvenmek yeterli değildir
# (ör. 'ı' bazı normalizasyonlarda kaybolabilir), bu yüzden açık tablo kullanılır.
_TR_MAP = str.maketrans({
    "ı": "i", "I": "i", "İ": "i", "i": "i",
    "ş": "s", "Ş": "s",
    "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u",
    "ö": "o", "Ö": "o",
    "ç": "c", "Ç": "c",
    "â": "a", "Â": "a",
    "î": "i", "Î": "i",
    "û": "u", "Û": "u",
})


def normalize(value) -> str:
    """Karşılaştırma için metni normalize eder.

    - None/boş -> ""
    - Türkçe karakterler ASCII karşılığına çevrilir
    - küçük harfe indirilir
    - baştaki/sondaki boşluklar ve satır sonları temizlenir
    """
    if value is None:
        return ""
    text = str(value)
    # Unicode birleşik karakterleri ayrıştır (ör. i + combining dot)
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_TR_MAP)
    # Kalan aksanları temizle
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    text = text.lower()
    # Satır sonu / sekme / çoklu boşluk -> tek boşluk
    text = " ".join(text.split())
    return text.strip()


def contains(value, needle: str) -> bool:
    """Normalize edilmiş 'contains' kontrolü."""
    n = normalize(needle)
    return bool(n) and n in normalize(value)


def startswith(value, prefix: str) -> bool:
    """Normalize edilmiş 'startswith' kontrolü."""
    p = normalize(prefix)
    return bool(p) and normalize(value).startswith(p)


def to_number(value) -> float:
    """Hücre değerini güvenli şekilde sayıya çevirir. Boş/geçersiz -> 0.0"""
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text in {"-", "#REF!", "#N/A", "#DIV/0!", "#VALUE!"}:
        return 0.0
    # Türkçe/Avrupa ondalık biçimi: 1.234,56 -> 1234.56
    text = text.replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def cell(row, col_index):
    """1-tabanlı sütun indeksiyle satırdan değer okur (liste/tuple güvenli)."""
    idx = col_index - 1
    if 0 <= idx < len(row):
        return row[idx]
    return None


# --- Ana gruplar ------------------------------------------------------------

def is_group_p(row) -> bool:
    """P grubu: Rapor Tipi (P sütunu) 'Programlı İş' içerir."""
    return contains(cell(row, COL_RAPOR), "Programlı İş")


def is_group_k(row) -> bool:
    """K grubu: P grubu VE Q sütunu HD / Alt / Tamam ile başlar.

    K, P'nin alt kümesidir.
    """
    if not is_group_p(row):
        return False
    q = cell(row, COL_GERI)
    return startswith(q, "HD") or startswith(q, "Alt") or startswith(q, "Tamam")


def is_group_a(row) -> bool:
    """A grubu: Rapor Tipi 'Acil İş' veya 'Duruş İşi' içerir."""
    p = cell(row, COL_RAPOR)
    return contains(p, "Acil İş") or contains(p, "Duruş İşi")


def is_group_l(row) -> bool:
    """L grubu: Rapor Tipi 'İlave iş-2 (Saha)' içerir."""
    return contains(cell(row, COL_RAPOR), "İlave iş-2")


def is_group_k1(row) -> bool:
    """K-1 grubu: K grubunda olup (AF - AG) > 100 olan satırlar."""
    if not is_group_k(row):
        return False
    return (to_number(cell(row, COL_AF)) - to_number(cell(row, COL_AG))) > KAPSAM_ARTIS_ESIK


GROUP_TESTS = {
    "P":  is_group_p,
    "K":  is_group_k,
    "A":  is_group_a,
    "L":  is_group_l,
    "K1": is_group_k1,
    # ALL: fazla mesai (F) hesabı için tüm satırlar. Output şablonundaki
    # "Gerçekleşen Fazla Mesai" satırı ana gruplarla sınırlı değildir.
    "ALL": lambda row: True,
}


# --- Alt kümeler ------------------------------------------------------------

def match_isyeri(row, kod: str) -> bool:
    """E sütunu (Çalışma Yapan Disiplin) verilen işyeri kodunu içeriyor mu?"""
    return contains(cell(row, COL_DISIPLIN), kod)


def isyeri_kodu(row):
    """Satırın işyeri kodunu döndürür; tanımlı kodlardan biri değilse None."""
    for kod in ISYERI_KODLARI:
        if match_isyeri(row, kod):
            return kod
    return None


def build_groups(rows):
    """Tüm satırları ana gruplara ve işyeri koduna göre alt kümelere ayırır.

    Dönüş:
        {
          "P":  {"_all": [...], "MET-DIS": [...], ...},
          "K":  {...}, "A": {...}, "L": {...}, "K1": {...}
        }
    """
    groups = {g: {"_all": []} for g in GROUP_TESTS}
    for g in groups:
        for kod in ISYERI_KODLARI:
            groups[g][kod] = []

    for row in rows:
        kod = isyeri_kodu(row)
        for gname, test in GROUP_TESTS.items():
            if test(row):
                groups[gname]["_all"].append(row)
                if kod:
                    groups[gname][kod].append(row)
    return groups
