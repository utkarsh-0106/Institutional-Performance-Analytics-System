"""Dynamic recommendation engine based on KPI gaps."""
import pandas as pd

THRESHOLDS = {
    "placement_score": 60,
    "research_score": 55,
    "faculty_score": 50,
    "infrastructure_score_kpi": 55,
    "accreditation_score": 65,
    "academic_score": 55,
}


class RecommendationEngine:
    RULES = [
        {
            "kpi": "placement_score",
            "category": "Placement",
            "message": "Recommend stronger industry partnerships and campus placement drives to improve graduate employability.",
            "priority": "high",
        },
        {
            "kpi": "research_score",
            "category": "Research",
            "message": "Recommend increasing publications, research grants, and collaboration with R&D institutions.",
            "priority": "high",
        },
        {
            "kpi": "faculty_score",
            "category": "Faculty",
            "message": "Recommend faculty development programs, PhD hiring, and faculty-student ratio improvement.",
            "priority": "medium",
        },
        {
            "kpi": "infrastructure_score_kpi",
            "category": "Infrastructure",
            "message": "Recommend upgrading labs, library resources, digital infrastructure, and campus facilities.",
            "priority": "medium",
        },
        {
            "kpi": "accreditation_score",
            "category": "Accreditation",
            "message": "Recommend NAAC/NBA compliance workshops and documentation for accreditation upgrade.",
            "priority": "high",
        },
        {
            "kpi": "academic_score",
            "category": "Academic",
            "message": "Recommend curriculum enhancement, student support services, and academic quality audits.",
            "priority": "medium",
        },
    ]

    @staticmethod
    def generate_for_institution(institution_id: int, institution_name: str, kpi_row: pd.Series) -> list:
        recommendations = []
        for rule in RecommendationEngine.RULES:
            kpi_key = rule["kpi"]
            value = float(kpi_row.get(kpi_key, 0))
            threshold = THRESHOLDS.get(kpi_key, 50)
            if value < threshold:
                gap = round(threshold - value, 1)
                recommendations.append({
                    "institution_id": institution_id,
                    "institution_name": institution_name,
                    "category": rule["category"],
                    "message": f"{rule['message']} (Current score: {value:.1f}, gap: {gap} points)",
                    "priority": rule["priority"],
                })

        overall = float(kpi_row.get("overall_performance_index", 0))
        if overall >= 80:
            recommendations.append({
                "institution_id": institution_id,
                "institution_name": institution_name,
                "category": "Excellence",
                "message": "Institution demonstrates strong overall performance. Maintain benchmarks and mentor peer institutions.",
                "priority": "low",
            })
        elif not recommendations:
            recommendations.append({
                "institution_id": institution_id,
                "institution_name": institution_name,
                "category": "General",
                "message": "Performance is balanced. Focus on continuous improvement across all KPI dimensions.",
                "priority": "low",
            })
        return recommendations

    @staticmethod
    def generate_all(kpi_df: pd.DataFrame, inst_df: pd.DataFrame) -> list:
        if kpi_df.empty:
            return []

        id_map = {}
        if not inst_df.empty and "id" in inst_df.columns:
            id_map = dict(zip(inst_df["institution_name"], inst_df["id"]))

        all_recs = []
        for _, row in kpi_df.iterrows():
            inst_id = int(id_map.get(row["institution_name"], row.get("institution_id", 0)))
            all_recs.extend(
                RecommendationEngine.generate_for_institution(
                    inst_id, row["institution_name"], row
                )
            )
        return all_recs
