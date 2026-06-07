"""Data Management - Module 2."""
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from auth.session import is_admin
from app.ui_common import load_data, page_header, render_kpi_cards, show_data_banner, widget_key
from config.data_sources import AISHE_FILE, MERGED_DATASET_PATH, NAAC_FILE, NIRF_FILE, UGC_FILE
from config.settings import SYNTHETIC_DATASET_PATH
from services.etl.pipeline import ETLPipeline
from services.pipeline_service import PipelineService


def render():
    page_header("Data Management", "NIRF, AISHE, NAAC, UGC ingestion and analytics pipeline")

    data = load_data()
    show_data_banner(data)
    st.write(f"Current records in view: **{len(data['institutions'])}** institutions")
    render_kpi_cards(data["institutions"], data["kpis"])

    if not is_admin():
        st.info("Institution users have read-only access. Contact admin for data uploads.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Real Data ETL", "Upload Data", "Process Pipeline", "Dataset Info",
    ])

    with tab1:
        st.subheader("Indian Higher Education Data Sources")
        st.markdown("""
        | Source | File | Status |
        |--------|------|--------|
        """)
        sources = {
            "NIRF Rankings": NIRF_FILE,
            "AISHE Statistics": AISHE_FILE,
            "NAAC Accreditation": NAAC_FILE,
            "UGC Institutions": UGC_FILE,
        }
        for label, path in sources.items():
            st.write(f"- **{label}**: `{'✅' if path.exists() else '❌'} {path.name}`")

        if MERGED_DATASET_PATH.exists():
            mdf = pd.read_csv(MERGED_DATASET_PATH)
            st.success(f"Merged dataset: **{len(mdf)}** institutions → `{MERGED_DATASET_PATH.name}`")
            if "data_sources" in mdf.columns:
                st.caption("Sources tracked per institution in `data_sources` column.")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Build Real Seed CSVs", key=widget_key("data_mgmt", "build_seed")):
                with st.spinner("Building NIRF/AISHE/NAAC/UGC raw files..."):
                    from scripts.build_real_seed_data import main as build_real
                    build_real()
                st.success("Raw real-data CSVs created.")
                st.rerun()
        with col_b:
            if st.button("Run ETL → SQLite", type="primary", key=widget_key("data_mgmt", "run_etl")):
                with st.spinner("Merging and loading into database..."):
                    from scripts.run_etl import main as run_etl
                    run_etl()
                st.session_state.pipeline_initialized = False
                st.success("ETL complete.")
                st.rerun()

    with tab2:
        st.subheader("Upload CSV or Excel")
        if is_admin():
            uploaded = st.file_uploader(
                "Choose file",
                type=["csv", "xlsx", "xls"],
                key=widget_key("data_mgmt", "uploader"),
            )
            if uploaded:
                suffix = Path(uploaded.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = Path(tmp.name)
                file_type = "excel" if suffix in [".xlsx", ".xls"] else "csv"
                if st.button("Upload & Process", type="primary", key=widget_key("data_mgmt", "upload_btn")):
                    with st.spinner("Validating and processing..."):
                        result = PipelineService().load_uploaded_file(tmp_path, file_type)
                    if result.get("success"):
                        st.success(f"Processed {result['institutions']} institutions.")
                        st.session_state.pipeline_initialized = False
                        st.rerun()
                    else:
                        st.error(result.get("errors", ["Processing failed"]))
        else:
            st.warning("Upload restricted to Admin role.")

    with tab3:
        st.subheader("Run Analytics Pipeline")
        st.write("Uses **merged real data** first; synthetic CSV is fallback only.")
        if st.button("Initialize / Reprocess All Data", type="primary", key=widget_key("data_mgmt", "pipeline_btn")):
            with st.spinner("Running pipeline..."):
                result = PipelineService().initialize_system()
            if result.get("success"):
                st.success(f"Done — source: **{result.get('data_source', 'unknown')}**")
                st.metric("Institutions Processed", result["institutions"])
                st.session_state.pipeline_initialized = True
                if result.get("ml_metrics"):
                    st.json(result["ml_metrics"])
            else:
                st.error(result.get("errors", ["Pipeline failed"]))

    with tab4:
        st.subheader("Dataset Information")
        if MERGED_DATASET_PATH.exists():
            df = pd.read_csv(MERGED_DATASET_PATH)
            st.success(f"**Primary (real merged):** `{MERGED_DATASET_PATH.name}` — {len(df)} rows")
            st.dataframe(df.head(15), use_container_width=True)
        if SYNTHETIC_DATASET_PATH.exists():
            sdf = pd.read_csv(SYNTHETIC_DATASET_PATH)
            st.info(f"**Fallback (synthetic):** `{SYNTHETIC_DATASET_PATH.name}` — {len(sdf)} rows")

        st.caption("ETL status: " + str(ETLPipeline.source_status()))
