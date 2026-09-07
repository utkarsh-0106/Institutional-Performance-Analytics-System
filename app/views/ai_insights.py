"""AI Insights Module - Module 10."""
import streamlit as st

from app.ui_common import load_data, page_header, section_panel, show_data_banner, widget_key
from auth.session import get_current_user
from services.insights_service import InsightsService


def render():
    page_header("AI Insights", "Automated human-readable performance narratives")

    data = load_data()
    show_data_banner(data)
    inst_df = data["institutions"]
    kpi_df = data["kpis"]
    ml_df = data["predictions"]

    tab1, tab2 = st.tabs(["System Insights", "Institution Insights"])

    with tab1:
        section_panel("System-wide Insights")
        if data.get("using_sample"):
            for text in [
                "System preview: 5 sample institutions loaded.",
                "National average placement rate is approximately 73%.",
                "Research output varies significantly across institution types.",
            ]:
                st.info(text)
        else:
            insights = InsightsService.generate_system_insights(inst_df, kpi_df)
            if insights:
                for insight in insights:
                    st.info(insight)
            else:
                st.info("No system insights available yet.")

    with tab2:
        user = get_current_user()
        institutions = sorted(inst_df["institution_name"].tolist())
        default_inst = user.get("linked_institution") or institutions[0]
        default_idx = institutions.index(default_inst) if default_inst in institutions else 0
        selected = st.selectbox(
            "Select Institution",
            institutions,
            index=default_idx,
            key=widget_key("ai_insights", "institution"),
        )
        st.subheader(f"Insights for {selected}")
        if data.get("using_sample"):
            for text in [
                "Placement performance is near sample average.",
                "Research output can be improved with grant programs.",
                "Institution shows moderate accreditation readiness.",
            ]:
                st.success(text)
        else:
            insights = InsightsService.generate_institution_insights(
                selected, inst_df, kpi_df, ml_df if not ml_df.empty else None
            )
            if insights:
                for insight in insights:
                    st.success(insight)
            else:
                st.success("No institution-specific insights generated.")
