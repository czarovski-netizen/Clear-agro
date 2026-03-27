from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parents[1]
SNAPSHOT_PATH = BASE_DIR / "data" / "latest_snapshot.json"
LOGO_CANDIDATES = [
    WORKSPACE_ROOT / "02_financeiro" / "CLEAR logo.png",
    WORKSPACE_ROOT / "data" / "CLEAR.png",
]
MONTH_NAMES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


st.set_page_config(
    page_title="Clear Agro Financeiro",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --brand-ink: #193326;
            --brand-green: #2f6548;
            --brand-sage: #eef5ef;
            --brand-gold: #b88b2f;
            --brand-line: #d5ddd3;
            --brand-card: rgba(255,255,255,0.8);
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(184,139,47,0.16), transparent 24%),
                linear-gradient(180deg, #f8f4ea 0%, #fbfcf8 20%, #f1f7f0 100%);
        }
        .block-container {
            max-width: 1420px;
            padding-top: 1.1rem;
            padding-bottom: 2rem;
        }
        html, body, [class*="css"] {
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        }
        h1, h2, h3 {
            color: var(--brand-ink);
        }
        h1 {
            font-size: 3rem !important;
            line-height: 1 !important;
            letter-spacing: 0.02em;
            margin-bottom: 0.35rem !important;
        }
        h2 {
            font-size: 1.6rem !important;
            margin-top: 1rem !important;
            padding-bottom: 0.2rem;
            border-bottom: 1px solid var(--brand-line);
        }
        h3 {
            font-size: 1.04rem !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .hero-title-wrap {
            padding: 5.2rem 0 0.8rem 0;
        }
        .hero-title {
            font-size: 2.8rem;
            line-height: 1;
            font-weight: 700;
            margin: 0;
            color: var(--brand-ink);
            letter-spacing: 0.01em;
        }
        .hero-header {
            display: flex;
            align-items: flex-start;
            justify-content: flex-start;
            gap: 28px;
            margin-bottom: 0.8rem;
        }
        .hero-title-box {
            flex: 1 1 auto;
            min-width: 0;
        }
        .hero-logo-box {
            flex: 0 0 34%;
            padding-top: 4.2rem;
        }
        .section-note {
            background: rgba(255,255,255,0.76);
            border: 1px solid var(--brand-line);
            border-left: 6px solid var(--brand-gold);
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin-bottom: 1rem;
            color: #46584c;
        }
        div[data-testid="stMetric"] {
            background: var(--brand-card);
            border: 1px solid var(--brand-line);
            border-radius: 18px;
            padding: 0.9rem 1rem 1rem 1rem;
            box-shadow: 0 10px 22px rgba(25,51,38,0.05);
        }
        div[data-testid="stMetricLabel"] {
            color: #617166;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.72rem;
        }
        div[data-testid="stMetricValue"] {
            color: var(--brand-ink);
            font-size: 1rem;
            line-height: 1.2;
            word-break: break-word;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .sidebar-logo {
            display: flex;
            justify-content: center;
            margin: -0.2rem 0 1rem 0;
        }
        .sidebar-box {
            background: rgba(255,255,255,0.78);
            border: 1px solid var(--brand-line);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-top: 0.8rem;
        }
        .dre-column {
            background: rgba(255,255,255,0.82);
            border: 1px solid var(--brand-line);
            border-radius: 18px;
            padding: 1rem 1rem 0.9rem 1rem;
            min-height: 560px;
            box-shadow: 0 10px 22px rgba(25,51,38,0.05);
        }
        .dre-column h4 {
            margin: 0 0 0.75rem 0;
            color: var(--brand-ink);
            font-size: 0.98rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .dre-total {
            margin: 0.8rem 0 0.55rem 0;
            padding-top: 0.7rem;
            border-top: 1px solid var(--brand-line);
            font-weight: 700;
            color: var(--brand-ink);
        }
        .dre-line {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            padding: 0.22rem 0;
            font-size: 0.92rem;
            color: #31463a;
        }
        .dre-line-label {
            flex: 1 1 auto;
        }
        .dre-line-value {
            flex: 0 0 auto;
            text-align: right;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }
        .dre-note {
            margin-top: 0.55rem;
            font-size: 0.8rem;
            color: #617166;
        }
        .dre-matrix-wrap {
            border: 1px solid var(--brand-line);
            border-radius: 18px;
            background: rgba(255,255,255,0.86);
            box-shadow: 0 10px 22px rgba(25,51,38,0.05);
            overflow: auto;
            max-height: 680px;
        }
        .dre-matrix {
            width: max-content;
            min-width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.82rem;
            color: #31463a;
            text-transform: uppercase;
        }
        .dre-matrix th,
        .dre-matrix td {
            padding: 0.5rem 0.62rem;
            border-bottom: 1px solid rgba(213,221,211,0.9);
            white-space: nowrap;
        }
        .dre-matrix thead th {
            position: sticky;
            top: 0;
            z-index: 4;
            background: #f4f8f1;
            color: var(--brand-ink);
            letter-spacing: 0.04em;
        }
        .dre-matrix .dre-matrix-account {
            position: sticky;
            left: 0;
            z-index: 3;
            min-width: 260px;
            max-width: 260px;
            white-space: pre-wrap;
            background: #fcfdf9;
        }
        .dre-matrix thead .dre-matrix-account {
            z-index: 5;
            background: #edf4ea;
        }
        .dre-matrix .dre-matrix-value {
            min-width: 116px;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }
        .dre-matrix .dre-matrix-percent {
            min-width: 54px;
            text-align: right;
            font-size: 0.78em;
            color: #7b867f;
        }
        .dre-matrix tbody tr:hover td {
            background: rgba(238,245,239,0.78);
        }
        .dre-matrix tbody tr:hover .dre-matrix-account {
            background: rgba(232,241,232,0.96);
        }
        .dre-matrix .dre-matrix-strong td {
            color: #193326;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_snapshot(snapshot_mtime_ns: int) -> dict[str, Any]:
    with SNAPSHOT_PATH.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def find_logo() -> Path | None:
    for path in LOGO_CANDIDATES:
        if path.exists():
            return path
    return None


def render_logo(path: Path, width: int = 220, sidebar: bool = False) -> None:
    suffix = path.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }[suffix]
    image_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    style = "width:220px; max-width:94%; height:auto;" if sidebar else f"width:{width}px; max-width:100%; height:auto;"
    wrapper = "sidebar-logo" if sidebar else ""
    st.markdown(
        f'<div class="{wrapper}"><img src="data:{mime};base64,{image_b64}" alt="Clear Agro" style="{style}"></div>',
        unsafe_allow_html=True,
    )


def brl(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "R$ 0,00"
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def pct(value: Any) -> str:
    try:
        number = float(value or 0) * 100
    except (TypeError, ValueError):
        return "0,0%"
    return f"{number:.1f}%".replace(".", ",")


def integer(value: Any) -> str:
    try:
        return f"{int(float(value or 0)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def as_frame(rows: list[dict[str, Any]] | None) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def load_jsonl_frame(paths: list[Path]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if "empresa" not in obj:
                    obj["empresa"] = "CR" if path.name.endswith("_cr.jsonl") else "CZ"
                rows.append(obj)
    if not rows:
        return pd.DataFrame()
    return pd.json_normalize(rows)


@st.cache_data(show_spinner=False)
def load_effective_sales_frame() -> pd.DataFrame:
    caches = [
        WORKSPACE_ROOT / "bling_api" / "nfe_2026_cache.jsonl",
        WORKSPACE_ROOT / "bling_api" / "nfe_2026_cache_cr.jsonl",
        WORKSPACE_ROOT / "bling_api" / "nfe_2025_cache.jsonl",
        WORKSPACE_ROOT / "bling_api" / "nfe_2025_cache_cr.jsonl",
    ]
    df = load_jsonl_frame(caches)
    if df.empty:
        return df
    if "dataEmissao" in df.columns:
        df["data"] = pd.to_datetime(df["dataEmissao"], errors="coerce")
    elif "dataOperacao" in df.columns:
        df["data"] = pd.to_datetime(df["dataOperacao"], errors="coerce")
    else:
        df["data"] = pd.NaT
    if "valorNota" in df.columns:
        df["receita"] = pd.to_numeric(df["valorNota"], errors="coerce").fillna(0.0)
    else:
        df["receita"] = pd.to_numeric(df.get("valor"), errors="coerce").fillna(0.0)
    if "naturezaOperacao.id" in df.columns:
        df["natureza"] = df["naturezaOperacao.id"].fillna("").astype(str)
    else:
        df["natureza"] = ""
    if "vendedor.id" in df.columns:
        df["vendedor_id"] = df["vendedor.id"].fillna("").astype(str).str.strip()
    elif "vendedor_id" in df.columns:
        df["vendedor_id"] = df["vendedor_id"].fillna("").astype(str).str.strip()
    else:
        df["vendedor_id"] = ""
    item_cfops: list[str] = []
    for items in df.get("itens", pd.Series([[]] * len(df))):
        cfop = ""
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                cfop = str(first.get("cfop") or "").strip()
        item_cfops.append(cfop)
    df["cfop"] = item_cfops
    natureza_txt = (df["natureza"] + " " + df["cfop"]).astype(str).str.upper()
    receita = pd.to_numeric(df["receita"], errors="coerce").fillna(0.0)
    vendedor_id = df["vendedor_id"].fillna("").astype(str).str.strip()
    cfop = df["cfop"].fillna("").astype(str).str.strip()
    is_return_cfop = cfop.str.match(r"^[1267]20[1-9]$|^[12]201$|^[56]202$")
    is_non_sale_cfop = cfop.isin({"5910", "6910", "5911", "6911", "5917", "6917", "5949", "6949"})
    is_devolucao = natureza_txt.str.contains("DEVOL|RETORNO|ESTORNO|CANCEL", regex=True) | receita.lt(0) | is_return_cfop
    is_non_sale = natureza_txt.str.contains("REMESSA|CONSIGN|BONIFIC", regex=True) | is_non_sale_cfop
    is_vendor_zero = vendedor_id.eq("0")
    df = df[~is_devolucao & ~is_non_sale & ~is_vendor_zero & receita.gt(0)].copy()
    df = df.dropna(subset=["data"])
    return df


def effective_sales_total(year: int | None, month: int | None) -> float:
    df = load_effective_sales_frame()
    if df.empty:
        return 0.0
    out = df.copy()
    if year is not None:
        out = out[out["data"].dt.year == int(year)]
    if month is not None:
        out = out[out["data"].dt.month == int(month)]
    return float(pd.to_numeric(out["receita"], errors="coerce").fillna(0.0).sum())


def metric_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics, strict=False):
        col.metric(label, value)


def metric_grid(metrics: list[tuple[str, str]], columns: int = 2) -> None:
    if not metrics:
        return
    for start in range(0, len(metrics), columns):
        row = metrics[start:start + columns]
        metric_row(row)


def metric_section(title: str, metrics: list[tuple[str, str]], columns: int = 2) -> None:
    st.markdown(f"#### {title}")
    metric_grid(metrics, columns=columns)


def metric_rows(rows: list[list[tuple[str, str] | None]]) -> None:
    if not rows:
        return
    width = max(len(row) for row in rows)
    for row in rows:
        cols = st.columns(width)
        for idx in range(width):
            item = row[idx] if idx < len(row) else None
            if item is None:
                cols[idx].markdown("&nbsp;")
            else:
                label, value = item
                cols[idx].metric(label, value)


def render_dre_column(title: str, rows: list[tuple[str, str]], total_label: str, total_value: str, note: str = "") -> None:
    def esc(text: Any) -> str:
        return (
            str(text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    lines = "".join(
        f'<div class="dre-line"><span class="dre-line-label">{esc(label)}</span><span class="dre-line-value">{esc(value)}</span></div>'
        for label, value in rows
    )
    note_html = f'<div class="dre-note">{esc(note)}</div>' if note else ""
    st.markdown(
        f"""
        <div class="dre-column">
            <h4>{esc(title)}</h4>
            {lines}
            <div class="dre-total">{esc(total_label)}: {esc(total_value)}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dre_matrix(frame: pd.DataFrame) -> None:
    if frame.empty:
        return

    def esc(text: Any) -> str:
        return (
            str(text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    percent_cols = [col for col in frame.columns if col.endswith("%")]

    def row_class(label: Any) -> str:
        text = upper_text(label)
        if "RESULTADO" in text:
            return "dre-matrix-strong"
        if "MARGEM" in text:
            return "dre-matrix-strong"
        if "RECEITA TOTAL" in text or "CUSTOS FIXOS TOTAIS" in text:
            return "dre-matrix-strong"
        if "CMV" in text:
            return "dre-matrix-strong"
        return ""

    header_html = "".join(
        (
            f'<th class="dre-matrix-account">{esc(col)}</th>'
            if col == "CONTA"
            else f'<th class="{"dre-matrix-percent" if col in percent_cols else "dre-matrix-value"}">{esc("%" if col in percent_cols else col)}</th>'
        )
        for col in frame.columns
    )

    body_rows: list[str] = []
    for _, row in frame.iterrows():
        row_html = []
        for col in frame.columns:
            value = esc(row.get(col, ""))
            if col == "CONTA":
                row_html.append(f'<td class="dre-matrix-account">{value}</td>')
            else:
                cell_class = "dre-matrix-percent" if col in percent_cols else "dre-matrix-value"
                row_html.append(f'<td class="{cell_class}">{value}</td>')
        body_rows.append(f'<tr class="{row_class(row.get("CONTA"))}">{"".join(row_html)}</tr>')

    st.markdown(
        f"""
        <div class="dre-matrix-wrap">
            <table class="dre-matrix">
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {"".join(body_rows)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def upper_text(value: Any) -> str:
    return str(value or "").strip().upper()


def monthly_frame(snapshot: dict[str, Any], key: str = "monthly") -> pd.DataFrame:
    frame = as_frame(snapshot.get(key))
    if frame.empty:
        return frame
    frame["mes"] = frame["mes"].astype(str)
    frame["ano"] = frame["mes"].str[:4].astype(int)
    frame["mes_num"] = frame["mes_num"].astype(int)
    frame["mes_nome"] = frame["mes_num"].map(MONTH_NAMES)
    frame["periodo"] = frame["mes_nome"] + "/" + frame["ano"].astype(str)
    for col in [
        "receita_liquida",
        "custos_variaveis_total",
        "cmv_proxy",
        "cmv_sales_cost",
        "cmv_purchase_fallback",
        "custo_fixo_base",
        "despesas_ap_proxy",
        "margem_contribuicao",
        "ebitda",
    ]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    return frame.sort_values(["ano", "mes_num"]).reset_index(drop=True)


def cash_days_frame(snapshot: dict[str, Any]) -> pd.DataFrame:
    frame = as_frame(snapshot.get("cash_projection", {}).get("days"))
    if frame.empty:
        return frame
    frame["data"] = pd.to_datetime(frame["data"], errors="coerce")
    frame = frame.dropna(subset=["data"]).copy()
    frame["ano"] = frame["data"].dt.year.astype(int)
    frame["mes_num"] = frame["data"].dt.month.astype(int)
    frame["data_label"] = frame["data"].dt.strftime("%d/%m/%Y")
    for col in ["inflow", "outflow", "net", "cumulative_net"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    return frame


def bank_balance_frame(snapshot: dict[str, Any]) -> pd.DataFrame:
    frame = as_frame((snapshot.get("bank_balances") or {}).get("balances"))
    if frame.empty:
        return frame
    if "balance" in frame.columns:
        frame["balance"] = pd.to_numeric(frame["balance"], errors="coerce").fillna(0.0)
    if "balance_status" not in frame.columns:
        frame["balance_status"] = "API"
    if "as_of" in frame.columns:
        frame["as_of_dt"] = pd.to_datetime(frame["as_of"], errors="coerce")
        frame["as_of_label"] = frame["as_of_dt"].dt.strftime("%d/%m/%Y")
    return frame


def future_flow_monthly(frame: pd.DataFrame, value_col: str = "valor") -> pd.DataFrame:
    if frame.empty or "data_vencimento" not in frame.columns:
        return pd.DataFrame(columns=["ano", "mes_num", "periodo", "valor"])
    work = frame.copy()
    work["data_vencimento"] = pd.to_datetime(work["data_vencimento"], errors="coerce")
    work = work.dropna(subset=["data_vencimento"]).copy()
    today = pd.Timestamp(datetime.now().date())
    work = work[work["data_vencimento"] >= today].copy()
    if work.empty:
        return pd.DataFrame(columns=["ano", "mes_num", "periodo", "valor"])
    work["ano"] = work["data_vencimento"].dt.year.astype(int)
    work["mes_num"] = work["data_vencimento"].dt.month.astype(int)
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce").fillna(0.0)
    out = work.groupby(["ano", "mes_num"], as_index=False)[value_col].sum()
    out["periodo"] = out["mes_num"].map(MONTH_NAMES).fillna(out["mes_num"].astype(str)) + "/" + out["ano"].astype(str)
    out = out.rename(columns={value_col: "valor"})
    return out.sort_values(["ano", "mes_num"]).reset_index(drop=True)


def top_flow_frame(rows: list[dict[str, Any]] | None) -> pd.DataFrame:
    frame = as_frame(rows)
    if frame.empty:
        return frame
    frame["data"] = pd.to_datetime(frame["data"], errors="coerce")
    frame = frame.dropna(subset=["data"]).copy()
    frame["ano"] = frame["data"].dt.year.astype(int)
    frame["mes_num"] = frame["data"].dt.month.astype(int)
    frame["data_label"] = frame["data"].dt.strftime("%d/%m/%Y")
    frame["valor"] = pd.to_numeric(frame["valor"], errors="coerce").fillna(0.0)
    return frame.sort_values("valor", ascending=False).reset_index(drop=True)


def account_detail_frame(snapshot: dict[str, Any], key: str, fallback_rows: list[dict[str, Any]] | None, tipo: str) -> pd.DataFrame:
    frame = as_frame(snapshot.get(key))
    if frame.empty:
        frame = top_flow_frame(fallback_rows).copy()
        if frame.empty:
            return frame
        frame["cliente_fornecedor"] = frame.get("contato", "N/D")
        frame["fornecedor"] = frame["cliente_fornecedor"] if tipo == "pagar" else ""
        frame["cliente"] = frame["cliente_fornecedor"] if tipo == "receber" else ""
        frame["data_emissao"] = frame["data"].dt.strftime("%Y-%m-%d")
        frame["vencimento"] = frame["data"].dt.strftime("%Y-%m-%d")
        frame["situacao"] = "A vencer"
        frame["company"] = ""
        frame["documento"] = ""
        frame["cultura"] = ""
        frame["zafra"] = ""
        frame["juros"] = 0.0
        frame["dias_atraso"] = 0
        frame["vencido"] = False
        frame["data_vencimento"] = pd.to_datetime(frame["vencimento"], errors="coerce")
    else:
        if "valor" in frame.columns:
            frame["valor"] = pd.to_numeric(frame["valor"], errors="coerce").fillna(0.0)
        if "juros" not in frame.columns:
            frame["juros"] = 0.0
        frame["juros"] = pd.to_numeric(frame["juros"], errors="coerce").fillna(0.0)
        if "dias_atraso" not in frame.columns:
            frame["dias_atraso"] = 0
        frame["dias_atraso"] = pd.to_numeric(frame["dias_atraso"], errors="coerce").fillna(0).astype(int)
        if "vencimento" in frame.columns:
            frame["data_vencimento"] = pd.to_datetime(frame["vencimento"], errors="coerce")
        else:
            frame["data_vencimento"] = pd.NaT
        if "data_emissao" in frame.columns:
            frame["data_emissao_dt"] = pd.to_datetime(frame["data_emissao"], errors="coerce")
        elif "data" in frame.columns:
            frame["data_emissao_dt"] = pd.to_datetime(frame["data"], errors="coerce")
        else:
            frame["data_emissao_dt"] = pd.NaT
    if "data_vencimento" in frame.columns:
        frame["ano"] = pd.to_datetime(frame["data_vencimento"], errors="coerce").dt.year
        frame["mes_num"] = pd.to_datetime(frame["data_vencimento"], errors="coerce").dt.month
    elif "data_emissao_dt" in frame.columns:
        frame["ano"] = pd.to_datetime(frame["data_emissao_dt"], errors="coerce").dt.year
        frame["mes_num"] = pd.to_datetime(frame["data_emissao_dt"], errors="coerce").dt.month
    if "data_emissao_dt" in frame.columns:
        frame["data_emissao_label"] = pd.to_datetime(frame["data_emissao_dt"], errors="coerce").dt.strftime("%d/%m/%Y")
    if "data_vencimento" in frame.columns:
        frame["data_label"] = pd.to_datetime(frame["data_vencimento"], errors="coerce").dt.strftime("%d/%m/%Y")
    elif "vencimento" in frame.columns:
        frame["data_label"] = pd.to_datetime(frame["vencimento"], errors="coerce").dt.strftime("%d/%m/%Y")
    for col in ["cliente_fornecedor", "fornecedor", "cliente", "cultura", "zafra", "situacao", "documento", "company"]:
        if col not in frame.columns:
            frame[col] = ""
        frame[col] = frame[col].fillna("").astype(str).str.strip()
    for col in ["cliente_fornecedor", "fornecedor", "cliente"]:
        if col in frame.columns:
            frame[col] = frame[col].str.upper()
    return frame


def period_options(monthly: pd.DataFrame) -> tuple[list[int], dict[str, int | None]]:
    years = sorted(monthly["ano"].unique().tolist()) if not monthly.empty else []
    month_map: dict[str, int | None] = {"Todos": None}
    if not monthly.empty:
        for mes_num in sorted(monthly["mes_num"].unique().tolist()):
            month_map[MONTH_NAMES.get(mes_num, str(mes_num))] = mes_num
    return years, month_map


def period_options_from_frames(frames: list[pd.DataFrame]) -> tuple[list[int], dict[str, int | None]]:
    years_set: set[int] = set()
    months_set: set[int] = set()
    for frame in frames:
        if frame.empty:
            continue
        if "ano" in frame.columns:
            years_set.update(
                {
                    int(value)
                    for value in pd.to_numeric(frame["ano"], errors="coerce").dropna().tolist()
                }
            )
        if "mes_num" in frame.columns:
            months_set.update(
                {
                    int(value)
                    for value in pd.to_numeric(frame["mes_num"], errors="coerce").dropna().tolist()
                }
            )
    years = sorted(years_set)
    month_map: dict[str, int | None] = {"Todos": None}
    for mes_num in sorted(months_set):
        month_map[MONTH_NAMES.get(mes_num, str(mes_num))] = mes_num
    return years, month_map


def filter_monthly(frame: pd.DataFrame, year: int | None, month: int | None) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    if year is not None:
        out = out[out["ano"] == int(year)]
    if month is not None:
        out = out[out["mes_num"] == int(month)]
    return out


def filter_dated(frame: pd.DataFrame, year: int | None, month: int | None) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    if year is not None and "ano" in out.columns:
        out = out[out["ano"] == int(year)]
    if month is not None and "mes_num" in out.columns:
        out = out[out["mes_num"] == int(month)]
    return out


def filter_company(frame: pd.DataFrame, company: str | None) -> pd.DataFrame:
    if frame.empty or not company or company == "Todas" or "company" not in frame.columns:
        return frame
    out = frame.copy()
    return out[out["company"].fillna("").astype(str).str.upper() == str(company).upper()]


def aging_bucket(days_overdue: Any) -> str:
    try:
        days = int(days_overdue or 0)
    except (TypeError, ValueError):
        days = 0
    if days <= 0:
        return "A vencer"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    if days <= 180:
        return "91-180"
    return ">180"


def status_label(raw_status: Any, days_overdue: Any, value: Any) -> str:
    text = str(raw_status or "").strip().upper()
    if "CANCEL" in text:
        return "Cancelado"
    try:
        status_code = int(float(raw_status))
    except (TypeError, ValueError):
        status_code = None
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    try:
        days = int(days_overdue or 0)
    except (TypeError, ValueError):
        days = 0
    if status_code == 3:
        return "Parcial em atraso" if days > 0 else "Parcial em dia"
    if amount <= 0:
        return "Sem saldo"
    if days > 0:
        return "Vencido"
    return "A vencer"


def period_summary(monthly: pd.DataFrame) -> dict[str, float]:
    if monthly.empty:
        return {
            "receita_liquida": 0.0,
            "cmv_proxy": 0.0,
            "cmv_pct": 0.0,
            "custos_variaveis_total": 0.0,
            "custo_fixo_base": 0.0,
            "margem_contribuicao": 0.0,
            "ebitda": 0.0,
            "margem_ebitda_pct": 0.0,
            "meses": 0.0,
        }
    receita = float(monthly["receita_liquida"].sum())
    custos_variaveis = float(monthly["custos_variaveis_total"].sum())
    margem_contribuicao = float(monthly["margem_contribuicao"].sum())
    if "cmv_proxy" in monthly.columns:
        cmv_proxy = float(monthly["cmv_proxy"].sum())
    else:
        cmv_proxy = float(receita - margem_contribuicao - custos_variaveis)
    ebitda = float(monthly["ebitda"].sum())
    return {
        "receita_liquida": receita,
        "cmv_proxy": cmv_proxy,
        "cmv_pct": (cmv_proxy / receita) if receita else 0.0,
        "custos_variaveis_total": custos_variaveis,
        "custo_fixo_base": float(monthly["custo_fixo_base"].sum()),
        "margem_contribuicao": margem_contribuicao,
        "ebitda": ebitda,
        "margem_ebitda_pct": (ebitda / receita) if receita else 0.0,
        "meses": float(len(monthly)),
    }


def has_proxy_rows(monthly: pd.DataFrame) -> bool:
    return (
        not monthly.empty
        and "dre_model" in monthly.columns
        and monthly["dre_model"].astype(str).isin(["bling_proxy", "bling_erp"]).any()
    )


def period_label(year: int | None, month: int | None) -> str:
    if year is None:
        return "Base completa"
    if month is None:
        return f"Ano {year}"
    return f"{MONTH_NAMES.get(month, str(month))}/{year}"


def compute_bling_management_summary(ap_frame: pd.DataFrame, ar_frame: pd.DataFrame, cash_frame: pd.DataFrame) -> dict[str, float]:
    ap = ap_frame.copy() if not ap_frame.empty else pd.DataFrame()
    ar = ar_frame.copy() if not ar_frame.empty else pd.DataFrame()
    cash = cash_frame.copy() if not cash_frame.empty else pd.DataFrame()

    for frame in [ap, ar]:
        if not frame.empty:
            frame["valor"] = pd.to_numeric(frame["valor"], errors="coerce").fillna(0.0)
            frame["dias_atraso"] = pd.to_numeric(frame["dias_atraso"], errors="coerce").fillna(0).astype(int)

    if not cash.empty:
        for col in ["inflow", "outflow", "net", "cumulative_net"]:
            cash[col] = pd.to_numeric(cash[col], errors="coerce").fillna(0.0)

    ap_total = float(ap["valor"].sum()) if not ap.empty else 0.0
    ar_total = float(ar["valor"].sum()) if not ar.empty else 0.0
    ap_vencido = float(ap.loc[ap["dias_atraso"] > 0, "valor"].sum()) if not ap.empty else 0.0
    ar_vencido = float(ar.loc[ar["dias_atraso"] > 0, "valor"].sum()) if not ar.empty else 0.0
    ap_a_vencer = float(ap.loc[ap["dias_atraso"] <= 0, "valor"].sum()) if not ap.empty else 0.0
    ar_a_vencer = float(ar.loc[ar["dias_atraso"] <= 0, "valor"].sum()) if not ar.empty else 0.0

    ap_top = 0.0
    if not ap.empty and "fornecedor" in ap.columns:
        ap_top = float(ap.groupby("fornecedor", dropna=False)["valor"].sum().max())
    ar_top = 0.0
    if not ar.empty and "cliente" in ar.columns:
        ar_top = float(ar.groupby("cliente", dropna=False)["valor"].sum().max())

    return {
        "ap_total": ap_total,
        "ar_total": ar_total,
        "ap_vencido": ap_vencido,
        "ar_vencido": ar_vencido,
        "ap_a_vencer": ap_a_vencer,
        "ar_a_vencer": ar_a_vencer,
        "saldo_aberto": ar_total - ap_total,
        "saldo_vencido": ar_vencido - ap_vencido,
        "fluxo_30d": float(cash["net"].sum()) if not cash.empty else 0.0,
        "entrada_30d": float(cash["inflow"].sum()) if not cash.empty else 0.0,
        "saida_30d": float(cash["outflow"].sum()) if not cash.empty else 0.0,
        "menor_caixa_30d": float(cash["cumulative_net"].min()) if not cash.empty else 0.0,
        "titulos_ap": float(len(ap)),
        "titulos_ar": float(len(ar)),
        "ap_maior_fornecedor": ap_top,
        "ar_maior_cliente": ar_top,
        "inadimplencia_ar_pct": (ar_vencido / ar_total) if ar_total else 0.0,
        "pressao_ap_pct": (ap_vencido / ap_total) if ap_total else 0.0,
    }


def render_hero(snapshot: dict[str, Any], title: str, subtitle: str, logo_path: Path | None) -> None:
    logo_html = ""
    if logo_path is not None and logo_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }[logo_path.suffix.lower()]
        image_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        logo_html = (
            f'<div class="hero-logo-box">'
            f'<img src="data:{mime};base64,{image_b64}" alt="Clear Agro" '
            f'style="width:100%; max-width:760px; height:auto; display:block;">'
            f"</div>"
        )
    st.markdown(
        f"""
        <div class="hero-header">
            <div class="hero-title-box">
                <div class="hero-title-wrap" style="text-align:left;">
                    <div class="hero-title">{title}</div>
                </div>
            </div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_note(text: str) -> None:
    st.markdown(f'<div class="section-note">{text}</div>', unsafe_allow_html=True)


def render_overview(
    snapshot: dict[str, Any],
    monthly_period: pd.DataFrame,
    monthly_all: pd.DataFrame,
    ap_period: pd.DataFrame,
    ar_period: pd.DataFrame,
    cash_period: pd.DataFrame,
    year: int | None,
    month: int | None,
    label: str,
) -> None:
    quality = snapshot["quality_reconciliation"]
    governance = snapshot["governance"]
    classic = snapshot["classic_kpis"]
    summary = compute_bling_management_summary(ap_period, ar_period, cash_period)
    dre_summary = period_summary(monthly_period)
    proxy_period = has_proxy_rows(monthly_period)

    st.header("Resumo Executivo")
    metric_row(
        [
            ("AR Total", brl(summary["ar_total"])),
            ("AP Total", brl(summary["ap_total"])),
            ("Saldo em Aberto", brl(summary["saldo_aberto"])),
            ("Qualidade", classic["quality_status"]),
        ]
    )
    metric_row(
        [
            ("AR A Vencer", brl(summary["ar_a_vencer"])),
            ("AP A Vencer", brl(summary["ap_a_vencer"])),
            ("Fluxo Liquido 30d", brl(summary["fluxo_30d"])),
            ("Checks com Falha", integer(quality["quality_check_fail"])),
        ]
    )

    if proxy_period:
        commercial_sales_total = effective_sales_total(year, month)
        cmv_sales_total = (
            float(pd.to_numeric(monthly_period.get("cmv_sales_cost"), errors="coerce").fillna(0.0).sum())
            if "cmv_sales_cost" in monthly_period.columns
            else 0.0
        )
        cmv_sales_pct = (cmv_sales_total / commercial_sales_total) if commercial_sales_total else 0.0
        st.subheader("Resultado Gerencial do Periodo")
        metric_rows(
            [
                [
                    ("Faturamento NF-e", brl(dre_summary["receita_liquida"])),
                    ("Vendas efetivas", brl(commercial_sales_total)),
                ],
                [
                    ("Custo total das vendas efetivas", brl(cmv_sales_total)),
                    ("CMV sobre vendas", pct(cmv_sales_pct)),
                ],
                [
                    ("Despesa AP Proxy", brl(dre_summary["custo_fixo_base"])),
                    ("EBITDA Proxy", brl(dre_summary["ebitda"])),
                ],
            ]
        )

    left, right = st.columns([1.5, 1.0])
    with left:
        st.subheader("Abertos por Origem")
        base = pd.DataFrame(
            [
                {"indicador": "AR total", "valor": summary["ar_total"]},
                {"indicador": "AR vencido", "valor": summary["ar_vencido"]},
                {"indicador": "AP total", "valor": summary["ap_total"]},
                {"indicador": "AP vencido", "valor": summary["ap_vencido"]},
            ]
        )
        st.bar_chart(base.set_index("indicador")["valor"], use_container_width=True)
    with right:
        st.subheader("Semaforo Gerencial")
        status = pd.DataFrame(
            [
                {"tema": "Dashboard pronto", "status": "Sim" if snapshot["health"]["ready"] else "Nao"},
                {"tema": "Gate de qualidade", "status": classic["quality_status"]},
                {"tema": "Inadimplencia AR", "status": pct(summary["inadimplencia_ar_pct"])},
                {"tema": "Pressao AP vencido", "status": pct(summary["pressao_ap_pct"])},
                {"tema": "Fornecedores em revisao", "status": integer(governance["review_count"])},
                {"tema": "Pendencias de nome", "status": integer(governance["pending_count"])},
            ]
        )
        st.dataframe(status, use_container_width=True, hide_index=True)

    st.subheader("Concentracao da Carteira")
    concentration = pd.DataFrame(
        [
            {"indicador": "Maior cliente em AR", "valor": brl(summary["ar_maior_cliente"])},
            {"indicador": "Maior fornecedor em AP", "valor": brl(summary["ap_maior_fornecedor"])},
            {"indicador": "Titulos AR", "valor": integer(summary["titulos_ar"])},
            {"indicador": "Titulos AP", "valor": integer(summary["titulos_ap"])},
        ]
    )
    st.dataframe(concentration, use_container_width=True, hide_index=True)


def render_executive(
    snapshot: dict[str, Any],
    monthly_period: pd.DataFrame,
    ap_period: pd.DataFrame,
    ar_period: pd.DataFrame,
    cash_period: pd.DataFrame,
    label: str,
) -> None:
    classic = snapshot["classic_kpis"]
    summary = compute_bling_management_summary(ap_period, ar_period, cash_period)
    dre_summary = period_summary(monthly_period)
    proxy_period = has_proxy_rows(monthly_period)

    st.header("Painel Executivo Financeiro")
    st.subheader("Exposicao Consolidada")
    metric_row(
        [
            ("AR Total", brl(summary["ar_total"])),
            ("AP Total", brl(summary["ap_total"])),
            ("Saldo em Aberto", brl(summary["saldo_aberto"])),
            ("Fluxo Liquido 30d", brl(summary["fluxo_30d"])),
        ]
    )

    if proxy_period:
        st.subheader("DRE Proxy do Periodo")
        metric_row(
            [
                ("Receita NF-e", brl(dre_summary["receita_liquida"])),
                ("CMV 2026", brl(dre_summary["cmv_proxy"])),
                ("Despesa AP Proxy", brl(dre_summary["custo_fixo_base"])),
                ("EBITDA Proxy", brl(dre_summary["ebitda"])),
            ]
        )

    st.subheader("A Vencer vs Vencido")
    metric_row(
        [
            ("AR A Vencer", brl(summary["ar_a_vencer"])),
            ("AR Vencido", brl(summary["ar_vencido"])),
            ("AP A Vencer", brl(summary["ap_a_vencer"])),
            ("AP Vencido", brl(summary["ap_vencido"])),
        ]
    )

    aging_ap = as_frame(classic["aging_ap"])
    aging_ar = as_frame(classic["aging_ar"])
    left, right = st.columns(2)
    with left:
        st.subheader("Aging de Contas a Pagar")
        if not aging_ap.empty:
            st.bar_chart(aging_ap.set_index("bucket")["valor"], use_container_width=True)
            show = aging_ap.rename(columns={"bucket": "faixa", "valor": "valor"})
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Aging de Contas a Receber")
        if not aging_ar.empty:
            st.bar_chart(aging_ar.set_index("bucket")["valor"], use_container_width=True)
            show = aging_ar.rename(columns={"bucket": "faixa", "valor": "valor"})
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show, use_container_width=True, hide_index=True)

    st.subheader("Indicadores de Risco")
    risk = pd.DataFrame(
        [
            {"indicador": "Inadimplencia AR", "valor": pct(summary["inadimplencia_ar_pct"])},
            {"indicador": "Pressao AP vencido", "valor": pct(summary["pressao_ap_pct"])},
            {"indicador": "Menor caixa 30d", "valor": brl(summary["menor_caixa_30d"])},
            {"indicador": "Maior cliente em AR", "valor": brl(summary["ar_maior_cliente"])},
            {"indicador": "Maior fornecedor em AP", "valor": brl(summary["ap_maior_fornecedor"])},
        ]
    )
    st.dataframe(risk, use_container_width=True, hide_index=True)


def render_dre(
    snapshot: dict[str, Any],
    monthly_legacy_period: pd.DataFrame,
    monthly_legacy_all: pd.DataFrame,
    monthly_bling_period: pd.DataFrame,
    monthly_bling_all: pd.DataFrame,
    label: str,
    year: int | None,
    month: int | None,
) -> None:
    ap_details = account_detail_frame(
        snapshot,
        "ap_details",
        snapshot.get("cash_projection", {}).get("top_outflows"),
        "pagar",
    )
    ap_period = filter_dated(ap_details, year, month)

    st.header("DRE e EBITDA")
    source_options = []
    if not monthly_bling_all.empty:
        source_options.append("ERP Bling")
    if not monthly_legacy_all.empty:
        source_options.append("Finance Recon Hub")
    if not source_options:
        source_options = ["ERP Bling"]
    selected_source = st.radio("Fonte do DRE", options=source_options, horizontal=True)
    if selected_source == "ERP Bling":
        monthly_period = monthly_bling_period
        monthly_all = monthly_bling_all
        source_label = "ERP Bling"
    else:
        monthly_period = monthly_legacy_period
        monthly_all = monthly_legacy_all
        source_label = "Finance Recon Hub"

    summary = period_summary(monthly_period)
    proxy_period = has_proxy_rows(monthly_period)
    tab_resumo, tab_analitico, tab_cmv = st.tabs(["Resumo", "Analitico", "Detalhe do CMV"])

    with tab_resumo:
        if proxy_period:
            commercial_sales_total = effective_sales_total(year, month)
            cmv_sales_total = (
                float(pd.to_numeric(monthly_period.get("cmv_sales_cost"), errors="coerce").fillna(0.0).sum())
                if "cmv_sales_cost" in monthly_period.columns
                else 0.0
            )
            cmv_sales_pct = (cmv_sales_total / commercial_sales_total) if commercial_sales_total else 0.0
            metric_rows(
                [
                    [
                        ("Faturamento NF-e", brl(summary["receita_liquida"])),
                        ("Vendas efetivas", brl(commercial_sales_total)),
                    ],
                    [
                        ("Custo total das vendas efetivas", brl(cmv_sales_total)),
                        ("CMV sobre vendas", pct(cmv_sales_pct)),
                    ],
                    [
                        (f"Despesa AP {source_label}", brl(summary["custo_fixo_base"])),
                        (f"EBITDA {source_label}", brl(summary["ebitda"])),
                    ],
                ]
            )
            st.caption(
                "Base ERP Bling: receita por NF-e emitida, CMV por custo dos itens vendidos e despesas por contas a pagar totais sem cancelados."
            )
        else:
            metric_grid(
                [
                    ("Receita Liquida", brl(summary["receita_liquida"])),
                    ("CMV %", pct(summary["cmv_pct"])),
                    ("Custos Variaveis", brl(summary["custos_variaveis_total"])),
                    ("Custo Fixo Base", brl(summary["custo_fixo_base"])),
                    ("EBITDA", brl(summary["ebitda"])),
                ],
                columns=2,
            )

        if not monthly_all.empty:
            st.subheader("Historico Mensal")
            st.line_chart(
                monthly_all.set_index("periodo")[["receita_liquida", "margem_contribuicao", "ebitda"]],
                use_container_width=True,
            )

        if not monthly_period.empty:
            show = monthly_period.copy()
            for col in [
                "receita_liquida",
                "cmv_proxy",
                "custos_variaveis_total",
                "custo_fixo_base",
                "margem_contribuicao",
                "ebitda",
            ]:
                show[col] = show[col].map(brl)
            if "despesas_ap_proxy" in show.columns:
                show["despesas_ap_proxy"] = show["despesas_ap_proxy"].map(brl)
            if proxy_period and "cmv_proxy" in monthly_period.columns:
                cmv_series = pd.to_numeric(monthly_period["cmv_proxy"], errors="coerce").fillna(0.0)
                receita_series = pd.to_numeric(monthly_period["receita_liquida"], errors="coerce").fillna(0.0)
                show["cmv_pct"] = [pct((cmv / receita) if receita else 0.0) for cmv, receita in zip(cmv_series, receita_series, strict=False)]
            elif {"receita_liquida", "margem_contribuicao", "custos_variaveis_total"} <= set(monthly_period.columns):
                cmv_series = (
                    pd.to_numeric(monthly_period["receita_liquida"], errors="coerce").fillna(0.0)
                    - pd.to_numeric(monthly_period["margem_contribuicao"], errors="coerce").fillna(0.0)
                    - pd.to_numeric(monthly_period["custos_variaveis_total"], errors="coerce").fillna(0.0)
                )
                receita_series = pd.to_numeric(monthly_period["receita_liquida"], errors="coerce").fillna(0.0)
                show["cmv_pct"] = [pct((cmv / receita) if receita else 0.0) for cmv, receita in zip(cmv_series, receita_series, strict=False)]
            st.subheader("Tabela do Periodo")
            if proxy_period:
                cols = ["periodo", "receita_liquida", "cmv_proxy", "cmv_pct", "despesas_ap_proxy", "ebitda"]
                labels = {
                    "periodo": "periodo",
                    "receita_liquida": "receita_nfe",
                    "cmv_proxy": "cmv_erp",
                    "cmv_pct": "cmv_pct",
                    "despesas_ap_proxy": "despesa_ap_erp",
                    "ebitda": "ebitda_erp",
                }
            else:
                cols = [
                    "periodo",
                    "receita_liquida",
                    "cmv_pct",
                    "custos_variaveis_total",
                    "custo_fixo_base",
                    "margem_contribuicao",
                    "ebitda",
                ]
                labels = None
            st.dataframe(show[cols].rename(columns=labels) if labels else show[cols], use_container_width=True, hide_index=True)

    with tab_analitico:
        commercial_sales_total = effective_sales_total(year, month)
        bank_balances = bank_balance_frame(snapshot)
        capital_atual = float(bank_balances["balance"].sum()) if not bank_balances.empty else 0.0
        cmv_sales_total = (
            float(pd.to_numeric(monthly_period.get("cmv_sales_cost"), errors="coerce").fillna(0.0).sum())
            if "cmv_sales_cost" in monthly_period.columns
            else 0.0
        )
        receita_total = float(summary["receita_liquida"])
        custos_variaveis_total = float(summary["cmv_proxy"] + summary["custos_variaveis_total"])
        margem_contribuicao = float(summary["margem_contribuicao"])
        custo_fixo_total = float(summary["custo_fixo_base"])
        ebitda = float(summary["ebitda"])
        margem_contribuicao_pct = (margem_contribuicao / receita_total) if receita_total else 0.0
        rentabilidade_capital = (ebitda / capital_atual) if capital_atual else 0.0

        receita_items = pd.DataFrame(
            [
                {"item": "Faturamento NF-e", "valor": receita_total},
                {"item": "Vendas efetivas", "valor": commercial_sales_total},
            ]
        )
        receita_items["valor_fmt"] = receita_items["valor"].map(brl)

        custos_variaveis_items = pd.DataFrame(
            [
                {
                    "item": "CMV Proxy",
                    "valor": float(summary["cmv_proxy"]),
                    "pct": (float(summary["cmv_proxy"]) / receita_total) if receita_total else 0.0,
                },
                {
                    "item": "Custos variaveis adicionais",
                    "valor": float(summary["custos_variaveis_total"]),
                    "pct": (float(summary["custos_variaveis_total"]) / receita_total) if receita_total else 0.0,
                },
                {
                    "item": "Custo das vendas efetivas",
                    "valor": cmv_sales_total,
                    "pct": (cmv_sales_total / commercial_sales_total) if commercial_sales_total else 0.0,
                },
            ]
        )
        custos_variaveis_items["valor_fmt"] = custos_variaveis_items["valor"].map(brl)
        custos_variaveis_items["pct_fmt"] = custos_variaveis_items["pct"].map(pct)

        resultado_items = pd.DataFrame(
            [
                {"item": "Margem de contribuicao", "valor": margem_contribuicao, "aux": pct(margem_contribuicao_pct)},
                {"item": "Custos fixos mensais", "valor": custo_fixo_total, "aux": pct((custo_fixo_total / receita_total) if receita_total else 0.0)},
                {"item": "Resultado operacional (EBITDA)", "valor": ebitda, "aux": pct(summary["margem_ebitda_pct"])},
                {"item": "Rentabilidade sobre capital atual", "valor": capital_atual, "aux": pct(rentabilidade_capital)},
            ]
        )
        resultado_items["valor_fmt"] = resultado_items["valor"].map(brl)

        analysis_year = year if year is not None else datetime.now().year
        dre_monthly = monthly_all[monthly_all["ano"] == int(analysis_year)].copy() if not monthly_all.empty else pd.DataFrame()
        month_cols = []
        month_labels: dict[int, str] = {}
        if not dre_monthly.empty:
            month_cols = sorted(dre_monthly["mes_num"].dropna().astype(int).unique().tolist())
            month_labels = {mes: MONTH_NAMES.get(mes, str(mes))[:3] for mes in month_cols}

        classification_rows = (snapshot.get("ap_classification") or {}).get("category_monthly") or []
        classification_df = pd.DataFrame(classification_rows)
        if not classification_df.empty and {"mes", "label", "valor"} <= set(classification_df.columns):
            classification_df["valor"] = pd.to_numeric(classification_df["valor"], errors="coerce").fillna(0.0)
            classification_df["ano"] = classification_df["mes"].astype(str).str[:4].astype(int)
            classification_df["mes_num"] = classification_df["mes"].astype(str).str[-2:].astype(int)
            classification_df = classification_df[classification_df["ano"] == int(analysis_year)].copy()
            classification_df["grupo_dre"] = classification_df["label"].apply(
                lambda value: "Custos Variaveis"
                if str(value).strip().upper().startswith("VARIAVEL")
                else "Despesas Operacionais"
            )
            variable_category_items = (
                classification_df[classification_df["grupo_dre"] == "Custos Variaveis"]
                .groupby("label", as_index=False)["valor"]
                .sum()
                .sort_values("valor", ascending=False)
                .head(8)
                .copy()
            )
            fixed_cost_items = (
                classification_df[classification_df["grupo_dre"] == "Despesas Operacionais"]
                .groupby("label", as_index=False)["valor"]
                .sum()
                .sort_values("valor", ascending=False)
                .head(12)
                .copy()
            )
            variable_month_map = {
                label: {
                    int(row["mes_num"]): float(row["valor"])
                    for _, row in group.iterrows()
                }
                for label, group in classification_df[classification_df["grupo_dre"] == "Custos Variaveis"].groupby("label")
            }
            fixed_month_map = {
                label: {
                    int(row["mes_num"]): float(row["valor"])
                    for _, row in group.iterrows()
                }
                for label, group in classification_df[classification_df["grupo_dre"] == "Despesas Operacionais"].groupby("label")
            }
        else:
            variable_category_items = pd.DataFrame(columns=["label", "valor"])
            fixed_cost_items = pd.DataFrame(columns=["label", "valor"])
            variable_month_map = {}
            fixed_month_map = {}

        if fixed_cost_items.empty and not ap_period.empty:
            fixed_cost_items = (
                ap_period.groupby("fornecedor", dropna=False, as_index=False)["valor"]
                .sum()
                .sort_values("valor", ascending=False)
                .head(12)
                .copy()
                .rename(columns={"fornecedor": "label"})
            )
            fixed_cost_items["label"] = fixed_cost_items["label"].replace("", "N/D")
            fixed_month_map = {str(row["label"]): {} for _, row in fixed_cost_items.iterrows()}

        nfe_sales_by_month = {}
        sales_df = load_effective_sales_frame()
        if not sales_df.empty:
            sales_work = sales_df[sales_df["data"].dt.year == int(analysis_year)].copy()
            if not sales_work.empty:
                nfe_sales_by_month = (
                    sales_work.groupby(sales_work["data"].dt.month)["receita"].sum().to_dict()
                )

        month_rows: list[tuple[str, dict[int, float]]] = [
            ("CAPITAL ATUAL INVESTIDO", {mes: capital_atual for mes in month_cols}),
            ("RECEITA TOTAL", {mes: float(dre_monthly.loc[dre_monthly["mes_num"] == mes, "receita_liquida"].sum()) for mes in month_cols}),
            ("VENDA EFETIVA", {mes: float(nfe_sales_by_month.get(mes, 0.0)) for mes in month_cols}),
            ("CMV / CUSTOS VARIAVEIS", {mes: float(dre_monthly.loc[dre_monthly["mes_num"] == mes, "cmv_proxy"].sum()) for mes in month_cols}),
            ("MARGEM DE CONTRIBUICAO", {mes: float(dre_monthly.loc[dre_monthly["mes_num"] == mes, "margem_contribuicao"].sum()) for mes in month_cols}),
            ("DESPESAS OPERACIONAIS", {mes: float(dre_monthly.loc[dre_monthly["mes_num"] == mes, "custo_fixo_base"].sum()) for mes in month_cols}),
            ("RESULTADO OPERACIONAL", {mes: float(dre_monthly.loc[dre_monthly["mes_num"] == mes, "ebitda"].sum()) for mes in month_cols}),
        ]

        pct_labels = {
            "CMV / CUSTOS VARIAVEIS",
            "MARGEM DE CONTRIBUICAO",
            "DESPESAS OPERACIONAIS",
            "RESULTADO OPERACIONAL",
        }

        matrix_rows: list[dict[str, str]] = []
        variable_detail_rows = []
        if not variable_category_items.empty:
            for row_item in variable_category_items.to_dict("records"):
                label_name = str(row_item["label"])
                variable_detail_rows.append(
                    (
                        f"   {upper_text(label_name)}",
                        variable_month_map.get(label_name, {}),
                        float(row_item["valor"]),
                    )
                )
        fixed_detail_rows = []
        if not fixed_cost_items.empty:
            for row_item in fixed_cost_items.to_dict("records"):
                label_name = str(row_item["label"])
                fixed_detail_rows.append(
                    (
                        f"   {upper_text(label_name)}",
                        fixed_month_map.get(label_name, {}),
                        float(row_item["valor"]),
                    )
                )

        for label, values_by_month in month_rows:
            label_upper = upper_text(label)
            row = {"CONTA": label_upper}
            total_row = 0.0
            for mes in month_cols:
                value = float(values_by_month.get(mes, 0.0))
                receita_mes = float(dre_monthly.loc[dre_monthly["mes_num"] == mes, "receita_liquida"].sum()) if not dre_monthly.empty else 0.0
                total_row += value
                row[upper_text(month_labels[mes])] = brl(value)
                row[f"{upper_text(month_labels[mes])} %"] = pct((value / receita_mes) if receita_mes else 0.0) if label_upper in pct_labels else ""
            row["TOTAL"] = brl(total_row)
            total_receita = float(dre_monthly["receita_liquida"].sum()) if not dre_monthly.empty else 0.0
            row["TOTAL %"] = pct((total_row / total_receita) if total_receita else 0.0) if label_upper in pct_labels else ""
            matrix_rows.append(row)
            if label_upper == "CMV / CUSTOS VARIAVEIS" and variable_detail_rows:
                for detail_label, detail_values_by_month, detail_total in variable_detail_rows:
                    detail_row = {"CONTA": detail_label}
                    for mes in month_cols:
                        month_value = float(detail_values_by_month.get(mes, 0.0))
                        detail_row[upper_text(month_labels[mes])] = brl(month_value) if month_value else ""
                        detail_row[f"{upper_text(month_labels[mes])} %"] = ""
                    detail_row["TOTAL"] = brl(detail_total)
                    detail_row["TOTAL %"] = pct((detail_total / total_receita) if total_receita else 0.0)
                    matrix_rows.append(detail_row)
            if label_upper == "DESPESAS OPERACIONAIS" and fixed_detail_rows:
                for detail_label, detail_values_by_month, detail_total in fixed_detail_rows:
                    detail_row = {"CONTA": detail_label}
                    for mes in month_cols:
                        month_value = float(detail_values_by_month.get(mes, 0.0))
                        detail_row[upper_text(month_labels[mes])] = brl(month_value) if month_value else ""
                        detail_row[f"{upper_text(month_labels[mes])} %"] = ""
                    detail_row["TOTAL"] = brl(detail_total)
                    detail_row["TOTAL %"] = pct((detail_total / total_receita) if total_receita else 0.0)
                    matrix_rows.append(detail_row)

        st.subheader(f"DRE ANALITICA EM COLUNAS - {analysis_year}")
        if matrix_rows:
            matrix_df = pd.DataFrame(matrix_rows)
            render_dre_matrix(matrix_df)
        else:
            st.info("NAO HA BASE MENSAL SUFICIENTE PARA MONTAR A DRE ANALITICA EM COLUNAS PARA O ANO SELECIONADO.")

    with tab_cmv:
        proxy_info = snapshot.get("dre_bling_info") or {}
        if not proxy_period:
            st.info("O detalhamento de CMV fica disponível quando o snapshot traz a visão proxy de DRE.")
        else:
            cmv_sales_total = (
                float(pd.to_numeric(monthly_period.get("cmv_sales_cost"), errors="coerce").fillna(0.0).sum())
                if "cmv_sales_cost" in monthly_period.columns
                else 0.0
            )
            cmv_purchase_total = (
                float(pd.to_numeric(monthly_period.get("cmv_purchase_fallback"), errors="coerce").fillna(0.0).sum())
                if "cmv_purchase_fallback" in monthly_period.columns
                else 0.0
            )
            faturamento_nfe = summary["receita_liquida"]
            commercial_sales_total = effective_sales_total(year, month)
            cmv_sales_rate = (cmv_sales_total / faturamento_nfe) if faturamento_nfe else 0.0
            cmv_cover_ratio = (commercial_sales_total / summary["cmv_proxy"]) if summary["cmv_proxy"] else 0.0
            cmv_pct = (summary["cmv_proxy"] / commercial_sales_total) if commercial_sales_total else 0.0

            metric_grid(
                [
                    ("Faturamento NF-e", brl(faturamento_nfe)),
                    ("Vendas efetivas", brl(commercial_sales_total)),
                    ("Custo total das vendas efetivas", brl(cmv_sales_total)),
                    ("CMV ERP", brl(summary["cmv_proxy"])),
                    ("Vendas / CMV", f"{cmv_cover_ratio:.2f}x" if cmv_cover_ratio else "0,00x"),
                    ("CMV % sobre vendas", pct(cmv_pct)),
                    ("CMV itens vendidos %", pct(cmv_sales_rate)),
                    ("EBITDA ERP", brl(summary["ebitda"])),
                ],
                columns=2,
            )

            cmv_detail = pd.DataFrame(
                [
                    {"indicador": "Faturamento NF-e", "valor": brl(faturamento_nfe)},
                    {"indicador": "Vendas efetivas", "valor": brl(commercial_sales_total)},
                    {"indicador": "Custo total das vendas efetivas", "valor": brl(cmv_sales_total)},
                    {"indicador": "CMV ERP", "valor": brl(summary["cmv_proxy"])},
                    {"indicador": "CMV fallback compras", "valor": brl(cmv_purchase_total)},
                    {"indicador": "Relacao vendas / CMV", "valor": f"{cmv_cover_ratio:.2f}x" if cmv_cover_ratio else "0,00x"},
                    {"indicador": "CMV % sobre vendas", "valor": pct(cmv_pct)},
                    {"indicador": "CMV itens vendidos %", "valor": pct(cmv_sales_rate)},
                    {"indicador": "Formula", "valor": "Vendas efetivas / custo total das mercadorias vendidas"},
                    {"indicador": "Itens de CMV conciliados", "valor": integer(proxy_info.get("cmv_item_matched") or 0)},
                    {"indicador": "Itens de CMV sem correspondencia", "valor": integer(proxy_info.get("cmv_item_missing") or 0)},
                    {"indicador": "Taxa de conciliacao CMV", "valor": pct(float(proxy_info.get("cmv_match_rate") or 0.0))},
                ]
            )
            st.dataframe(cmv_detail, use_container_width=True, hide_index=True)


def render_cash(snapshot: dict[str, Any], cash_period: pd.DataFrame, year: int | None, month: int | None, label: str) -> None:
    cash = snapshot["cash_projection"]
    inflows = filter_dated(top_flow_frame(cash["top_inflows"]), year, month)
    outflows = filter_dated(top_flow_frame(cash["top_outflows"]), year, month)

    st.header("Caixa e Projecao")
    metric_row(
        [
            ("Entradas do Horizonte", brl(cash_period["inflow"].sum() if not cash_period.empty else cash["inflow_30d"])),
            ("Saidas do Horizonte", brl(cash_period["outflow"].sum() if not cash_period.empty else cash["outflow_30d"])),
            ("Liquido do Horizonte", brl(cash_period["net"].sum() if not cash_period.empty else cash["net_30d"])),
            ("Pior Acumulado", brl(cash_period["cumulative_net"].min() if not cash_period.empty else cash["min_cumulative_30d"])),
        ]
    )

    if not cash_period.empty:
        st.subheader("Fluxo Diario")
        st.line_chart(cash_period.set_index("data_label")[["inflow", "outflow", "net"]], use_container_width=True)
        st.subheader("Acumulado Liquido")
        st.line_chart(cash_period.set_index("data_label")[["cumulative_net"]], use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Principais Entradas")
        if not inflows.empty:
            show = inflows.copy()
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show[["data_label", "contato", "valor"]], use_container_width=True, hide_index=True)
    with right:
        st.subheader("Principais Saidas")
        if not outflows.empty:
            show = outflows.copy()
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show[["data_label", "contato", "valor"]], use_container_width=True, hide_index=True)


def render_cash_management(
    snapshot: dict[str, Any],
    bank_balances: pd.DataFrame,
    cash_all: pd.DataFrame,
    ap_all: pd.DataFrame,
    ar_all: pd.DataFrame,
    selected_company: str,
) -> None:
    st.header("FX de Caixa Proj.")

    work_banks = bank_balances.copy() if not bank_balances.empty else pd.DataFrame()
    if not work_banks.empty and selected_company != "Todas" and "company" in work_banks.columns:
        work_banks = work_banks[
            work_banks["company"].fillna("").astype(str).str.upper() == str(selected_company).upper()
        ].copy()

    total_balance = float(work_banks["balance"].sum()) if not work_banks.empty else 0.0
    horizon = cash_all.copy() if not cash_all.empty else pd.DataFrame()
    ap_future = ap_all.copy() if not ap_all.empty else pd.DataFrame()
    ar_future = ar_all.copy() if not ar_all.empty else pd.DataFrame()
    if selected_company != "Todas":
        if not ap_future.empty and "company" in ap_future.columns:
            ap_future = ap_future[ap_future["company"].fillna("").astype(str).str.upper() == str(selected_company).upper()].copy()
        if not ar_future.empty and "company" in ar_future.columns:
            ar_future = ar_future[ar_future["company"].fillna("").astype(str).str.upper() == str(selected_company).upper()].copy()
    if not horizon.empty:
        horizon = horizon.sort_values("data").reset_index(drop=True)
        horizon["projected_balance"] = total_balance + pd.to_numeric(
            horizon["cumulative_net"], errors="coerce"
        ).fillna(0.0)
    ap_monthly = future_flow_monthly(ap_future)
    ar_monthly = future_flow_monthly(ar_future)
    horizon_days = [0, 15, 30, 60, 90, 120]
    horizon_projection_rows: list[dict[str, Any]] = []
    today = pd.Timestamp(datetime.now().date())
    for days in horizon_days:
        cutoff = today + pd.Timedelta(days=days)
        ar_h = 0.0
        ap_h = 0.0
        if not ar_future.empty and "data_vencimento" in ar_future.columns:
            ar_work = ar_future.copy()
            ar_work["data_vencimento"] = pd.to_datetime(ar_work["data_vencimento"], errors="coerce")
            ar_work["valor"] = pd.to_numeric(ar_work["valor"], errors="coerce").fillna(0.0)
            ar_h = float(ar_work.loc[(ar_work["data_vencimento"] >= today) & (ar_work["data_vencimento"] <= cutoff), "valor"].sum())
        if not ap_future.empty and "data_vencimento" in ap_future.columns:
            ap_work = ap_future.copy()
            ap_work["data_vencimento"] = pd.to_datetime(ap_work["data_vencimento"], errors="coerce")
            ap_work["valor"] = pd.to_numeric(ap_work["valor"], errors="coerce").fillna(0.0)
            ap_h = float(ap_work.loc[(ap_work["data_vencimento"] >= today) & (ap_work["data_vencimento"] <= cutoff), "valor"].sum())
        caixa_h = ar_h - ap_h
        horizon_projection_rows.append(
            {
                "janela": "Hoje" if days == 0 else f"{days}d",
                "a_receber": ar_h,
                "a_pagar": ap_h,
                "caixa": caixa_h,
                "banco_projetado": total_balance + caixa_h,
            }
        )
    horizon_projection = pd.DataFrame(horizon_projection_rows)

    proj_7 = total_balance
    proj_15 = total_balance
    proj_30 = total_balance
    min_balance = total_balance
    risk_days = 0
    ar_total_future = float(ar_monthly["valor"].sum()) if not ar_monthly.empty else 0.0
    ap_total_future = float(ap_monthly["valor"].sum()) if not ap_monthly.empty else 0.0
    if not horizon.empty:
        proj_7 = float(horizon.head(8)["projected_balance"].iloc[-1])
        proj_15 = float(horizon.head(16)["projected_balance"].iloc[-1]) if len(horizon) >= 16 else float(horizon["projected_balance"].iloc[-1])
        proj_30 = float(horizon["projected_balance"].iloc[-1])
        min_balance = float(horizon["projected_balance"].min())
        risk_days = int((horizon["projected_balance"] < 0).sum())

    metric_rows(
        [
            [
                ("Saldo Bancario Atual", brl(total_balance)),
                ("Caixa/Bancos", integer(len(work_banks))),
            ],
            [
                ("A Receber Futuro", brl(ar_total_future)),
                ("A Pagar Futuro", brl(ap_total_future)),
            ],
            [
                ("Saldo Projetado 7d", brl(proj_7)),
                ("Saldo Projetado 15d", brl(proj_15)),
            ],
            [
                ("Saldo Projetado 30d", brl(proj_30)),
                ("Menor Saldo Projetado", brl(min_balance)),
            ],
            [
                ("Dias com Caixa Negativo", integer(risk_days)),
                ("Base Bancaria", "Disponivel" if not work_banks.empty else "Indisponivel"),
            ],
        ]
    )

    if work_banks.empty:
        st.info(
            "Nao ha saldos bancarios sincronizados no snapshot atual. A tela ja usa a projecao de AP/AR, "
            "mas precisa de uma base de bancos para calcular o saldo inicial consolidado."
        )
    else:
        show_banks = work_banks.copy()
        show_banks["balance"] = show_banks["balance"].map(brl)
        display_cols = [c for c in ["company", "bank_name", "account_name", "balance", "balance_status", "as_of_label"] if c in show_banks.columns]
        rename_map = {
            "company": "empresa",
            "bank_name": "banco",
            "account_name": "conta",
            "balance": "saldo_atual",
            "balance_status": "status_saldo",
            "as_of_label": "data_saldo",
        }
        st.subheader("Saldos por Banco")
        st.dataframe(show_banks[display_cols].rename(columns=rename_map), use_container_width=True, hide_index=True)

    if not horizon_projection.empty:
        st.subheader("Fluxo Projetado por Horizonte")
        horizon_map = {
            str(row["janela"]): {
                "a_receber": float(row["a_receber"]),
                "a_pagar": float(row["a_pagar"]),
                "caixa": float(row["caixa"]),
                "banco_projetado": float(row["banco_projetado"]),
            }
            for _, row in horizon_projection.iterrows()
        }
        horizon_cols = ["Hoje", "15d", "30d", "60d", "90d", "120d"]
        rows: list[dict[str, str]] = []
        if not work_banks.empty:
            for _, bank_row in work_banks.sort_values(["bank_name", "account_name"]).iterrows():
                label = str(bank_row.get("bank_name") or bank_row.get("account_name") or "BANCO").upper()
                if bank_row.get("account_name") and str(bank_row.get("account_name")).strip() != str(bank_row.get("bank_name") or "").strip():
                    label = f"{label} - {str(bank_row.get('account_name')).upper()}"
                row = {"valor": label}
                for col in horizon_cols:
                    row[col] = brl(bank_row.get("balance"))
                rows.append(row)

        caixa_row = {"valor": "CAIXA"}
        total_bancos_row = {"valor": "TOTAL BANCOS"}
        ar_header_row = {"valor": "CONTAS A RECEBER"}
        ar_total_row = {"valor": "TOTAL A RECEBER"}
        ap_header_row = {"valor": "CONTAS A PAGAR"}
        ap_total_row = {"valor": "TOTAL A PAGAR"}
        saldo_row = {"valor": "SALDO LIQUIDO"}
        for col in horizon_cols:
            values = horizon_map.get(col, {"a_receber": 0.0, "a_pagar": 0.0, "caixa": 0.0, "banco_projetado": total_balance})
            caixa_row[col] = brl(total_balance)
            total_bancos_row[col] = brl(total_balance)
            ar_header_row[col] = ""
            ar_total_row[col] = brl(values["a_receber"])
            ap_header_row[col] = ""
            ap_total_row[col] = brl(values["a_pagar"])
            saldo_row[col] = brl(values["banco_projetado"])

        rows.extend(
            [
                caixa_row,
                total_bancos_row,
                ar_header_row,
                ar_total_row,
                ap_header_row,
                ap_total_row,
                saldo_row,
            ]
        )
        show_horizon = pd.DataFrame(rows)
        st.dataframe(show_horizon, use_container_width=True, hide_index=True)


    if not horizon.empty:
        st.subheader("Curva de Caixa Projetada")
        st.line_chart(
            horizon.set_index("data_label")[["projected_balance", "inflow", "outflow", "net"]],
            use_container_width=True,
        )

        critical = horizon[horizon["projected_balance"] < 0].copy()
        if not critical.empty:
            critical["projected_balance"] = critical["projected_balance"].map(brl)
            critical["net"] = critical["net"].map(brl)
            st.subheader("Dias de Risco")
            st.dataframe(
                critical[["data_label", "net", "projected_balance"]].rename(
                    columns={"data_label": "data", "net": "fluxo_liquido", "projected_balance": "saldo_projetado"}
                ),
                use_container_width=True,
                hide_index=True,
            )


def render_accounts_page(frame: pd.DataFrame, page_title: str, entity_col: str, label: str) -> None:
    st.header(page_title)
    if frame.empty:
        st.info("Nao ha detalhes disponiveis para este recorte no snapshot atual.")
        return

    work = frame.copy()
    if "dias_atraso" not in work.columns:
        work["dias_atraso"] = 0
    if "juros" not in work.columns:
        work["juros"] = 0.0
    work["dias_atraso"] = pd.to_numeric(work["dias_atraso"], errors="coerce").fillna(0).astype(int)
    work["juros"] = pd.to_numeric(work["juros"], errors="coerce").fillna(0.0)
    work["valor"] = pd.to_numeric(work["valor"], errors="coerce").fillna(0.0)
    work["status_titulo"] = work["dias_atraso"].apply(lambda x: "Vencido" if x > 0 else "A vencer")
    work["faixa_atraso"] = work["dias_atraso"].apply(aging_bucket)
    work["situacao_legivel"] = [
        status_label(raw, days, amount)
        for raw, days, amount in zip(work.get("situacao", ""), work["dias_atraso"], work["valor"], strict=False)
    ]

    total_valor = float(work["valor"].sum())
    vencidos = work[work["status_titulo"] == "Vencido"].copy()
    a_vencer = work[work["status_titulo"] == "A vencer"].copy()
    total_juros = float(work["juros"].sum())

    metric_grid(
        [
            ("Valor Total", brl(total_valor)),
            ("Valor A Vencer", brl(a_vencer["valor"].sum() if not a_vencer.empty else 0)),
            ("Valor Vencido", brl(vencidos["valor"].sum() if not vencidos.empty else 0)),
            ("Juros Identificados", brl(total_juros)),
        ],
        columns=2,
    )
    metric_row(
        [
            ("Titulos A Vencer", integer(len(a_vencer))),
            ("Titulos Vencidos", integer(len(vencidos))),
            ("Maior Atraso", integer(work["dias_atraso"].max())),
            ("Empresas no Recorte", integer(work["company"].replace("", pd.NA).dropna().nunique() if "company" in work.columns else 0)),
        ]
    )

    filter_left, filter_mid, filter_right = st.columns(3)
    with filter_left:
        status_choice = st.selectbox(
            "Status do titulo",
            options=["Todos", "A vencer", "Vencido"],
            key=f"status_{page_title.lower().replace(' ', '_')}",
        )
    with filter_mid:
        situacao_options = ["Todas"] + sorted(work["situacao_legivel"].fillna("").astype(str).replace("", pd.NA).dropna().unique().tolist())
        situacao_choice = st.selectbox(
            "Situacao operacional",
            options=situacao_options,
            key=f"situacao_{page_title.lower().replace(' ', '_')}",
        )
    with filter_right:
        aging_options = ["Todas", "A vencer", "1-30", "31-60", "61-90", "91-180", ">180"]
        aging_choice = st.selectbox(
            "Faixa de atraso",
            options=aging_options,
            key=f"aging_{page_title.lower().replace(' ', '_')}",
        )

    search_col, doc_col = st.columns(2)
    with search_col:
        search_name = st.text_input("Buscar por nome", key=f"nome_{page_title.lower().replace(' ', '_')}")
    with doc_col:
        search_doc = st.text_input("Buscar por documento", key=f"doc_{page_title.lower().replace(' ', '_')}")

    if status_choice != "Todos":
        work = work[work["status_titulo"] == status_choice].copy()
    if situacao_choice != "Todas":
        work = work[work["situacao_legivel"] == situacao_choice].copy()
    if aging_choice != "Todas":
        work = work[work["faixa_atraso"] == aging_choice].copy()
    if search_name.strip():
        work = work[work[entity_col].fillna("").astype(str).str.contains(search_name.strip(), case=False, na=False)].copy()
    if search_doc.strip():
        work = work[work["documento"].fillna("").astype(str).str.contains(search_doc.strip(), case=False, na=False)].copy()

    top_entities = (
        work.groupby(entity_col, dropna=False)["valor"]
        .sum()
        .reset_index()
        .sort_values("valor", ascending=False)
        .head(15)
    )
    top_five = (
        work.groupby(entity_col, dropna=False)
        .agg(
            valor=("valor", "sum"),
            titulos=("valor", "size"),
            vencido=("valor", lambda s: float(work.loc[s.index].loc[work.loc[s.index, "status_titulo"] == "Vencido", "valor"].sum())),
            a_vencer=("valor", lambda s: float(work.loc[s.index].loc[work.loc[s.index, "status_titulo"] == "A vencer", "valor"].sum())),
        )
        .reset_index()
        .sort_values("valor", ascending=False)
        .head(5)
    )
    status_value = (
        work.groupby("status_titulo", dropna=False)["valor"]
        .sum()
        .reset_index()
        .sort_values("valor", ascending=False)
    )
    aging = (
        work.groupby("faixa_atraso", dropna=False)["valor"]
        .sum()
        .reset_index()
    )

    left, right = st.columns(2)
    with left:
        st.subheader(f"Maiores {entity_col.replace('_', ' ').title()}")
        if not top_entities.empty:
            st.bar_chart(top_entities.set_index(entity_col)["valor"], use_container_width=True)
    with right:
        st.subheader("Status dos Titulos")
        if not status_value.empty:
            st.bar_chart(status_value.set_index("status_titulo")["valor"], use_container_width=True)

    st.subheader("Aging por Faixa")
    if not aging.empty:
        st.bar_chart(aging.set_index("faixa_atraso")["valor"], use_container_width=True)

    st.subheader(f"Top 5 {'Fornecedores' if entity_col == 'fornecedor' else 'Clientes'} em Aberto")
    if not top_five.empty:
        show_top = top_five.rename(columns={entity_col: "nome"}).copy()
        show_top["titulos"] = show_top["titulos"].map(integer)
        for col in ["valor", "vencido", "a_vencer"]:
            show_top[col] = show_top[col].map(brl)
        st.dataframe(show_top, use_container_width=True, hide_index=True)

    st.subheader("Resumo Detalhado")
    resumo_detalhado = pd.DataFrame(
        [
            {
                "indicador": "Valor Total",
                "status": "Todos",
                "titulos": len(work),
                "valor": total_valor,
            },
            {
                "indicador": "Valor A Vencer",
                "status": "A vencer",
                "titulos": len(a_vencer),
                "valor": float(a_vencer["valor"].sum()) if not a_vencer.empty else 0.0,
            },
            {
                "indicador": "Valor Vencido",
                "status": "Vencido",
                "titulos": len(vencidos),
                "valor": float(vencidos["valor"].sum()) if not vencidos.empty else 0.0,
            },
            {
                "indicador": "Juros Identificados",
                "status": "Todos",
                "titulos": len(work),
                "valor": total_juros,
            },
        ]
    )
    resumo_detalhado["titulos"] = resumo_detalhado["titulos"].map(integer)
    resumo_detalhado["valor"] = resumo_detalhado["valor"].map(brl)
    st.dataframe(resumo_detalhado, use_container_width=True, hide_index=True)

    show = work.copy()
    for col in ["valor", "juros"]:
        if col in show.columns:
            show[col] = show[col].map(brl)
    show = show.sort_values(["dias_atraso", "valor"], ascending=[False, False])
    display_cols = [
        c
        for c in [
            entity_col,
            "company",
            "documento",
            "valor",
            "data_emissao_label",
            "data_label",
            "status_titulo",
            "faixa_atraso",
            "situacao_legivel",
            "dias_atraso",
            "juros",
        ]
        if c in show.columns
    ]
    rename_map = {
        "fornecedor": "fornecedor",
        "cliente": "cliente",
        "company": "empresa",
        "documento": "documento",
        "valor": "valor",
        "data_emissao_label": "data_nota",
        "data_label": "vencimento",
        "status_titulo": "status",
        "faixa_atraso": "faixa_atraso",
        "situacao_legivel": "situacao_operacional",
        "dias_atraso": "dias_atraso",
        "juros": "juros",
    }
    st.subheader("Detalhamento")
    st.dataframe(show[display_cols].rename(columns=rename_map), use_container_width=True, hide_index=True)


def render_ap_governance(snapshot: dict[str, Any]) -> None:
    gov = snapshot["ap_governance"]
    governance = snapshot["governance"]

    st.header("Governanca de AP")
    metric_row(
        [
            ("Valor AP Classificado", brl(gov["ap_total_value"])),
            ("Lancamentos AP", integer(gov["ap_total_rows"])),
            ("Em Revisao", integer(governance["review_count"])),
            ("Pendentes de Nome", integer(governance["pending_count"])),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Mapeamento por Valor")
        mapped = as_frame(gov["mapped_status_value"])
        if not mapped.empty:
            st.bar_chart(mapped.set_index("label")["valor"], use_container_width=True)
    with right:
        st.subheader("Categorias com Maior Exposicao")
        category = as_frame(gov["category_value"]).head(10)
        if not category.empty:
            st.bar_chart(category.set_index("label")["valor"], use_container_width=True)

    low_left, low_right = st.columns(2)
    with low_left:
        st.subheader("Top Fornecedores")
        suppliers = as_frame(gov["top_suppliers"])
        if not suppliers.empty:
            suppliers["valor"] = suppliers["valor"].map(brl)
            st.dataframe(suppliers.rename(columns={"label": "fornecedor"}), use_container_width=True, hide_index=True)
    with low_right:
        st.subheader("Subcategorias Criticas")
        sub = as_frame(gov["subcategory_value"]).head(12)
        if not sub.empty:
            sub["valor"] = sub["valor"].map(brl)
            st.dataframe(sub.rename(columns={"label": "subcategoria"}), use_container_width=True, hide_index=True)


def render_quality(snapshot: dict[str, Any]) -> None:
    quality = snapshot["quality_reconciliation"]

    st.header("Qualidade e Reconciliacao")
    metric_row(
        [
            ("Checks OK", f"{quality['quality_check_ok']}/{quality['quality_check_total']}"),
            ("Health Ready", "Sim" if quality["health_ready"] else "Nao"),
            ("Falhas de Check", integer(quality["quality_check_fail"])),
            ("Gate Atual", quality["gate_detail"] or "N/D"),
        ]
    )

    rows = []
    for label, item in [
        ("Reconciliation geral", quality["latest_reconciliation"]),
        ("Reconciliation CZ", quality["latest_reconciliation_cz"]),
        ("Reconciliation CR", quality["latest_reconciliation_cr"]),
        ("Finance ingest hub", quality["latest_ingest"]),
        ("Import generator", quality["latest_import_generator"]),
        ("Cutover health", quality["latest_cutover_health"]),
    ]:
        rows.append(
            {
                "processo": label,
                "status": item.get("status", ""),
                "run_id": item.get("run_id", ""),
                "gerado_em": item.get("generated_at", ""),
                "arquivo": item.get("name", ""),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_qa(snapshot: dict[str, Any]) -> None:
    qa = snapshot["qa"]
    governance = snapshot["governance"]

    st.header("QA e Governanca")
    metric_row(
        [
            ("Warn QA", integer(qa["warn_count"])),
            ("Fail QA", integer(qa["fail_count"])),
            ("Meses EBITDA Negativo", integer(qa["negative_ebitda_months"])),
            ("Fornecedores em Revisao", integer(governance["review_count"])),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Checks de QA")
        checks = as_frame(qa["checks"])
        if not checks.empty:
            st.dataframe(checks, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Top Fornecedores em Revisao")
        review = as_frame(governance["top_review"])
        if not review.empty:
            review["valor_total"] = review["valor_total"].map(brl)
            st.dataframe(review, use_container_width=True, hide_index=True)

    pending = as_frame(governance["top_pending"])
    if not pending.empty:
        pending["valor_total"] = pending["valor_total"].map(brl)
        st.subheader("Pendencias de Nome")
        st.dataframe(pending, use_container_width=True, hide_index=True)


def main() -> None:
    inject_styles()
    snapshot_mtime_ns = SNAPSHOT_PATH.stat().st_mtime_ns if SNAPSHOT_PATH.exists() else 0
    snapshot = load_snapshot(snapshot_mtime_ns)
    logo_path = find_logo()
    monthly_all = monthly_frame(snapshot)
    monthly_bling_all = monthly_frame(snapshot, "monthly_bling")
    bank_balances_all = bank_balance_frame(snapshot)
    ap_details_all = account_detail_frame(snapshot, "ap_details", snapshot.get("cash_projection", {}).get("top_outflows"), "pagar")
    ar_details_all = account_detail_frame(snapshot, "ar_details", snapshot.get("cash_projection", {}).get("top_inflows"), "receber")
    cash_all = cash_days_frame(snapshot)
    years, month_map = period_options_from_frames([monthly_all, monthly_bling_all, cash_all, ap_details_all, ar_details_all])
    current_year = datetime.now().year
    selected_year = current_year if current_year in years else (years[-1] if years else None)
    selected_month = None
    selected_company = "Todas"

    with st.sidebar:
        if logo_path is not None:
            render_logo(logo_path, sidebar=True)
        st.markdown("## Navegacao")
        page = st.radio(
            "Selecione a visao",
            [
                "Resumo Executivo",
                "Painel Executivo Financeiro",
                "DRE e EBITDA",
                "FX de Caixa Proj.",
                "Caixa e Projecao",
                "Contas a Pagar",
                "Contas a Receber",
                "Governanca de AP",
                "Qualidade e Reconciliacao",
                "QA e Governanca",
            ],
        )
        year_filter_label = "Ano/Vencimento" if page in {"Contas a Pagar", "Contas a Receber"} else "Ano"
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.markdown("### Filtros de Periodo")
        if years:
            default_year = current_year if current_year in years else years[-1]
            selected_year = st.selectbox(year_filter_label, options=years, index=years.index(default_year))
        month_label_selected = st.selectbox("Mes", options=list(month_map.keys()), index=0)
        selected_month = month_map[month_label_selected]
        st.markdown("</div>", unsafe_allow_html=True)
        company_options = ["Todas"]
        company_values = sorted(
            {
                value
                for frame in [ap_details_all, ar_details_all, cash_all, bank_balances_all]
                if not frame.empty and "company" in frame.columns
                for value in frame["company"].fillna("").astype(str).str.strip().tolist()
                if value
            }
        )
        company_options.extend(company_values)
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.markdown("### Empresa")
        selected_company = st.selectbox("Empresa", options=company_options, index=0)
        st.markdown("</div>", unsafe_allow_html=True)

    current_label = period_label(selected_year, selected_month)
    monthly_period = filter_monthly(monthly_all, selected_year, selected_month)
    monthly_bling_period = filter_monthly(monthly_bling_all, selected_year, selected_month)
    cash_period = filter_company(filter_dated(cash_all, selected_year, selected_month), selected_company)
    ap_details_period = filter_company(filter_dated(ap_details_all, selected_year, selected_month), selected_company)
    ar_details_period = filter_company(filter_dated(ar_details_all, selected_year, selected_month), selected_company)

    render_hero(
        snapshot,
        "AGRO FINANCEIRO",
        "",
        logo_path,
    )

    if page == "Resumo Executivo":
        render_overview(
            snapshot,
            monthly_period,
            monthly_all,
            ap_details_period,
            ar_details_period,
            cash_period,
            selected_year,
            selected_month,
            current_label,
        )
    elif page == "Painel Executivo Financeiro":
        render_executive(snapshot, monthly_period, ap_details_period, ar_details_period, cash_period, current_label)
    elif page == "DRE e EBITDA":
        render_dre(
            snapshot,
            monthly_period,
            monthly_all,
            monthly_bling_period,
            monthly_bling_all,
            current_label,
            selected_year,
            selected_month,
        )
    elif page == "FX de Caixa Proj.":
        render_cash_management(snapshot, bank_balances_all, cash_all, ap_details_all, ar_details_all, selected_company)
    elif page == "Caixa e Projecao":
        render_cash(snapshot, cash_period, selected_year, selected_month, current_label)
    elif page == "Contas a Pagar":
        render_accounts_page(ap_details_period, "Contas a Pagar", "fornecedor", current_label)
    elif page == "Contas a Receber":
        render_accounts_page(ar_details_period, "Contas a Receber", "cliente", current_label)
    elif page == "Governanca de AP":
        render_ap_governance(snapshot)
    elif page == "Qualidade e Reconciliacao":
        render_quality(snapshot)
    else:
        render_qa(snapshot)

if __name__ == "__main__":
    main()
