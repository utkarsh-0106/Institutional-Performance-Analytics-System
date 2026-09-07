"""Focused tests for DataValidationService.quality_report."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.data_validation import DataValidationService
from services.pipeline_service import PipelineService


def _valid_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "institution_name": ["Alpha Institute", "Beta College"],
            "student_enrollment": [1000, 8000],
            "faculty_count": [80, 200],
            "placement_percentage": [55.0, 90.0],
            "research_publications": [40, 400],
            "infrastructure_score": [40.0, 85.0],
            "accreditation_grade": ["B+", "A++"],
            "nirf_rank": [200, 12],
        }
    )


def test_quality_report_valid_dataset():
    report = DataValidationService.quality_report(_valid_df())
    valid, errors = DataValidationService.validate(_valid_df())
    assert valid is True
    assert errors == []
    assert report["status"] == "PASS"
    assert report["row_count"] == 2
    assert report["duplicate_institution_count"] == 0
    assert report["missing_required_columns"] == []
    assert all(v == 0 for v in report["missing_value_counts"].values())
    assert all(v == 0 for v in report["invalid_numeric_counts"].values())
    assert all(v == 0 for v in report["out_of_range_counts"].values())


def test_quality_report_missing_values():
    df = _valid_df()
    df.loc[0, "faculty_count"] = None
    report = DataValidationService.quality_report(df)
    valid, _ = DataValidationService.validate(df)
    assert valid is True
    assert report["status"] == "WARNING"
    assert report["missing_value_counts"]["faculty_count"] == 1


def test_quality_report_duplicate_institutions():
    df = _valid_df()
    df.loc[1, "institution_name"] = "Alpha Institute"
    report = DataValidationService.quality_report(df)
    valid, _ = DataValidationService.validate(df)
    assert valid is True
    assert report["status"] == "WARNING"
    assert report["duplicate_institution_count"] == 1


def test_quality_report_invalid_and_out_of_range_values():
    df = pd.DataFrame(
        {
            "institution_name": ["Alpha Institute", "Beta College"],
            "student_enrollment": ["not-a-number", 8000],
            "faculty_count": [80, 200],
            "placement_percentage": [55.0, 150],
            "research_publications": [40, 400],
            "infrastructure_score": [40.0, 85.0],
            "accreditation_grade": ["B+", "A++"],
            "nirf_rank": [200, 12],
        }
    )
    report = DataValidationService.quality_report(df)
    valid, errors = DataValidationService.validate(df)
    assert valid is False
    assert any("placement_percentage" in e for e in errors)
    assert report["status"] == "FAIL"
    assert report["invalid_numeric_counts"]["student_enrollment"] == 1
    assert report["out_of_range_counts"]["placement_percentage"] == 1


def test_quality_report_missing_required_column():
    df = _valid_df().drop(columns=["nirf_rank"])
    report = DataValidationService.quality_report(df)
    valid, errors = DataValidationService.validate(df)
    assert valid is False
    assert any("Missing required columns" in e for e in errors)
    assert report["status"] == "FAIL"
    assert "nirf_rank" in report["missing_required_columns"]
    assert report["row_count"] == 2


def test_ingest_attaches_quality_report_on_validation_failure():
    df = _valid_df().drop(columns=["accreditation_grade"])
    result = PipelineService().ingest_and_process(df)
    assert result["success"] is False
    assert "quality_report" in result
    assert result["quality_report"]["status"] == "FAIL"
    assert "accreditation_grade" in result["quality_report"]["missing_required_columns"]
