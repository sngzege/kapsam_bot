"""Kapsam Bot — Analitik Dashboard (Streamlit + Plotly)

Aşama 1 hattı tarafından doldurulan SQLite veritabanını
(`data/kapsam_bot.db`, tablo: `geri_bildirim`) okuyarak etkileşimli
analiz sunar. Ayrıca Output tablosundaki TUM/DIS satırlarından HPU ve
HPU Kapsam değerlerini de hesaplar.

Güvenlik / Performans:
- Kullanıcıdan gelen **değerler** (`?` placeholder) parametreli SQL ile geçirilir.
- Kullanıcının seçtiği **kolon adları** sabit bir whitelist üzerinden doğrulanır;
  asla doğrudan SQL'ye yazılmaz (SQL enjeksiyonuna karşı koruma).
- Filtreler SQL seviyesinde (WHERE) uygulanır; tüm tablo pandas'e yüklenip
  filtrelenmez.
- Sorgular `@st.cache_data` ile önbelleğe alınır; anahtarın mtime'ı
  değiştiğinde (yeni pipeline çalıştırması) önbellek geçersizleşir.

Çalıştırma:  python app/main.py   (önce veri aktar)
            streamlit run app/dashboard.py
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- #
# Sabit tanımlar
# --------------------------------------------------------------------------- #
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kapsam_bot.db"
TABLE = "geri_bildirim"

# Kullanıcının X / Y ekseni olarak seçebileceği (etiket -> kolon) haritalar.
X_COLUMNS = {
    "İşyeri Kodu": "calisma_yapan_disiplin",
    "Program Haftası": "program_haftasi",
    "TUM / GBY": "tum_gby",
    "Sipariş": "siparis",
    "Teknik Birim": "teknik_birim",
    "Rapor Tipi": "rapor_tipi",
    "Sorumlu Şef": "sorumlu_sef",
    "Planlanan Başlangıç Tarihi": "planlanan_baslangic_tarihi",
}
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

# Sidebar filtrelerinde kullanılan sütunlar.
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
    | {"id_1"}
)

AGG_FUNCS = {"Toplam": "SUM", "Ortalama": "AVG", "Adet": "COUNT"}


def _valid_col(col: str) -> str:
    """Kolon adının whitelist içinde olduğunu doğrular.

    Kullanıcı girdisi olarak gelen kolon adları bu kontrolden geçmeden
    SQL ifadesine yazılmaz.
    """
    if col not in ALLOWED_COLUMNS:
        raise ValueError(f"İzin verilmeyen kolon adı: {col!r}")
    return col


# --------------------------------------------------------------------------- #
# Sorgu yardımcıları (önbelleğe alınmış)
# --------------------------------------------------------------------------- #
def _conn(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=60)
def table_exists(db_path: str, mtime: float) -> bool:
    conn = _conn(db_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_distinct(db_path: str, mtime: float, column: str):
    _valid_col(column)
    conn = _conn(db_path)
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
    """Filtre tuple'ından parametreli WHERE cümlesi + değer listesi üretir.

    `f` = (program_haftasi, tum_dis, disiplin, teknik, rapor, sef,
           tarih_etkin, t_start, t_end)
    Kolon adları sabittir; kullanıcı DEĞERLERİ `?` placeholder ile geçirilir.
    """
    (prog, tum_dis, disiplin, teknik, rapor, sef,
     tarih_etkin, t_start, t_end) = f

    clauses: list[str] = []
    params: list = []

    if prog:
        ph = ", ".join("?" * len(prog))
        clauses.append(f"program_haftasi IN ({ph})")
        params.extend(prog)
    if tum_dis == "tum":
        clauses.append("calisma_yapan_disiplin LIKE 'TUM-%'")
    elif tum_dis == "dis":
        clauses.append("calisma_yapan_disiplin LIKE '%-DIS'")

    def _in(col, vals):
        if vals:
            ph = ", ".join("?" * len(vals))
            clauses.append(f'"{col}" IN ({ph})')
            params.extend(vals)

    _in("calisma_yapan_disiplin", disiplin)
    _in("teknik_birim", teknik)
    _in("rapor_tipi", rapor)
    _in("sorumlu_sef", sef)

    if tarih_etkin and t_start and t_end:
        clauses.append("date(planlanan_baslangic_tarihi) >= ?")
        params.append(t_start)
        clauses.append("date(planlanan_baslangic_tarihi) <= ?")
        params.append(t_end)

    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params


@st.cache_data(ttl=60)
def get_filtered_rows(db_path: str, mtime: float, f) -> pd.DataFrame:
    where, params = _build_where(f)
    conn = _conn(db_path)
    try:
        return pd.read_sql_query(f"SELECT * FROM {TABLE} {where}", conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_chart_data(db_path: str, mtime: float, f, x_col: str,
                   y_cols: tuple, agg: str) -> pd.DataFrame:
    """X'e göre gruplandırılmış, birden fazla Y için toplulaştırılmış veri."""
    _valid_col(x_col)
    for y in y_cols:
        _valid_col(y)
    agg_sql = AGG_FUNCS[agg]
    where, params = _build_where(f)
    selects = ", ".join(
        f'{agg_sql}("{y}") AS "{y}"' for y in y_cols
    )
    # x için DISTINCT değerleri de alalım (grup satırlarındaki label)
    conn = _conn(db_path)
    try:
        # X label'ları
        xcur = conn.execute(
            f'SELECT DISTINCT "{x_col}" FROM {TABLE} {where} '
            f'GROUP BY "{x_col}" ORDER BY "{x_col}"',
            params,
        )
        x_labels = [r[0] for r in xcur.fetchall()]
        # Her Y için ayrı topluluk
        df = pd.DataFrame({"_x": x_labels})
        for y in y_cols:
            ycur = conn.execute(
                f'SELECT "{x_col}", {agg_sql}("{y}") AS v '
                f'FROM {TABLE} {where} GROUP BY "{x_col}" ORDER BY "{x_col}"',
                params,
            )
            vals = {r[0]: r[1] for r in ycur.fetchall()}
            df[y] = df["_x"].map(vals).fillna(0)
        df.drop(columns=["_x"], inplace=True)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_hpu_from_db(db_path: str, mtime: float) -> dict:
    """Output tablosuna denk HPU / HPU Kapsam değerlerini DB'den hesaplar.

    HPU = K / (P - A - L + F)   (K: kazanılan süre, P: planlanan, A: acil,
                                 L: ilave, F: fazla mesai)
    """
    conn = _conn(db_path)
    try:
        sums = conn.execute(
            f"SELECT "
            f"  SUM(CASE WHEN rapor_tipi LIKE '%Programlı İş%' THEN 1 ELSE 0 END) AS p_cnt,"
            f"  SUM(planlanan_sure_dk) AS p,"
            f"  SUM(CASE WHEN rapor_tipi LIKE '%Acil İş%' OR rapor_tipi LIKE '%Duruş İşi%' THEN 1 ELSE 0 END) AS a_cnt,"
            f"  SUM(CASE WHEN rapor_tipi LIKE '%Acil İş%' OR rapor_tipi LIKE '%Duruş İşi%' THEN top_harcanan_sure_dk ELSE 0 END) AS a,"
            f"  SUM(CASE WHEN rapor_tipi LIKE '%İlave iş-2%' THEN top_harcanan_sure_dk ELSE 0 END) AS l,"
            f"  SUM(fazla_mesai_dk) AS f,"
            f"  SUM(CASE WHEN rapor_tipi LIKE '%Programlı İş%' AND ("
            f"  geribildirim_sahadan_gelen_bilgi LIKE 'HD%' OR "
            f"  geribildirim_sahadan_gelen_bilgi LIKE 'Alt%' OR "
            f"  geribildirim_sahadan_gelen_bilgi LIKE 'Tamam%' ) "
            f"  THEN kazanilan_sure_dk ELSE 0 END) AS k, "
            f"  SUM(CASE WHEN rapor_tipi LIKE '%Programlı İş%' AND ("
            f"  geribildirim_sahadan_gelen_bilgi LIKE 'HD%' OR "
            f"  geribildirim_sahadan_gelen_bilgi LIKE 'Alt%' OR "
            f"  geribildirim_sahadan_gelen_bilgi LIKE 'Tamam%' ) AND "
            f" (top_harcanan_sure_dk - kazanilan_sure_dk) > 100 "
            f"  THEN (top_harcanan_sure_dk - kazanilan_sure_dk) ELSE 0 END) AS k1 "
            f"FROM {TABLE}"
        ).fetchone()
        p, a, l, f, k, k1 = sums["p"], sums["a"], sums["l"], sums["f"], sums["k"], sums["k1"] or 0
        payda = p - a - l + f
        hpu = (k / payda) if payda else 0.0
        hpu_kapsam = ((k + k1) / payda) if payda else 0.0
        return {"hpu": hpu, "hpu_kapsam": hpu_kapsam}
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Ana uygulama
# --------------------------------------------------------------------------- #
def main() -> None:
    st.set_page_config(page_title="Kapsam Bot — Analiz", layout="wide")

    # --- Pencere boyutu ayarı ------------------------------------------------
    st.sidebar.header("⚙️ Pencere")
    layout = st.sidebar.radio(
        "Sayfa düzeni",
        options=["wide", "centered"],
        format_func=lambda v: "Geniş" if v == "wide" else "Ortalanmış",
        horizontal=True,
    )
    if layout != "wide":
        st.markdown(
            "<style> .main .block-container { max-width: 900px; }</style>",
            unsafe_allow_html=True,
        )

    st.title("Kapsam Bot — Analitik Dashboard")
    st.caption(
        "Excel geri bildirim verisinden hesaplanan KPI'ları filtreleyerek "
        "etkileşimli grafiklerle inceleyin."
    )

    # --- Veritabanı kontrolü ------------------------------------------------
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

    # --- Sidebar: dinamik filtreler ------------------------------------------
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
        format_func=lambda v: {"hepsi": "Hepsi", "tum": "TUM (TUM-*)",
                               "dis": "DİS (*-DIS)"}[v],
        horizontal=True,
    )
    sel_disiplin = st.sidebar.multiselect("Çalışma Yapan Disiplin", disiplin_opts)
    sel_teknik = st.sidebar.multiselect("Teknik Birim", teknik_opts)
    sel_rapor = st.sidebar.multiselect("Rapor Tipi", rapor_opts)
    sel_sef = st.sidebar.multiselect("Sorumlu Şef", sef_opts)

    tarih_etkin = st.sidebar.checkbox("Tarih aralığına göre filtrele (Planlanan Başlangıç)")
    t_start = t_end = None
    if tarih_etkin:
        tarih_araligi = st.sidebar.date_input(
            "Planlanan Başlangıç Tarihi Aralığı",
            value=(date.today(), date.today()),
        )
        if isinstance(tarih_araligi, (tuple, list)) and len(tarih_araligi) == 2:
            t_start = tarih_araligi[0].isoformat()
            t_end = tarih_araligi[1].isoformat()

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

    # --- KPI kartları -------------------------------------------------------
    st.subheader("Özet Göstergeler (KPI)")
    try:
        df = get_filtered_rows(db_str, mtime, f)
    except Exception as exc:  # savunma
        st.error(f"Veri sorgulanırken bir hata oluştu: {exc}")
        st.stop()

    def _safe_sum(col: str) -> float:
        if col not in df.columns or len(df) == 0:
            return 0.0
        return float(pd.to_numeric(df[col], errors="coerce").sum())

    cols = st.columns(5)
    cols[0].metric("Kayıt Sayısı", len(df))
    cols[1].metric("Planlanan Süre (dk)", round(_safe_sum("planlanan_sure_dk"), 1))
    cols[2].metric("Kazanılan Süre (dk)", round(_safe_sum("kazanilan_sure_dk"), 1))
    cols[3].metric("Top. Harcanan Süre (dk)", round(_safe_sum("top_harcanan_sure_dk"), 1))
    cols[4].metric("Fazla Mesai (dk)", round(_safe_sum("fazla_mesai_dk"), 1))

    # HPU hızlı kart (DB'den global olarak hesaplanır, filtrelere göre değil)
    hpu = get_hpu_from_db(db_str, mtime)
    hcol1, hcol2 = st.columns(2)
    hcol1.metric("HPU (Küresel)", f"{hpu['hpu']:.4f}")
    hcol2.metric("HPU Kapsam (Küresel)", f"{hpu['hpu_kapsam']:.4f}")

    # --- Grafik kontrolleri -------------------------------------------------
    st.subheader("Grafik")
    x_keys = list(X_COLUMNS.keys())
    y_keys = list(Y_COLUMNS.keys())
    default_x = "İşyeri Kodu"
    default_y = "Planlanan Süre (dk)"

    col_x, col_y_multi, col_agg, col_type = st.columns([1, 2, 1, 1])
    x_label = col_x.selectbox("X Ekseni", x_keys, index=x_keys.index(default_x))
    # ÇOKLU Y SEÇİMİ
    y_labels = col_y_multi.multiselect(
        "Y Ekseni (birden fazla seçilebilir)",
        y_keys,
        default=[default_y],
    )
    if not y_labels:
        st.warning("En az bir Y ekseni seçin.")
        st.stop()
    agg = col_agg.selectbox("Toplulaştırma", list(AGG_FUNCS.keys()))
    chart_type = col_type.selectbox("Grafik Tipi", ["Bar", "Line", "Scatter"])

    x_col = _valid_col(X_COLUMNS[x_label])
    y_cols = tuple(_valid_col(Y_COLUMNS[y]) for y in y_labels)

    if df.empty:
        st.info("Seçilen filtrelere uygun kayıt bulunamadı.")
    else:
        try:
            chart_df = get_chart_data(db_str, mtime, f, x_col, y_cols, agg)
        except Exception as exc:
            st.error(f"Grafik verisi oluşturulurken hata: {exc}")
            chart_df = pd.DataFrame()

        if chart_df.empty or chart_df.shape[0] == 0:
            st.info("Seçilen eksen ve filtrelerle grafik çizilemedi (veri yok).")
        else:
            title = f"{agg} — {', '.join(y_labels)} göre {x_label}"
            if chart_type == "Bar":
                # Çoklu Y için gruplanmış bar
                if len(y_cols) > 1:
                    fig = go.Figure()
                    for y in y_cols:
                        fig.add_trace(go.Bar(
                            name=y, x=chart_df.index, y=chart_df[y],
                            text=chart_df[y].round(1), textposition="auto",
                        ))
                    fig.update_layout(barmode="group", legend_title_text="Metrik")
                else:
                    fig = px.bar(chart_df, x=chart_df.index, y=y_cols[0],
                                 labels={"x": x_label}, title=title)
            elif chart_type == "Line":
                # ÇOKLU DEĞİŞKEN ÇİZGİ GRAFİĞİ
                fig = go.Figure()
                for y in y_cols:
                    fig.add_trace(go.Scatter(
                        name=y, x=chart_df.index, y=chart_df[y],
                        mode="lines+markers",
                    ))
                fig.update_layout(legend_title_text="Metrik")
            else:  # Scatter
                fig = go.Figure()
                for y in y_cols:
                    fig.add_trace(go.Scatter(
                        name=y, mode="markers",
                        x=chart_df.index, y=chart_df[y],
                    ))
                fig.update_layout(legend_title_text="Metrik")

            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title=x_label,
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Ham veri + CSV -----------------------------------------------------
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
