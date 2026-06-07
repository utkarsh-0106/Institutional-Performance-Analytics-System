"""End-to-end ETL: ingest → clean → merge → persist."""
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from config.data_sources import MERGED_DATASET_PATH
from config.settings import SYNTHETIC_DATASET_PATH
from services.data_cleaning import DataCleaningService
from services.data_validation import DataValidationService
from services.etl.cleaners import ETLCleaners
from services.etl.merger import InstitutionMerger


class ETLPipeline:
    def __init__(self):
        self.merger = InstitutionMerger()

    def run_merge(self, save_path: Path = None) -> pd.DataFrame:
        sources = self.merger.load_sources()
        counts = {k: len(v) for k, v in sources.items()}
        merged = self.merger.merge(sources)

        if merged.empty:
            return pd.DataFrame()

        merged = ETLCleaners.fill_missing_from_state_medians(merged)
        merged = ETLCleaners.clean_merged(merged)

        output_cols = [
            "institution_name", "state", "student_enrollment", "faculty_count",
            "placement_percentage", "research_publications", "infrastructure_score",
            "accreditation_grade", "nirf_rank", "data_sources",
        ]
        merged = merged[[c for c in output_cols if c in merged.columns]]

        cleaned = DataCleaningService.clean(merged)
        save_path = save_path or MERGED_DATASET_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(save_path, index=False)

        return cleaned

    @staticmethod
    def source_status() -> Dict[str, int]:
        sources = InstitutionMerger().load_sources()
        return {k: len(v) for k, v in sources.items()}

    @staticmethod
    def load_merged_or_fallback() -> tuple:
        """
        Returns (dataframe, source_label).
        Priority: merged real data → synthetic fallback.
        """
        if MERGED_DATASET_PATH.exists():
            df = pd.read_csv(MERGED_DATASET_PATH)
            if len(df) >= 50:
                return df, "real_merged"

        if SYNTHETIC_DATASET_PATH.exists():
            return pd.read_csv(SYNTHETIC_DATASET_PATH), "synthetic_fallback"

        from scripts.generate_dataset import generate_dataset
        df = generate_dataset(500)
        df.to_csv(SYNTHETIC_DATASET_PATH, index=False)
        return df, "synthetic_generated"

    def run_and_ingest_sqlite(self, pipeline_service) -> dict:
        """Run ETL and load into SQLite via PipelineService."""
        df = self.run_merge()
        if df.empty:
            df, label = self.load_merged_or_fallback()
            if df.empty:
                return {"success": False, "errors": ["No data from ETL or fallback."]}
            return pipeline_service.ingest_and_process(df)

        result = pipeline_service.ingest_and_process(df)
        result["data_source"] = "real_merged"
        result["source_counts"] = self.source_status()
        return result
