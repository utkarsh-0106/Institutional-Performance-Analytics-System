"""Machine learning models for institutional analytics."""
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from config.settings import MODELS_DIR

FEATURE_COLS = [
    "student_enrollment",
    "faculty_count",
    "placement_percentage",
    "research_publications",
    "infrastructure_score",
]

PERFORMANCE_MODEL_PATH = MODELS_DIR / "performance_regressor.joblib"
ACCREDITATION_MODEL_PATH = MODELS_DIR / "accreditation_classifier.joblib"
RANKING_MODEL_PATH = MODELS_DIR / "ranking_classifier.joblib"
LABEL_ENCODERS_PATH = MODELS_DIR / "label_encoders.joblib"


def _accreditation_label(score: float, acc_score: float) -> str:
    if score >= 75 and acc_score >= 80:
        return "Ready"
    if score >= 55 and acc_score >= 60:
        return "Partially Ready"
    return "Not Ready"


class MLService:
    def __init__(self):
        self.performance_model: Optional[RandomForestRegressor] = None
        self.accreditation_model: Optional[RandomForestClassifier] = None
        self.ranking_model: Optional[RandomForestClassifier] = None
        self.label_encoders: Dict = {}

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[FEATURE_COLS].copy()

    def _build_training_frame(self, inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> pd.DataFrame:
        kpi_cols = [
            "institution_name", "overall_performance_index", "accreditation_score",
            "institution_rank", "ranking_category",
        ]
        return inst_df.merge(kpi_df[kpi_cols], on="institution_name", how="inner")

    def train_models(self, inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> Dict[str, float]:
        if inst_df.empty or kpi_df.empty:
            return {}

        merged = self._build_training_frame(inst_df, kpi_df)
        X = self._prepare_features(merged)

        metrics = {}

        y_perf = merged["overall_performance_index"]
        X_train, X_test, y_train, y_test = train_test_split(X, y_perf, test_size=0.2, random_state=42)
        self.performance_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=12)
        self.performance_model.fit(X_train, y_train)
        metrics["performance_r2"] = round(float(self.performance_model.score(X_test, y_test)), 4)

        y_acc = merged.apply(
            lambda r: _accreditation_label(r["overall_performance_index"], r["accreditation_score"]),
            axis=1,
        )
        self.label_encoders["accreditation"] = LabelEncoder()
        y_acc_enc = self.label_encoders["accreditation"].fit_transform(y_acc)
        Xa_train, Xa_test, ya_train, ya_test = train_test_split(X, y_acc_enc, test_size=0.2, random_state=42)
        self.accreditation_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.accreditation_model.fit(Xa_train, ya_train)
        metrics["accreditation_accuracy"] = round(float(self.accreditation_model.score(Xa_test, ya_test)), 4)

        self.label_encoders["ranking"] = LabelEncoder()
        y_rank_enc = self.label_encoders["ranking"].fit_transform(merged["ranking_category"])
        Xr_train, Xr_test, yr_train, yr_test = train_test_split(X, y_rank_enc, test_size=0.2, random_state=42)
        self.ranking_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.ranking_model.fit(Xr_train, yr_train)
        metrics["ranking_accuracy"] = round(float(self.ranking_model.score(Xr_test, yr_test)), 4)

        self._save_models()
        return metrics

    def _save_models(self) -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.performance_model, PERFORMANCE_MODEL_PATH)
        joblib.dump(self.accreditation_model, ACCREDITATION_MODEL_PATH)
        joblib.dump(self.ranking_model, RANKING_MODEL_PATH)
        joblib.dump(self.label_encoders, LABEL_ENCODERS_PATH)

    def load_models(self) -> bool:
        try:
            if not PERFORMANCE_MODEL_PATH.exists():
                return False
            self.performance_model = joblib.load(PERFORMANCE_MODEL_PATH)
            self.accreditation_model = joblib.load(ACCREDITATION_MODEL_PATH)
            self.ranking_model = joblib.load(RANKING_MODEL_PATH)
            self.label_encoders = joblib.load(LABEL_ENCODERS_PATH)
            return True
        except Exception:
            return False

    def predict_all(self, inst_df: pd.DataFrame) -> pd.DataFrame:
        if inst_df.empty:
            return pd.DataFrame()

        if self.performance_model is None and not self.load_models():
            return pd.DataFrame()

        X = self._prepare_features(inst_df)
        perf_pred = self.performance_model.predict(X)
        acc_pred = self.label_encoders["accreditation"].inverse_transform(
            self.accreditation_model.predict(X)
        )
        rank_pred = self.label_encoders["ranking"].inverse_transform(
            self.ranking_model.predict(X)
        )

        ids = inst_df["id"].values if "id" in inst_df.columns else list(range(len(inst_df)))

        return pd.DataFrame({
            "institution_id": ids,
            "institution_name": inst_df["institution_name"].values,
            "predicted_performance_score": np.round(perf_pred, 2),
            "accreditation_readiness": acc_pred,
            "ranking_category_pred": rank_pred,
        })

    def predict_single(self, record: dict) -> dict:
        df = pd.DataFrame([{
            "student_enrollment": record["student_enrollment"],
            "faculty_count": record["faculty_count"],
            "placement_percentage": record["placement_percentage"],
            "research_publications": record["research_publications"],
            "infrastructure_score": record["infrastructure_score"],
            "institution_name": record.get("institution_name", "Custom"),
        }])
        result = self.predict_all(df)
        return result.iloc[0].to_dict() if not result.empty else {}

    def to_db_records(self, pred_df: pd.DataFrame) -> list:
        return [
            {
                "institution_id": int(row.get("institution_id", 0)),
                "institution_name": str(row["institution_name"]),
                "predicted_performance_score": float(row["predicted_performance_score"]),
                "accreditation_readiness": str(row["accreditation_readiness"]),
                "ranking_category_pred": str(row["ranking_category_pred"]),
            }
            for _, row in pred_df.iterrows()
        ]
