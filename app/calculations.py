"""Output hesaplamaları: toplamlar, kapsam artışı, HPU formülleri."""

from config import (
    COL_AC,
    COL_AE,
    COL_AF,
    COL_AG,
    ISYERI_KODLARI,
    OUTPUT_COLUMNS,
    TOTAL_COL,
)
from filters import cell, to_number


def _sum_col(rows, col_index) -> float:
    """Verilen satır listesinde bir sütunun güvenli toplamı."""
    return sum(to_number(cell(r, col_index)) for r in rows)


def compute_metrics(groups):
    """Her işyeri kodu için ham metrikleri hesaplar.

    Dönüş: {kod: {metrik: değer}}
    """
    result = {}
    for kod in ISYERI_KODLARI:
        # Fazla mesai (F): Output şablonunda satır etiketi "Gerçekleşen Fazla
        # Mesai" olduğu için ana gruplarla sınırlı değildir; ilgili işyeri
        # kodundaki TÜM satırların AE toplamı alınır.
        unique_f = groups["ALL"][kod]

        kapsam_artisi = sum(
            to_number(cell(r, COL_AF)) - to_number(cell(r, COL_AG))
            for r in groups["K1"][kod]
        )

        result[kod] = {
            "fazla_mesai":    _sum_col(unique_f, COL_AE),
            "program_isgucu": _sum_col(groups["P"][kod], COL_AC),
            "kazanilan_sure": _sum_col(groups["K"][kod], COL_AG),
            "acil_harcanan":  _sum_col(groups["A"][kod], COL_AF),
            "ilave_harcanan": _sum_col(groups["L"][kod], COL_AF),
            "kapsam_artisi":  kapsam_artisi,
        }
    return result


def _safe_div(numerator: float, denominator: float) -> float:
    """Sıfıra bölmeye karşı güvenli bölme."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_output(metrics):
    """Output sayfasına yazılacak nihai değerleri üretir.

    Dönüş: {kategori: {sütun_harfi: {metrik: değer}}}
            kategori = "tum" | "dis", sütun harfi D..I
    """
    output = {}
    for kategori, col_map in OUTPUT_COLUMNS.items():
        output[kategori] = {}
        totals = {
            "fazla_mesai": 0.0,
            "program_isgucu": 0.0,
            "kazanilan_sure": 0.0,
            "acil_harcanan": 0.0,
            "ilave_harcanan": 0.0,
            "kapsam_artisi": 0.0,
        }

        for col, kodlar in col_map.items():
            agg = {k: 0.0 for k in totals}
            for kod in kodlar:
                for key in agg:
                    agg[key] += metrics.get(kod, {}).get(key, 0.0)

            # HPU formülleri: payda = P - A - L + F
            payda = (
                agg["program_isgucu"]
                - agg["acil_harcanan"]
                - agg["ilave_harcanan"]
                + agg["fazla_mesai"]
            )
            agg["hpu"] = _safe_div(agg["kazanilan_sure"], payda)
            agg["hpu_kapsam"] = _safe_div(
                agg["kazanilan_sure"] + agg["kapsam_artisi"], payda
            )

            output[kategori][col] = agg
            for key in totals:
                totals[key] += agg[key]

        # TOPLAM sütunu (I): bileşenler toplanır, oranlar toplamdan yeniden hesaplanır
        payda_t = (
            totals["program_isgucu"]
            - totals["acil_harcanan"]
            - totals["ilave_harcanan"]
            + totals["fazla_mesai"]
        )
        totals["hpu"] = _safe_div(totals["kazanilan_sure"], payda_t)
        totals["hpu_kapsam"] = _safe_div(
            totals["kazanilan_sure"] + totals["kapsam_artisi"], payda_t
        )
        output[kategori][TOTAL_COL] = totals

    return output
