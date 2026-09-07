"""Authentication UI and credential verification."""
import streamlit as st

from app.ui_common import image_data_uri, inject_global_css
from auth.auth_service import authenticate_user
from auth.session import login_user
from config.settings import APP_SUBTITLE, APP_TITLE


def render_login_page():
    inject_global_css()
    hero = image_data_uri("campus-hero.jpg")
    bg = f"url('{hero}')" if hero else "linear-gradient(135deg, #0b1f3a, #1e4e8c)"

    left, right = st.columns([1.15, 0.95], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="ipa-hero" style="background-image: linear-gradient(180deg, rgba(7,20,40,0.35) 0%, rgba(7,20,40,0.82) 100%), {bg}; background-size: cover; background-position: center; min-height: 520px; display: flex; align-items: flex-end;">
                <div class="ipa-hero-overlay" style="position: relative; background: none; width: 100%;">
                    <div class="ipa-kicker">Modern Institutional Intelligence</div>
                    <h1>{APP_TITLE}</h1>
                    <p>Evaluate, benchmark, rank, and forecast higher-education performance from a single analytics workspace.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(APP_SUBTITLE)

    with right:
        st.markdown('<div class="ipa-panel">', unsafe_allow_html=True)
        st.subheader("Sign in")
        st.caption("Access institutional KPIs, rankings, benchmarking, and predictive insights.")
        username = st.text_input("Username", placeholder="admin or institution_user", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
        login_btn = st.button("Login", type="primary", use_container_width=True, key="login_submit")

        if login_btn:
            try:
                user = authenticate_user(username, password)
                if user:
                    login_user(user)
                    st.success(f"Welcome, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception as exc:
                st.error(f"Login failed: {exc}")
                st.exception(exc)

        with st.expander("Demo Credentials"):
            st.markdown("""
            **Admin:** username `admin` / password `admin123`  
            **Institution User:** username `institution_user` / password `user123`
            """)
        st.markdown("</div>", unsafe_allow_html=True)
