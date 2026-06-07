"""Smoke tests for core pipeline."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.data_cleaning import DataCleaningService
from services.data_validation import DataValidationService
from services.kpi_engine import KPIEngine
from services.pipeline_service import PipelineService
from services.ranking_engine import RankingEngine


def test_pipeline_runs():
    result = PipelineService().reprocess_existing()
    assert result.get("success"), result.get("errors")
    assert result["institutions"] >= 500


def test_kpi_and_ranking():
    data = PipelineService().get_all_data()
    inst_df = data["institutions"]
    kpi_df = KPIEngine.calculate_kpis(inst_df)
    ranked = RankingEngine.apply_rankings(kpi_df)
    assert "overall_performance_index" in ranked.columns
    assert ranked["institution_rank"].min() == 1


def test_validation_cleaning():
    data = PipelineService().get_all_data()
    df = data["institutions"]
    valid, _ = DataValidationService.validate(df)
    assert valid
    cleaned = DataCleaningService.clean(df)
    assert len(cleaned) > 0
