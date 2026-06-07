"""Shared utility helpers."""
import hashlib
from typing import Any

import numpy as np
import pandas as pd


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    if max_val <= min_val:
        return 0.0
    return max(0.0, min(100.0, ((value - min_val) / (max_val - min_val)) * 100))


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def format_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:.0f}"


def accreditation_to_score(grade: str, grade_map: dict) -> float:
    if pd.isna(grade):
        return 30.0
    key = str(grade).strip().upper()
    return float(grade_map.get(key, 30))


def nirf_to_score(rank: float) -> float:
    """Lower NIRF rank is better; convert to 0-100 score."""
    if pd.isna(rank) or rank <= 0:
        return 50.0
    return max(0.0, min(100.0, 100 - (float(rank) / 10)))
