"""Recommendation Engine - Module 7."""
import streamlit as st

from app.ui_common import load_data, page_header, section_panel, show_data_banner, widget_key
from auth.session import get_current_user


def render():
    page_header(
        "AI Recommendations",
        "Improvement guidance generated from institutional KPI performance gaps",
    )

    data = load_data()
    show_data_banner(data)
    rec_df = data["recommendations"]
    kpi_df = data["kpis"]
    user = get_current_user()

    if rec_df.empty:
        st.warning("No recommendations available. Reprocess data from Data Management.")

    institutions = (
        sorted(rec_df["institution_name"].unique().tolist())
        if not rec_df.empty
        else []
    )
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

    if not kpi_df.empty:
        inst_kpi = kpi_df[kpi_df["institution_name"] == selected]
        if not inst_kpi.empty:
            row = inst_kpi.iloc[0]
            section_panel("Current KPI Health")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Academic", f"{row.get('academic_score', 0):.1f}")
                st.metric("Research", f"{row.get('research_score', 0):.1f}")
            with c2:
                st.metric("Placement", f"{row.get('placement_score', 0):.1f}")
                st.metric("Infrastructure", f"{row.get('infrastructure_score_kpi', 0):.1f}")
            with c3:
                st.metric("Faculty", f"{row.get('faculty_score', 0):.1f}")
                st.metric("Accreditation", f"{row.get('accreditation_score', 0):.1f}")

    section_panel(f"Recommendations for {selected}")
    inst_recs = rec_df[rec_df["institution_name"] == selected] if not rec_df.empty else rec_df
    if not inst_recs.empty:
        for _, rec in inst_recs.iterrows():
            priority = str(rec.get("priority", "")).lower()
            label = f"**{rec['category']}** · {priority.title()} priority  \n{rec['message']}"
            if priority == "high":
                st.error(label)
            elif priority == "medium":
                st.warning(label)
            else:
                st.success(label)
    else:
        st.success("No major performance gaps detected. Institution performance is balanced.")

    section_panel("Recommendation Summary")
    if not rec_df.empty:
        summary = rec_df.groupby(["institution_name", "category"]).size().reset_index(name="count")
        st.dataframe(summary.head(100), use_container_width=True, hide_index=True)

    st.caption("Institutional Performance Analytics | AI Recommendation Engine")
