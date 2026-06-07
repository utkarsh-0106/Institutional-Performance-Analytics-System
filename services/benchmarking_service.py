"""Benchmarking against state, national, and top performers."""
import pandas as pd


class BenchmarkingService:
    @staticmethod
    def _merge_inst_kpi(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> pd.DataFrame:
        kpi_cols = [c for c in kpi_df.columns if c not in inst_df.columns or c == "institution_name"]
        return inst_df.merge(kpi_df[kpi_cols], on="institution_name", how="inner")

    @staticmethod
    def compute_national_averages(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> dict:
        if inst_df.empty or kpi_df.empty:
            return {}
        merged = BenchmarkingService._merge_inst_kpi(inst_df, kpi_df)
        return {
            "avg_placement": round(float(merged["placement_percentage"].mean()), 2),
            "avg_research": round(float(merged["research_publications"].mean()), 2),
            "avg_infrastructure": round(float(merged["infrastructure_score"].mean()), 2),
            "avg_enrollment": round(float(merged["student_enrollment"].mean()), 2),
            "avg_faculty": round(float(merged["faculty_count"].mean()), 2),
            "avg_academic_score": round(float(merged["academic_score"].mean()), 2),
            "avg_research_score": round(float(merged["research_score"].mean()), 2),
            "avg_placement_score": round(float(merged["placement_score"].mean()), 2),
            "avg_overall_kpi": round(float(merged["overall_performance_index"].mean()), 2),
        }

    @staticmethod
    def compute_state_averages(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> pd.DataFrame:
        if inst_df.empty or "state" not in inst_df.columns:
            return pd.DataFrame()
        merged = BenchmarkingService._merge_inst_kpi(inst_df, kpi_df)
        return merged.groupby("state").agg(
            avg_placement=("placement_percentage", "mean"),
            avg_research=("research_publications", "mean"),
            avg_infrastructure=("infrastructure_score", "mean"),
            avg_overall_kpi=("overall_performance_index", "mean"),
            institution_count=("institution_name", "count"),
        ).round(2).reset_index()

    @staticmethod
    def get_top_performer_benchmarks(kpi_df: pd.DataFrame, top_n: int = 10) -> dict:
        if kpi_df.empty:
            return {}
        top = kpi_df.nsmallest(top_n, "institution_rank")
        return {
            "avg_academic_score": round(float(top["academic_score"].mean()), 2),
            "avg_research_score": round(float(top["research_score"].mean()), 2),
            "avg_placement_score": round(float(top["placement_score"].mean()), 2),
            "avg_infrastructure_score": round(float(top["infrastructure_score_kpi"].mean()), 2),
            "avg_faculty_score": round(float(top["faculty_score"].mean()), 2),
            "avg_overall_kpi": round(float(top["overall_performance_index"].mean()), 2),
        }

    @staticmethod
    def compare_institution(
        institution_name: str,
        inst_df: pd.DataFrame,
        kpi_df: pd.DataFrame,
    ) -> dict:
        if inst_df.empty or kpi_df.empty:
            return {}

        inst_row = inst_df[inst_df["institution_name"] == institution_name]
        kpi_row = kpi_df[kpi_df["institution_name"] == institution_name]
        if inst_row.empty or kpi_row.empty:
            return {}

        inst = inst_row.iloc[0]
        kpi = kpi_row.iloc[0]
        national = BenchmarkingService.compute_national_averages(inst_df, kpi_df)
        top = BenchmarkingService.get_top_performer_benchmarks(kpi_df)

        state_avg = {}
        state_df = BenchmarkingService.compute_state_averages(inst_df, kpi_df)
        if not state_df.empty and "state" in inst:
            state_row = state_df[state_df["state"] == inst["state"]]
            if not state_row.empty:
                state_avg = state_row.iloc[0].to_dict()

        gaps = {
            "placement_vs_national": round(float(kpi["placement_score"]) - national.get("avg_placement_score", 0), 2),
            "research_vs_national": round(float(kpi["research_score"]) - national.get("avg_research_score", 0), 2),
            "overall_vs_national": round(float(kpi["overall_performance_index"]) - national.get("avg_overall_kpi", 0), 2),
            "overall_vs_top": round(float(kpi["overall_performance_index"]) - top.get("avg_overall_kpi", 0), 2),
        }

        if state_avg:
            gaps["placement_vs_state"] = round(
                float(kpi["placement_score"]) - float(state_avg.get("avg_overall_kpi", 0)), 2
            )

        return {
            "institution_name": institution_name,
            "state": inst.get("state", "Unknown"),
            "kpi_scores": kpi.to_dict(),
            "institution_metrics": {
                "placement_percentage": inst["placement_percentage"],
                "research_publications": inst["research_publications"],
                "infrastructure_score": inst["infrastructure_score"],
            },
            "national_benchmark": national,
            "state_benchmark": state_avg,
            "top_performer_benchmark": top,
            "performance_gaps": gaps,
        }
