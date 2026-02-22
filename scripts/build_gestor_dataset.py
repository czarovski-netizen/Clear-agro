from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "out" / "base_unificada.xlsx"
DEST = ROOT / "out" / "base_unificada_gestor.xlsx"
ACL = ROOT / "data" / "access_control.json"


def _clean_list(values):
    return [v for v in values if v not in (None, "", "TODOS")]


def main() -> int:
    if not SRC.exists():
        print("Base nao encontrada:", SRC)
        return 2

    acl = {}
    if ACL.exists():
        try:
            acl = pd.read_json(ACL).get("gestor", {})
        except Exception:
            import json

            acl = json.loads(ACL.read_text(encoding="utf-8")).get("gestor", {})

    allow = _clean_list(acl.get("allow_vendedores", []))
    block = _clean_list(acl.get("block_vendedores", []))
    block_canais = [str(c).strip().upper() for c in _clean_list(acl.get("block_canais", []))]
    block_clientes = [str(c).strip().upper() for c in _clean_list(acl.get("block_clientes", []))]

    xls = pd.ExcelFile(SRC)
    out = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(SRC, sheet_name=sheet)
        if "vendedor" in df.columns:
            if allow:
                df = df[df["vendedor"].isin(allow)]
            elif block:
                df = df[~df["vendedor"].isin(block)]
        if "canal" in df.columns and block_canais:
            df["canal"] = df["canal"].astype(str)
            df = df[~df["canal"].str.upper().isin(block_canais)]
        if "cliente" in df.columns and block_clientes:
            df["cliente"] = df["cliente"].astype(str)
            df = df[~df["cliente"].str.upper().isin(block_clientes)]
        out[sheet] = df

    with pd.ExcelWriter(DEST, engine="openpyxl") as writer:
        for name, df in out.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    print("Gerado:", DEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
