"""Role and permission definitions for the IPAS three-role RBAC model."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    INSTITUTION = "INSTITUTION"


ROLE_ALIASES = {
    "admin": Role.ADMIN.value,
    "administrator": Role.ADMIN.value,
    "analyst": Role.ANALYST.value,
    "institution_user": Role.INSTITUTION.value,
    "institution": Role.INSTITUTION.value,
}

PAGE_PERMISSIONS = {
    "Home": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Dashboard": {Role.ADMIN.value, Role.ANALYST.value},
    "Data Management": {Role.ADMIN.value},
    "KPI Overview": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Institution Profile": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Rankings": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "ML Predictions": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Recommendations": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Benchmarking": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "AI Insights": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Reports": {Role.ADMIN.value, Role.ANALYST.value, Role.INSTITUTION.value},
    "Admin": {Role.ADMIN.value},
}

ADMIN_PERMISSIONS = {
    "manage_users",
    "manage_roles",
    "manage_institutions",
    "manage_institution_assignments",
    "data_management",
    "etl",
    "data_quality",
    "audit_logs",
    "system_settings",
    "system_analytics",
}

ANALYST_PERMISSIONS = {
    "system_analytics",
    "institution_analytics",
    "rankings",
    "benchmarking",
    "ml_predictions",
    "recommendations",
    "ai_insights",
    "reports",
}

INSTITUTION_PERMISSIONS = {
    "institution_analytics",
    "own_rankings",
    "own_benchmarking",
    "own_ml_predictions",
    "own_recommendations",
    "own_ai_insights",
    "own_reports",
}

ROLE_PERMISSIONS = {
    Role.ADMIN.value: ADMIN_PERMISSIONS,
    Role.ANALYST.value: ANALYST_PERMISSIONS,
    Role.INSTITUTION.value: INSTITUTION_PERMISSIONS,
}


def normalize_role(role: str | None) -> str | None:
    if not role:
        return None
    value = str(role).strip().upper()
    if value in {r.value for r in Role}:
        return value
    return ROLE_ALIASES.get(str(role).strip().lower())


def role_can(role: str | None, permission: str) -> bool:
    normalized = normalize_role(role)
    return normalized in ROLE_PERMISSIONS and permission in ROLE_PERMISSIONS[normalized]


def page_allowed(role: str | None, page: str) -> bool:
    normalized = normalize_role(role)
    return normalized in PAGE_PERMISSIONS.get(page, set())


def allowed_pages(role: str | None, pages: list[str]) -> list[str]:
    return [page for page in pages if page_allowed(role, page)]
