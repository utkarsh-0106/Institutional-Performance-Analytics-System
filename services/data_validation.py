"""Data validation for institutional uploads."""
from typing import Dict, List, Tuple

import pandas as pd

from config.settings import COLUMN_ALIASES, NUMERIC_RANGES, REQUIRED_COLUMNS

NUMERIC_COLUMNS = list(NUMERIC_RANGES.keys())


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

        for col in NUMERIC_COLUMNS:
            non_numeric = pd.to_numeric(df[col], errors="coerce").isna().sum()
            if non_numeric > len(df) * 0.5:
                errors.append(f"Column '{col}' has too many invalid numeric values.")

        lo, hi = NUMERIC_RANGES["placement_percentage"]
        placement = pd.to_numeric(df["placement_percentage"], errors="coerce")
        invalid_placement = ((placement < lo) | (placement > hi)).sum()
        if invalid_placement > 0:
            errors.append(f"{invalid_placement} rows have placement_percentage outside {lo}-{hi}.")

        return len(errors) == 0, errors

    @staticmethod
    def quality_report(df: pd.DataFrame) -> Dict:
        """Inspect a dataset without cleaning or mutating it."""
        work = DataValidationService.normalize_columns(df)
        valid, errors = DataValidationService.validate(work)

        missing_required = [c for c in REQUIRED_COLUMNS if c not in work.columns]
        present_cols = [c for c in work.columns if c in REQUIRED_COLUMNS or c in NUMERIC_COLUMNS]

        missing_value_counts = {
            col: int(work[col].isna().sum())
            for col in present_cols
        }

        duplicate_institution_count = 0
        if "institution_name" in work.columns:
            names = work["institution_name"]
            duplicate_institution_count = int(names.duplicated().sum())

        invalid_numeric_counts = {}
        out_of_range_counts = {}
        for col in NUMERIC_COLUMNS:
            if col not in work.columns:
                invalid_numeric_counts[col] = 0
                out_of_range_counts[col] = 0
                continue
            numeric = pd.to_numeric(work[col], errors="coerce")
            originally_present = work[col].notna()
            invalid_numeric_counts[col] = int((originally_present & numeric.isna()).sum())
            lo, hi = NUMERIC_RANGES[col]
            out_of_range_counts[col] = int(((numeric < lo) | (numeric > hi)).sum())

        has_warnings = (
            duplicate_institution_count > 0
            or any(v > 0 for v in missing_value_counts.values())
            or any(v > 0 for v in invalid_numeric_counts.values())
            or any(v > 0 for v in out_of_range_counts.values())
        )
        if not valid:
            status = "FAIL"
        elif has_warnings:
            status = "WARNING"
        else:
            status = "PASS"

        return {
            "status": status,
            "row_count": int(len(work)),
            "missing_required_columns": missing_required,
            "missing_value_counts": missing_value_counts,
            "duplicate_institution_count": duplicate_institution_count,
            "invalid_numeric_counts": invalid_numeric_counts,
            "out_of_range_counts": out_of_range_counts,
            "errors": errors,
        }
