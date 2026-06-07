"""Run full ETL: NIRF + AISHE + NAAC + UGC → merge → SQLite."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    from config.data_sources import MERGED_DATASET_PATH, NIRF_FILE
    from database.connection import init_db
    from services.etl.pipeline import ETLPipeline
    from services.pipeline_service import PipelineService

    if not NIRF_FILE.exists():
        print("Raw data missing — building real seed files...")
        from scripts.build_real_seed_data import main as build_seed
        build_seed()

    init_db()
    etl = ETLPipeline()
    print("Source row counts:", etl.source_status())

    ps = PipelineService()
    result = etl.run_and_ingest_sqlite(ps)

    if result.get("success"):
        print(f"ETL complete: {result['institutions']} institutions in SQLite")
        print(f"Merged CSV: {MERGED_DATASET_PATH}")
        print("Data source:", result.get("data_source", "real_merged"))
    else:
        print("ETL failed:", result.get("errors"))
        sys.exit(1)


if __name__ == "__main__":
    main()
