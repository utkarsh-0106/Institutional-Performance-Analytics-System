"""Custom institutional ranking engine."""
import pandas as pd

from config.settings import RANKING_WEIGHTS


class RankingEngine:
    @staticmethod
    def apply_rankings(kpi_df: pd.DataFrame) -> pd.DataFrame:
        if kpi_df.empty:
            return kpi_df

        work = kpi_df.copy()
        work["composite_rank_score"] = (
            work["academic_score"] * RANKING_WEIGHTS["academic"]
            + work["placement_score"] * RANKING_WEIGHTS["placement"]
            + work["research_score"] * RANKING_WEIGHTS["research"]
            + work["infrastructure_score_kpi"] * RANKING_WEIGHTS["infrastructure"]
            + work["faculty_score"] * RANKING_WEIGHTS["faculty"]
            + work["accreditation_score"] * RANKING_WEIGHTS["accreditation"]
        ).round(2)

        work = work.sort_values("composite_rank_score", ascending=False).reset_index(drop=True)
        work["institution_rank"] = range(1, len(work) + 1)

        def categorize(rank: int) -> str:
            if rank <= 50:
                return "Top 50"
            if rank <= 100:
                return "Top 100"
            if rank <= 200:
                return "Top 200"
            return "Beyond 200"

        work["ranking_category"] = work["institution_rank"].apply(categorize)
        return work

    @staticmethod
    def get_top_n(kpi_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        if kpi_df.empty:
            return kpi_df
        return kpi_df.nsmallest(n, "institution_rank") if "institution_rank" in kpi_df.columns else kpi_df.head(n)

    @staticmethod
    def update_db_records(kpi_df: pd.DataFrame, records: list) -> list:
        rank_map = {
            row["institution_name"]: {
                "composite_rank_score": float(row["composite_rank_score"]),
                "institution_rank": int(row["institution_rank"]),
                "ranking_category": str(row["ranking_category"]),
            }
            for _, row in kpi_df.iterrows()
        }
        for rec in records:
            info = rank_map.get(rec["institution_name"], {})
            rec.update(info)
        return records
