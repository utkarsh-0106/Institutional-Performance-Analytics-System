"""Server-side data scoping for authenticated IPAS users."""
from __future__ import annotations

import pandas as pd

from auth.rbac import Role, normalize_role


def scope_data_for_user(data: dict, user: dict) -> dict:
    """Return a role-scoped copy of analytics data.

    ADMIN/ANALYST receive the existing system-wide data. INSTITUTION receives
    only rows belonging to its trusted database association. No request/UI
    supplied institution name is accepted as an authority here.
    """
    role = normalize_role(user.get("role"))
    if role != Role.INSTITUTION.value:
        return data

    institution_id = user.get("institution_id")
    institution_name = user.get("linked_institution")
    if institution_id is None and not institution_name:
        raise PermissionError("Institution account has no institution association.")

    result = dict(data)
    inst = data.get("institutions", pd.DataFrame())
    if inst.empty:
        return result

    if institution_id is not None and "id" in inst.columns:
        mask = inst["id"].eq(int(institution_id))
    else:
        mask = inst["institution_name"].eq(str(institution_name))

    scoped_inst = inst.loc[mask].copy()
    if scoped_inst.empty:
        raise PermissionError("Assigned institution was not found in the current dataset.")

    result["institutions"] = scoped_inst
    names = set(scoped_inst["institution_name"].astype(str))

    for key in ("kpis", "predictions", "recommendations"):
        frame = data.get(key, pd.DataFrame())
        if frame is None or frame.empty:
            result[key] = frame
        elif "institution_id" in frame.columns and institution_id is not None:
            result[key] = frame.loc[frame["institution_id"].eq(int(institution_id))].copy()
        else:
            result[key] = frame.loc[frame["institution_name"].astype(str).isin(names)].copy()

    result["scoped_to_institution"] = True
    return result
