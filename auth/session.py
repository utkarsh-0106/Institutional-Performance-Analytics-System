"""Streamlit session state management — stores plain user dicts only."""
import streamlit as st

USER_SESSION_KEY = "user"


def init_session_state():
    defaults = {
        "authenticated": False,
        USER_SESSION_KEY: None,
        "pipeline_initialized": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_user(user: dict) -> None:
    """Store authenticated user as a plain dictionary."""
    st.session_state.authenticated = True
    st.session_state[USER_SESSION_KEY] = {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "linked_institution": user.get("linked_institution"),
    }


def logout_user():
    st.session_state.authenticated = False
    st.session_state[USER_SESSION_KEY] = None


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated")) and st.session_state.get(USER_SESSION_KEY) is not None


def is_admin() -> bool:
    user = get_current_user()
    return user.get("role") == "admin"


def get_current_user() -> dict:
    """Return the logged-in user dict from session state (never an ORM object)."""
    user = st.session_state.get(USER_SESSION_KEY)
    if user is None:
        return {
            "id": None,
            "username": None,
            "role": None,
            "linked_institution": None,
        }
    return dict(user)
