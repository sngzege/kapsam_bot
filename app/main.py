"""Kapsam Bot — Aşama 1 ana akış.

Kullanım:
    python app/main.py
"""

import sys
import warnings
from pathlib import Path

# app/ dizinini import yoluna ekle (modüller birbirini düz isimle çağırır)
sys.path.insert(0, str(Path(__file__).resolve().parent))

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

import calculations  # noqa: E402
import database  # noqa: E402
import excel_processor as xl  # noqa: E402
import filters  # noqa: E402
from config import ISYERI_KODLARI, OUTPUT_ROWS  # noqa: E402


def _fmt(value) -> str:
    if isinstance(value, float):
        if abs(value) < 10:
            return f"{value:,.4f}"
        return f"{value:,.0f}"
    return str(value)


def run(verbose: bool = True) -> dict:
    """Tüm Aşama 1 akışını çalıştırır ve özet sözlüğü döndürür."""
    log = print if verbose else (lambda *a, **k: None)

    log("=" * 62)
    log("KAPSAM BOT — Aşama 1")
    log("=" * 62)

    # 1-3. Kaynak Excel'i oku
    log("\n[1/6] Kaynak Excel okunuyor...")
    rows = xl.read_source()
    log(f"      {len(rows):,} satır okundu (5. satırdan, AH sütununa kadar)")

    # 4. Hedef Excel'e values-only aktar
    log("\n[2/6] HPU.xlsx yedekleniyor ve veri aktarılıyor...")
    backup = xl.backup_target()
    log(f"      Yedek: docs/backups/{backup.name}")
    wb = xl.open_target()

    template_warnings = xl.verify_output_template(wb)
    for w in template_warnings:
        log(f"      UYARI: {w}")

    transferred = xl.write_data_sheet(wb, rows)
    log(f"      {transferred:,} satır 'Geri Bildirim' sayfasına yazıldı (values-only)")

    # 5. SQLite'a kaydet
    log("\n[3/6] SQLite'a kaydediliyor...")
    conn = database.connect()
    database.init_db(conn)
    inserted, updated, skipped = database.upsert_rows(conn, rows)
    total_db = database.row_count(conn)
    conn.close()
    log(f"      Eklenen : {inserted:,}")
    log(f"      Güncellenen: {updated:,}")
    if skipped:
        log(f"      Atlanan (ID-1 boş): {skipped:,}")
    log(f"      Veritabanı toplam: {total_db:,} kayıt")

    # 6-9. Gruplar
    log("\n[4/6] Gruplar oluşturuluyor...")
    groups = filters.build_groups(rows)
    for gname in ("P", "K", "A", "L", "K1"):
        log(f"      Grup {gname:<2}: {len(groups[gname]['_all']):>5,} satır")

    # 10-13. Hesaplamalar
    log("\n[5/6] Hesaplamalar yapılıyor...")
    metrics = calculations.compute_metrics(groups)
    output = calculations.compute_output(metrics)

    for kategori in ("tum", "dis"):
        toplam = output[kategori]["I"]
        log(
            f"      {kategori.upper():<3} | P={_fmt(toplam['program_isgucu'])} "
            f"K={_fmt(toplam['kazanilan_sure'])} "
            f"A={_fmt(toplam['acil_harcanan'])} "
            f"L={_fmt(toplam['ilave_harcanan'])} "
            f"F={_fmt(toplam['fazla_mesai'])} "
            f"K1={_fmt(toplam['kapsam_artisi'])}"
        )
        log(
            f"          | HPU={toplam['hpu']:.4f}  "
            f"HPU Kapsam={toplam['hpu_kapsam']:.4f}"
        )

    # 14-15. Output'a yaz ve kaydet
    log("\n[6/6] Output sayfasına yazılıyor...")
    written = xl.write_output(wb, output)
    xl.save_target(wb)
    log(f"      {written} hücre güncellendi, HPU.xlsx kaydedildi")

    log("\n" + "=" * 62)
    log("ÖZET")
    log("=" * 62)
    log(f"  Okunan satır          : {len(rows):,}")
    log(f"  Excel'e aktarılan     : {transferred:,}")
    log(f"  SQLite eklenen        : {inserted:,}")
    log(f"  SQLite güncellenen    : {updated:,}")
    log(
        f"  Gruplar               : K={len(groups['K']['_all']):,} "
        f"A={len(groups['A']['_all']):,} "
        f"L={len(groups['L']['_all']):,} "
        f"P={len(groups['P']['_all']):,} "
        f"K1={len(groups['K1']['_all']):,}"
    )
    log(f"  Output                : tamamlandı ({written} hücre)")
    log("  Hata                  : yok")
    log("=" * 62)

    return {
        "read": len(rows),
        "transferred": transferred,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "db_total": total_db,
        "groups": {g: len(groups[g]["_all"]) for g in groups},
        "metrics": metrics,
        "output": output,
        "cells_written": written,
        "warnings": template_warnings,
    }


def main() -> int:
    try:
        run()
        return 0
    except xl.ExcelError as exc:
        print(f"\nHATA:\n{exc}\n", file=sys.stderr)
        return 1
    except Exception as exc:  # beklenmeyen hata
        print(f"\nBEKLENMEYEN HATA: {type(exc).__name__}: {exc}\n", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
