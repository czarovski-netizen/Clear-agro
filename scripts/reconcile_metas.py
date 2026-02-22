from __future__ import annotations

from pathlib import Path

import pandas as pd
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "out" / "base_unificada.xlsx"
DB = ROOT / "data" / "metas.db"
OUT_CSV = ROOT / "out" / "reconciliacao_metas.csv"
OUT_MD = ROOT / "out" / "reconciliacao_metas.md"


def _month_from_date(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.month


def main() -> int:
    if not BASE.exists():
        print("Base nao encontrada:", BASE)
        return 2
    if not DB.exists():
        print("metas.db nao encontrado:", DB)
        return 2

    # Base metas
    df_base = pd.read_excel(BASE, sheet_name="metas")
    if "data" in df_base.columns:
        df_base["mes"] = _month_from_date(df_base["data"])
    else:
        df_base["mes"] = None
    df_base["meta"] = pd.to_numeric(df_base.get("meta"), errors="coerce").fillna(0)
    df_base["realizado"] = pd.to_numeric(df_base.get("realizado"), errors="coerce").fillna(0)
    df_base["vendedor"] = df_base.get("vendedor", "")
    base_agg = (
        df_base.groupby(["mes", "vendedor"])[["meta", "realizado"]]
        .sum()
        .reset_index()
        .rename(columns={"meta": "meta_base", "realizado": "realizado_base"})
    )

    # metas.db
    con = sqlite3.connect(DB)
    df_db = pd.read_sql_query(
        "select mes, vendedor_id, meta_valor, realizado_valor from metas where periodo_tipo='MONTH'",
        con,
    )
    df_db["meta_valor"] = pd.to_numeric(df_db["meta_valor"], errors="coerce").fillna(0)
    df_db["realizado_valor"] = pd.to_numeric(df_db["realizado_valor"], errors="coerce").fillna(0)
    db_agg = (
        df_db.groupby(["mes", "vendedor_id"])[["meta_valor", "realizado_valor"]]
        .sum()
        .reset_index()
        .rename(columns={"meta_valor": "meta_db", "realizado_valor": "realizado_db", "vendedor_id": "vendedor"})
    )

    # Merge and diff
    rec = pd.merge(base_agg, db_agg, on=["mes", "vendedor"], how="outer").fillna(0)
    rec["delta_meta"] = rec["meta_base"] - rec["meta_db"]
    rec["delta_realizado"] = rec["realizado_base"] - rec["realizado_db"]

    rec.to_csv(OUT_CSV, index=False)

    # Summary
    total = rec[["meta_base", "meta_db", "realizado_base", "realizado_db", "delta_meta", "delta_realizado"]].sum()
    md = [
        "# Reconciliacao Metas (base_unificada vs metas.db)",
        "",
        f"Linhas comparadas: {len(rec)}",
        "",
        "## Totais",
        f"- Meta base: {total['meta_base']:.2f}",
        f"- Meta db: {total['meta_db']:.2f}",
        f"- Delta meta: {total['delta_meta']:.2f}",
        f"- Realizado base: {total['realizado_base']:.2f}",
        f"- Realizado db: {total['realizado_db']:.2f}",
        f"- Delta realizado: {total['delta_realizado']:.2f}",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print("Gerado:", OUT_CSV)
    print("Resumo:", OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
