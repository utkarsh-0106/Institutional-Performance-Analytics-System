"""Main Streamlit application entry point."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.ui_common import inject_global_css
from auth.login import render_login_page
from auth.session import get_current_user, init_session_state, is_authenticated, logout_user
from config.settings import APP_TITLE
from services.pipeline_service import PipelineService

# Page modules live in app/views/ (NOT app/pages/) to avoid Streamlit auto-multipage blank screens.
PAGES = {
    "Home": "app.views.home",
    "Dashboard": "app.views.dashboard",
    "Data Management": "app.views.data_management",
    "KPI Overview": "app.views.kpi_overview",
    "Rankings": "app.views.ranking",
    "ML Predictions": "app.views.ml_predictions",
    "Recommendations": "app.views.recommendations",
    "Benchmarking": "app.views.benchmarking",
    "AI Insights": "app.views.ai_insights",
    "Reports": "app.views.reports",
}


def _load_page(module_path: str):
    import importlib
    return importlib.import_module(module_path)


def render_sidebar() -> str:
    st.sidebar.markdown(
        """
        <div class="ipa-brand">
            <h2>Institutional Analytics</h2>
            <p>Higher Education Intelligence</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_authenticated():
        st.sidebar.info("Please log in to access modules.")
        return "Home"

    user = get_current_user()
    st.sidebar.caption(f"Signed in as {user.get('username', '')}")
    st.sidebar.caption(f"Role · {user.get('role', '')}")
    if user.get("linked_institution"):
        st.sidebar.caption(user["linked_institution"])

    st.sidebar.markdown("")
    page = st.sidebar.radio(
        "Navigate",
        list(PAGES.keys()),
        index=0,
        label_visibility="visible",
        key="sidebar_nav_page",
    )

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()
        st.rerun()

    return page


def ensure_pipeline():
    if st.session_state.get("pipeline_initialized"):
        return
    try:
        with st.spinner("Initializing analytics system..."):
                PipelineService().initialize_system()
        st.session_state.pipeline_initialized = True
    except Exception as exc:
        st.session_state.pipeline_initialized = True
        st.sidebar.warning(f"Pipeline init: {exc}")


def render_current_page(page: str) -> None:
    module_path = PAGES.get(page, PAGES["Home"])
    try:
        module = _load_page(module_path)
        if hasattr(module, "render") and callable(module.render):
            module.render()
        else:
            st.error(f"Page module `{module_path}` has no render() function.")
    except Exception as exc:
        st.error(f"Error loading page **{page}**: {exc}")
        st.exception(exc)


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_css()
    init_session_state()

    if not is_authenticated():
        render_login_page()
        return

    ensure_pipeline()
    page = render_sidebar()
    render_current_page(page)


# Streamlit executes the script on every rerun — always invoke main().
main()
