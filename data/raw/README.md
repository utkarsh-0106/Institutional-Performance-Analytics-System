# Raw Indian Higher Education Datasets

Place official CSV/Excel exports here, or run the bundled builder:

```bash
python scripts/build_real_seed_data.py
python scripts/run_etl.py
```

## Expected files

| Source | Path | Description |
|--------|------|-------------|
| NIRF | `nirf/nirf_rankings.csv` | NIRF overall ranks and parameter scores |
| AISHE | `aishe/aishe_statistics.csv` | Enrollment and faculty (AISHE survey) |
| NAAC | `naac/naac_accreditation.csv` | CGPA / accreditation grades |
| UGC | `ugc/ugc_institutions.csv` | UGC recognized universities |

## Official portals

- NIRF: https://www.nirfindia.org/
- AISHE: https://www.education.gov.in/aishe
- NAAC: https://www.naac.gov.in/
- UGC: https://www.ugc.gov.in/

Download helper: `python scripts/download_datasets.py`

Merged output: `data/processed/merged_institutions.csv`  
Synthetic fallback: `data/synthetic_institutions.csv`
