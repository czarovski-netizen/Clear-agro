from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "out" / "base_unificada.xlsx"
OUT = ROOT / "out" / "validacao_kpis.md"

lines = []
lines.append("# Validacao de KPIs\n")

if not BASE.exists():
    lines.append("Base nao encontrada")
else:
    xls = pd.ExcelFile(BASE)
    metas = pd.read_excel(BASE, sheet_name="metas") if "metas" in xls.sheet_names else pd.DataFrame()
    real = pd.read_excel(BASE, sheet_name="realizado") if "realizado" in xls.sheet_names else pd.DataFrame()

    if "data" in metas.columns:
        metas["data"] = pd.to_datetime(metas["data"], errors="coerce")
    if "meta" in metas.columns:
        metas["meta"] = pd.to_numeric(metas["meta"], errors="coerce")
    if "data" in real.columns:
        real["data"] = pd.to_datetime(real["data"], errors="coerce")
    if "receita" in real.columns:
        real["receita"] = pd.to_numeric(real["receita"], errors="coerce")

    # Checagem: meta_mes muda quando troca mes
    if not metas.empty:
        jan = metas[metas["data"].dt.month == 1]["meta"].sum()
        fev = metas[metas["data"].dt.month == 2]["meta"].sum()
        lines.append(f"- Meta Jan (soma vendedores): {jan:.2f}")
        lines.append(f"- Meta Fev (soma vendedores): {fev:.2f}")
        lines.append("- OK: meta_mes muda por mes" if jan != fev else "- ALERTA: meta_mes igual (verificar)")

        # Checagem por vendedor (Planilha Geral)
        if "vendedor" in metas.columns:
            sample_v = metas["vendedor"].dropna().unique().tolist()[:3]
            lines.append("\\n## Meta por vendedor (Jan/Fev)\\n")
            for v in sample_v:
                vjan = metas[(metas["vendedor"] == v) & (metas["data"].dt.month == 1)]["meta"].sum()
                vfev = metas[(metas["vendedor"] == v) & (metas["data"].dt.month == 2)]["meta"].sum()
                lines.append(f"- {v}: Jan={vjan:.2f}, Fev={vfev:.2f}")

            # Tabela completa por vendedor e mes
            table = metas.copy()
            table["mes"] = table["data"].dt.strftime("%b").str.title()
            pivot = table.pivot_table(index="vendedor", columns="mes", values="meta", aggfunc="sum", fill_value=0)
            lines.append("\\n## Tabela completa (meta por vendedor e mes)\\n")
            lines.append(pivot.to_string())

    # Atingimento por vendedor varia
    if "vendedor" in metas.columns:
        msum = metas.groupby("vendedor")["meta"].sum().reset_index()
        rsum = real.groupby("vendedor")["receita"].sum().reset_index() if "vendedor" in real.columns else pd.DataFrame(columns=["vendedor","receita"])
        perf = msum.merge(rsum, on="vendedor", how="left")
        perf["receita"] = perf["receita"].fillna(0)
        perf["ating"] = perf.apply(lambda r: (r["receita"] / r["meta"] * 100) if r["meta"] else 0, axis=1)
        vals = perf["ating"].round(2).unique().tolist()
        lines.append("- OK: atingimento varia" if len(vals) > 1 else "- ALERTA: atingimento constante")

        lines.append("\n## Exemplos por vendedor (3)\n")
        for _, r in perf.head(3).iterrows():
            lines.append(f"- {r['vendedor']}: meta={r['meta']:.2f}, realizado={r['receita']:.2f}, atingimento={r['ating']:.1f}%")

    # Total confere
    total_meta = metas["meta"].sum() if "meta" in metas.columns else 0
    total_real = real["receita"].sum() if "receita" in real.columns else 0
    lines.append(f"\n- Total meta: {total_meta:.2f}")
    lines.append(f"- Total realizado: {total_real:.2f}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(str(OUT))
