from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import load_bling_nfe, load_bling_realizado  # noqa: E402
from src.metas_db import list_metas  # noqa: E402
from src.telegram import send_telegram_message, telegram_enabled  # noqa: E402


def _format_brl(value: float) -> str:
    text = f"{value:,.2f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


def _maybe_load_env_from_file() -> None:
    if telegram_enabled():
        return
    candidate = Path.home() / "Documents" / "telegram.txt"
    if not candidate.exists():
        return
    lines = [line.strip() for line in candidate.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return
    token = lines[0]
    chat = ""
    for line in lines[1:]:
        if "id" in line.lower():
            chat = line.replace("Id", "").replace("id", "").replace("=", "").strip()
            break
    if token and chat:
        import os
        os.environ["TELEGRAM_BOT_TOKEN"] = token
        os.environ["TELEGRAM_CHAT_ID"] = chat


def _month_name(dt: datetime) -> str:
    meses = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez",
    ]
    return meses[dt.month - 1]


def _calc_meta(metas: pd.DataFrame, year: int, month: int | None = None, month_upto: int | None = None) -> float:
    if metas.empty:
        return 0.0
    df = metas[(metas["ano"] == year) & (metas["periodo_tipo"] == "MONTH")]
    if month:
        df = df[df["mes"] == month]
    elif month_upto:
        df = df[df["mes"] <= month_upto]
    return float(pd.to_numeric(df["meta_valor"], errors="coerce").fillna(0).sum())


def _calc_realizado_nfe(nfe: pd.DataFrame, year: int, month: int | None = None, month_upto: int | None = None) -> tuple[float, int]:
    if nfe.empty:
        return 0.0, 0
    df = nfe[nfe["data"].dt.year == year]
    if month:
        df = df[df["data"].dt.month == month]
    elif month_upto:
        df = df[df["data"].dt.month <= month_upto]
    total = float(pd.to_numeric(df["valor"], errors="coerce").fillna(0).sum())
    return total, int(df.shape[0])


def _top_vendedores(vendas: pd.DataFrame, year: int, month: int | None, top_n: int = 5) -> list[tuple[str, float]]:
    if vendas.empty or "vendedor" not in vendas.columns:
        return []
    df = vendas.copy()
    df = df[df["data"].dt.year == year]
    if month:
        df = df[df["data"].dt.month == month]
    df["receita"] = pd.to_numeric(df["receita"], errors="coerce").fillna(0)
    agg = df.groupby("vendedor")["receita"].sum().sort_values(ascending=False).head(top_n)
    return list(agg.items())


def _top_estados_meta(metas: pd.DataFrame, year: int, month: int | None, top_n: int = 5) -> list[tuple[str, float]]:
    if metas.empty or "estado" not in metas.columns:
        return []
    df = metas[(metas["ano"] == year) & (metas["periodo_tipo"] == "MONTH")]
    if month:
        df = df[df["mes"] == month]
    df["meta_valor"] = pd.to_numeric(df["meta_valor"], errors="coerce").fillna(0)
    agg = df.groupby("estado")["meta_valor"].sum().sort_values(ascending=False).head(top_n)
    return list(agg.items())


def build_message(year: int) -> str:
    now = datetime.now()
    month = now.month
    month_name = _month_name(now)

    nfe = load_bling_nfe(year)
    vendas = load_bling_realizado()
    metas = list_metas({"ano": year, "periodo_tipo": "MONTH"})

    faturamento_mes, notas_mes = _calc_realizado_nfe(nfe, year, month=month)
    faturamento_ytd, notas_ytd = _calc_realizado_nfe(nfe, year, month_upto=month)
    faturamento_ano, notas_ano = _calc_realizado_nfe(nfe, year, None)
    meta_mes = _calc_meta(metas, year, month=month)
    meta_ytd = _calc_meta(metas, year, month_upto=month)
    meta_ano = _calc_meta(metas, year, None)

    ating_mes = (faturamento_mes / meta_mes * 100) if meta_mes else 0.0
    ating_ytd = (faturamento_ytd / meta_ytd * 100) if meta_ytd else 0.0
    ating_ano = (faturamento_ano / meta_ano * 100) if meta_ano else 0.0
    delta_mes = faturamento_mes - meta_mes
    delta_ytd = faturamento_ytd - meta_ytd
    delta_ano = faturamento_ano - meta_ano

    ticket_mes = (faturamento_mes / notas_mes) if notas_mes else 0.0
    ticket_ytd = (faturamento_ytd / notas_ytd) if notas_ytd else 0.0
    ticket_ano = (faturamento_ano / notas_ano) if notas_ano else 0.0

    top_vend_mes = _top_vendedores(vendas, year, month)
    top_vend_ytd = _top_vendedores(vendas, year, None)
    top_uf_meta_mes = _top_estados_meta(metas, year, month)

    hoje = now.strftime("%Y-%m-%d")

    lines = [
        "Clear Agro - Resumo semanal",
        f"Data: {hoje}",
        f"Ano base: {year}",
        "",
        f"{month_name}/{year} — Faturamento (NFe): {_format_brl(faturamento_mes)}",
        f"{month_name}/{year} — Meta: {_format_brl(meta_mes)}",
        f"{month_name}/{year} — Delta: {_format_brl(delta_mes)} | Ating.: {ating_mes:.1f}%",
        f"{month_name}/{year} — Ticket médio (NFe): {_format_brl(ticket_mes)}",
        "",
        f"YTD {year} (Jan-{month_name}) — Faturamento (NFe): {_format_brl(faturamento_ytd)}",
        f"YTD {year} (Jan-{month_name}) — Meta: {_format_brl(meta_ytd)}",
        f"YTD {year} (Jan-{month_name}) — Delta: {_format_brl(delta_ytd)} | Ating.: {ating_ytd:.1f}%",
        f"YTD {year} (Jan-{month_name}) — Ticket médio (NFe): {_format_brl(ticket_ytd)}",
        "",
        f"Ano {year} — Faturamento (NFe): {_format_brl(faturamento_ano)}",
        f"Ano {year} — Meta total: {_format_brl(meta_ano)}",
        f"Ano {year} — Delta: {_format_brl(delta_ano)} | Ating.: {ating_ano:.1f}%",
        f"Ano {year} — Ticket médio (NFe): {_format_brl(ticket_ano)}",
        "",
    ]

    if top_vend_mes:
        lines.append(f"Top vendedores {month_name}/{year} (Bling Vendas):")
        for v, val in top_vend_mes:
            lines.append(f"- {v}: {_format_brl(val)}")
        lines.append("")
    else:
        lines.append("Top vendedores (Bling Vendas): sem dados")
        lines.append("")

    if top_vend_ytd:
        lines.append(f"Top vendedores YTD {year} (Bling Vendas):")
        for v, val in top_vend_ytd:
            lines.append(f"- {v}: {_format_brl(val)}")
        lines.append("")

    if top_uf_meta_mes:
        lines.append(f"Top estados por meta {month_name}/{year} (Metas):")
        for uf, val in top_uf_meta_mes:
            lines.append(f"- {uf}: {_format_brl(val)}")
        lines.append("")

    lines.append("Fonte: Bling NFe + Metas + Bling Vendas")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Envia resumo semanal via Telegram")
    parser.add_argument("--year", type=int, default=datetime.now().year)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    message = build_message(args.year)
    if args.dry_run:
        print(message)
        return 0

    _maybe_load_env_from_file()
    if not telegram_enabled():
        print("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID nao configurados.")
        return 2

    ok, detail = send_telegram_message(message)
    print(detail)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
