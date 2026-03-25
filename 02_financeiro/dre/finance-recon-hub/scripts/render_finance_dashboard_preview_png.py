from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, value: str) -> None:
    draw.rounded_rectangle(box, radius=20, fill="#fffdf8", outline="#d9d0c1", width=2)
    x1, y1, x2, y2 = box
    draw.text((x1 + 18, y1 + 18), title, fill="#5c6a70", font=font(20, bold=False))
    draw.text((x1 + 18, y1 + 60), value, fill="#172126", font=font(30, bold=True))


def bar_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    values: list[float],
    labels: list[str],
    title: str,
    subtitle: str,
    color: str,
    baseline_zero: bool = False,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill="#fffdf8", outline="#d9d0c1", width=2)
    draw.text((x1 + 22, y1 + 18), title, fill="#172126", font=font(26, bold=True))
    draw.text((x1 + 22, y1 + 54), subtitle, fill="#5c6a70", font=font(17))

    chart_x1 = x1 + 30
    chart_y1 = y1 + 96
    chart_x2 = x2 - 20
    chart_y2 = y2 - 42
    draw.rectangle((chart_x1, chart_y1, chart_x2, chart_y2), fill="#faf6ee")

    min_val = min(values) if values else 0
    max_val = max(values) if values else 0
    if baseline_zero:
        min_val = min(min_val, 0)
        max_val = max(max_val, 0)
    if max_val == min_val:
        max_val += 1
        min_val -= 1

    def scale_y(value: float) -> float:
        ratio = (value - min_val) / (max_val - min_val)
        return chart_y2 - ratio * (chart_y2 - chart_y1)

    zero_y = scale_y(0 if baseline_zero else min_val)
    draw.line((chart_x1, zero_y, chart_x2, zero_y), fill="#9aaab1", width=2)

    gap = 12
    width = chart_x2 - chart_x1
    bar_w = max((width - gap * (len(values) - 1)) / max(len(values), 1), 12)
    for idx, value in enumerate(values):
        bx1 = chart_x1 + idx * (bar_w + gap)
        bx2 = bx1 + bar_w
        if baseline_zero:
            top = min(zero_y, scale_y(value))
            bottom = max(zero_y, scale_y(value))
        else:
            top = scale_y(value)
            bottom = chart_y2
        draw.rounded_rectangle((bx1, top, bx2, bottom), radius=6, fill=color)
        draw.text((bx1, chart_y2 + 8), labels[idx], fill="#5c6a70", font=font(15))


def qa_table(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rows: list[dict[str, str]]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill="#fffdf8", outline="#d9d0c1", width=2)
    draw.text((x1 + 22, y1 + 18), "Checklist de QA", fill="#172126", font=font(26, bold=True))
    top = y1 + 70
    draw.text((x1 + 24, top), "Check", fill="#5c6a70", font=font(17, bold=True))
    draw.text((x1 + 340, top), "Status", fill="#5c6a70", font=font(17, bold=True))
    draw.text((x1 + 460, top), "Detalhe", fill="#5c6a70", font=font(17, bold=True))
    y = top + 30
    for row in rows[:11]:
        draw.line((x1 + 20, y - 8, x2 - 20, y - 8), fill="#e9dfd1", width=1)
        draw.text((x1 + 24, y), row["check"], fill="#172126", font=font(15))
        status = row["status"]
        fill = "#1f7a4d" if status == "PASS" else "#c15c2d"
        draw.text((x1 + 340, y), status, fill=fill, font=font(15, bold=True))
        detail = row.get("details") or "-"
        draw.text((x1 + 460, y), detail[:42], fill="#3c4a50", font=font(15))
        y += 30


def monthly_table(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rows: list[dict[str, str]]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill="#fffdf8", outline="#d9d0c1", width=2)
    draw.text((x1 + 22, y1 + 18), "DRE mensal", fill="#172126", font=font(26, bold=True))
    top = y1 + 70
    headers = [("Mes", 24), ("Receita", 110), ("Custos", 310), ("Fixo", 470), ("EBITDA", 610)]
    for label, offset in headers:
        draw.text((x1 + offset, top), label, fill="#5c6a70", font=font(17, bold=True))
    y = top + 30
    for row in rows[:12]:
        draw.line((x1 + 20, y - 8, x2 - 20, y - 8), fill="#e9dfd1", width=1)
        draw.text((x1 + 24, y), row["mes"], fill="#172126", font=font(15))
        draw.text((x1 + 110, y), brl(parse_float(row, "receita_liquida")), fill="#172126", font=font(15))
        draw.text((x1 + 310, y), brl(parse_float(row, "custos_variaveis_total")), fill="#172126", font=font(15))
        draw.text((x1 + 470, y), brl(parse_float(row, "custo_fixo_base")), fill="#172126", font=font(15))
        draw.text((x1 + 610, y), brl(parse_float(row, "ebitda")), fill="#172126", font=font(15))
        y += 30


def build_png(run_dir: Path, output_path: Path) -> None:
    exports_dir = run_dir / "control_tower" / "data" / "exports"
    out_dir = run_dir / "control_tower" / "out"
    mensal_rows = load_csv_rows(exports_dir / "dre_mckinsey_mensal.csv")
    resumo = load_csv_rows(exports_dir / "dre_mckinsey_resumo.csv")[0]
    qa_rows = load_csv_rows(exports_dir / "qa_finance_report.csv")
    health = load_json(out_dir / "dashboard_healthcheck.json")

    image = Image.new("RGB", (1600, 1400), "#f5f1e8")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((40, 30, 1030, 180), radius=28, fill="#fffaf1", outline="#d9d0c1", width=2)
    draw.text((72, 58), "Dashboard Financeiro", fill="#172126", font=font(52, bold=True))
    draw.text(
        (72, 125),
        f"Preview standalone do run {run_dir.name}",
        fill="#5c6a70",
        font=font(22),
    )

    status_fill = "#1a2c2f" if health.get("ready") else "#61311d"
    draw.rounded_rectangle((1070, 30, 1560, 180), radius=28, fill=status_fill)
    draw.text((1102, 62), "STATUS", fill="#d8ebe5", font=font(18, bold=True))
    draw.text((1102, 96), "READY" if health.get("ready") else "PENDENTE", fill="white", font=font(36, bold=True))
    draw.text((1102, 143), health.get("quality_gate", {}).get("detail", "n/a"), fill="#d9e9e3", font=font(16))

    card(draw, (40, 220, 335, 355), "Receita liquida", brl(float(resumo["receita_liquida_total"])))
    card(draw, (355, 220, 650, 355), "Margem bruta", pct(float(resumo["margem_bruta_pct_total"])))
    card(draw, (670, 220, 965, 355), "Margem contribuicao", brl(float(resumo["margem_contribuicao_total"])))
    card(draw, (985, 220, 1280, 355), "Custo fixo", brl(float(resumo["custo_fixo_total"])))
    card(draw, (1300, 220, 1560, 355), "EBITDA total", brl(float(resumo["ebitda_total"])))

    meses = [row["mes"][-2:] for row in mensal_rows]
    receita = [parse_float(row, "receita_liquida") for row in mensal_rows]
    ebitda = [parse_float(row, "ebitda") for row in mensal_rows]

    bar_chart(
        draw,
        (40, 390, 780, 760),
        receita,
        meses,
        "Receita liquida mensal",
        "Base empresa_receita_operacional",
        "#0c7a6d",
        baseline_zero=False,
    )
    bar_chart(
        draw,
        (820, 390, 1560, 760),
        ebitda,
        meses,
        "EBITDA mensal",
        "Com meses negativos abaixo da linha-base",
        "#c15c2d",
        baseline_zero=True,
    )

    monthly_table(draw, (40, 800, 860, 1360), mensal_rows)
    qa_table(draw, (900, 800, 1560, 1360), qa_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PNG preview for a finance dashboard run.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    output_path = Path(args.output).resolve() if args.output else run_dir / "control_tower" / "out" / "dashboard_preview.png"
    build_png(run_dir, output_path)
    print(str(output_path))


if __name__ == "__main__":
    main()
