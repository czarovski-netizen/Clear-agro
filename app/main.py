import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

BASE = ROOT / "out" / "base_unificada.xlsx"

from src.data import load_sheets, load_bling_realizado
from src.metrics import compute_kpis, vendedor_performance_period, meta_realizado_mensal, sparkline_last_months, period_label
from src.viz import fmt_brl_abbrev, fmt_brl, fmt_pct, bar_meta_realizado, bar_meta_realizado_single, sparkline

APP_TITLE = "McKinsey Agro CRM"
DEFAULT_YEAR = 2026

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1280px; margin: 0 auto;}
    h1, h2, h3 {color:#1f2a44;}
    div[data-testid="stMetricValue"] {font-size: 20px; white-space: nowrap;}
    div[data-testid="stMetricLabel"] {font-size: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)


def style_table(df: pd.DataFrame, numeric_cols=None):
    if numeric_cols is None:
        numeric_cols = []
    styler = df.style
    # zebra rows
    styler = styler.apply(lambda x: ["background-color: #f7f8fa" if i % 2 else "" for i in range(len(x))], axis=0)
    styler = styler.set_properties(**{"text-align": "left"})
    if numeric_cols:
        styler = styler.set_properties(subset=numeric_cols, **{"text-align": "right"})
    return styler

if st.sidebar.button("Recarregar base"):
    try:
        load_sheets.clear()
    except Exception:
        pass
sheets = load_sheets()
if not sheets:
    st.warning("Base nao encontrada em ./out/base_unificada.xlsx")
    st.stop()

# Sidebar controls
years = set()
for key in ["metas", "realizado"]:
    df = sheets.get(key, pd.DataFrame())
    if not df.empty and "data" in df.columns:
        years.update(df["data"].dt.year.dropna().astype(int).unique().tolist())
years = sorted(years) if years else [DEFAULT_YEAR]

year = st.sidebar.selectbox("Ano", options=years, index=years.index(DEFAULT_YEAR) if DEFAULT_YEAR in years else 0)

months = list(range(1, 13))
month_labels = ["TODOS"] + [pd.Timestamp(year=year, month=m, day=1).strftime("%b").title() for m in months]
month_map = {"TODOS": None}
for m, label in zip(months, month_labels[1:]):
    month_map[label] = m

month_label = st.sidebar.selectbox("Mes", options=month_labels, index=0)
ytd = st.sidebar.checkbox("Ver YTD", value=True)

vendors = ["TODOS"]
if "metas" in sheets and not sheets["metas"].empty and "vendedor" in sheets["metas"].columns:
    vendors += sorted(sheets["metas"]["vendedor"].dropna().unique().tolist())
sel_vendor = st.sidebar.selectbox("Vendedor", options=vendors, index=0)

page = st.sidebar.selectbox(
    "Pagina",
    options=[
        "Executive Cockpit",
        "Pipeline Manager",
        "Performance & Ritmo",
        "Insights & Alertas",
    ],
)

use_bling = st.sidebar.checkbox("Usar realizado do Bling", value=False)
if use_bling:
    br = load_bling_realizado()
    if not br.empty:
        sheets["realizado"] = br
    else:
        st.sidebar.info("Bling: cache nao encontrado. Usando realizado local.")

st.title(APP_TITLE)
period = period_label(year, month_map[month_label], ytd)
st.caption(f"Periodo: {period}")

# Apply vendor filter to metas/realizado
if sel_vendor != "TODOS":
    if "metas" in sheets and "vendedor" in sheets["metas"].columns:
        sheets["metas"] = sheets["metas"][sheets["metas"]["vendedor"] == sel_vendor]
    if "realizado" in sheets and "vendedor" in sheets["realizado"].columns:
        sheets["realizado"] = sheets["realizado"][sheets["realizado"]["vendedor"] == sel_vendor]

# Page A - Executive Cockpit
if page == "Executive Cockpit":
    st.subheader("Executive Cockpit")
    kpis = compute_kpis(sheets, year, month_map[month_label], ytd)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Realizado", fmt_brl_abbrev(kpis.realizado))
    c2.metric("Meta", fmt_brl_abbrev(kpis.meta))
    c3.metric("Atingimento %", fmt_pct(kpis.atingimento_pct))
    c4.metric("Gap (R$)", fmt_brl_abbrev(kpis.gap))
    c5.metric("Pipeline Ponderado", fmt_brl_abbrev(kpis.pipeline_ponderado) if kpis.pipeline_ponderado is not None else "-")
    c6.metric("% c/ Proximo Passo", fmt_pct(kpis.pct_proximo_passo) if kpis.pct_proximo_passo is not None else "-")

    series = meta_realizado_mensal(sheets, year)
    if not series.empty:
        st.subheader("Meta vs Realizado")
        if month_map[month_label] is None or ytd:
            st.altair_chart(bar_meta_realizado(series), width="stretch")
        else:
            single = series[series["data"].dt.month == month_map[month_label]].copy()
            if not single.empty:
                st.altair_chart(bar_meta_realizado_single(single), width="stretch")
                last6 = sparkline_last_months(series, 6)
                if len(last6) >= 3:
                    st.caption("Ultimos 6 meses (realizado)")
                    sp = sparkline(last6)
                    st.altair_chart(sp, width="stretch")
                else:
                    total = last6["receita"].sum() if "receita" in last6.columns else 0
                    avg = last6["receita"].mean() if "receita" in last6.columns else 0
                    best = last6["receita"].max() if "receita" in last6.columns else 0
                    st.info(f"Ultimos 6 meses: Realizado total {fmt_brl_abbrev(total)} | Media {fmt_brl_abbrev(avg)} | Melhor mes {fmt_brl_abbrev(best)}")
            else:
                st.info("Pendencia: sem dados no mes selecionado.")
    else:
        st.info("Pendencia: faltam dados de metas ou realizado com data.")

    # So what
    st.subheader("So what?")
    bullets = []
    perf = vendedor_performance_period(sheets, year, month_map[month_label], ytd)
    if not perf.empty:
        perf = perf.sort_values("gap", ascending=False)
        top_gap = perf.head(3)
        bullets.append("Top gaps vs meta: " + ", ".join(top_gap["vendedor"].tolist()))

        zero_real = perf[(perf["receita"] == 0) & (perf["meta"] > 0)]
        if not zero_real.empty:
            bullets.append("0 realizado (com meta): " + ", ".join(zero_real["vendedor"].head(5).tolist()))

        total = perf["receita"].sum()
        top5 = perf.sort_values("receita", ascending=False).head(5)
        if total > 0:
            share = top5["receita"].sum() / total * 100
            bullets.append(f"Concentracao top 5: {share:.0f}% do realizado")

    # Mes em risco
    if month_map[month_label] is not None and not ytd:
        today = pd.Timestamp.today()
        if today.year == year and today.month == month_map[month_label]:
            esperado = (today.day / today.days_in_month) * kpis.meta
            if kpis.meta > 0 and kpis.realizado < esperado * 0.8:
                bullets.append("Mes em risco: realizado abaixo do esperado")

    # Disciplina
    opps = sheets.get("oportunidades", pd.DataFrame())
    if "data_proximo_passo" in opps.columns:
        sem_passo = opps[opps["data_proximo_passo"].isna()]
        bullets.append(f"Disciplina: {len(sem_passo)} oportunidades sem proximo passo")
    else:
        bullets.append("Pendencia: coluna data_proximo_passo ausente")

    while len(bullets) < 5:
        bullets.append("Pendencia: dados insuficientes para este insight")
    for b in bullets[:5]:
        st.write(f"- {b}")

# Page B - Pipeline Manager
if page == "Pipeline Manager":
    st.subheader("Pipeline Manager")
    opps = sheets.get("oportunidades", pd.DataFrame())
    if opps.empty:
        st.info("Pendencia: aba oportunidades vazia")
    else:
        df = opps.copy()
        if "volume_potencial" in df.columns:
            df["valor"] = df["volume_potencial"]
        if "probabilidade" in df.columns:
            df["prob"] = pd.to_numeric(df["probabilidade"], errors="coerce")
        if "data_proximo_passo" in df.columns:
            df["proximo_passo"] = df["data_proximo_passo"]
        df["oportunidade"] = df.get("oportunidade", df.get("cliente", ""))

        if "canal" in df.columns:
            canal = st.sidebar.multiselect("Canal", sorted(df["canal"].dropna().unique().tolist()))
            if canal:
                df = df[df["canal"].isin(canal)]
        if "etapa" in df.columns:
            etapa = st.sidebar.multiselect("Etapa", sorted(df["etapa"].dropna().unique().tolist()))
            if etapa:
                df = df[df["etapa"].isin(etapa)]

        df["alerta"] = ""
        if "proximo_passo" in df.columns:
            df.loc[df["proximo_passo"].isna(), "alerta"] = "Sem proximo passo"
        if "valor" in df.columns and "prob" in df.columns:
            df["score"] = df["valor"] * (df["prob"].fillna(0) / 100)
        elif "valor" in df.columns:
            df["score"] = df["valor"]
        else:
            df["score"] = None

        cols = ["cliente", "oportunidade", "etapa", "valor", "prob", "proximo_passo", "alerta", "score", "vendedor"]
        view = df[[c for c in cols if c in df.columns]].copy()
        st.dataframe(
            style_table(view, numeric_cols=["valor", "prob", "score"]),
            height=420,
        )

        out = BytesIO()
        view.to_excel(out, index=False, sheet_name="prioridades")
        st.download_button("Exportar Prioridades da Semana", data=out.getvalue(), file_name="prioridades_semana.xlsx")

# Page C - Performance & Ritmo
if page == "Performance & Ritmo":
    st.subheader("Performance & Ritmo")
    perf = vendedor_performance_period(sheets, year, month_map[month_label], ytd)
    if perf.empty:
        st.info("Pendencia: metas/realizado por vendedor nao disponivel")
    else:
        perf = perf.sort_values("gap", ascending=False)
        perf["rank"] = range(1, len(perf) + 1)
        perf_disp = perf.copy()
        perf_disp["meta"] = perf_disp["meta"].apply(fmt_brl_abbrev)
        perf_disp["receita"] = perf_disp["receita"].apply(fmt_brl_abbrev)
        perf_disp["gap"] = perf_disp["gap"].apply(fmt_brl_abbrev)
        perf_disp["atingimento_pct"] = perf_disp["atingimento_pct"].apply(fmt_pct)
        perf_disp = perf_disp[["vendedor", "meta", "receita", "atingimento_pct", "gap", "rank"]]
        topn = st.slider("Top N", min_value=5, max_value=30, value=15)
        st.dataframe(
            style_table(perf_disp.head(topn), numeric_cols=["meta", "receita", "atingimento_pct", "gap", "rank"]),
            height=420,
            column_config={
                "vendedor": st.column_config.TextColumn(width="large"),
                "meta": st.column_config.TextColumn(width="small"),
                "receita": st.column_config.TextColumn(width="small"),
                "atingimento_pct": st.column_config.TextColumn(width="small"),
                "gap": st.column_config.TextColumn(width="small"),
                "rank": st.column_config.NumberColumn(width="small"),
            },
        )

    acts = sheets.get("atividades", pd.DataFrame())
    if acts.empty:
        st.info("Pendencia: sem dados de atividades")

# Page D - Insights & Alertas
if page == "Insights & Alertas":
    st.subheader("Insights & Alertas")
    opps = sheets.get("oportunidades", pd.DataFrame())
    alerts = []

    if "data_proximo_passo" in opps.columns:
        sem_passo = opps[opps["data_proximo_passo"].isna()]
        alerts.append(("Sem proximo passo", len(sem_passo)))
    else:
        alerts.append(("Sem proximo passo", "pendente"))

    for title, val in alerts:
        st.metric(title, val)
