"""NAAC accreditation data ingestion."""
from pathlib import Path

import pandas as pd

from config.data_sources import NAAC_CGPA_TO_GRADE, NAAC_COLUMN_MAP, NAAC_FILE
from services.ingestion.base import add_normalized_key, apply_column_map, load_csv_or_excel


class NAACIngestion:
    source_name = "NAAC"

    def __init__(self, file_path: Path = None):
        self.file_path = file_path or NAAC_FILE

    @staticmethod
    def cgpa_to_grade(cgpa: float) -> str:
        if pd.isna(cgpa):
            return "NA"
        for low, high, grade in NAAC_CGPA_TO_GRADE:
            if low <= float(cgpa) <= high:
                return grade
        return "NA"

    def load(self) -> pd.DataFrame:
        raw = load_csv_or_excel(self.file_path)
        if raw is None or raw.empty:
            return pd.DataFrame()

        df = apply_column_map(raw, NAAC_COLUMN_MAP)
        if "institution_name" not in df.columns:
            return pd.DataFrame()

        df["institution_name"] = df["institution_name"].astype(str).str.strip()
        df = df[df["institution_name"].str.len() > 2]

        if "naac_cgpa" in df.columns:
            df["naac_cgpa"] = pd.to_numeric(df["naac_cgpa"], errors="coerce")
            if "accreditation_grade" not in df.columns:
                df["accreditation_grade"] = None
            cgpa_mask = df["naac_cgpa"].notna()
            grade_mask = df["accreditation_grade"].isna() | (df["accreditation_grade"].astype(str).str.strip() == "")
            df.loc[cgpa_mask & grade_mask, "accreditation_grade"] = df.loc[cgpa_mask, "naac_cgpa"].apply(self.cgpa_to_grade)

        if "accreditation_grade" in df.columns:
            df["accreditation_grade"] = (
                df["accreditation_grade"].astype(str).str.strip().str.upper()
                .str.replace("GRADE ", "", regex=False)
            )

        df = df.drop_duplicates(subset=["institution_name"], keep="first")
        return add_normalized_key(df)
