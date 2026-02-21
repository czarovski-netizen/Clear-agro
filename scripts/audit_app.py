from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "main.py"
BASE = ROOT / "out" / "base_unificada.xlsx"
OUT = ROOT / "out" / "auditoria_app.md"

lines = []
lines.append("# Auditoria do App\n")
lines.append("## Arquivo principal\n")
lines.append(f"- {APP}\n")

lines.append("## Fontes de dados\n")
lines.append(f"- {BASE}\n")

schema = {}
if BASE.exists():
    xls = pd.ExcelFile(BASE)
    for s in xls.sheet_names:
        df = pd.read_excel(BASE, sheet_name=s, nrows=5)
        schema[s] = list(df.columns)

lines.append("## Schema real (colunas)\n")
for s, cols in schema.items():
    lines.append(f"- {s}: {cols}")

lines.append("\n## KPIs e formulas atuais\n")
lines.append("- Realizado YTD: soma de receita em realizado para o ano (coluna data)")
lines.append("- Meta YTD: soma de meta em metas para o ano ate o mes atual")
lines.append("- Atingimento %: realizado_ytd / meta_ytd (se meta=0 => 0)")
lines.append("- Pipeline Total: soma de volume_potencial em oportunidades")
lines.append("- Pipeline Ponderado: volume_potencial * probabilidade (se existir)")
lines.append("- % com proximo passo: proporcao de data_proximo_passo nao nula")

lines.append("\n## Possiveis causas de bugs\n")
lines.append("- Colunas ausentes: data_proximo_passo, probabilidade, volume_potencial")
lines.append("- Tipos errados em meta/realizado (texto em vez de numero)")
lines.append("- Metas sem data ou data fora do ano => meta_ytd = 0")
lines.append("- Oportunidades sem valor => pipeline_total = 0")
lines.append("- Realizado sem data => YTD nao filtra corretamente")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(str(OUT))
