# 🎓 Institutional Performance Analytics

An AI-powered Institutional Performance Analytics platform designed to evaluate, benchmark, rank, and analyze higher education institutions using academic, research, placement, faculty, accreditation, and infrastructure KPIs.

## 🌐 Live Demo

**Deployed Application:**
https://institutional-performance-analytics-system-ujfv7cfx2uwpefuuzdb.streamlit.app

---

## 📌 Project Overview

Institutional Performance Analytics is a data-driven platform that helps educational institutions assess their performance using multiple Key Performance Indicators (KPIs).

The system integrates institutional datasets from official sources and generates:

* Institutional Rankings
* KPI Analytics
* Benchmarking Reports
* Performance Insights
* Recommendation Engine Outputs
* Machine Learning Predictions

The project was developed as a Final Year Engineering Project under the Smart India Hackathon (SIH) problem statement for Institutional Analytics.

---

## 🚀 Key Features

### 📊 KPI Analytics

Analyze institutions using:

* Academic Score
* Research Score
* Placement Score
* Faculty Score
* Infrastructure Score
* Accreditation Score

### 🏆 Ranking Engine

Generate institution rankings using a weighted composite score:

| KPI                  | Weight |
| -------------------- | ------ |
| Academic Score       | 25%    |
| Research Score       | 20%    |
| Placement Score      | 25%    |
| Infrastructure Score | 5%     |
| Faculty Score        | 15%    |
| Accreditation Score  | 10%    |

### 📈 Benchmarking

Compare institutions against:

* National Average
* State Average
* Top Performing Institutions

### 🤖 Recommendation Engine

Rule-based recommendation system that identifies weak KPI areas and generates actionable institutional improvement suggestions.

### 🔮 ML Predictions

Machine Learning module for institutional performance forecasting and trend analysis.

### 📋 Reporting

Generate institutional performance reports and KPI summaries.

---

## 🏗️ System Architecture

Raw Data Sources

↓

ETL Pipeline

↓

Data Cleaning & Validation

↓

SQLite Database

↓

KPI Engine

↓

Ranking Engine

↓

Benchmarking Engine

↓

Recommendation Engine

↓

Machine Learning Models

↓

Interactive Dashboard

---

## 📚 Data Sources

The platform integrates higher education datasets from:

* NIRF (National Institutional Ranking Framework)
* AISHE (All India Survey on Higher Education)
* NAAC Accreditation Records
* UGC Institution Data
* AKTU Engineering Colleges Dataset

---

## 📊 KPI Methodology

### Academic Score

Academic Score =

0.6 × Enrollment Score

*

0.4 × NIRF Score

---

### Research Score

Calculated using normalized research publication counts.

---

### Placement Score

Placement Score = Placement Percentage

---

### Faculty Score

Calculated using normalized faculty strength indicators.

---

### Accreditation Score

Mapped from NAAC accreditation grades.

| Grade | Score |
| ----- | ----- |
| A++   | 100   |
| A+    | 90    |
| A     | 80    |
| B++   | 70    |
| B+    | 60    |
| B     | 50    |

---

### Overall Performance Index

Overall Performance Index =

(Academic × 25%)

*

(Research × 20%)

*

(Placement × 25%)

*

(Infrastructure × 5%)

*

(Faculty × 15%)

*

(Accreditation × 10%)

---

## 🛠️ Technology Stack

### Frontend

* Streamlit
* Plotly

### Backend

* Python

### Database

* SQLite

### Data Processing

* Pandas
* NumPy

### Machine Learning

* Scikit-Learn

### ORM

* SQLAlchemy

### Deployment

* Streamlit Community Cloud

---

## 📂 Project Structure

```text
Institutional-Performance-Analytics/
│
├── app/
├── services/
├── database/
├── config/
├── scripts/
├── data/
│   ├── raw/
│   ├── processed/
│   └── seed/
│
├── models/
├── utils/
├── run.py
├── requirements.txt
└── README.md
```

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/Institutional-Performance-Analytics.git
cd Institutional-Performance-Analytics
```

Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python run.py
```

---

## 🎯 Project Highlights

* Integrated 160+ institutional records
* Multi-source educational data integration
* KPI-driven ranking methodology
* Rule-based recommendation engine
* Interactive analytics dashboard
* Cloud-deployed production application
* Real-world higher education analytics use case

---

## 🔮 Future Enhancements

* Institution Comparison Module
* Advanced Predictive Analytics
* AI-Based Insight Generation
* PDF Report Export
* Interactive Geographic Analytics
* Multi-User Role Management
* Automated Data Refresh Pipelines

---

## 👨‍💻 Author

**Utkarsh Maheshwari**

Final Year Engineering Student

Specialization: Data Analytics, Machine Learning, Software Development

GitHub: https://github.com/utkarsh-0106

---

## 📄 License

This project is developed for educational and research purposes as part of a Final Year Engineering Project.
