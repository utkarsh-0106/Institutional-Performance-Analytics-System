"""Data cleaning and preprocessing."""
import pandas as pd

from config.settings import ACCREDITATION_GRADE_MAP
from services.data_validation import DataValidationService


class DataCleaningService:
    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        df = DataValidationService.normalize_columns(df.copy())

        df["institution_name"] = df["institution_name"].astype(str).str.strip()
        df = df[df["institution_name"].str.len() > 0]
        df = df.drop_duplicates(subset=["institution_name"], keep="first")

        numeric_defaults = {
            "student_enrollment": 0,
            "faculty_count": 0,
            "placement_percentage": 0.0,
            "research_publications": 0,
            "infrastructure_score": 0.0,
            "nirf_rank": 999,
        }
        for col, default in numeric_defaults.items():
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)

        df["placement_percentage"] = df["placement_percentage"].clip(0, 100)
        df["infrastructure_score"] = df["infrastructure_score"].clip(0, 100)
        df["student_enrollment"] = df["student_enrollment"].clip(0, 100000).astype(int)
        df["faculty_count"] = df["faculty_count"].clip(0, 5000).astype(int)
        df["research_publications"] = df["research_publications"].clip(0, 10000).astype(int)
        df["nirf_rank"] = df["nirf_rank"].clip(1, 999).astype(int)

        df["accreditation_grade"] = (
            df["accreditation_grade"].astype(str).str.strip().str.upper()
        )
        valid_grades = set(ACCREDITATION_GRADE_MAP.keys())
        df["accreditation_grade"] = df["accreditation_grade"].apply(
            lambda g: g if g in valid_grades else "NA"
        )

        if "state" not in df.columns:
            df["state"] = "Unknown"
        else:
            df["state"] = df["state"].fillna("Unknown").astype(str).str.strip()

        return df.reset_index(drop=True)
