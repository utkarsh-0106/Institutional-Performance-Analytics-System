"""ETL cleaning transforms for merged institutional records."""
import pandas as pd

from config.settings import ACCREDITATION_GRADE_MAP
from services.ingestion.base import normalize_institution_name


class ETLCleaners:
    @staticmethod
    def clean_merged(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        work = df.copy()
        work["institution_name"] = work["institution_name"].astype(str).str.strip()
        work = work[work["institution_name"].str.len() > 2]
        work = work.drop_duplicates(subset=["institution_name"], keep="first")

        if "_merge_key" not in work.columns:
            work["_merge_key"] = work["institution_name"].apply(normalize_institution_name)

        # Fill missing merge columns only. Range clipping belongs to DataCleaningService.
        numeric_defaults = {
            "student_enrollment": 3000,
            "faculty_count": 150,
            "placement_percentage": 65.0,
            "research_publications": 120,
            "infrastructure_score": 60.0,
            "nirf_rank": 500,
        }
        for col, default in numeric_defaults.items():
            if col not in work.columns:
                work[col] = default
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(default)

        if "accreditation_grade" not in work.columns:
            work["accreditation_grade"] = "NA"
        work["accreditation_grade"] = (
            work["accreditation_grade"].astype(str).str.strip().str.upper()
        )
        valid = set(ACCREDITATION_GRADE_MAP.keys())
        work["accreditation_grade"] = work["accreditation_grade"].apply(
            lambda g: g if g in valid else "NA"
        )

        if "state" not in work.columns:
            work["state"] = "Unknown"
        work["state"] = work["state"].fillna("Unknown").astype(str).str.strip()

        if "data_sources" not in work.columns:
            work["data_sources"] = "merged"

        drop_cols = [c for c in work.columns if c.startswith("_") and c != "_merge_key"]
        work = work.drop(columns=[c for c in drop_cols if c in work.columns], errors="ignore")

        return work.reset_index(drop=True)

    @staticmethod
    def fill_missing_from_state_medians(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "state" not in df.columns:
            return df
        work = df.copy()
        for col in ["student_enrollment", "faculty_count", "placement_percentage"]:
            if col not in work.columns:
                continue
            state_medians = work.groupby("state")[col].transform("median")
            work[col] = work[col].fillna(state_medians)
        return work
