"""Paths and column mappings for Indian higher-education data sources."""
from pathlib import Path

from config.settings import DATA_DIR

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SEED_DIR = DATA_DIR / "seed"

NIRF_DIR = RAW_DIR / "nirf"
AISHE_DIR = RAW_DIR / "aishe"
NAAC_DIR = RAW_DIR / "naac"
UGC_DIR = RAW_DIR / "ugc"

for d in (RAW_DIR, PROCESSED_DIR, SEED_DIR, NIRF_DIR, AISHE_DIR, NAAC_DIR, UGC_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Standard filenames (place downloads here or run scripts/download_datasets.py)
NIRF_FILE = NIRF_DIR / "nirf_rankings.csv"
AISHE_FILE = AISHE_DIR / "aishe_statistics.csv"
NAAC_FILE = NAAC_DIR / "naac_accreditation.csv"
UGC_FILE = UGC_DIR / "ugc_institutions.csv"

MERGED_DATASET_PATH = PROCESSED_DIR / "merged_institutions.csv"
REGISTRY_PATH = SEED_DIR / "institution_registry.csv"

# Public dataset URLs (data.gov.in / official portals — may change; download script handles failures)
DATASET_URLS = {
    "aishe": "https://www.data.gov.in/sites/default/files/all_india_survey_on_higher_education_2020-21.csv",
    "ugc_universities": "https://www.ugc.gov.in/universitylistpdf.aspx",
}

NIRF_COLUMN_MAP = {
    "institute": "institution_name",
    "institute name": "institution_name",
    "institution": "institution_name",
    "name": "institution_name",
    "rank": "nirf_rank",
    "nirf rank": "nirf_rank",
    "overall rank": "nirf_rank",
    "score": "nirf_score",
    "overall score": "nirf_score",
    "state": "state",
    "city": "city",
    "category": "nirf_category",
    "teaching learning resources": "tlr_score",
    "research professional practice": "rp_score",
    "graduation outcomes": "go_score",
    "outreach inclusivity": "oi_score",
    "peer perception": "peer_score",
}

AISHE_COLUMN_MAP = {
    "institution name": "institution_name",
    "name of institution": "institution_name",
    "college name": "institution_name",
    "university name": "institution_name",
    "state": "state",
    "state name": "state",
    "total student enrolment": "student_enrollment",
    "student enrolment": "student_enrollment",
    "enrolment": "student_enrollment",
    "total enrolment": "student_enrollment",
    "number of teachers": "faculty_count",
    "teachers": "faculty_count",
    "faculty": "faculty_count",
    "year": "aishe_year",
}

NAAC_COLUMN_MAP = {
    "institution": "institution_name",
    "institution name": "institution_name",
    "name of the institution": "institution_name",
    "cgpa": "naac_cgpa",
    "grade": "accreditation_grade",
    "accreditation grade": "accreditation_grade",
    "cycle": "naac_cycle",
    "state": "state",
}

UGC_COLUMN_MAP = {
    "university name": "institution_name",
    "institution name": "institution_name",
    "name": "institution_name",
    "college": "institution_name",
    "state": "state",
    "state/ut": "state",
    "type": "institution_type",
    "university type": "institution_type",
    "year of establishment": "year_established",
}

# NAAC CGPA → letter grade (NAAC grading system)
NAAC_CGPA_TO_GRADE = [
    (3.51, 4.0, "A++"),
    (3.26, 3.50, "A+"),
    (3.01, 3.25, "A"),
    (2.76, 3.00, "B++"),
    (2.51, 2.75, "B+"),
    (2.01, 2.50, "B"),
    (1.51, 2.00, "C"),
    (0.0, 1.50, "D"),
]
