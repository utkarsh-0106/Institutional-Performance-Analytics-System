"""Administrative workspace for the IPAS RBAC system."""
import streamlit as st

from app.ui_common import load_data, page_header, section_panel, show_data_banner, widget_key
from auth.rbac import Role, normalize_role
from auth.session import get_current_user
from database.repositories import AuditRepository, InstitutionRepository, UserRepository
from database.session import get_db_session, init_db
from utils.helpers import hash_password


def _require_admin() -> bool:
    if get_current_user().get("role") != Role.ADMIN.value:
        st.error("Access denied: Admin privileges are required.")
        return False
    return True


def _users_table(users):
    return [
        {
            "ID": u.id,
            "Username": u.username,
            "Role": normalize_role(u.role),
            "Institution": u.linked_institution or "—",
            "Created": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "—",
        }
        for u in users
    ]


def _user_management(institutions):
    section_panel("User Management", "Create users, assign one of the three roles, and associate institution accounts safely.")
    with get_db_session() as session:
        users = UserRepository.get_all(session)
        st.dataframe(_users_table(users), use_container_width=True, hide_index=True)

    with st.expander("Create user", expanded=False):
        username = st.text_input("Username", key=widget_key("admin", "new_username"))
        password = st.text_input("Password", type="password", key=widget_key("admin", "new_password"))
        role = st.selectbox("Role", [Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value], key=widget_key("admin", "new_role"))
        institution_names = [i.institution_name for i in institutions]
        selected_institution = None
        if role == Role.INSTITUTION.value:
            selected_institution = st.selectbox("Assigned institution", institution_names, key=widget_key("admin", "new_institution")) if institution_names else None
            if not institution_names:
                st.warning("No institutions are available for association.")
        if st.button("Create user", type="primary", key=widget_key("admin", "create_user")):
            if not username.strip() or len(password) < 6:
                st.error("Username is required and password must be at least 6 characters.")
                return
            with get_db_session() as session:
                if UserRepository.get_by_username(session, username.strip()):
                    st.error("Username already exists.")
                    return
                institution_id = None
                if role == Role.INSTITUTION.value:
                    if not selected_institution:
                        st.error("Institution users must be assigned to an institution.")
                        return
                    inst = InstitutionRepository.get_by_name(session, selected_institution)
                    if inst is None:
                        st.error("Selected institution no longer exists.")
                        return
                    institution_id = inst.id
                user = UserRepository.create_user(
                    session, username.strip(), hash_password(password), role,
                    selected_institution, institution_id,
                )
                AuditRepository.add(session, get_current_user()["id"], get_current_user()["username"], "user_creation", "user", str(user.id), f"role={role}")
            st.success(f"Created {role} user `{username.strip()}`.")
            st.rerun()

    st.markdown("### Change role / institution")
    editable = [u for u in users if u.username != "admin"]
    if not editable:
        st.info("No non-admin users available for editing.")
        return
    selected_user_name = st.selectbox("User", [u.username for u in editable], key=widget_key("admin", "edit_user"))
    current = next(u for u in editable if u.username == selected_user_name)
    new_role = st.selectbox("New role", [Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value], index=[Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value].index(normalize_role(current.role)), key=widget_key("admin", "edit_role"))
    institution_names = [i.institution_name for i in institutions]
    current_inst = current.linked_institution if current.linked_institution in institution_names else (institution_names[0] if institution_names else None)
    new_inst = None
    if new_role == Role.INSTITUTION.value:
        new_inst = st.selectbox("Institution", institution_names, index=institution_names.index(current_inst) if current_inst else 0, key=widget_key("admin", "edit_institution")) if institution_names else None
    if st.button("Save access changes", type="primary", key=widget_key("admin", "save_access")):
        with get_db_session() as session:
            user = UserRepository.get_by_username(session, selected_user_name)
            institution_id = None
            if new_role == Role.INSTITUTION.value:
                inst = InstitutionRepository.get_by_name(session, new_inst) if new_inst else None
                if inst is None:
                    st.error("Institution assignment is required for institution users.")
                    return
                institution_id = inst.id
            UserRepository.update_user(session, user, role=new_role, institution_id=institution_id, linked_institution=new_inst)
            actor = get_current_user()
            AuditRepository.add(session, actor["id"], actor["username"], "role_or_assignment_change", "user", str(user.id), f"role={new_role}; institution={new_inst}")
        st.success("Access settings updated.")
        st.rerun()


def _institution_management(institutions):
    section_panel("Institution Management", "Review the institution registry and user associations. Institution records remain governed by the existing ETL/data pipeline.")
    rows = [{"ID": i.id, "Institution": i.institution_name, "State": i.state, "NIRF Rank": i.nirf_rank} for i in institutions]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _audit_logs():
    section_panel("Audit Logs", "Security and administrative events. Passwords and authentication secrets are never recorded.")
    with get_db_session() as session:
        logs = AuditRepository.get_recent(session, 200)
    rows = [
        {"Time": l.created_at.strftime("%Y-%m-%d %H:%M:%S"), "User": l.username or "system", "Action": l.action, "Target": f"{l.target_type or ''}:{l.target_id or ''}", "Details": l.details or ""}
        for l in logs
    ]
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No audit events recorded yet.")


def render():
    if not _require_admin():
        return
    init_db()
    data = load_data()
    show_data_banner(data)
    with get_db_session() as session:
        institutions = InstitutionRepository.get_all(session)
    page_header("Admin Console", "System administration, access control, data operations, and audit visibility")
    c1, c2, c3 = st.columns(3)
    with get_db_session() as session:
        user_count = len(UserRepository.get_all(session))
    c1.metric("Users", user_count)
    c2.metric("Institutions", len(institutions))
    c3.metric("RBAC Roles", 3)
    tabs = st.tabs(["Overview", "Users", "Institutions", "Audit Logs"])
    with tabs[0]:
        st.success("RBAC is active with exactly three canonical roles: ADMIN, ANALYST, INSTITUTION.")
        st.write("Data Management and ETL remain protected by the existing validation and pipeline services.")
    with tabs[1]:
        _user_management(institutions)
    with tabs[2]:
        _institution_management(institutions)
    with tabs[3]:
        _audit_logs()
