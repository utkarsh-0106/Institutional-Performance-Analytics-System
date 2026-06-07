"""NIRF rankings ingestion."""
from pathlib import Path
from typing import Optional

import pandas as pd

from config.data_sources import NIRF_COLUMN_MAP, NIRF_FILE
from services.ingestion.base import add_normalized_key, apply_column_map, load_csv_or_excel


class NIRFIngestion:
    source_name = "NIRF"

    def __init__(self, file_path: Path = None):
        self.file_path = file_path or NIRF_FILE

    def load(self) -> pd.DataFrame:
        raw = load_csv_or_excel(self.file_path)
        if raw is None or raw.empty:
            return pd.DataFrame()

        df = apply_column_map(raw, NIRF_COLUMN_MAP)
        if "institution_name" not in df.columns:
            return pd.DataFrame()

        df["institution_name"] = df["institution_name"].astype(str).str.strip()
        df = df[df["institution_name"].str.len() > 0]

        if "nirf_rank" in df.columns:
            df["nirf_rank"] = pd.to_numeric(df["nirf_rank"], errors="coerce")
        for col in ["nirf_score", "tlr_score", "rp_score", "go_score", "oi_score", "peer_score"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.drop_duplicates(subset=["institution_name"], keep="first")
        return add_normalized_key(df)

    @staticmethod
    def derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Map NIRF score components to platform metrics."""
        if df.empty:
            return df
        out = df.copy()
        if "go_score" in out.columns:
            out["placement_percentage"] = out["go_score"].clip(0, 100)
        elif "nirf_score" in out.columns:
            out["placement_percentage"] = (out["nirf_score"] * 0.85).clip(30, 99)
        else:
            out["placement_percentage"] = 65.0

        if "rp_score" in out.columns:
            out["research_publications"] = (out["rp_score"] * 8).astype(int).clip(10, 2000)
        else:
            out["research_publications"] = 100

        if "oi_score" in out.columns and "tlr_score" in out.columns:
            out["infrastructure_score"] = ((out["oi_score"].fillna(50) + out["tlr_score"].fillna(50)) / 2).clip(0, 100)
        elif "nirf_score" in out.columns:
            out["infrastructure_score"] = out["nirf_score"].clip(0, 100)
        else:
            out["infrastructure_score"] = 60.0

        return out
