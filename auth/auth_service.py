"""Authentication service — returns plain dicts only, never detached ORM objects."""
from typing import Optional

from config.settings import DEFAULT_USERS
from database.session import get_db_session, init_db
from database.repositories import UserRepository
from utils.helpers import hash_password, verify_password


def _default_user_dict(username: str) -> Optional[dict]:
    if username not in DEFAULT_USERS:
        return None
    info = DEFAULT_USERS[username]
    return {
        "id": 0,
        "username": username,
        "role": info["role"],
        "password_hash": hash_password(info["password"]),
        "linked_institution": info.get("institution"),
    }


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Verify credentials and return a plain user dict, or None if invalid.
    Never returns SQLAlchemy ORM User instances.
    """
    if not username or not password:
        return None

    username = username.strip()
    init_db()

    with get_db_session() as session:
        UserRepository.seed_default_users(session, DEFAULT_USERS, hash_password)
        user_dict = UserRepository.get_user_dict_by_username(session, username)

    if user_dict is not None:
        if verify_password(password, user_dict["password_hash"]):
            return {
                "id": user_dict["id"],
                "username": user_dict["username"],
                "role": user_dict["role"],
                "linked_institution": user_dict.get("linked_institution"),
            }
        return None

    fallback = _default_user_dict(username)
    if fallback and verify_password(password, fallback["password_hash"]):
        return {
            "id": fallback["id"],
            "username": fallback["username"],
            "role": fallback["role"],
            "linked_institution": fallback.get("linked_institution"),
        }

    return None
