from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FINANCE_RENDER_PATHS = [
    "02_financeiro/dashboard_online/data/latest_snapshot.json",
    "data/exports/finance_executive_summary.csv",
    "data/exports/finance_kpis_monthly.csv",
    "data/exports/finance_pack.md",
    "data/exports/finance_reconciliation_exceptions.csv",
    "data/marts/fact_ap_ar.csv",
    "data/marts/fact_cashflow_detailed.csv",
    "data/marts/fact_dre_finance.csv",
    "data/marts/fact_reconciliation_finance.csv",
    "data/quality/finance_pack_report.json",
    "data/staging/stg_banks.csv",
]


def run_cmd(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def run_python(script: str, *extra: str) -> None:
    cmd = [sys.executable, script, *extra]
    result = run_cmd(cmd)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)


def git_has_staged_changes() -> bool:
    result = run_cmd(["git", "diff", "--cached", "--quiet"], check=False)
    return result.returncode != 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild finance dashboard artifacts and publish them for Render auto-deploy."
    )
    parser.add_argument(
        "--push-remote",
        action="append",
        default=[],
        help="Git remote to push after commit. Repeat for multiple remotes, e.g. --push-remote fork --push-remote origin",
    )
    parser.add_argument(
        "--commit-message",
        default="Refresh finance dashboard snapshot",
        help="Git commit message to use when artifacts changed.",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Build and commit only, without pushing.",
    )
    args = parser.parse_args()

    run_id = datetime.now().strftime("finance_render_%Y%m%d_%H%M%S")

    print("[1/4] Building finance pack...")
    run_python("src/reports/build_finance_pack.py")

    print("[2/4] Building finance dashboard snapshot...")
    run_python("02_financeiro/dashboard_online/build_snapshot.py")

    print("[3/4] Generating finance dashboard healthcheck...")
    run_python("scripts/finance_dashboard_publisher.py", "--config", "templates/default_config.yaml", "--run-id", run_id)

    print("[4/4] Staging finance dashboard artifacts...")
    run_cmd(["git", "add", "--", *FINANCE_RENDER_PATHS])

    if not git_has_staged_changes():
        print("No staged finance artifact changes detected.")
        return 0

    commit_result = run_cmd(["git", "commit", "-m", args.commit_message])
    if commit_result.stdout.strip():
        print(commit_result.stdout.strip())
    if commit_result.stderr.strip():
        print(commit_result.stderr.strip(), file=sys.stderr)

    if args.skip_push:
        print("Push skipped by parameter.")
        return 0

    for remote in args.push_remote:
        print(f"Pushing to {remote}...")
        push_result = run_cmd(["git", "push", remote, "main"])
        if push_result.stdout.strip():
            print(push_result.stdout.strip())
        if push_result.stderr.strip():
            print(push_result.stderr.strip(), file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
