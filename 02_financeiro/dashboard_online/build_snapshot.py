from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def to_float(value: str | None) -> float:
    return float((value or "0").strip())


def load_jsonl_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def contato_nome(row: dict) -> str:
    contato = row.get("contato") or {}
    if isinstance(contato, dict):
        nome = str(contato.get("nome") or "").strip()
        if nome:
            return nome
        contato_id = contato.get("id")
        if contato_id:
            return f"Contato {contato_id}"
    return "N/D"


def normalize_contas(paths: list[Path], tipo: str) -> list[dict]:
    items: list[dict] = []
    for path in paths:
        for row in load_jsonl_rows(path):
            try:
                valor = float(row.get("valor") or 0)
            except Exception:
                valor = 0.0
            vencimento = str(row.get("vencimento") or "").strip()
            items.append(
                {
                    "tipo": tipo,
                    "valor": valor,
                    "vencimento": vencimento,
                    "situacao": str(row.get("situacao") or ""),
                    "contato": contato_nome(row),
                }
            )
    return items


def aging_bucket(delta_days: int) -> str:
    if delta_days < -60:
        return "Vencido >60"
    if delta_days < -30:
        return "Vencido 31-60"
    if delta_days < 0:
        return "Vencido 1-30"
    if delta_days <= 30:
        return "A vencer 0-30"
    if delta_days <= 60:
        return "A vencer 31-60"
    return "A vencer >60"


def build_aging(rows: list[dict], today_dt: datetime) -> list[dict]:
    buckets = {
        "Vencido >60": 0.0,
        "Vencido 31-60": 0.0,
        "Vencido 1-30": 0.0,
        "A vencer 0-30": 0.0,
        "A vencer 31-60": 0.0,
        "A vencer >60": 0.0,
    }
    for row in rows:
        vencimento = row.get("vencimento") or ""
        if not vencimento:
            continue
        try:
            due = datetime.fromisoformat(vencimento)
        except ValueError:
            continue
        delta = (due.date() - today_dt.date()).days
        buckets[aging_bucket(delta)] += float(row.get("valor") or 0.0)
    return [{"bucket": key, "valor": round(value, 2)} for key, value in buckets.items()]


def build_cash_projection(ap_rows: list[dict], ar_rows: list[dict], today_dt: datetime, days: int = 30) -> dict:
    horizon = today_dt.date() + timedelta(days=days)
    daily: dict[str, dict[str, float]] = {}

    def ensure_day(day: str) -> dict[str, float]:
        if day not in daily:
            daily[day] = {"inflow": 0.0, "outflow": 0.0}
        return daily[day]

    def process(rows: list[dict], kind: str) -> list[dict]:
        upcoming: list[dict] = []
        for row in rows:
            vencimento = row.get("vencimento") or ""
            if not vencimento:
                continue
            try:
                due = datetime.fromisoformat(vencimento).date()
            except ValueError:
                continue
            if not (today_dt.date() <= due <= horizon):
                continue
            bucket = ensure_day(due.isoformat())
            value = float(row.get("valor") or 0.0)
            if kind == "inflow":
                bucket["inflow"] += value
            else:
                bucket["outflow"] += value
            upcoming.append(
                {
                    "data": due.isoformat(),
                    "contato": row.get("contato", "N/D"),
                    "valor": round(value, 2),
                    "tipo": kind,
                }
            )
        upcoming.sort(key=lambda item: item["valor"], reverse=True)
        return upcoming

    upcoming_in = process(ar_rows, "inflow")
    upcoming_out = process(ap_rows, "outflow")

    ordered_days = []
    cumulative = 0.0
    for offset in range(days + 1):
        day = (today_dt.date() + timedelta(days=offset)).isoformat()
        values = ensure_day(day)
        net = values["inflow"] - values["outflow"]
        cumulative += net
        ordered_days.append(
            {
                "data": day,
                "inflow": round(values["inflow"], 2),
                "outflow": round(values["outflow"], 2),
                "net": round(net, 2),
                "cumulative_net": round(cumulative, 2),
            }
        )

    negative_days = sum(1 for row in ordered_days if row["cumulative_net"] < 0)
    return {
        "days": ordered_days,
        "inflow_30d": round(sum(row["inflow"] for row in ordered_days), 2),
        "outflow_30d": round(sum(row["outflow"] for row in ordered_days), 2),
        "net_30d": round(sum(row["net"] for row in ordered_days), 2),
        "min_cumulative_30d": round(min(row["cumulative_net"] for row in ordered_days), 2),
        "negative_cumulative_days": negative_days,
        "top_inflows": upcoming_in[:12],
        "top_outflows": upcoming_out[:12],
        "opening_balance_available": False,
    }


def aggregate_sum(rows: list[dict[str, str]], key: str, value_key: str) -> list[dict]:
    bucket: dict[str, float] = {}
    for row in rows:
        name = str(row.get(key) or "N/D").strip() or "N/D"
        bucket[name] = bucket.get(name, 0.0) + to_float(row.get(value_key))
    items = [{"label": label, "valor": round(valor, 2)} for label, valor in bucket.items()]
    items.sort(key=lambda item: item["valor"], reverse=True)
    return items


def aggregate_count(rows: list[dict[str, str]], key: str) -> list[dict]:
    bucket: dict[str, int] = {}
    for row in rows:
        name = str(row.get(key) or "N/D").strip() or "N/D"
        bucket[name] = bucket.get(name, 0) + 1
    items = [{"label": label, "qtd": qtd} for label, qtd in bucket.items()]
    items.sort(key=lambda item: item["qtd"], reverse=True)
    return items


def latest_file(paths: list[Path], pattern: str) -> Path | None:
    matches: list[Path] = []
    for base in paths:
        if base.exists():
            matches.extend([p for p in base.glob(pattern) if p.is_file()])
    if not matches:
        return None
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def load_status_summary(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {"exists": False}
    payload = load_json(path)
    return {
        "exists": True,
        "file": str(path),
        "name": path.name,
        "generated_at": payload.get("generated_at", ""),
        "status": payload.get("status", ""),
        "run_id": payload.get("run_id", ""),
        "checks_summary": payload.get("checks_summary", {}),
        "company_scope": payload.get("company_scope", ""),
        "warnings": payload.get("warnings", []),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    clear_os_root = root.parent
    integration_status_roots = [
        clear_os_root / "logs" / "integration" / "status",
        clear_os_root / "11_agentes_automacoes" / "12_integracoes_agent" / "pipeline" / "out" / "status",
    ]
    latest_path = root / "dre" / "finance-recon-hub" / "out" / "aios" / "monthly-fin-close" / "latest.json"
    latest = load_json(latest_path)
    run_dir = Path(str(latest["path"])).resolve()

    exports_dir = run_dir / "control_tower" / "data" / "exports"
    out_dir = run_dir / "control_tower" / "out"

    mensal_rows = load_csv_rows(exports_dir / "dre_mckinsey_mensal.csv")
    resumo_rows = load_csv_rows(exports_dir / "dre_mckinsey_resumo.csv")
    qa_rows = load_csv_rows(exports_dir / "qa_finance_report.csv")
    review_rows = load_csv_rows(exports_dir / "fornecedores_revisao_governanca.csv")
    pending_rows = load_csv_rows(exports_dir / "fornecedores_pendentes_nome.csv")
    ap_rows_classificados = load_csv_rows(exports_dir / "ap_bling_classificado.csv")
    health = load_json(out_dir / "dashboard_healthcheck.json")
    today_dt = datetime.now()

    ap_rows = normalize_contas(
        [
            clear_os_root / "bling_api" / "contas_pagar_cache.jsonl",
            clear_os_root / "bling_api" / "contas_pagar_cache_cr.jsonl",
        ],
        "pagar",
    )
    ar_rows = normalize_contas(
        [
            clear_os_root / "bling_api" / "contas_receber_cache.jsonl",
            clear_os_root / "bling_api" / "contas_receber_cache_cr.jsonl",
        ],
        "receber",
    )

    resumo = resumo_rows[0] if resumo_rows else {}
    warn_count = sum(1 for row in qa_rows if (row.get("status") or "").upper() == "WARN")
    fail_count = sum(1 for row in qa_rows if (row.get("status") or "").upper() == "FAIL")

    negative_months = 0
    for row in qa_rows:
        if row.get("check") == "meses_ebitda_negativo_monitorado":
            details = row.get("details") or ""
            for part in details.split(";"):
                part = part.strip()
                if part.startswith("meses_negativos="):
                    negative_months = int(part.split("=", 1)[1])
                    break

    horizon = today_dt + timedelta(days=30)
    ap_aberto = round(sum(float(row["valor"]) for row in ap_rows), 2)
    ar_aberto = round(sum(float(row["valor"]) for row in ar_rows), 2)
    ap_vencido = round(
        sum(float(row["valor"]) for row in ap_rows if row["vencimento"] and datetime.fromisoformat(row["vencimento"]).date() < today_dt.date()),
        2,
    )
    ar_vencido = round(
        sum(float(row["valor"]) for row in ar_rows if row["vencimento"] and datetime.fromisoformat(row["vencimento"]).date() < today_dt.date()),
        2,
    )
    ap_30 = round(
        sum(
            float(row["valor"])
            for row in ap_rows
            if row["vencimento"] and today_dt.date() <= datetime.fromisoformat(row["vencimento"]).date() <= horizon.date()
        ),
        2,
    )
    ar_30 = round(
        sum(
            float(row["valor"])
            for row in ar_rows
            if row["vencimento"] and today_dt.date() <= datetime.fromisoformat(row["vencimento"]).date() <= horizon.date()
        ),
        2,
    )

    latest_recon_all = latest_file(integration_status_roots, "bling_supabase_reconciliation*_status.json")
    latest_recon_cz = latest_file(integration_status_roots, "bling_supabase_reconciliation*cz*_status.json")
    latest_recon_cr = latest_file(integration_status_roots, "bling_supabase_reconciliation*cr*_status.json")
    latest_ingest = latest_file(integration_status_roots, "finance_ingest_hub*_status.json")
    latest_import = latest_file(integration_status_roots, "bling_import_generator*_status.json")
    latest_cutover = latest_file(integration_status_roots, "check_bling_cutover_health*_status.json")

    quality_checks = health.get("checks", [])
    quality_ok = sum(1 for item in quality_checks if item.get("ok") is True)
    quality_fail = sum(1 for item in quality_checks if item.get("ok") is False)

    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "run_id": run_dir.name,
        "source_run_dir": str(run_dir),
        "health": health,
        "classic_kpis": {
            "ap_aberto": ap_aberto,
            "ar_aberto": ar_aberto,
            "ap_vencido": ap_vencido,
            "ar_vencido": ar_vencido,
            "fluxo_liquido_previsto_30d": round(ar_30 - ap_30, 2),
            "aging_ap": build_aging(ap_rows, today_dt),
            "aging_ar": build_aging(ar_rows, today_dt),
            "quality_status": "PASS" if health.get("ready") else "FAIL",
        },
        "summary": {
            "receita_liquida_total": to_float(resumo.get("receita_liquida_total")),
            "cmv_proxy_total": to_float(resumo.get("cmv_proxy_total")),
            "lucro_bruto_total": to_float(resumo.get("lucro_bruto_total")),
            "custos_variaveis_total": to_float(resumo.get("custos_variaveis_total")),
            "margem_contribuicao_total": to_float(resumo.get("margem_contribuicao_total")),
            "custo_fixo_total": to_float(resumo.get("custo_fixo_total")),
            "ebitda_total": to_float(resumo.get("ebitda_total")),
            "margem_bruta_pct_total": to_float(resumo.get("margem_bruta_pct_total")),
        },
        "monthly": [
            {
                "mes": row["mes"],
                "mes_num": int(row["mes_num"]),
                "receita_liquida": to_float(row.get("receita_liquida")),
                "custos_variaveis_total": to_float(row.get("custos_variaveis_total")),
                "custo_fixo_base": to_float(row.get("custo_fixo_base")),
                "margem_contribuicao": to_float(row.get("margem_contribuicao")),
                "ebitda": to_float(row.get("ebitda")),
            }
            for row in mensal_rows
        ],
        "qa": {
            "warn_count": warn_count,
            "fail_count": fail_count,
            "negative_ebitda_months": negative_months,
            "checks": qa_rows,
        },
        "governance": {
            "review_count": len(review_rows),
            "review_total_value": round(sum(to_float(row.get("valor_total")) for row in review_rows), 2),
            "pending_count": len(pending_rows),
            "pending_total_value": round(sum(to_float(row.get("valor_total")) for row in pending_rows), 2),
            "top_review": [
                {
                    "fornecedor": row.get("fornecedor", ""),
                    "valor_total": to_float(row.get("valor_total")),
                    "qtd_lancamentos": int(float(row.get("qtd_lancamentos", "0"))),
                    "motivo_governanca": row.get("motivo_governanca", ""),
                }
                for row in review_rows[:10]
            ],
            "top_pending": [
                {
                    "fornecedor": row.get("fornecedor", ""),
                    "valor_total": to_float(row.get("valor_total")),
                    "qtd_lancamentos": int(float(row.get("qtd_lancamentos", "0"))),
                    "motivo_governanca": row.get("motivo_governanca", ""),
                }
                for row in pending_rows[:10]
            ],
        },
        "ap_governance": {
            "ap_total_value": round(sum(to_float(row.get("valor")) for row in ap_rows_classificados), 2),
            "ap_total_rows": len(ap_rows_classificados),
            "mapped_status_value": aggregate_sum(ap_rows_classificados, "status_mapeamento", "valor")[:10],
            "mapped_status_count": aggregate_count(ap_rows_classificados, "status_mapeamento")[:10],
            "category_value": aggregate_sum(ap_rows_classificados, "categoria_mckinsey", "valor")[:12],
            "subcategory_value": aggregate_sum(ap_rows_classificados, "subcategoria_mckinsey", "valor")[:12],
            "top_suppliers": aggregate_sum(ap_rows_classificados, "fornecedor", "valor")[:15],
            "confidence_count": aggregate_count(ap_rows_classificados, "confianca_classificacao")[:10],
        },
        "quality_reconciliation": {
            "quality_check_total": len(quality_checks),
            "quality_check_ok": quality_ok,
            "quality_check_fail": quality_fail,
            "health_ready": bool(health.get("ready")),
            "gate_detail": health.get("quality_gate", {}).get("detail", ""),
            "latest_reconciliation": load_status_summary(latest_recon_all),
            "latest_reconciliation_cz": load_status_summary(latest_recon_cz),
            "latest_reconciliation_cr": load_status_summary(latest_recon_cr),
            "latest_ingest": load_status_summary(latest_ingest),
            "latest_import_generator": load_status_summary(latest_import),
            "latest_cutover_health": load_status_summary(latest_cutover),
        },
        "cash_projection": build_cash_projection(ap_rows, ar_rows, today_dt, days=30),
    }

    output_dir = root / "dashboard_online" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "latest_snapshot.json"
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
