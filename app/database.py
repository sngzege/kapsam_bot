"""SQLite katmanı: tablo oluşturma ve ID-1 bazlı INSERT/UPDATE (upsert)."""

import sqlite3
from datetime import date, datetime

from config import DB_COLUMNS, DB_PATH, DB_TABLE


def _serialize(value, sql_type: str):
    """Excel hücre değerini SQLite'a uygun tipe dönüştürür."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if sql_type == "REAL":
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text or text == "-":
            return None
        text = text.replace(" ", "")
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None
    if isinstance(value, str):
        return value.strip()
    return str(value)


def connect():
    """Veritabanı bağlantısı açar, dizini yoksa oluşturur."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn):
    """Tabloyu ve indeksleri oluşturur (varsa dokunmaz)."""
    cols = ",\n    ".join(
        f"{name} {sql_type}" + (" PRIMARY KEY" if name == "id_1" else "")
        for _, name, sql_type in DB_COLUMNS
    )
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {DB_TABLE} (\n    {cols},\n    updated_at TEXT\n)"
    )
    # Haftalık analizler için indeks
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{DB_TABLE}_hafta "
        f"ON {DB_TABLE}(program_haftasi)"
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{DB_TABLE}_disiplin "
        f"ON {DB_TABLE}(calisma_yapan_disiplin)"
    )
    conn.commit()


def upsert_rows(conn, rows):
    """Satırları ID-1 anahtarına göre ekler veya günceller.

    Dönüş: (eklenen, guncellenen, atlanan)
    """
    col_names = [name for _, name, _ in DB_COLUMNS]
    placeholders = ", ".join("?" for _ in col_names) + ", ?"  # + updated_at
    update_set = ", ".join(
        f"{name}=excluded.{name}" for name in col_names if name != "id_1"
    )
    sql = (
        f"INSERT INTO {DB_TABLE} ({', '.join(col_names)}, updated_at) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT(id_1) DO UPDATE SET {update_set}, updated_at=excluded.updated_at"
    )

    existing = {r[0] for r in conn.execute(f"SELECT id_1 FROM {DB_TABLE}")}
    now = datetime.now().isoformat(sep=" ", timespec="seconds")

    inserted = updated = skipped = 0
    payload = []
    for row in rows:
        raw_id = row[0] if row else None
        if raw_id is None or str(raw_id).strip() == "":
            skipped += 1
            continue
        key = str(raw_id).strip()
        values = []
        for excel_idx, _name, sql_type in DB_COLUMNS:
            v = row[excel_idx - 1] if excel_idx - 1 < len(row) else None
            values.append(_serialize(v, sql_type))
        values[0] = key
        values.append(now)
        payload.append(values)
        if key in existing:
            updated += 1
        else:
            inserted += 1
            existing.add(key)

    if payload:
        conn.executemany(sql, payload)
        conn.commit()
    return inserted, updated, skipped


def row_count(conn) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {DB_TABLE}").fetchone()[0]
