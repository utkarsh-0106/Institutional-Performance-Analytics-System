"""UGC recognized institutions ingestion."""
from pathlib import Path

import pandas as pd

from config.data_sources import UGC_COLUMN_MAP, UGC_FILE
from services.ingestion.base import add_normalized_key, apply_column_map, load_csv_or_excel


class UGCIngestion:
    source_name = "UGC"

    def __init__(self, file_path: Path = None):
        self.file_path = file_path or UGC_FILE

    def load(self) -> pd.DataFrame:
        raw = load_csv_or_excel(self.file_path)
        if raw is None or raw.empty:
            return pd.DataFrame()

        df = apply_column_map(raw, UGC_COLUMN_MAP)
        if "institution_name" not in df.columns:
            return pd.DataFrame()

        df["institution_name"] = df["institution_name"].astype(str).str.strip()
        df = df[df["institution_name"].str.len() > 2]

        if "state" in df.columns:
            df["state"] = df["state"].astype(str).str.strip().str.title()
        if "year_established" in df.columns:
            df["year_established"] = pd.to_numeric(df["year_established"], errors="coerce")

        df = df.drop_duplicates(subset=["institution_name"], keep="first")
        return add_normalized_key(df)
