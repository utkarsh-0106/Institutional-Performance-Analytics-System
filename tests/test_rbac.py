"""RBAC and institution-isolation tests."""
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auth.rbac import Role, allowed_pages, normalize_role, page_allowed
from database.models import Base, Institution
from database.repositories import AuditRepository, UserRepository
from services.access_control import scope_data_for_user
from utils.helpers import hash_password


def _db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _bundle():
    inst = pd.DataFrame([
        {"id": 1, "institution_name": "Alpha Institute", "state": "Delhi"},
        {"id": 2, "institution_name": "Beta College", "state": "UP"},
    ])
    kpi = pd.DataFrame([
        {"institution_id": 1, "institution_name": "Alpha Institute", "institution_rank": 2},
        {"institution_id": 2, "institution_name": "Beta College", "institution_rank": 1},
    ])
    pred = pd.DataFrame([
        {"institution_id": 1, "institution_name": "Alpha Institute"},
        {"institution_id": 2, "institution_name": "Beta College"},
    ])
    rec = pd.DataFrame([
        {"institution_id": 1, "institution_name": "Alpha Institute"},
        {"institution_id": 2, "institution_name": "Beta College"},
    ])
    return {"institutions": inst, "kpis": kpi, "predictions": pred, "recommendations": rec}


def test_exactly_three_canonical_roles_and_alias_migration():
    assert {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value} == {"ADMIN", "ANALYST", "INSTITUTION"}
    assert normalize_role("admin") == Role.ADMIN.value
    assert normalize_role("institution_user") == Role.INSTITUTION.value
    assert normalize_role("analyst") == Role.ANALYST.value


def test_role_page_permissions():
    assert page_allowed("ADMIN", "Admin")
    assert page_allowed("ANALYST", "Dashboard")
    assert page_allowed("ANALYST", "Rankings")
    assert not page_allowed("ANALYST", "Admin")
    assert page_allowed("INSTITUTION", "Institution Profile")
    assert not page_allowed("INSTITUTION", "Data Management")
    assert not page_allowed("INSTITUTION", "Admin")
    assert "Data Management" not in allowed_pages("ANALYST", ["Dashboard", "Data Management", "Rankings"])


def test_institution_user_gets_only_assigned_institution_data():
    scoped = scope_data_for_user(_bundle(), {"role": "INSTITUTION", "institution_id": 1, "linked_institution": "Alpha Institute"})
    assert scoped["institutions"]["institution_name"].tolist() == ["Alpha Institute"]
    assert scoped["kpis"]["institution_name"].tolist() == ["Alpha Institute"]
    assert scoped["predictions"]["institution_name"].tolist() == ["Alpha Institute"]
    assert scoped["recommendations"]["institution_name"].tolist() == ["Alpha Institute"]


def test_institution_scope_rejects_missing_association():
    try:
        scope_data_for_user(_bundle(), {"role": "INSTITUTION", "institution_id": None, "linked_institution": None})
    except PermissionError:
        return
    assert False, "Institution users without an association must be rejected"


def test_admin_and_analyst_keep_system_scope():
    bundle = _bundle()
    assert len(scope_data_for_user(bundle, {"role": "ADMIN"})["institutions"]) == 2
    assert len(scope_data_for_user(bundle, {"role": "ANALYST"})["institutions"]) == 2


def test_user_creation_role_change_and_audit_logging():
    session = _db()
    session.add_all([
        Institution(id=1, institution_name="Alpha Institute"),
        Institution(id=2, institution_name="Beta College"),
    ])
    session.flush()
    user = UserRepository.create_user(session, "analyst1", hash_password("secret1"), Role.ANALYST.value)
    assert user.role == Role.ANALYST.value
    UserRepository.update_user(session, user, role=Role.INSTITUTION.value, institution_id=2, linked_institution="Beta College")
    assert user.role == Role.INSTITUTION.value
    assert user.institution_id == 2
    AuditRepository.add(session, 99, "admin", "role_or_assignment_change", "user", str(user.id), "role=INSTITUTION; institution=Beta College")
    logs = AuditRepository.get_recent(session)
    assert len(logs) == 1
    assert logs[0].action == "role_or_assignment_change"
    session.close()
