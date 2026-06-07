"""Merge NIRF, AISHE, NAAC, and UGC datasets into unified institutional schema."""
import pandas as pd

from services.ingestion.aishe import AISHEIngestion
from services.ingestion.naac import NAACIngestion
from services.ingestion.nirf import NIRFIngestion
from services.ingestion.ugc import UGCIngestion


class InstitutionMerger:
    """ETL merge: UGC master → NIRF → AISHE → NAAC."""

    def __init__(self):
        self.nirf = NIRFIngestion()
        self.aishe = AISHEIngestion()
        self.naac = NAACIngestion()
        self.ugc = UGCIngestion()

    def load_sources(self) -> dict:
        return {
            "ugc": self.ugc.load(),
            "nirf": self.nirf.load(),
            "aishe": self.aishe.load(),
            "naac": self.naac.load(),
        }

    def merge(self, sources: dict = None) -> pd.DataFrame:
        sources = sources or self.load_sources()
        ugc_df = sources.get("ugc", pd.DataFrame())
        nirf_df = sources.get("nirf", pd.DataFrame())
        aishe_df = sources.get("aishe", pd.DataFrame())
        naac_df = sources.get("naac", pd.DataFrame())

        base = self._select_base(ugc_df, nirf_df, aishe_df, naac_df)
        if base.empty:
            return pd.DataFrame()

        merged = base.copy()
        merged["data_sources"] = merged.get("data_sources", "ugc")

        if not nirf_df.empty:
            nirf_df = NIRFIngestion.derive_metrics(nirf_df)
            nirf_cols = [
                "_merge_key", "nirf_rank", "nirf_score", "nirf_category",
                "placement_percentage", "research_publications", "infrastructure_score",
                "state",
            ]
            nirf_sub = nirf_df[[c for c in nirf_cols if c in nirf_df.columns]].drop_duplicates("_merge_key")
            merged = merged.merge(nirf_sub, on="_merge_key", how="left", suffixes=("", "_nirf"))
            merged = self._coalesce_columns(merged, "state", "state_nirf")
            merged = self._tag_source(merged, "nirf")

        if not aishe_df.empty:
            aishe_cols = ["_merge_key", "student_enrollment", "faculty_count", "state", "aishe_year"]
            aishe_sub = aishe_df[[c for c in aishe_cols if c in aishe_df.columns]].drop_duplicates("_merge_key")
            merged = merged.merge(aishe_sub, on="_merge_key", how="left", suffixes=("", "_aishe"))
            merged = self._coalesce_columns(merged, "student_enrollment", "student_enrollment_aishe")
            merged = self._coalesce_columns(merged, "faculty_count", "faculty_count_aishe")
            merged = self._coalesce_columns(merged, "state", "state_aishe")
            merged = self._tag_source(merged, "aishe")

        if not naac_df.empty:
            naac_cols = ["_merge_key", "accreditation_grade", "naac_cgpa", "naac_cycle", "state"]
            naac_sub = naac_df[[c for c in naac_cols if c in naac_df.columns]].drop_duplicates("_merge_key")
            merged = merged.merge(naac_sub, on="_merge_key", how="left", suffixes=("", "_naac"))
            merged = self._coalesce_columns(merged, "accreditation_grade", "accreditation_grade_naac")
            merged = self._coalesce_columns(merged, "state", "state_naac")
            merged = self._tag_source(merged, "naac")

        merged = self._apply_rank_defaults(merged)
        return merged

    @staticmethod
    def _select_base(ugc_df, nirf_df, aishe_df, naac_df) -> pd.DataFrame:
        if not ugc_df.empty:
            cols = ["institution_name", "_merge_key", "state", "institution_type", "year_established"]
            return ugc_df[[c for c in cols if c in ugc_df.columns]].copy()

        frames = [nirf_df, aishe_df, naac_df]
        for df in frames:
            if not df.empty and "institution_name" in df.columns:
                out = df[["institution_name", "_merge_key"]].copy()
                if "state" in df.columns:
                    out["state"] = df["state"]
                return out
        return pd.DataFrame()

    @staticmethod
    def _coalesce_columns(df: pd.DataFrame, primary: str, secondary: str) -> pd.DataFrame:
        if secondary in df.columns:
            if primary not in df.columns:
                df[primary] = df[secondary]
            else:
                df[primary] = df[primary].fillna(df[secondary])
            df = df.drop(columns=[secondary], errors="ignore")
        return df

    @staticmethod
    def _tag_source(df: pd.DataFrame, source: str) -> pd.DataFrame:
        if "data_sources" not in df.columns:
            df["data_sources"] = source
        else:
            df["data_sources"] = df["data_sources"].fillna("") + f",{source}"
            df["data_sources"] = df["data_sources"].str.strip(",").str.replace(",,", ",")
        return df

    @staticmethod
    def _apply_rank_defaults(df: pd.DataFrame) -> pd.DataFrame:
        if "nirf_rank" not in df.columns:
            df["nirf_rank"] = 999
        df["nirf_rank"] = pd.to_numeric(df["nirf_rank"], errors="coerce")
        missing_rank = df["nirf_rank"].isna()
        if missing_rank.any():
            df.loc[missing_rank, "nirf_rank"] = (
                df.loc[missing_rank].index.to_series().rank(method="first").astype(int) + 200
            )
        return df
