"""Home page — landing content after login."""
import streamlit as st

from app.ui_common import load_data, page_header, render_kpi_cards, render_sample_bar_chart, show_data_banner
from auth.session import get_current_user
from config.settings import APP_SUBTITLE

def render():
    user = get_current_user()

    data = load_data()
    inst_df = data["institutions"]
    kpi_df = data["kpis"]

    total_inst = len(inst_df)
    total_students = int(inst_df["student_enrollment"].sum())
    total_faculty = int(inst_df["faculty_count"].sum())
    avg_placement = round(inst_df["placement_percentage"].mean(), 2)

    st.markdown("""
    # 🎓 Institutional Performance Analytics Platform

    ### AI-Powered Higher Education Benchmarking & Ranking System

    Analyze • Benchmark • Predict • Improve
    """)

    st.success(
        f"👋 Welcome {user.get('username','User')} | Role: {user.get('role','Admin').upper()}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("🏫 Institutions", total_inst)

    with c2:
        st.metric("🎓 Students", f"{total_students:,}")

    with c3:
        st.metric("👨‍🏫 Faculty", f"{total_faculty:,}")

    with c4:
        st.metric("📈 Avg Placement", f"{avg_placement}%")

    st.markdown("---")

    show_data_banner(data)

    st.markdown("## 📊 System Performance Overview")
    render_kpi_cards(inst_df, kpi_df)

    st.markdown("---")

    st.markdown("## 🚀 Platform Modules")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        📊 **Dashboard**

        Interactive analytics, KPI trends and visual insights.
        """)

        st.info("""
        🏆 **Rankings**

        Institution ranking based on weighted KPI scores.
        """)

        st.info("""
        🤖 **ML Predictions**

        Forecast future institutional performance.
        """)

    with col2:
        st.info("""
        📂 **Data Management**

        Upload and process institutional datasets.
        """)

        st.info("""
        📈 **KPI Overview**

        Academic, Research and Placement KPIs.
        """)

        st.info("""
        🎯 **Recommendations**

        AI-generated improvement suggestions.
        """)

    with col3:
        st.info("""
        📋 **Benchmarking**

        Compare institutions nationally and state-wise.
        """)

        st.info("""
        💡 **AI Insights**

        Automated performance analysis.
        """)

        st.info("""
        📄 **Reports**

        Export analytical reports.
        """)

    st.markdown("---")

    st.markdown("## 📉 Quick KPI Preview")
    render_sample_bar_chart(
        kpi_df,
        "Institution Performance Snapshot"
    )

    st.markdown("---")

    st.caption(
        "SIH 2025 | AICTE, UGC, NAAC & NIRF Institutional Analytics Platform"
    )