"""KPI calculation engine for institutional performance."""
import pandas as pd

from config.settings import ACCREDITATION_GRADE_MAP, RANKING_WEIGHTS
from utils.helpers import accreditation_to_score, nirf_to_score, normalize_score


class KPIEngine:
    """Computes academic, research, placement, infrastructure, faculty, accreditation KPIs."""

    @staticmethod
    def _compute_bounds(series: pd.Series) -> tuple:
        return float(series.min()), float(series.max())

    @staticmethod
    def calculate_kpis(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        work = df.copy()
        bounds = {}

        for col in ["student_enrollment", "research_publications", "faculty_count"]:
            bounds[col] = KPIEngine._compute_bounds(work[col])

        work["academic_score"] = work.apply(
            lambda r: (
                normalize_score(r["student_enrollment"], *bounds["student_enrollment"]) * 0.6
                + nirf_to_score(r["nirf_rank"]) * 0.4
            ),
            axis=1,
        ).round(2)

        work["research_score"] = work["research_publications"].apply(
            lambda v: normalize_score(v, *bounds["research_publications"])
        ).round(2)

        work["placement_score"] = work["placement_percentage"].round(2)

        work["infrastructure_score_kpi"] = work["infrastructure_score"].round(2)

        work["faculty_score"] = work.apply(
            lambda r: min(100.0, (r["faculty_count"] / max(r["student_enrollment"], 1)) * 500),
            axis=1,
        ).round(2)

        work["accreditation_score"] = work["accreditation_grade"].apply(
            lambda g: accreditation_to_score(g, ACCREDITATION_GRADE_MAP)
        ).round(2)

        work["overall_performance_index"] = KPIEngine.weighted_index(work)

        return work

    @staticmethod
    def weighted_index(work: pd.DataFrame) -> pd.Series:
        w = RANKING_WEIGHTS
        return (
            work["academic_score"] * w["academic"]
            + work["research_score"] * w["research"]
            + work["placement_score"] * w["placement"]
            + work["infrastructure_score_kpi"] * w["infrastructure"]
            + work["faculty_score"] * w["faculty"]
            + work["accreditation_score"] * w["accreditation"]
        ).round(2)

    @staticmethod
    def to_db_records(kpi_df: pd.DataFrame) -> list:
        records = []
        for _, row in kpi_df.iterrows():
            records.append({
                "institution_id": int(row.get("id", 0)),
                "institution_name": str(row["institution_name"]),
                "academic_score": float(row["academic_score"]),
                "research_score": float(row["research_score"]),
                "placement_score": float(row["placement_score"]),
                "infrastructure_score_kpi": float(row["infrastructure_score_kpi"]),
                "faculty_score": float(row["faculty_score"]),
                "accreditation_score": float(row["accreditation_score"]),
                "overall_performance_index": float(row["overall_performance_index"]),
                "composite_rank_score": 0.0,
                "institution_rank": 0,
                "ranking_category": "",
            })
        return records
