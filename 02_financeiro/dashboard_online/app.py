from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = BASE_DIR / "data" / "latest_snapshot.json"


st.set_page_config(
    page_title="Clear OS Financeiro",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_snapshot() -> dict[str, Any]:
    with SNAPSHOT_PATH.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


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


def as_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def metric_row(metrics: list[tuple[str, str]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics, strict=False):
        column.metric(label, value)


def render_home(snapshot: dict[str, Any]) -> None:
    health = snapshot["health"]
    qa = snapshot["qa"]
    governance = snapshot["governance"]
    summary = snapshot["summary"]

    st.title("Clear OS Financeiro")
    st.caption(
        f"Run {snapshot['run_id']} | Gerado em {snapshot['generated_at']} | "
        f"Ready={health['ready']}"
    )

    metric_row(
        [
            ("Receita liquida total", brl(summary["receita_liquida_total"])),
            ("EBITDA total", brl(summary["ebitda_total"])),
            ("Margem bruta", pct(summary["margem_bruta_pct_total"])),
            ("Qualidade", snapshot["classic_kpis"]["quality_status"]),
        ]
    )
    metric_row(
        [
            ("Meses EBITDA negativo", str(qa["negative_ebitda_months"])),
            ("Warn QA", str(qa["warn_count"])),
            ("Fornecedores em revisao", str(governance["review_count"])),
            ("Pendentes de nome", str(governance["pending_count"])),
        ]
    )

    st.subheader("Mapa de Dashboards")
    catalog = pd.DataFrame(
        [
            {
                "dashboard": "Financeiro Executivo - 8 Cards",
                "objetivo": "Liquidez, aging e status operacional diario",
            },
            {
                "dashboard": "Governanca de AP",
                "objetivo": "Mapeamento, concentracao e backlog de fornecedores",
            },
            {
                "dashboard": "Caixa & Projecao",
                "objetivo": "Fluxo 30d, acumulado e pressao de caixa",
            },
            {
                "dashboard": "DRE & EBITDA",
                "objetivo": "Receita, contribuicao e rentabilidade mensal",
            },
            {
                "dashboard": "Qualidade & Reconciliacao",
                "objetivo": "Saude do pipeline e conciliacao Bling x base",
            },
            {
                "dashboard": "QA & Governanca",
                "objetivo": "Checks de auditoria e pendencias para aprovacao",
            },
        ]
    )
    st.dataframe(catalog, use_container_width=True, hide_index=True)

    monthly = as_frame(snapshot["monthly"])
    if not monthly.empty:
        view = monthly.set_index("mes")[["receita_liquida", "ebitda"]]
        st.subheader("Tendencia Mensal")
        st.line_chart(view, use_container_width=True)


def render_executive(snapshot: dict[str, Any]) -> None:
    classic = snapshot["classic_kpis"]
    st.title("Financeiro Executivo - 8 Cards")

    metric_row(
        [
            ("AP aberto", brl(classic["ap_aberto"])),
            ("AR aberto", brl(classic["ar_aberto"])),
            ("AP vencido", brl(classic["ap_vencido"])),
            ("AR vencido", brl(classic["ar_vencido"])),
        ]
    )
    metric_row(
        [
            ("Fluxo liquido 30d", brl(classic["fluxo_liquido_previsto_30d"])),
            ("Qualidade", classic["quality_status"]),
        ]
    )

    aging_ap = as_frame(classic["aging_ap"])
    aging_ar = as_frame(classic["aging_ar"])
    left, right = st.columns(2)

    with left:
        st.subheader("Aging AP")
        if not aging_ap.empty:
            st.bar_chart(aging_ap.set_index("bucket")["valor"], use_container_width=True)
            show = aging_ap.rename(columns={"bucket": "faixa", "valor": "valor"})
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Aging AR")
        if not aging_ar.empty:
            st.bar_chart(aging_ar.set_index("bucket")["valor"], use_container_width=True)
            show = aging_ar.rename(columns={"bucket": "faixa", "valor": "valor"})
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show, use_container_width=True, hide_index=True)


def render_ap_governance(snapshot: dict[str, Any]) -> None:
    gov = snapshot["ap_governance"]
    backlog = snapshot["governance"]
    st.title("Governanca de AP")

    metric_row(
        [
            ("Valor AP classificado", brl(gov["ap_total_value"])),
            ("Lancamentos AP", f"{gov['ap_total_rows']:,}".replace(",", ".")),
            ("Em revisao", str(backlog["review_count"])),
            ("Pendentes de nome", str(backlog["pending_count"])),
        ]
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Status de mapeamento por valor")
        mapped_value = as_frame(gov["mapped_status_value"])
        if not mapped_value.empty:
            st.bar_chart(mapped_value.set_index("label")["valor"], use_container_width=True)
    with right:
        st.subheader("Categorias por valor")
        category_value = as_frame(gov["category_value"]).head(10)
        if not category_value.empty:
            st.bar_chart(category_value.set_index("label")["valor"], use_container_width=True)

    low_left, low_right = st.columns(2)
    with low_left:
        st.subheader("Top fornecedores")
        top_suppliers = as_frame(gov["top_suppliers"])
        if not top_suppliers.empty:
            show = top_suppliers.rename(columns={"label": "fornecedor", "valor": "valor"})
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show, use_container_width=True, hide_index=True)
    with low_right:
        st.subheader("Subcategorias criticas")
        subcategory_value = as_frame(gov["subcategory_value"]).head(12)
        if not subcategory_value.empty:
            show = subcategory_value.rename(columns={"label": "subcategoria", "valor": "valor"})
            show["valor"] = show["valor"].map(brl)
            st.dataframe(show, use_container_width=True, hide_index=True)


def render_cash(snapshot: dict[str, Any]) -> None:
    cash = snapshot["cash_projection"]
    st.title("Caixa & Projecao")

    metric_row(
        [
            ("Entradas 30d", brl(cash["inflow_30d"])),
            ("Saidas 30d", brl(cash["outflow_30d"])),
            ("Liquido 30d", brl(cash["net_30d"])),
            ("Pior acumulado", brl(cash["min_cumulative_30d"])),
        ]
    )

    days = as_frame(cash["days"])
    if not days.empty:
        view = days.set_index("data")[["inflow", "outflow", "net"]]
        st.subheader("Fluxo diario")
        st.line_chart(view, use_container_width=True)

        st.subheader("Acumulado liquido")
        st.line_chart(days.set_index("data")[["cumulative_net"]], use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Top entradas")
        inflows = as_frame(cash["top_inflows"])
        if not inflows.empty:
            inflows["valor"] = inflows["valor"].map(brl)
            st.dataframe(inflows[["data", "contato", "valor"]], use_container_width=True, hide_index=True)
    with right:
        st.subheader("Top saidas")
        outflows = as_frame(cash["top_outflows"])
        if not outflows.empty:
            outflows["valor"] = outflows["valor"].map(brl)
            st.dataframe(outflows[["data", "contato", "valor"]], use_container_width=True, hide_index=True)


def render_dre(snapshot: dict[str, Any]) -> None:
    summary = snapshot["summary"]
    monthly = as_frame(snapshot["monthly"])
    st.title("DRE & EBITDA")

    metric_row(
        [
            ("Receita liquida total", brl(summary["receita_liquida_total"])),
            ("Lucro bruto", brl(summary["lucro_bruto_total"])),
            ("Margem de contribuicao", brl(summary["margem_contribuicao_total"])),
            ("EBITDA total", brl(summary["ebitda_total"])),
        ]
    )

    if not monthly.empty:
        chart = monthly.set_index("mes")[["receita_liquida", "margem_contribuicao", "ebitda"]]
        st.subheader("Serie mensal")
        st.line_chart(chart, use_container_width=True)

        st.subheader("Tabela mensal")
        show = monthly.copy()
        for column in [
            "receita_liquida",
            "custos_variaveis_total",
            "custo_fixo_base",
            "margem_contribuicao",
            "ebitda",
        ]:
            show[column] = show[column].map(brl)
        st.dataframe(show, use_container_width=True, hide_index=True)


def render_quality(snapshot: dict[str, Any]) -> None:
    quality = snapshot["quality_reconciliation"]
    st.title("Qualidade & Reconciliacao")

    metric_row(
        [
            ("Checks OK", f"{quality['quality_check_ok']}/{quality['quality_check_total']}"),
            ("Health ready", "Sim" if quality["health_ready"] else "Nao"),
            ("Gate", quality["gate_detail"]),
        ]
    )

    rows = []
    for label, item in [
        ("Reconciliation latest", quality["latest_reconciliation"]),
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
    st.title("QA & Governanca")

    metric_row(
        [
            ("Warn QA", str(qa["warn_count"])),
            ("Fail QA", str(qa["fail_count"])),
            ("Meses EBITDA negativo", str(qa["negative_ebitda_months"])),
            ("Revisao manual", str(governance["review_count"])),
        ]
    )

    top_left, top_right = st.columns(2)
    with top_left:
        st.subheader("Checks de QA")
        checks = as_frame(qa["checks"])
        if not checks.empty:
            st.dataframe(checks, use_container_width=True, hide_index=True)
    with top_right:
        st.subheader("Top fornecedores em revisao")
        review = as_frame(governance["top_review"])
        if not review.empty:
            review["valor_total"] = review["valor_total"].map(brl)
            st.dataframe(review, use_container_width=True, hide_index=True)

    st.subheader("Pendencias de nome")
    pending = as_frame(governance["top_pending"])
    if not pending.empty:
        pending["valor_total"] = pending["valor_total"].map(brl)
        st.dataframe(pending, use_container_width=True, hide_index=True)


def main() -> None:
    snapshot = load_snapshot()

    with st.sidebar:
        st.title("Dashboards")
        choice = st.radio(
            "Selecione a visao",
            [
                "Visao Geral",
                "Financeiro Executivo - 8 Cards",
                "Governanca de AP",
                "Caixa & Projecao",
                "DRE & EBITDA",
                "Qualidade & Reconciliacao",
                "QA & Governanca",
            ],
        )
        st.caption(f"Run ativo: {snapshot['run_id']}")
        st.caption(f"Snapshot: {snapshot['generated_at']}")

    if choice == "Visao Geral":
        render_home(snapshot)
    elif choice == "Financeiro Executivo - 8 Cards":
        render_executive(snapshot)
    elif choice == "Governanca de AP":
        render_ap_governance(snapshot)
    elif choice == "Caixa & Projecao":
        render_cash(snapshot)
    elif choice == "DRE & EBITDA":
        render_dre(snapshot)
    elif choice == "Qualidade & Reconciliacao":
        render_quality(snapshot)
    else:
        render_qa(snapshot)


if __name__ == "__main__":
    main()
