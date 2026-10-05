"""Authenticated session state with server-side user rehydration."""
import streamlit as st

from auth.rbac import Role, normalize_role
from database.repositories import AuditRepository, UserRepository
from database.session import get_db_session, init_db

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
    st.session_state.authenticated = True
    st.session_state[USER_SESSION_KEY] = {"id": user.get("id")}
    try:
        init_db()
        with get_db_session() as session:
            AuditRepository.add(
                session, user.get("id"), user.get("username"), "login", "user", str(user.get("id"))
            )
    except Exception:
        # Authentication must not fail solely because audit logging is unavailable.
        pass


def record_audit(action: str, target_type: str | None = None, target_id: str | None = None, details: str | None = None) -> None:
    user = get_current_user()
    try:
        if user.get("id"):
            with get_db_session() as session:
                AuditRepository.add(session, user.get("id"), user.get("username"), action, target_type, target_id, details)
    except Exception:
        pass


def logout_user() -> None:
    user = get_current_user()
    try:
        if user.get("id"):
            with get_db_session() as session:
                AuditRepository.add(
                    session, user.get("id"), user.get("username"), "logout", "user", str(user.get("id"))
                )
    except Exception:
        pass
    st.session_state.authenticated = False
    st.session_state[USER_SESSION_KEY] = None


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated")) and st.session_state.get(USER_SESSION_KEY) is not None


def get_current_user() -> dict:
    """Rehydrate the authenticated user from the database on every access.

    The role and institution association are therefore not trusted from a UI
    parameter or a freely editable request value.
    """
    stored = st.session_state.get(USER_SESSION_KEY) or {}
    user_id = stored.get("id")
    if not user_id:
        return {"id": None, "username": None, "role": None, "linked_institution": None, "institution_id": None}

    try:
        init_db()
        with get_db_session() as session:
            user = UserRepository.get_by_id(session, int(user_id))
            if user is None:
                return {"id": None, "username": None, "role": None, "linked_institution": None, "institution_id": None}
            return {
                "id": user.id,
                "username": user.username,
                "role": normalize_role(user.role),
                "linked_institution": user.linked_institution,
                "institution_id": user.institution_id,
            }
    except Exception:
        return {"id": None, "username": None, "role": None, "linked_institution": None, "institution_id": None}


def is_admin() -> bool:
    return get_current_user().get("role") == Role.ADMIN.value
