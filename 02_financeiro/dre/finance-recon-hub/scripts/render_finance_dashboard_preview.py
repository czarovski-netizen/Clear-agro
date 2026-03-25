from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def brl(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def parse_float(row: dict[str, str], key: str) -> float:
    return float((row.get(key) or "0").strip())


def build_bar_svg(values: list[float], labels: list[str], color: str, baseline_zero: bool = False) -> str:
    width = 880
    height = 260
    pad_x = 42
    pad_top = 20
    pad_bottom = 38
    chart_height = height - pad_top - pad_bottom
    chart_width = width - pad_x * 2
    count = max(len(values), 1)
    gap = 12
    bar_width = max((chart_width - gap * (count - 1)) / count, 12)

    min_val = min(values) if values else 0
    max_val = max(values) if values else 0
    if baseline_zero:
        min_val = min(min_val, 0)
        max_val = max(max_val, 0)
    if max_val == min_val:
        max_val += 1
        min_val -= 1

    def y_pos(value: float) -> float:
        ratio = (value - min_val) / (max_val - min_val)
        return pad_top + (1 - ratio) * chart_height

    zero_y = y_pos(0 if baseline_zero else min_val)
    elements: list[str] = [
        f'<line x1="{pad_x}" y1="{zero_y:.1f}" x2="{width - pad_x}" y2="{zero_y:.1f}" '
        'stroke="#8fa3ad" stroke-width="1"/>'
    ]

    for idx, value in enumerate(values):
        x = pad_x + idx * (bar_width + gap)
        top = y_pos(max(value, 0) if baseline_zero else value)
        bottom = zero_y if baseline_zero else y_pos(min_val)
        if baseline_zero and value < 0:
            top = zero_y
            bottom = y_pos(value)
        rect_y = min(top, bottom)
        rect_h = max(abs(bottom - top), 1.5)
        label_y = height - 12
        text_value = brl(value)
        elements.append(
            f'<rect x="{x:.1f}" y="{rect_y:.1f}" width="{bar_width:.1f}" height="{rect_h:.1f}" '
            f'rx="6" fill="{color}"/>'
        )
        elements.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{label_y}" text-anchor="middle" '
            'font-size="11" fill="#3b4a52">'
            f"{html.escape(labels[idx])}</text>"
        )
        value_y = rect_y - 6 if value >= 0 else rect_y + rect_h + 14
        elements.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{value_y:.1f}" text-anchor="middle" '
            'font-size="11" fill="#243238">'
            f"{html.escape(text_value)}</text>"
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" '
        f'aria-label="Grafico">{ "".join(elements) }</svg>'
    )


def render_html(run_id: str, mensal_rows: list[dict[str, str]], resumo: dict[str, str], qa_rows: list[dict[str, str]], health: dict) -> str:
    meses = [row["mes"][-2:] for row in mensal_rows]
    receita = [parse_float(row, "receita_liquida") for row in mensal_rows]
    ebitda = [parse_float(row, "ebitda") for row in mensal_rows]

    receita_total = float(resumo["receita_liquida_total"])
    margem_bruta = float(resumo["margem_bruta_pct_total"])
    ebitda_total = float(resumo["ebitda_total"])
    margem_contrib = float(resumo["margem_contribuicao_total"])
    custo_fixo = float(resumo["custo_fixo_total"])

    warn_rows = [row for row in qa_rows if (row.get("status") or "").upper() == "WARN"]
    neg_months = 0
    if warn_rows:
        details = warn_rows[0].get("details") or ""
        for part in details.split(";"):
            part = part.strip()
            if part.startswith("meses_negativos="):
                neg_months = int(part.split("=", 1)[1])
                break

    status_color = "#1f7a4d" if health.get("ready") else "#b44b1f"
    status_text = "READY" if health.get("ready") else "PENDENTE"
    quality = health.get("quality_gate", {})
    quality_text = quality.get("detail", "n/a")
    revenue_svg = build_bar_svg(receita, meses, "#0c7a6d", baseline_zero=False)
    ebitda_svg = build_bar_svg(ebitda, meses, "#c15c2d", baseline_zero=True)

    rows_html = "".join(
        "<tr>"
        f"<td>{html.escape(row['mes'])}</td>"
        f"<td>{html.escape(brl(parse_float(row, 'receita_liquida')))}</td>"
        f"<td>{html.escape(brl(parse_float(row, 'custos_variaveis_total')))}</td>"
        f"<td>{html.escape(brl(parse_float(row, 'custo_fixo_base')))}</td>"
        f"<td>{html.escape(brl(parse_float(row, 'ebitda')))}</td>"
        "</tr>"
        for row in mensal_rows
    )
    qa_html = "".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row.get('details') or '-')}</td>"
        "</tr>"
        for row in qa_rows
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Finance Dashboard Preview - {html.escape(run_id)}</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --ink: #172126;
      --muted: #5c6a70;
      --panel: #fffdf8;
      --line: #d9d0c1;
      --green: #0c7a6d;
      --orange: #c15c2d;
      --soft-green: #dff2eb;
      --soft-orange: #f8e3d8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #efe4ce 0, transparent 28%),
        linear-gradient(180deg, #f9f5ee 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 22px 56px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 18px;
      align-items: end;
      margin-bottom: 22px;
    }}
    .title {{
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
      padding: 22px;
      border-radius: 18px;
      box-shadow: 0 18px 50px rgba(65, 54, 34, 0.08);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 42px;
      line-height: 1;
      letter-spacing: -0.03em;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 16px;
    }}
    .statusbox {{
      background: linear-gradient(135deg, #1a2c2f 0%, #324247 100%);
      color: white;
      padding: 22px;
      border-radius: 18px;
      min-height: 140px;
    }}
    .chip {{
      display: inline-block;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      background: {status_color};
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
      margin-bottom: 18px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 12px 30px rgba(65, 54, 34, 0.05);
    }}
    .metric .label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .metric .value {{
      font-size: 28px;
      line-height: 1.05;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 12px 30px rgba(65, 54, 34, 0.05);
    }}
    h2 {{
      margin: 0 0 10px;
      font-size: 22px;
      letter-spacing: -0.02em;
    }}
    .caption {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 14px;
    }}
    .chart {{
      width: 100%;
      height: auto;
      display: block;
      border-radius: 12px;
      background: linear-gradient(180deg, rgba(242,236,224,0.6), rgba(255,255,255,0.85));
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .note {{
      padding: 14px 16px;
      border-radius: 14px;
      margin-top: 12px;
      font-size: 14px;
    }}
    .note.warn {{ background: var(--soft-orange); }}
    .note.ok {{ background: var(--soft-green); }}
    @media (max-width: 960px) {{
      .hero, .row, .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="title">
        <h1>Dashboard Financeiro</h1>
        <p class="subtitle">Preview standalone do run <strong>{html.escape(run_id)}</strong> gerado a partir dos exports do fechamento financeiro.</p>
      </div>
      <div class="statusbox">
        <div class="chip">{status_text}</div>
        <p><strong>Quality gate:</strong> {html.escape(quality_text)}</p>
        <p><strong>QA:</strong> 0 FAIL / {len(warn_rows)} WARN</p>
        <p><strong>EBITDA negativo:</strong> {neg_months} meses monitorados</p>
      </div>
    </section>

    <section class="grid">
      <article class="metric">
        <div class="label">Receita líquida</div>
        <div class="value">{html.escape(brl(receita_total))}</div>
      </article>
      <article class="metric">
        <div class="label">Margem bruta</div>
        <div class="value">{html.escape(pct(margem_bruta))}</div>
      </article>
      <article class="metric">
        <div class="label">Margem de contribuição</div>
        <div class="value">{html.escape(brl(margem_contrib))}</div>
      </article>
      <article class="metric">
        <div class="label">Custo fixo</div>
        <div class="value">{html.escape(brl(custo_fixo))}</div>
      </article>
      <article class="metric">
        <div class="label">EBITDA total</div>
        <div class="value">{html.escape(brl(ebitda_total))}</div>
      </article>
    </section>

    <section class="row">
      <article class="panel">
        <h2>Receita líquida mensal</h2>
        <div class="caption">Base `empresa_receita_operacional` aplicada no DRE consistente de 2025.</div>
        {revenue_svg}
      </article>
      <article class="panel">
        <h2>EBITDA mensal</h2>
        <div class="caption">Meses abaixo de zero aparecem abaixo da linha-base.</div>
        {ebitda_svg}
      </article>
    </section>

    <section class="row">
      <article class="panel">
        <h2>DRE mensal</h2>
        <table>
          <thead>
            <tr>
              <th>Mês</th>
              <th>Receita</th>
              <th>Custos variáveis</th>
              <th>Custo fixo</th>
              <th>EBITDA</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </article>
      <article class="panel">
        <h2>Checklist de QA</h2>
        <table>
          <thead>
            <tr>
              <th>Check</th>
              <th>Status</th>
              <th>Detalhe</th>
            </tr>
          </thead>
          <tbody>{qa_html}</tbody>
        </table>
        <div class="note {'warn' if warn_rows else 'ok'}">
          {'Atencao: o dataset continua com meses de EBITDA negativo em monitoramento, apesar de o gate tecnico estar aprovado.' if warn_rows else 'Todos os checks passaram sem alertas adicionais.'}
        </div>
      </article>
    </section>
  </div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a standalone HTML preview for a finance dashboard run.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    exports_dir = run_dir / "control_tower" / "data" / "exports"
    out_dir = run_dir / "control_tower" / "out"

    mensal_rows = load_csv_rows(exports_dir / "dre_mckinsey_mensal.csv")
    resumo_rows = load_csv_rows(exports_dir / "dre_mckinsey_resumo.csv")
    qa_rows = load_csv_rows(exports_dir / "qa_finance_report.csv")
    health = load_json(out_dir / "dashboard_healthcheck.json")

    if not resumo_rows:
        raise RuntimeError("dre_mckinsey_resumo.csv vazio")

    output_path = Path(args.output).resolve() if args.output else out_dir / "dashboard_preview.html"
    html_content = render_html(run_dir.name, mensal_rows, resumo_rows[0], qa_rows, health)
    output_path.write_text(html_content, encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
