"""Authentication UI and credential verification."""
import streamlit as st

from auth.auth_service import authenticate_user
from auth.session import login_user
from config.settings import APP_SUBTITLE, APP_TITLE


def render_login_page():
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.write("Sign in to access the Institutional Performance Analytics platform.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login")
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
