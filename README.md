# Institutional Performance Analytics System (IPAS)

An analytics platform for evaluating, comparing, and understanding
higher-education institution performance through key performance
indicators (KPIs), institutional rankings, benchmarking,
machine-learning predictions, recommendations, and reports.

**Live Demo:**
https://institutional-performance-analytics-system-ujfv7cfx2uwpefuuzdb.streamlit.app/\
**GitHub Repository:**
https://github.com/utkarsh-0106/Institutional-Performance-Analytics-System

------------------------------------------------------------------------

## Table of Contents

-   [Overview](#overview)
-   [Features](#features)
-   [Role-Based Access Control](#role-based-access-control-rbac)
-   [Data Sources and Processing](#data-sources-and-processing)
-   [Technology Stack](#technology-stack)
-   [Architecture](#architecture)
-   [Run Locally](#run-locally)
-   [Run Tests](#run-tests)
-   [Demo Accounts](#demo-accounts)
-   [Security Notes](#security-notes)
-   [Project Structure](#project-structure)
-   [Future Improvements](#future-improvements)

## Overview

IPAS consolidates institutional data and turns it into analytics that
help users inspect performance across academic, research, placement,
faculty, infrastructure, and accreditation dimensions.

The project includes data ingestion and validation, KPI processing,
rankings, benchmarking, machine-learning predictions, recommendations,
and report generation. It also includes role-based access control so
different users receive different capabilities and data scopes.

## Features

### Analytics and dashboards

-   KPI overview and institutional performance dashboards.
-   Institutional rankings based on the project's composite scoring
    logic.
-   Benchmarking against available institutional comparison groups.
-   Institution profiles and performance history where data is
    available.
-   Charts and visual summaries using Plotly.

### Data management and quality

-   ETL adapters for UGC, NIRF, AISHE, and NAAC data.
-   Schema and range validation with data-quality reporting.
-   Data upload and ingestion workflows supported by the application.
-   SQLite-backed persistence through SQLAlchemy.
-   Approximately 165 consolidated institutional records in the project
    dataset; available records depend on the data configured in the
    deployment.

### Decision support

-   Machine-learning predictions for institutional performance.
-   Recommendations that highlight areas for improvement.
-   AI insight and benchmarking views available through the application.
-   Performance reports and data export workflows supported by the
    existing UI.

### Access management

-   Three canonical roles: `ADMIN`, `ANALYST`, and `INSTITUTION`.
-   Role-aware navigation and Home page.
-   Authorization checks beyond simply hiding navigation items.
-   Institution-level data scoping for institution users.
-   Administrative workflows for user and institution management.
-   Audit logging for supported administrative and system actions.

## Role-Based Access Control (RBAC)

RBAC means **Role-Based Access Control**: permissions are assigned
according to a user's role.

  -----------------------------------------------------------------------
  Role                    Scope                   Main capabilities
  ----------------------- ----------------------- -----------------------
  `ADMIN`                 System-wide             Manage users, roles,
                                                  institution
                                                  associations,
                                                  data-management
                                                  workflows, and
                                                  administrative views;
                                                  inspect system-wide
                                                  analytics and supported
                                                  audit information.

  `ANALYST`               All institutions        Use institutional
                                                  dashboards, KPIs,
                                                  rankings, benchmarking,
                                                  predictions,
                                                  recommendations,
                                                  insights, and reports.
                                                  Does not receive
                                                  administrative
                                                  user-management
                                                  permissions.

  `INSTITUTION`           Assigned institution    View the assigned
                          only                    institution's available
                                                  analytics and supported
                                                  reports. Cannot access
                                                  other institutions'
                                                  data or administrative
                                                  operations.
  -----------------------------------------------------------------------

**In short:** Admin manages the system; Analyst analyzes all
institutions; Institution users analyze their assigned institution.

Authorization should be enforced in application/service logic, not only
through UI visibility. Institution scope should come from the
authenticated user's trusted identity and association rather than an
editable institution identifier supplied by the user.

## Data Sources and Processing

The project includes adapters for: - **UGC** --- University Grants
Commission institutional data. - **NIRF** --- National Institutional
Ranking Framework data. - **AISHE** --- All India Survey on Higher
Education data. - **NAAC** --- accreditation information.

The general processing flow is:

1.  Load or ingest source data.
2.  Validate schemas and value ranges.
3.  Produce data-quality results for the ingestion workflow.
4.  Persist records in the database.
5.  Process KPIs and composite ranking data.
6.  Display dashboards, rankings, benchmarking, predictions,
    recommendations, and reports.

The exact results depend on the records available to the application.
This README does not redefine the project's KPI or ranking formulas.

## Technology Stack

-   **Language:** Python
-   **Application UI:** Streamlit
-   **Database:** SQLite
-   **ORM / persistence:** SQLAlchemy
-   **Data processing:** Pandas, NumPy
-   **Visualization:** Plotly
-   **Machine learning:** Scikit-learn
-   **Testing:** pytest

## Architecture

``` text
UGC / NIRF / AISHE / NAAC
            |
            v
     ETL and ingestion
            |
            v
  Schema and range validation
            |
            v
       SQLite database
            |
            v
      KPI processing
            |
            v
   Rankings and benchmarking
            |
      +-----+------+----------------+
      |            |                |
      v            v                v
 Recommendations  ML predictions  Reports / insights
      |            |                |
      +------------+----------------+
                   |
                   v
          Streamlit application
                   |
                   v
      Role-aware access and data scope
```

## Run Locally

### 1. Clone the repository

``` bash
git clone https://github.com/utkarsh-0106/Institutional-Performance-Analytics-System.git
cd Institutional-Performance-Analytics-System
```

### 2. Create and activate a virtual environment

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

``` powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Start the application

The project has been run locally using:

``` bash
python run.py
```

Follow the local URL printed by the application in your terminal. If the
repository's launcher or deployment configuration changes, use the entry
point documented in the current source code.

### 5. Database and configuration

The application uses SQLite and its existing database initialization
workflow. Keep the project's expected database/configuration files in
place, and back up any database containing data you need before testing
schema changes. Do not commit local secrets, credentials, or private
datasets.

## Run Tests

Install the test runner in the active virtual environment if it is not
already installed:

``` bash
python -m pip install pytest
```

Run the test suite from the repository root:

``` bash
python -m pytest -q
```

**Latest recorded local verification:** 18 tests passed. SQLAlchemy
emitted deprecation warnings related to `datetime.utcnow()`; these
warnings did not fail that test run. Re-run the tests against the
current checkout before relying on this status after future changes.

## Demo Accounts

The application login screen has included these demonstration accounts:

  Role          Username             Password
  ------------- -------------------- --------------
  Admin         `admin`              `admin123`
  Analyst       `analyst`            `analyst123`
  Institution   `institution_user`   `user123`

These are **demo credentials only**. Do not use them for production or
expose a production deployment with default credentials. Change or
disable demonstration accounts before using the application with
sensitive or real institutional data.

## Security Notes

-   Assign each user the least privilege required for their work.
-   Keep institution-user records associated with the correct
    institution.
-   Enforce authorization in application/service logic as well as the
    UI.
-   Do not trust user-editable URL parameters or form fields to
    establish an institution user's identity or scope.
-   Use unique, strong credentials outside local demonstrations.
-   Keep private configuration and secrets out of version control.
-   Review audit logs and application logs for sensitive information
    before sharing them.

## Project Structure

The main application areas include:

``` text
.
├── app/
│   ├── main.py
│   ├── theme.css
│   ├── ui_common.py
│   └── views/
│       ├── admin.py
│       ├── dashboard.py
│       ├── data_management.py
│       ├── home.py
│       ├── ml_predictions.py
│       └── reports.py
├── auth/
│   ├── auth_service.py
│   ├── login.py
│   ├── rbac.py
│   └── session.py
├── config/
├── database/
│   ├── models.py
│   ├── repositories.py
│   └── session.py
├── services/
│   └── access_control.py
├── tests/
│   └── test_rbac.py
├── requirements.txt
└── run.py
```

Other existing project modules support KPI processing, rankings,
recommendations, ETL, benchmarking, and machine-learning workflows.

## Future Improvements

-   Replace deprecated UTC timestamp calls with timezone-aware UTC
    datetimes.
-   Expand automated authorization tests for direct page access and
    cross-institution access attempts.
-   Add documented database migration procedures for future schema
    changes.
-   Add deployment-specific secret and account-management guidance.
-   Increase test coverage for ingestion, analytics, reporting, and
    end-to-end user journeys.
