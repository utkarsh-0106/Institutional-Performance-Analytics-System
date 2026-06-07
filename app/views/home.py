"""Home page — landing content after login."""
import streamlit as st

from app.ui_common import load_data, page_header, render_kpi_cards, render_sample_bar_chart, show_data_banner
from auth.session import get_current_user
from config.settings import APP_SUBTITLE


def render():
    page_header("Home", APP_SUBTITLE)
    user = get_current_user()
    st.write(f"Welcome, **{user.get('username', 'User')}** ({user.get('role', 'guest')}).")

    st.markdown("""
    Use the **sidebar** to navigate modules:
    - **Dashboard** — KPI metrics and charts
    - **Data Management** — Upload and process institutional data
    - **KPI Overview** — Detailed performance scores
    - **Rankings** — Weighted institutional rankings
    - **ML Predictions** — Performance and accreditation forecasts
    - **Recommendations** — Actionable improvement suggestions
    - **Benchmarking** — State and national comparisons
    - **AI Insights** — Automated narrative insights
    - **Reports** — PDF export
    """)

    data = load_data()
    show_data_banner(data)
    st.subheader("System Overview")
    render_kpi_cards(data["institutions"], data["kpis"])

    st.subheader("Quick KPI Preview")
    render_sample_bar_chart(data["kpis"], "Sample Institution KPI Breakdown")
