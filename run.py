"""Launch the Institutional Performance Analytics System."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def bootstrap():
    """Build real datasets, run ETL, and initialize SQLite."""
    sys.path.insert(0, str(ROOT))
    from config.data_sources import NIRF_FILE
    from config.settings import MERGED_DATASET_PATH, SYNTHETIC_DATASET_PATH

    if not NIRF_FILE.exists():
        print("Building real Indian HE seed data (NIRF, AISHE, NAAC, UGC)...")
        from scripts.build_real_seed_data import main as build_real
        build_real()

    if not MERGED_DATASET_PATH.exists():
        print("Running ETL merge...")
        from scripts.run_etl import main as run_etl
        run_etl()
        return

    if not SYNTHETIC_DATASET_PATH.exists():
        from scripts.generate_dataset import generate_dataset
        df = generate_dataset(500)
        df.to_csv(SYNTHETIC_DATASET_PATH, index=False)
        print(f"Synthetic fallback saved: {SYNTHETIC_DATASET_PATH}")

    from services.pipeline_service import PipelineService
    result = PipelineService().initialize_system()
    if result.get("success"):
        print(f"Pipeline ready: {result['institutions']} institutions ({result.get('data_source', 'unknown')})")
    else:
        print(f"Pipeline warning: {result.get('errors')}")


if __name__ == "__main__":
    if "--bootstrap" in sys.argv:
        bootstrap()
        sys.exit(0)

    app_path = ROOT / "app" / "main.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ], cwd=str(ROOT))
