"""Smoke tests for core pipeline."""
import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import RANKING_WEIGHTS
from services.data_cleaning import DataCleaningService
from services.data_validation import DataValidationService
from services.etl.cleaners import ETLCleaners
from services.etl.pipeline import ETLPipeline
from services.kpi_engine import KPIEngine
from services.pipeline_service import PipelineService
from services.ranking_engine import RankingEngine


def _sample_institutions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2],
            "institution_name": ["Alpha Institute", "Beta College"],
            "student_enrollment": [1000, 8000],
            "faculty_count": [80, 200],
            "placement_percentage": [55.0, 90.0],
            "research_publications": [40, 400],
            "infrastructure_score": [40.0, 85.0],
            "accreditation_grade": ["B+", "A++"],
            "nirf_rank": [200, 12],
            "state": ["Delhi", "Maharashtra"],
        }
    )


def test_pipeline_runs():
    result = PipelineService().reprocess_existing()
    assert result.get("success"), result.get("errors")
    assert result["institutions"] > 0


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


def test_kpi_ranking_shared_weights():
    assert RANKING_WEIGHTS == {
        "academic": 0.25,
        "research": 0.20,
        "placement": 0.25,
        "infrastructure": 0.05,
        "faculty": 0.15,
        "accreditation": 0.10,
    }
    assert abs(sum(RANKING_WEIGHTS.values()) - 1.0) < 1e-9

    kpi_df = KPIEngine.calculate_kpis(_sample_institutions())
    ranked = RankingEngine.apply_rankings(kpi_df)
    pd.testing.assert_series_equal(
        ranked["overall_performance_index"],
        ranked["composite_rank_score"],
        check_names=False,
    )
    assert ranked["institution_rank"].tolist() == [1, 2]
    assert ranked.iloc[0]["institution_name"] == "Beta College"


def test_etl_merge_hygiene_defers_range_clipping():
    raw = pd.DataFrame(
        {
            "institution_name": ["Gamma University"],
            "placement_percentage": [12.0],
            "student_enrollment": [100],
            "faculty_count": [5],
            "research_publications": [1],
            "infrastructure_score": [10.0],
            "nirf_rank": [3],
            "accreditation_grade": ["A"],
            "state": ["Kerala"],
        }
    )
    merged = ETLCleaners.clean_merged(raw)
    assert float(merged["placement_percentage"].iloc[0]) == 12.0

    cleaned = DataCleaningService.clean(merged)
    assert float(cleaned["placement_percentage"].iloc[0]) == 12.0
    assert "DataCleaningService" not in inspect.getsource(ETLPipeline.run_merge)


def test_ml_init_loads_and_does_not_train():
    analytics_src = inspect.getsource(PipelineService._run_analytics_pipeline)
    ingest_src = inspect.getsource(PipelineService.ingest_and_process)
    init_src = inspect.getsource(PipelineService.initialize_system)
    train_src = inspect.getsource(PipelineService.train_ml_models)

    assert "train_models" not in analytics_src
    assert "train_models" not in ingest_src
    assert "train_models" not in init_src
    assert "load_models" in analytics_src
    assert "train_models" in train_src

    ps = PipelineService()
    ps.ml_service = MagicMock()
    ps.ml_service.load_models.return_value = True
    ps.ml_service.predict_all.return_value = pd.DataFrame()
    ps.ml_service.train_models.side_effect = AssertionError("ingest must not train")

    @contextmanager
    def fake_session():
        yield MagicMock()

    with patch("services.pipeline_service.get_db_session", fake_session):
        result = ps._run_analytics_pipeline(_sample_institutions())

    assert result["success"] is True
    ps.ml_service.load_models.assert_called()
    ps.ml_service.train_models.assert_not_called()
