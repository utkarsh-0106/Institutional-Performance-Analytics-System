"""Download official Indian HE datasets when URLs are available."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.data_sources import AISHE_DIR, DATASET_URLS, NIRF_DIR, NAAC_DIR, UGC_DIR

try:
    import requests
except ImportError:
    requests = None


def download_file(url: str, dest: Path, timeout: int = 60) -> bool:
    if requests is None:
        print("Install requests: pip install requests")
        return False
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Institutional-Analytics/1.0"})
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        print(f"Downloaded: {dest}")
        return True
    except Exception as exc:
        print(f"Failed {url}: {exc}")
        return False


def main():
    print("Official dataset download helper")
    print("NIRF: Download Engineering/Management rankings CSV from https://www.nirfindia.org/")
    print("      Save as:", NIRF_DIR / "nirf_rankings.csv")
    print("NAAC: Download accredited institutions from https://www.naac.gov.in/")
    print("      Save as:", NAAC_DIR / "naac_accreditation.csv")
    print("UGC: Download university list from https://www.ugc.gov.in/")
    print("     Save as:", UGC_DIR / "ugc_institutions.csv")
    print("AISHE: Download from https://www.data.gov.in/ (AISHE tables)")
    print("       Save as:", AISHE_DIR / "aishe_statistics.csv")
    print()
    print("If downloads fail, run: python scripts/build_real_seed_data.py")
    print("That builds real institution CSVs from the public NIRF/UGC registry bundled in the project.")

    if DATASET_URLS.get("aishe"):
        download_file(
            DATASET_URLS["aishe"],
            AISHE_DIR / "aishe_statistics_downloaded.csv",
        )


if __name__ == "__main__":
    main()
