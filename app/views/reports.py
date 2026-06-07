"""Report Generation - Module 9."""
import streamlit as st

from app.ui_common import load_data, page_header, show_data_banner, widget_key
from auth.session import get_current_user
from services.insights_service import InsightsService
from services.report_service import ReportService


def render():
    page_header("PDF Reports", "Export institutional performance reports")

    data = load_data()
    show_data_banner(data)
    inst_df = data["institutions"]
    kpi_df = data["kpis"]
    ml_df = data["predictions"]
    rec_df = data["recommendations"]

    user = get_current_user()
    institutions = sorted(inst_df["institution_name"].tolist())
    default_inst = user.get("linked_institution") or institutions[0]
    default_idx = institutions.index(default_inst) if default_inst in institutions else 0
    selected = st.selectbox(
        "Select Institution for Report",
        institutions,
        index=default_idx,
        key=widget_key("reports", "institution"),
    )

    st.write(
        "Report includes: institution profile, KPI scores, rankings, "
        "ML predictions, recommendations, and AI insights."
    )

    if st.button("Generate PDF Report", type="primary", key=widget_key("reports", "generate_btn")):
        inst_row = inst_df[inst_df["institution_name"] == selected].iloc[0].to_dict()
        kpi_row = kpi_df[kpi_df["institution_name"] == selected]
        if kpi_row.empty:
            st.error("KPI data not found for institution.")
            return
        kpi_data = kpi_row.iloc[0].to_dict()
        ml_data = None
        if not ml_df.empty:
            ml_match = ml_df[ml_df["institution_name"] == selected]
            if not ml_match.empty:
                ml_data = ml_match.iloc[0].to_dict()
        recommendations = []
        if not rec_df.empty:
            recommendations = rec_df[rec_df["institution_name"] == selected].to_dict("records")
        insights = InsightsService.generate_institution_insights(
            selected, inst_df, kpi_df, ml_df if not ml_df.empty else None
        )
        if not insights:
            insights = ["Report generated from available institutional analytics data."]

        try:
            with st.spinner("Generating PDF..."):
                path = ReportService.generate_institution_report(
                    institution_name=selected,
                    inst_data=inst_row,
                    kpi_data=kpi_data,
                    ranking_data=kpi_data,
                    ml_data=ml_data,
                    recommendations=recommendations,
                    insights=insights,
                )
            st.success(f"Report generated: {path.name}")
            with open(path, "rb") as f:
                st.download_button(
                    "Download PDF Report",
                    data=f,
                    file_name=path.name,
                    mime="application/pdf",
                    key=widget_key("reports", f"download_{selected[:30]}"),
                )
        except Exception as exc:
            st.error(f"PDF generation failed: {exc}")
            st.exception(exc)
