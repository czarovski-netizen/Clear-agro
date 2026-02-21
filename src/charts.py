from __future__ import annotations

import pandas as pd


def build_meta_realizado_mensal(metas_m: pd.DataFrame, real_m: pd.DataFrame) -> pd.DataFrame:
    if metas_m.empty and real_m.empty:
        return pd.DataFrame()
    df = pd.merge(metas_m, real_m, on="data", how="outer").sort_values("data")
    if "meta" not in df.columns:
        df["meta"] = 0
    if "receita" not in df.columns:
        df["receita"] = 0
    return df
