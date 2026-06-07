"""PDF report generation using ReportLab."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config.settings import REPORTS_DIR


class ReportService:
    @staticmethod
    def generate_institution_report(
        institution_name: str,
        inst_data: dict,
        kpi_data: dict,
        ranking_data: dict,
        ml_data: Optional[dict],
        recommendations: List[dict],
        insights: List[str],
        output_path: Path = None,
    ) -> Path:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if output_path is None:
            safe_name = institution_name.replace(" ", "_")[:50]
            output_path = REPORTS_DIR / f"report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
        heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=8)
        body_style = styles["Normal"]

        story = []
        def para(text: str, style=body_style):
            return Paragraph(escape(str(text)), style)

        story.append(para("Institutional Performance Analytics Report", title_style))
        story.append(para(f"Institution: {institution_name}", heading_style))
        story.append(para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        story.append(para("SIH 2025 | Problem ID: SIH25253 | UGC & AICTE Analytics"))
        story.append(Spacer(1, 0.3 * inch))

        story.append(para("Institution Profile", heading_style))
        profile_data = [
            ["Field", "Value"],
            ["Student Enrollment", str(inst_data.get("student_enrollment", "N/A"))],
            ["Faculty Count", str(inst_data.get("faculty_count", "N/A"))],
            ["Placement %", f"{inst_data.get('placement_percentage', 0):.1f}"],
            ["Research Publications", str(inst_data.get("research_publications", "N/A"))],
            ["Infrastructure Score", f"{inst_data.get('infrastructure_score', 0):.1f}"],
            ["Accreditation Grade", str(inst_data.get("accreditation_grade", "N/A"))],
            ["NIRF Rank", str(inst_data.get("nirf_rank", "N/A"))],
            ["State", str(inst_data.get("state", "Unknown"))],
        ]
        story.append(ReportService._make_table(profile_data))
        story.append(Spacer(1, 0.2 * inch))

        story.append(para("KPI Scores", heading_style))
        kpi_table = [
            ["KPI", "Score"],
            ["Academic Score", f"{kpi_data.get('academic_score', 0):.2f}"],
            ["Research Score", f"{kpi_data.get('research_score', 0):.2f}"],
            ["Placement Score", f"{kpi_data.get('placement_score', 0):.2f}"],
            ["Infrastructure Score", f"{kpi_data.get('infrastructure_score_kpi', 0):.2f}"],
            ["Faculty Score", f"{kpi_data.get('faculty_score', 0):.2f}"],
            ["Accreditation Score", f"{kpi_data.get('accreditation_score', 0):.2f}"],
            ["Overall Performance Index", f"{kpi_data.get('overall_performance_index', 0):.2f}"],
        ]
        story.append(ReportService._make_table(kpi_table))
        story.append(Spacer(1, 0.2 * inch))

        story.append(para("Rankings", heading_style))
        rank_table = [
            ["Metric", "Value"],
            ["Composite Rank Score", f"{ranking_data.get('composite_rank_score', 0):.2f}"],
            ["Institution Rank", str(ranking_data.get("institution_rank", "N/A"))],
            ["Ranking Category", str(ranking_data.get("ranking_category", "N/A"))],
        ]
        story.append(ReportService._make_table(rank_table))
        story.append(Spacer(1, 0.2 * inch))

        if ml_data:
            story.append(para("ML Predictions", heading_style))
            ml_table = [
                ["Prediction", "Value"],
                ["Predicted Performance Score", f"{ml_data.get('predicted_performance_score', 0):.2f}"],
                ["Accreditation Readiness", str(ml_data.get("accreditation_readiness", "N/A"))],
                ["Ranking Category (Predicted)", str(ml_data.get("ranking_category_pred", "N/A"))],
            ]
            story.append(ReportService._make_table(ml_table))
            story.append(Spacer(1, 0.2 * inch))

        story.append(para("Recommendations", heading_style))
        if recommendations:
            for rec in recommendations[:10]:
                msg = f"[{rec.get('category', 'General')}] {rec.get('message', '')}"
                story.append(para(f"• {msg}"))
        else:
            story.append(para("No specific recommendations at this time."))
        story.append(Spacer(1, 0.2 * inch))

        story.append(para("AI Insights", heading_style))
        for insight in insights or ["No insights generated."]:
            story.append(para(f"• {insight}"))

        doc.build(story)
        return output_path

    @staticmethod
    def _make_table(data: list) -> Table:
        table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
        ]))
        return table
