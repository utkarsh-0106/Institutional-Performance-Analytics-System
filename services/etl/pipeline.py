"""End-to-end ETL: ingest → merge → persist (cleaning happens at ingest)."""
from pathlib import Path
from typing import Dict

import pandas as pd

from config.data_sources import MERGED_DATASET_PATH
from services.etl.cleaners import ETLCleaners
from services.etl.merger import InstitutionMerger


class ETLPipeline:
    def __init__(self):
        self.merger = InstitutionMerger()

    def run_merge(self, save_path: Path = None) -> pd.DataFrame:
        sources = self.merger.load_sources()
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

        save_path = save_path or MERGED_DATASET_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(save_path, index=False)

        return merged

    @staticmethod
    def source_status() -> Dict[str, int]:
        sources = InstitutionMerger().load_sources()
        return {k: len(v) for k, v in sources.items()}

    def run_and_ingest_sqlite(self, pipeline_service) -> dict:
        """Run ETL merge, then ingest via PipelineService (validate + clean once)."""
        df = self.run_merge()
        if df.empty:
            df, label = pipeline_service.load_primary_dataset()
            if df.empty:
                return {"success": False, "errors": ["No data from ETL or fallback."]}
            result = pipeline_service.ingest_and_process(df)
            result["data_source"] = label
            result["source_counts"] = self.source_status()
            return result

        result = pipeline_service.ingest_and_process(df)
        result["data_source"] = "real_merged"
        result["source_counts"] = self.source_status()
        return result
