"""Orchestration pipeline: load data, compute KPIs, rankings, ML, recommendations."""
from pathlib import Path

import pandas as pd

from config.settings import DEFAULT_USERS, MERGED_DATASET_PATH, SYNTHETIC_DATASET_PATH, USE_SYNTHETIC_FALLBACK
from database.connection import get_db_session, init_db
from database.repositories import (
    InstitutionRepository,
    KPIRepository,
    MLRepository,
    RecommendationRepository,
    UserRepository,
)
from services.data_cleaning import DataCleaningService
from services.data_validation import DataValidationService
from services.insights_service import InsightsService
from services.kpi_engine import KPIEngine
from services.ml_service import MLService
from services.ranking_engine import RankingEngine
from services.recommendation_engine import RecommendationEngine
from utils.helpers import hash_password


class PipelineService:
    def __init__(self):
        self.ml_service = MLService()

    def load_primary_dataset(self) -> tuple:
        """
        Load dataset with priority:
        1. Merged real data (NIRF+AISHE+NAAC+UGC)
        2. Run ETL if raw files exist but merged missing
        3. Synthetic fallback
        """
        from config.data_sources import NIRF_FILE

        if MERGED_DATASET_PATH.exists():
            df = pd.read_csv(MERGED_DATASET_PATH)
            if len(df) >= 50:
                return df, "real_merged"

        if NIRF_FILE.exists():
            from services.etl.pipeline import ETLPipeline
            df = ETLPipeline().run_merge()
            if not df.empty:
                return df, "real_etl"

        if USE_SYNTHETIC_FALLBACK and SYNTHETIC_DATASET_PATH.exists():
            return pd.read_csv(SYNTHETIC_DATASET_PATH), "synthetic_fallback"

        if USE_SYNTHETIC_FALLBACK:
            from scripts.generate_dataset import generate_dataset
            df = generate_dataset(500)
            df.to_csv(SYNTHETIC_DATASET_PATH, index=False)
            return df, "synthetic_generated"

        return pd.DataFrame(), "none"

    def initialize_system(self, load_synthetic: bool = False) -> dict:
        init_db()
        with get_db_session() as session:
            UserRepository.seed_default_users(session, DEFAULT_USERS, hash_password)

        df, source = self.load_primary_dataset()
        if df.empty:
            return {"success": False, "errors": ["No dataset available. Run scripts/build_real_seed_data.py"]}

        result = self.ingest_and_process(df)
        result["data_source"] = source
        return result

    def ingest_and_process(self, df: pd.DataFrame) -> dict:
        valid, errors = DataValidationService.validate(df)
        if not valid:
            return {"success": False, "errors": errors}

        cleaned = DataCleaningService.clean(df)

        with get_db_session() as session:
            InstitutionRepository.bulk_upsert_from_dataframe(session, cleaned)
            inst_df = InstitutionRepository.to_dataframe(session)

        return self._run_analytics_pipeline(inst_df)

    def reprocess_existing(self) -> dict:
        with get_db_session() as session:
            inst_df = InstitutionRepository.to_dataframe(session)
        if inst_df.empty:
            df, source = self.load_primary_dataset()
            if df.empty:
                return {"success": False, "errors": ["No institution data in database."]}
            result = self.ingest_and_process(df)
            result["data_source"] = source
            return result
        return self._run_analytics_pipeline(inst_df)

    def _run_analytics_pipeline(self, inst_df: pd.DataFrame) -> dict:
        kpi_df = KPIEngine.calculate_kpis(inst_df)
        kpi_df = RankingEngine.apply_rankings(kpi_df)

        kpi_records = KPIEngine.to_db_records(kpi_df)
        kpi_records = RankingEngine.update_db_records(kpi_df, kpi_records)

        try:
            ml_metrics = self.ml_service.train_models(inst_df, kpi_df)
        except Exception as exc:
            ml_metrics = {"error": str(exc)}
            self.ml_service.load_models()

        pred_df = self.ml_service.predict_all(inst_df)
        ml_records = self.ml_service.to_db_records(pred_df) if not pred_df.empty else []

        recommendations = RecommendationEngine.generate_all(kpi_df, inst_df)

        with get_db_session() as session:
            KPIRepository.bulk_save(session, kpi_records)
            MLRepository.clear_all(session)
            if ml_records:
                MLRepository.bulk_save(session, ml_records)
            RecommendationRepository.bulk_save(session, recommendations)

        system_insights = InsightsService.generate_system_insights(inst_df, kpi_df)

        return {
            "success": True,
            "institutions": len(inst_df),
            "kpi_records": len(kpi_records),
            "ml_predictions": len(ml_records),
            "recommendations": len(recommendations),
            "ml_metrics": ml_metrics,
            "top_10": kpi_df.nsmallest(10, "institution_rank")["institution_name"].tolist(),
            "system_insights": system_insights,
        }

    def load_uploaded_file(self, file_path: Path, file_type: str = "csv") -> dict:
        if file_type == "excel":
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        return self.ingest_and_process(df)

    def get_all_data(self) -> dict:
        with get_db_session() as session:
            inst_df = InstitutionRepository.to_dataframe(session)
            kpi_df = KPIRepository.to_dataframe(session)
            ml_df = MLRepository.to_dataframe(session)
            rec_df = RecommendationRepository.to_dataframe(session)
        return {
            "institutions": inst_df,
            "kpis": kpi_df,
            "predictions": ml_df,
            "recommendations": rec_df,
        }
