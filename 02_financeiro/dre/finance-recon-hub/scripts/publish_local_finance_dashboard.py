from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_latest_run(latest_json_path: Path) -> Path:
    payload = json.loads(latest_json_path.read_text(encoding="utf-8"))
    path = Path(str(payload["path"])).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Run path not found: {path}")
    return path


def run_renderer(script_path: Path, run_dir: Path, output_path: Path) -> None:
    cmd = [sys.executable, str(script_path), "--run-dir", str(run_dir), "--output", str(output_path)]
    subprocess.run(cmd, check=True)


def write_launcher(path: Path, html_path: Path) -> None:
    content = [
        "@echo off",
        f'start "" "{html_path}"',
    ]
    path.write_text("\n".join(content) + "\n", encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a stable local finance dashboard bundle from the latest valid run.")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    latest_json = repo_root / "out" / "aios" / "monthly-fin-close" / "latest.json"

    run_dir = Path(args.run_dir).resolve() if args.run_dir else load_latest_run(latest_json)
    publish_dir = repo_root / "out" / "local_dashboard" / "latest"
    publish_dir.mkdir(parents=True, exist_ok=True)

    html_out = publish_dir / "index.html"
    png_out = publish_dir / "dashboard.png"
    launcher_out = publish_dir / "open_dashboard.cmd"
    metadata_out = publish_dir / "manifest.json"

    run_renderer(scripts_dir / "render_finance_dashboard_preview.py", run_dir, html_out)
    run_renderer(scripts_dir / "render_finance_dashboard_preview_png.py", run_dir, png_out)

    source_health = run_dir / "control_tower" / "out" / "dashboard_healthcheck.json"
    if source_health.exists():
        shutil.copy2(source_health, publish_dir / "dashboard_healthcheck.json")

    write_launcher(launcher_out, html_out)

    manifest = {
        "published_at": datetime.now().isoformat(),
        "source_run_dir": str(run_dir),
        "artifacts": {
            "html": str(html_out),
            "png": str(png_out),
            "launcher": str(launcher_out),
        },
    }
    metadata_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(html_out))
    print(str(png_out))
    print(str(launcher_out))
    print(str(metadata_out))


if __name__ == "__main__":
    main()
