"""Data validation for institutional uploads."""
from typing import List, Tuple

import pandas as pd

from config.settings import COLUMN_ALIASES, REQUIRED_COLUMNS


class DataValidationService:
    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        rename_map = {c: COLUMN_ALIASES[c] for c in df.columns if c in COLUMN_ALIASES}
        df = df.rename(columns=rename_map)
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        return df

    @staticmethod
    def validate(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        df = DataValidationService.normalize_columns(df)

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")
            return False, errors

        if df.empty:
            errors.append("Dataset is empty.")
            return False, errors

        if df["institution_name"].isna().all():
            errors.append("All institution names are missing.")

        numeric_cols = [
            "student_enrollment", "faculty_count", "placement_percentage",
            "research_publications", "infrastructure_score", "nirf_rank",
        ]
        for col in numeric_cols:
            non_numeric = pd.to_numeric(df[col], errors="coerce").isna().sum()
            if non_numeric > len(df) * 0.5:
                errors.append(f"Column '{col}' has too many invalid numeric values.")

        invalid_placement = (
            (pd.to_numeric(df["placement_percentage"], errors="coerce") < 0) |
            (pd.to_numeric(df["placement_percentage"], errors="coerce") > 100)
        ).sum()
        if invalid_placement > 0:
            errors.append(f"{invalid_placement} rows have placement_percentage outside 0-100.")

        return len(errors) == 0, errors
