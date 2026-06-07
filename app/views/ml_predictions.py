"""Machine Learning Predictions - Module 6."""
import streamlit as st

from app.ui_common import load_data, page_header, show_data_banner, widget_key
from services.ml_service import MLService


def render():
    page_header(
        "ML Predictions",
        "Random Forest: performance score, accreditation readiness, ranking category",
    )

    data = load_data()
    show_data_banner(data)
    pred_df = data["predictions"]

    tab1, tab2 = st.tabs(["Batch Predictions", "Single Institution Predictor"])

    with tab1:
        st.subheader("Stored Predictions")
        if pred_df.empty:
            st.warning("No predictions in database. Run **Data Management → Initialize / Reprocess All Data**.")
            st.dataframe(data["institutions"].head(5), use_container_width=True)
        else:
            st.dataframe(pred_df, use_container_width=True, hide_index=True)
            if "accreditation_readiness" in pred_df.columns:
                st.subheader("Accreditation Readiness Distribution")
                st.bar_chart(pred_df["accreditation_readiness"].value_counts())

    with tab2:
        st.subheader("Predict for Custom Input")
        c1, c2 = st.columns(2)
        with c1:
            enrollment = st.number_input("Student Enrollment", 500, 30000, 5000, key=widget_key("ml", "enrollment"))
            faculty = st.number_input("Faculty Count", 20, 2000, 200, key=widget_key("ml", "faculty"))
            placement = st.slider("Placement Percentage", 0.0, 100.0, 70.0, key=widget_key("ml", "placement"))
        with c2:
            research = st.number_input("Research Publications", 0, 1500, 100, key=widget_key("ml", "research"))
            infrastructure = st.slider("Infrastructure Score", 0.0, 100.0, 65.0, key=widget_key("ml", "infra"))

        if st.button("Predict", type="primary", key=widget_key("ml", "predict_btn")):
            ml = MLService()
            if not ml.load_models():
                st.warning("Models not trained — showing illustrative sample output.")
                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted Performance Score", "72.50")
                m2.metric("Accreditation Readiness", "Partially Ready")
                m3.metric("Ranking Category", "Top 200")
            else:
                result = ml.predict_single({
                    "student_enrollment": enrollment,
                    "faculty_count": faculty,
                    "placement_percentage": placement,
                    "research_publications": research,
                    "infrastructure_score": infrastructure,
                })
                if result:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Predicted Performance Score", f"{result.get('predicted_performance_score', 0):.2f}")
                    m2.metric("Accreditation Readiness", result.get("accreditation_readiness", "N/A"))
                    m3.metric("Ranking Category", result.get("ranking_category_pred", "N/A"))
