"""Base utilities for data ingestion."""
import re
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def apply_column_map(df: pd.DataFrame, column_map: Dict[str, str]) -> pd.DataFrame:
    df = normalize_column_names(df)
    rename = {k: v for k, v in column_map.items() if k in df.columns}
    return df.rename(columns=rename)


def normalize_institution_name(name: str) -> str:
    """Canonical key for merging across NIRF, AISHE, NAAC, UGC."""
    if pd.isna(name):
        return ""
    s = str(name).lower().strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^\w\s]", " ", s)
    replacements = [
        (r"\buniv\b", "university"),
        (r"\binst\b", "institute"),
        (r"\bcoll\b", "college"),
        (r"\btech\b", "technology"),
        (r"\s+", " "),
    ]
    for pat, rep in replacements:
        s = re.sub(pat, rep, s)
    return s.strip()


def load_csv_or_excel(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        return pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", on_bad_lines="skip")
    except Exception:
        return None


def add_normalized_key(df: pd.DataFrame, name_col: str = "institution_name") -> pd.DataFrame:
    df = df.copy()
    if name_col in df.columns:
        df["_merge_key"] = df[name_col].apply(normalize_institution_name)
    return df
