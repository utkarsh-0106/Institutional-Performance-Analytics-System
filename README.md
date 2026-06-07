# Institutional Performance Analytics System

**SIH 2025 | Problem ID: SIH25253**  
AI-based analysis and performance indicators for academic institutions (UGC & AICTE).

## Features

| Module | Description |
|--------|-------------|
| Authentication | Admin & Institution User roles with session management |
| Data Management | NIRF, AISHE, NAAC, UGC ETL + CSV/Excel upload |
| KPI Engine | Academic, Research, Placement, Infrastructure, Faculty, Accreditation scores |
| Analytics Dashboard | Plotly charts and performance metrics |
| Ranking System | Weighted composite ranking (Top 10/50/100/200) |
| Machine Learning | Random Forest regression & classification |
| Recommendations | Dynamic KPI-gap based recommendations |
| Benchmarking | State, national, and top-performer comparisons |
| Reports | PDF export via ReportLab |
| AI Insights | Automated narrative insights |

## Quick Start

```bash
cd Institutional-Performance-Analytics
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py --bootstrap   # builds real data + ETL + SQLite
python run.py
```

Open: http://localhost:8501

## Real Indian Higher Education Data

Data priority: **merged real data** → synthetic fallback.

```bash
# Build raw CSVs from public NIRF/UGC institution registry (~130+ real HEIs)
python scripts/build_real_seed_data.py

# ETL merge → data/processed/merged_institutions.csv → SQLite
python scripts/run_etl.py

# Optional: download official exports (place in data/raw/)
python scripts/download_datasets.py
```

| Source | Raw path | Metrics contributed |
|--------|----------|---------------------|
| NIRF | `data/raw/nirf/nirf_rankings.csv` | Rank, scores, placement/research/infrastructure proxies |
| AISHE | `data/raw/aishe/aishe_statistics.csv` | Enrollment, faculty |
| NAAC | `data/raw/naac/naac_accreditation.csv` | CGPA, accreditation grade |
| UGC | `data/raw/ugc/ugc_institutions.csv` | Institution master, state, type |

Set `USE_SYNTHETIC_FALLBACK=false` to disable synthetic CSV fallback.

### Demo Login

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Institution User | institution_user | user123 |

## Project Structure

```
├── app/                    # Streamlit UI
│   ├── main.py             # Application entry
│   ├── components/         # Plotly charts
│   └── views/              # Streamlit view modules
├── auth/                   # Login & session
├── config/                 # Settings + data_sources
├── database/               # SQLAlchemy models & repos
├── services/
│   ├── ingestion/          # NIRF, AISHE, NAAC, UGC loaders
│   └── etl/                # Clean, merge, pipeline
├── scripts/                # ETL, seed builder, synthetic fallback
├── data/
│   ├── raw/                # Source CSVs
│   ├── processed/          # merged_institutions.csv
│   └── synthetic_institutions.csv
├── models/saved/           # Trained ML models
└── reports/generated/      # PDF exports
```

## MySQL Configuration

Set environment variables:

```
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=institutional_analytics
```

Install: `pip install pymysql`

## Tech Stack

Streamlit, Python, SQLite/MySQL, Pandas, NumPy, Scikit-learn, XGBoost, Plotly, ReportLab
