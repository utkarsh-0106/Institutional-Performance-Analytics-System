"""Recommendation Engine - Module 7."""
import streamlit as st

from app.ui_common import load_data, page_header, show_data_banner, widget_key
from auth.session import get_current_user


def render():
    page_header("Recommendations", "Dynamic suggestions based on KPI performance gaps")

    data = load_data()
    show_data_banner(data)
    rec_df = data["recommendations"]
    kpi_df = data["kpis"]

    user = get_current_user()
    if rec_df.empty:
        st.warning("No recommendations in database. Reprocess data from Data Management.")
        rec_df = data.get("recommendations", rec_df)

    institutions = sorted(rec_df["institution_name"].unique().tolist()) if not rec_df.empty else []
    if not institutions:
        institutions = sorted(kpi_df["institution_name"].unique().tolist())

    default_inst = user.get("linked_institution") or (institutions[0] if institutions else "Sample Institute of Technology")
    default_idx = institutions.index(default_inst) if default_inst in institutions else 0

    selected = st.selectbox(
        "Select Institution",
        institutions or ["Sample Institute of Technology"],
        index=default_idx,
        key=widget_key("recommendations", "institution"),
    )

    st.subheader(f"Recommendations for {selected}")
    inst_recs = rec_df[rec_df["institution_name"] == selected] if not rec_df.empty else rec_df

    if not inst_recs.empty:
        for _, rec in inst_recs.iterrows():
            icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            st.markdown(f"{icon} **{rec['category']}** — {rec['message']}")
    else:
        st.info("No specific recommendations — institution performance is balanced.")

    st.divider()
    st.subheader("All Recommendations Summary")
    if not rec_df.empty:
        summary = rec_df.groupby(["institution_name", "category"]).size().reset_index(name="count")
        st.dataframe(summary.head(100), use_container_width=True)

    if not kpi_df.empty:
        inst_kpi = kpi_df[kpi_df["institution_name"] == selected]
        if not inst_kpi.empty:
            st.subheader("Current KPI Scores")
            row = inst_kpi.iloc[0]
            cols = st.columns(6)
            kpis = [
                "academic_score", "research_score", "placement_score",
                "infrastructure_score_kpi", "faculty_score", "accreditation_score",
            ]
            for col, kpi in zip(cols, kpis):
                if kpi in row:
                    col.metric(kpi.replace("_", " ").title(), f"{row[kpi]:.1f}")
