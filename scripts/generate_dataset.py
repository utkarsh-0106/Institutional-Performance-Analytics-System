"""Generate synthetic institutional dataset (500+ institutions)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import SYNTHETIC_DATASET_PATH

STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Uttar Pradesh",
    "Gujarat", "Rajasthan", "West Bengal", "Telangana", "Kerala",
    "Punjab", "Haryana", "Madhya Pradesh", "Bihar", "Andhra Pradesh",
]

INSTITUTION_PREFIXES = [
    "National", "Indian", "Global", "Premier", "Central", "State",
    "Regional", "Metropolitan", "Urban", "Rural",
]

INSTITUTION_TYPES = [
    "Institute of Technology", "University", "College of Engineering",
    "Institute of Management", "Polytechnic", "Medical College",
    "Arts and Science College", "Business School",
]

ACCREDITATION_GRADES = ["A++", "A+", "A", "B++", "B+", "B", "C", "NA"]


def generate_institution_names(n: int, rng: np.random.Generator) -> list:
    names = set()
    while len(names) < n:
        prefix = rng.choice(INSTITUTION_PREFIXES)
        itype = rng.choice(INSTITUTION_TYPES)
        state = rng.choice(STATES).split()[0]
        suffix = rng.integers(1, 999)
        name = f"{prefix} {state} {itype} {suffix}"
        names.add(name)
    return list(names)


def generate_dataset(n_institutions: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = generate_institution_names(n_institutions, rng)

    student_enrollment = rng.integers(500, 25000, n_institutions)
    faculty_count = (student_enrollment / rng.uniform(12, 25, n_institutions)).astype(int)
    faculty_count = np.clip(faculty_count, 20, 1500)

    base_quality = rng.beta(2, 5, n_institutions)
    placement_percentage = np.clip(base_quality * 100 + rng.normal(0, 8, n_institutions), 30, 99).round(1)
    research_publications = np.clip(
        (base_quality * 800 + rng.poisson(50, n_institutions)).astype(int), 5, 1200
    )
    infrastructure_score = np.clip(base_quality * 100 + rng.normal(0, 10, n_institutions), 20, 99).round(1)

    grade_probs = [0.05, 0.10, 0.20, 0.15, 0.15, 0.15, 0.10, 0.10]
    accreditation_grade = rng.choice(ACCREDITATION_GRADES, n_institutions, p=grade_probs)

    nirf_rank = np.clip(
        (1000 - base_quality * 900 + rng.integers(-50, 50, n_institutions)).astype(int),
        1, 999,
    )

    states = rng.choice(STATES, n_institutions)

    df = pd.DataFrame({
        "institution_name": names,
        "student_enrollment": student_enrollment,
        "faculty_count": faculty_count,
        "placement_percentage": placement_percentage,
        "research_publications": research_publications,
        "infrastructure_score": infrastructure_score,
        "accreditation_grade": accreditation_grade,
        "nirf_rank": nirf_rank,
        "state": states,
    })
    return df


def main():
    df = generate_dataset(500)
    SYNTHETIC_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SYNTHETIC_DATASET_PATH, index=False)
    print(f"Generated {len(df)} institutions -> {SYNTHETIC_DATASET_PATH}")


if __name__ == "__main__":
    main()
