"""AI Insights - automated human-readable institutional insights."""
import pandas as pd

from services.benchmarking_service import BenchmarkingService


class InsightsService:
    @staticmethod
    def _pct_diff(value: float, benchmark: float) -> float:
        if benchmark == 0:
            return 0.0
        return round(((value - benchmark) / benchmark) * 100, 1)

    @staticmethod
    def generate_institution_insights(
        institution_name: str,
        inst_df: pd.DataFrame,
        kpi_df: pd.DataFrame,
        ml_df: pd.DataFrame = None,
    ) -> list:
        insights = []
        comparison = BenchmarkingService.compare_institution(institution_name, inst_df, kpi_df)
        if not comparison:
            return ["Insufficient data to generate insights for this institution."]

        kpi = comparison["kpi_scores"]
        national = comparison["national_benchmark"]
        gaps = comparison["performance_gaps"]
        state = comparison.get("state", "Unknown")

        research_diff = InsightsService._pct_diff(
            kpi.get("research_score", 0), national.get("avg_research_score", 1)
        )
        if research_diff < -10:
            insights.append(f"Research output is below national benchmark by {abs(research_diff):.1f}%.")
        elif research_diff > 10:
            insights.append(f"Research output exceeds national benchmark by {research_diff:.1f}%.")

        placement_diff = InsightsService._pct_diff(
            kpi.get("placement_score", 0), national.get("avg_placement_score", 1)
        )
        if placement_diff > 5:
            insights.append(f"Placement performance is above national average by {placement_diff:.1f}%.")
        elif placement_diff < -5:
            insights.append(f"Placement performance trails national average by {abs(placement_diff):.1f}%.")

        if gaps.get("overall_vs_top", 0) < -15:
            insights.append(
                f"Overall performance gap vs top institutions is {abs(gaps['overall_vs_top']):.1f} points."
            )
        elif gaps.get("overall_vs_top", 0) > -5:
            insights.append("Institution performance is competitive with top-performing peers.")

        if kpi.get("accreditation_score", 0) >= 80:
            insights.append("Institution has high accreditation readiness based on current grade profile.")
        elif kpi.get("accreditation_score", 0) < 60:
            insights.append("Accreditation profile needs strengthening for regulatory compliance.")

        rank = kpi.get("institution_rank", 999)
        category = kpi.get("ranking_category", "")
        insights.append(f"Current national rank: #{rank} ({category}).")

        if ml_df is not None and not ml_df.empty:
            ml_row = ml_df[ml_df["institution_name"] == institution_name]
            if not ml_row.empty:
                ml = ml_row.iloc[0]
                readiness = ml.get("accreditation_readiness", "")
                pred_score = ml.get("predicted_performance_score", 0)
                insights.append(
                    f"ML predicts performance score of {pred_score:.1f} with accreditation status: {readiness}."
                )

        insights.append(f"Institution is located in {state} — compare with state-level benchmarks for context.")
        return insights

    @staticmethod
    def generate_system_insights(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> list:
        if inst_df.empty or kpi_df.empty:
            return []

        insights = []
        total = len(inst_df)
        national = BenchmarkingService.compute_national_averages(inst_df, kpi_df)

        top50 = (kpi_df["institution_rank"] <= 50).sum()
        insights.append(f"System tracks {total} institutions with {top50} in Top 50 rankings.")

        avg_place = national.get("avg_placement", 0)
        insights.append(f"National average placement rate stands at {avg_place:.1f}%.")

        avg_research = national.get("avg_research", 0)
        insights.append(f"Average research publications per institution: {avg_research:.0f}.")

        high_perf = (kpi_df["overall_performance_index"] >= 75).sum()
        insights.append(f"{high_perf} institutions ({100*high_perf/total:.1f}%) exceed 75 overall performance index.")

        grade_counts = inst_df["accreditation_grade"].value_counts()
        top_grade = grade_counts.index[0] if len(grade_counts) > 0 else "N/A"
        insights.append(f"Most common accreditation grade: {top_grade}.")

        return insights
