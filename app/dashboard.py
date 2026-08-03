"""Kapsam Bot — Analitik Dashboard (Streamlit + Plotly)

Bu dosya, Aşama 1 hattı tarafından doldurulan SQLite veritabanını
(`data/kapsam_bot.db`, tablo: `geri_bildirim`) okuyarak etkileşimli bir
analiz arayüzü sunar.

Önemli güvenlik ve performans notları:
- Kullanıcıdan gelen DEĞERLER (filtre seçimleri) parametreli SQL ile geçirilir.
- Kullanıcının X/Y ekseni olarak seçtiği KOLON ADLARI, sabit bir whitelist
  üzerinden doğrulanmadan SQL içine yazılmaz.
- Filtreler SQL seviyesinde (WHERE) uygulanır; tüm tablo pandas'e yüklenip
  sonra filtrelenmez.
- Sorgu fonksiyonları `@st.cache_data(ttl=60)` ile önbelleğe alınır ve önbellek
  anahtarına veritabanı dosyasının mtime değeri eklenir; böylece yeni bir
  pipeline çalıştırması önbelleği otomatik geçersiz kılar.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Sabit tanımlar
# ---------------------------------------------------------------------------
# Dosya konumu: app/dashboard.py -> proje kökü -> data/kapsam_bot.db
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kapsam_bot.db"
TABLE = "geri_bildirim"

# Kullanıcının X ekseni olarak seçebileceği kategorik / tarihsel sütunlar.
# (etiket -> veritabanı kolon adı)
X_COLUMNS = {
    "İşyeri Kodu (Çalışma Yapan Disiplin)": "calisma_yapan_disiplin",
    "Program Haftası": "program_haftasi",
    "TUM / GBY": "tum_gby",
    "Sipariş": "siparis",
    "Teknik Birim": "teknik_birim",
    "Rapor Tipi": "rapor_tipi",
    "Sorumlu Şef": "sorumlu_sef",
    "Sorumlu İşyeri / TPY Disiplin": "sorumlu_isyeri_tpy_disiplin",
    "Planlanan Başlangıç Tarihi": "planlanan_baslangic_tarihi",
    "Gerçekleşen Başlangıç Tarihi": "gerceklesen_baslangic_tarihi",
}

# Kullanıcının Y ekseni olarak seçebileceği sayısal sütunlar.
Y_COLUMNS = {
    "Planlanan Süre (dk)": "planlanan_sure_dk",
    "Normal Mesai (dk)": "normal_mesai_dk",
    "Fazla Mesai (dk)": "fazla_mesai_dk",
    "Top. Harcanan Süre (dk)": "top_harcanan_sure_dk",
    "Kazanılan Süre (dk)": "kazanilan_sure_dk",
    "Geribildirim İlerleme": "geribildirim_ilerleme",
    "Metraj 1 Miktar": "metraj1_miktar",
    "Metraj 2 Miktar": "metraj2_miktar",
}

# Sidebar filtrelerinde kullanılan sütunlar (sabit kolon adları).
FILTER_COLUMNS = [
    "program_haftasi",
    "calisma_yapan_disiplin",
    "teknik_birim",
    "rapor_tipi",
    "sorumlu_sef",
]

# Güvenlik: yalnızca bu kümedeki kolon adlarına izin verilir.
ALLOWED_COLUMNS = (
    set(X_COLUMNS.values())
    | set(Y_COLUMNS.values())
    | set(FILTER_COLUMNS)
)

AGG_FUNCS = {"Toplam": "SUM", "Ortalama": "AVG", "Adet": "COUNT"}


def _valid_col(col: str) -> str:
    """Bir kolon adının whitelist içinde olduğunu doğrular.

    Kullanıcı girdisi olarak gelen kolon adları bu kontrolden geçmeden
    SQL ifadesine yazılamaz (SQL enjeksiyonuna karşı koruma).
    """
    if col not in ALLOWED_COLUMNS:
        raise ValueError(f"İzin verilmeyen kolon adı: {col!r}")
    return col


# ---------------------------------------------------------------------------
# Sorgu yardımcıları (önbelleğe alınmış)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def table_exists(db_path: str, mtime: float) -> bool:
    """Hedef tablonun veritabanında var olup olmadığını döndürür."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_distinct(db_path: str, mtime: float, column: str):
    """Belirli bir kolonun DISTINCT değerlerini döndürür (filtre seçenekleri)."""
    _valid_col(column)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            f'SELECT DISTINCT "{column}" FROM {TABLE} '
            f'WHERE "{column}" IS NOT NULL AND "{column}" != "" '
            f'ORDER BY "{column}"'
        )
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def _build_where(f) -> tuple[str, list]:
    """Filtre tuple'ından parametreli bir WHERE cümlesi ve değer listesi üretir.

    `f` tuple sırası:
        (program_haftasi, tum_dis, disiplin, teknik, rapor, sef,
         tarih_etkin, t_start, t_end)
    Kolon adları sabittir; tüm kullanıcı DEĞERLERİ `?` placeholder ile geçirilir.
    """
    (prog, tum_dis, disiplin, teknik, rapor, sef,
     tarih_etkin, t_start, t_end) = f

    clauses: list[str] = []
    params: list = []

    if prog:
        placeholders = ", ".join("?" * len(prog))
        clauses.append(f"program_haftasi IN ({placeholders})")
        params.extend(prog)

    if tum_dis == "tum":
        clauses.append("calisma_yapan_disiplin LIKE 'TUM-%'")
    elif tum_dis == "dis":
        clauses.append("calisma_yapan_disiplin LIKE '%-DIS'")

    if disiplin:
        placeholders = ", ".join("?" * len(disiplin))
        clauses.append(f"calisma_yapan_disiplin IN ({placeholders})")
        params.extend(disiplin)

    if teknik:
        placeholders = ", ".join("?" * len(teknik))
        clauses.append(f"teknik_birim IN ({placeholders})")
        params.extend(teknik)

    if rapor:
        placeholders = ", ".join("?" * len(rapor))
        clauses.append(f"rapor_tipi IN ({placeholders})")
        params.extend(rapor)

    if sef:
        placeholders = ", ".join("?" * len(sef))
        clauses.append(f"sorumlu_sef IN ({placeholders})")
        params.extend(sef)

    if tarih_etkin and t_start and t_end:
        clauses.append("date(planlanan_baslangic_tarihi) >= ?")
        params.append(t_start)
        clauses.append("date(planlanan_baslangic_tarihi) <= ?")
        params.append(t_end)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@st.cache_data(ttl=60)
def get_filtered_rows(db_path: str, mtime: float, f) -> pd.DataFrame:
    """Filtrelere uyan tüm satırları (SQL seviyesinde filtrelenmiş) döndürür."""
    where, params = _build_where(f)
    sql = f"SELECT * FROM {TABLE} {where}"
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_chart_data(db_path: str, mtime: float, f, x_col: str,
                   y_col: str, agg: str) -> pd.DataFrame:
    """Grafik için X'e göre gruplanmış toplulaştırılmış veriyi döndürür."""
    _valid_col(x_col)
    _valid_col(y_col)
    agg_sql = AGG_FUNCS[agg]
    where, params = _build_where(f)
    sql = (
        f'SELECT "{x_col}" AS x, {agg_sql}("{y_col}") AS y '
        f"FROM {TABLE} {where} "
        f'GROUP BY "{x_col}" ORDER BY "{x_col}"'
    )
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Ana uygulama
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Kapsam Bot — Analiz", layout="wide")

    st.title("Kapsam Bot — Analitik Dashboard")
    st.caption(
        "Excel geri bildirim verisinden hesaplanan KPI'ları filtreleyerek "
        "etkileşimli olarak inceleyin."
    )

    # --- Veritabanı varlık kontrolü -------------------------------------
    if not DB_PATH.exists():
        st.error(
            "Veritabanı dosyası bulunamadı: `data/kapsam_bot.db`.\n\n"
            "Lütfen önce veri aktarımını çalıştırın:\n"
            "`python app/main.py`"
        )
        st.stop()

    mtime = DB_PATH.stat().st_mtime

    if not table_exists(str(DB_PATH), mtime):
        st.error(
            "`geri_bildirim` tablosu veritabanında bulunamadı. "
            "Önce Aşama 1 veri aktarımını (`python app/main.py`) tamamlayın."
        )
        st.stop()

    db_str = str(DB_PATH)

    # --- Sidebar: dinamik filtreler -------------------------------------
    st.sidebar.header("Filtreler")

    prog_opts = get_distinct(db_str, mtime, "program_haftasi")
    disiplin_opts = get_distinct(db_str, mtime, "calisma_yapan_disiplin")
    teknik_opts = get_distinct(db_str, mtime, "teknik_birim")
    rapor_opts = get_distinct(db_str, mtime, "rapor_tipi")
    sef_opts = get_distinct(db_str, mtime, "sorumlu_sef")

    sel_prog = st.sidebar.multiselect("Program Haftası", prog_opts)

    tum_dis = st.sidebar.radio(
        "Kategori (TUM / DİS)",
        options=["hepsi", "tum", "dis"],
        format_func=lambda v: {
            "hepsi": "Hepsi",
            "tum": "TUM (TUM-*)",
            "dis": "DİS (*-DIS)",
        }[v],
        horizontal=True,
    )

    sel_disiplin = st.sidebar.multiselect(
        "Çalışma Yapan Disiplin", disiplin_opts
    )
    sel_teknik = st.sidebar.multiselect("Teknik Birim", teknik_opts)
    sel_rapor = st.sidebar.multiselect("Rapor Tipi", rapor_opts)
    sel_sef = st.sidebar.multiselect("Sorumlu Şef", sef_opts)

    tarih_etkin = st.sidebar.checkbox(
        "Tarih aralığına göre filtrele (Planlanan Başlangıç)"
    )
    t_start = None
    t_end = None
    if tarih_etkin:
        tarih_araligi = st.sidebar.date_input(
            "Planlanan Başlangıç Tarihi Aralığı",
            value=(date.today(), date.today()),
        )
        # Kullanıcı tek tarih veya tarih aralığı seçebilir; yalnızca
        # iki tarih seçiliyse filtre uygulanır.
        if isinstance(tarih_araligi, (tuple, list)) and len(tarih_araligi) == 2:
            t_start = tarih_araligi[0].isoformat()
            t_end = tarih_araligi[1].isoformat()

    # Filtreleri hash'lenebilir bir tuple içinde topla (önbellek anahtarı).
    f = (
        tuple(sel_prog),
        tum_dis,
        tuple(sel_disiplin),
        tuple(sel_teknik),
        tuple(sel_rapor),
        tuple(sel_sef),
        bool(tarih_etkin),
        t_start,
        t_end,
    )

    # --- Filtrelenmiş veriyi SQL seviyesinde çek ------------------------
    try:
        df = get_filtered_rows(db_str, mtime, f)
    except Exception as exc:  # pragma: no cover - savunma amaçlı
        st.error(f"Veri sorgulanırken bir hata oluştu: {exc}")
        st.stop()

    # --- KPI kartları ---------------------------------------------------
    st.subheader("Özet Göstergeler (KPI)")
    c1, c2, c3, c4, c5 = st.columns(5)

    def _safe_sum(col: str) -> float:
        if col not in df.columns or len(df) == 0:
            return 0.0
        return float(pd.to_numeric(df[col], errors="coerce").sum())

    c1.metric("Kayıt Sayısı", len(df))
    c2.metric("Planlanan Süre (dk)", round(_safe_sum("planlanan_sure_dk"), 1))
    c3.metric("Top. Harcanan Süre (dk)", round(_safe_sum("top_harcanan_sure_dk"), 1))
    c4.metric("Kazanılan Süre (dk)", round(_safe_sum("kazanilan_sure_dk"), 1))
    c5.metric("Fazla Mesai (dk)", round(_safe_sum("fazla_mesai_dk"), 1))

    # --- Grafik kontrolleri ---------------------------------------------
    st.subheader("Grafik")
    x_keys = list(X_COLUMNS.keys())
    y_keys = list(Y_COLUMNS.keys())
    default_x = "İşyeri Kodu (Çalışma Yapan Disiplin)"
    default_y = "Planlanan Süre (dk)"

    col_x, col_y, col_agg, col_type = st.columns(4)
    x_label = col_x.selectbox("X Ekseni", x_keys, index=x_keys.index(default_x))
    y_label = col_y.selectbox("Y Ekseni", y_keys, index=y_keys.index(default_y))
    agg = col_agg.selectbox("Toplulaştırma", list(AGG_FUNCS.keys()))
    chart_type = col_type.selectbox("Grafik Tipi", ["Bar", "Line", "Scatter"])

    x_col = _valid_col(X_COLUMNS[x_label])
    y_col = _valid_col(Y_COLUMNS[y_label])

    if df.empty:
        st.info("Seçilen filtrelere uygun kayıt bulunamadı.")
    else:
        try:
            chart_df = get_chart_data(db_str, mtime, f, x_col, y_col, agg)
        except Exception as exc:  # pragma: no cover
            st.error(f"Grafik verisi oluşturulurken hata: {exc}")
            chart_df = pd.DataFrame()

        if chart_df.empty:
            st.info("Seçilen eksen ve filtrelerle grafik çizilemedi (veri yok).")
        else:
            title = f"{agg} — {y_label} göre {x_label}"
            if chart_type == "Bar":
                fig = px.bar(chart_df, x="x", y="y", title=title,
                             labels={"x": x_label, "y": y_label})
            elif chart_type == "Line":
                fig = px.line(chart_df, x="x", y="y", title=title,
                              labels={"x": x_label, "y": y_label},
                              markers=True)
            else:  # Scatter
                fig = px.scatter(chart_df, x="x", y="y", title=title,
                                 labels={"x": x_label, "y": y_label})
            fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # --- Ham veri (ilk 1000 satır) + CSV indirme ------------------------
    with st.expander("Filtrelenmiş Ham Veri (ilk 1000 satır)"):
        if df.empty:
            st.write("Gösterilecek veri yok.")
        else:
            st.dataframe(df.head(1000), use_container_width=True)
            csv = df.head(1000).to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="CSV olarak indir",
                data=csv,
                file_name="filtrelenmis_veri.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    main()
