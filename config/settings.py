"""Application configuration with SQLite default and MySQL support."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models" / "saved"
REPORTS_DIR = BASE_DIR / "reports" / "generated"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database: SQLite by default; set DB_TYPE=mysql for production
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
SQLITE_PATH = DATA_DIR / "institutional_analytics.db"

if DB_TYPE == "mysql":
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "institutional_analytics")
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
else:
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

SYNTHETIC_DATASET_PATH = DATA_DIR / "synthetic_institutions.csv"
MERGED_DATASET_PATH = DATA_DIR / "processed" / "merged_institutions.csv"
USE_SYNTHETIC_FALLBACK = os.getenv("USE_SYNTHETIC_FALLBACK", "true").lower() == "true"

REQUIRED_COLUMNS = [
    "institution_name",
    "student_enrollment",
    "faculty_count",
    "placement_percentage",
    "research_publications",
    "infrastructure_score",
    "accreditation_grade",
    "nirf_rank",
]

COLUMN_ALIASES = {
    "Institution Name": "institution_name",
    "Student Enrollment": "student_enrollment",
    "Faculty Count": "faculty_count",
    "Placement Percentage": "placement_percentage",
    "Research Publications": "research_publications",
    "Infrastructure Score": "infrastructure_score",
    "Accreditation Grade": "accreditation_grade",
    "NIRF Rank": "nirf_rank",
}

RANKING_WEIGHTS = {
    "academic": 0.25,
    "placement": 0.25,
    "research": 0.20,
    "infrastructure": 0.15,
    "faculty": 0.10,
    "accreditation": 0.05,
}

ACCREDITATION_GRADE_MAP = {"A++": 100, "A+": 90, "A": 80, "B++": 70, "B+": 60, "B": 50, "C": 40, "NA": 30}

DEFAULT_USERS = {
    "admin": {"password": "admin123", "role": "admin", "institution": None},
    "institution_user": {"password": "user123", "role": "institution_user", "institution": "Indian Institute of Technology Bombay"},
}

APP_TITLE = "Institutional Performance Analytics System"
APP_SUBTITLE = "SIH 2025 | Problem ID: SIH25253 | UGC & AICTE Institutional Analytics"
