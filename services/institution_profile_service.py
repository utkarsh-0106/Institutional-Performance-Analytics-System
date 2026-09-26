"""Assembly layer for the Institution Intelligence Profile.

This module is an orchestrator, not a second analytics engine. It contains
**no** KPI, ranking, benchmark or recommendation logic. Every measured value it
returns is produced by the existing engines and read straight from their output:

    BenchmarkingService.compare_institution()   -> benchmarks and gaps
    InsightsService.generate_institution_insights() -> narrative text
    RecommendationRepository rows               -> priority + message
    RANKING_WEIGHTS (config.settings)           -> weighting for contribution

The only logic added here is presentation-neutral assembly:

* per-record field completeness (a count of populated fields, with the formula
  documented for the UI — it carries no performance meaning)
* ``data_sources`` provenance lookup (the column exists in the merged ETL
  output but is not persisted in the database, so no schema change is needed)
* ordering the six existing KPI scores to separate the strongest three from the
  three lowest. This is a sort, not a judgement: no threshold is introduced and
  the recommendation engine's thresholds are deliberately not reused.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable, Optional

import pandas as pd

from config.settings import MERGED_DATASET_PATH, RANKING_WEIGHTS
from services.benchmarking_service import BenchmarkingService
from services.insights_service import InsightsService

# The six KPI dimensions, in the column order produced by KPIEngine.
# (column, display label, icon name)
KPI_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("academic_score", "Academic", "book"),
    ("research_score", "Research", "flask"),
    ("placement_score", "Placement", "briefcase"),
    ("infrastructure_score_kpi", "Infrastructure", "layers"),
    ("faculty_score", "Faculty", "users"),
    ("accreditation_score", "Accreditation", "award"),
)

# Which RANKING_WEIGHTS key weights each KPI column.
KPI_WEIGHT_KEYS: dict[str, str] = {
    "academic_score": "academic",
    "research_score": "research",
    "placement_score": "placement",
    "infrastructure_score_kpi": "infrastructure",
    "faculty_score": "faculty",
    "accreditation_score": "accreditation",
}

# Fields whose presence defines record completeness. This is config.settings
# REQUIRED_COLUMNS plus "state", which the ETL adds. Completeness means "this
# field is populated" — it is never a statement about institutional quality.
COMPLETENESS_FIELDS: tuple[tuple[str, str], ...] = (
    ("institution_name", "Institution name"),
    ("state", "State"),
    ("student_enrollment", "Student enrollment"),
    ("faculty_count", "Faculty count"),
    ("placement_percentage", "Placement percentage"),
    ("research_publications", "Research publications"),
    ("infrastructure_score", "Infrastructure score"),
    ("accreditation_grade", "Accreditation grade"),
    ("nirf_rank", "NIRF rank"),
)

# Benchmark keys the existing service actually provides, per KPI column.
# Anything absent is reported as unavailable rather than estimated.
NATIONAL_BENCHMARK_KEYS = {
    "academic_score": "avg_academic_score",
    "research_score": "avg_research_score",
    "placement_score": "avg_placement_score",
}
TOP10_BENCHMARK_KEYS = {
    "academic_score": "avg_academic_score",
    "research_score": "avg_research_score",
    "placement_score": "avg_placement_score",
    "infrastructure_score_kpi": "avg_infrastructure_score",
    "faculty_score": "avg_faculty_score",
}

NOT_PROVIDED = "Not provided by current benchmark"

# Display-only tolerance for the above/at/below benchmark label. It is shown on
# screen next to the comparison table so the banding is never implicit.
BENCHMARK_NEAR_BAND = 1.0

# Dataset-level fallback provenance, used only when the merged ETL output is
# unavailable. Labelled as dataset-level so it is not read as per-institution.
PIPELINE_SOURCES = (
    "NIRF rankings",
    "AISHE statistics",
    "NAAC accreditation",
    "UGC institutions",
)


# ------------------------------------------------------------------ helpers --
def is_populated(value: Any) -> bool:
    """True when a field holds a usable value.

    ``0`` and ``0.0`` are genuine measurements in this data model (a normalised
    score can legitimately bottom out at zero), so they count as populated.
    Only ``None``/``NaN``/blank text count as absent.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    try:
        return not pd.isna(value)
    except (TypeError, ValueError):
        return True


def _as_float(value: Any) -> Optional[float]:
    """Return a float when the value is populated, else None (never 0.0-stand-in)."""
    if not is_populated(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def _provenance_index() -> dict[str, str]:
    """Map institution name -> data_sources, read from the merged ETL output.

    The ``data_sources`` column is produced by the ETL and stored in
    data/processed/merged_institutions.csv; it is intentionally not part of the
    database schema, so it is read from that file instead of adding a column.
    """
    path = MERGED_DATASET_PATH
    if not path.exists():
        return {}
    try:
        frame = pd.read_csv(path, usecols=["institution_name", "data_sources"])
    except (ValueError, OSError):
        return {}
    if frame.empty:
        return {}
    return {
        str(name): str(src)
        for name, src in zip(frame["institution_name"], frame["data_sources"])
        if is_populated(name) and is_populated(src)
    }


def data_sources_for(institution_name: str) -> tuple[list[str], str]:
    """Return (source labels, provenance kind) for one institution."""
    raw = _provenance_index().get(institution_name)
    if raw:
        return [part.strip() for part in str(raw).split(";") if part.strip()], "per-institution"
    return list(PIPELINE_SOURCES), "dataset-level"


# ------------------------------------------------------------- completeness --
def field_completeness(inst_row: pd.Series) -> dict:
    """Per-record completeness of the required fields.

    completeness = populated required fields / total required fields x 100

    This measures whether data exists for the institution. It is explicitly not
    a performance score and must never be presented as one.
    """
    available, missing = [], []
    for column, label in COMPLETENESS_FIELDS:
        if is_populated(inst_row.get(column)):
            available.append({"field": column, "label": label})
        else:
            missing.append({"field": column, "label": label})
    total = len(COMPLETENESS_FIELDS)
    return {
        "available": available,
        "missing": missing,
        "total": total,
        "populated": len(available),
        "percent": round((len(available) / total) * 100, 1) if total else 0.0,
        "formula": "populated required fields / total required fields x 100",
        "meaning": "Share of required record fields that hold a value. Not a performance score.",
    }


# ---------------------------------------------------------------- KPI blocks --
def kpi_breakdown(kpi_row: pd.Series) -> list[dict]:
    """The six existing KPI scores, with honest availability flags.

    A genuine 0.0 is reported as 0.0. Only a genuinely absent value is reported
    as unavailable, and it is then excluded from chart traces.
    """
    breakdown = []
    for column, label, icon_name in KPI_DIMENSIONS:
        raw = kpi_row.get(column)
        value = _as_float(raw)
        breakdown.append({
            "key": column,
            "label": label,
            "icon": icon_name,
            "value": value,
            "display": f"{value:.2f}" if value is not None else "Data unavailable",
            "available": value is not None,
        })
    return breakdown


def classify_kpis(breakdown: list[dict], top_n: int = 3) -> tuple[list[dict], list[dict]]:
    """Split the measured KPIs into the highest three and lowest three.

    Pure ordering of values already computed by KPIEngine — no threshold, no
    score interpretation, and the recommendation engine's thresholds are not
    used here.
    """
    measured = sorted(
        (k for k in breakdown if k["available"]),
        key=lambda k: k["value"],
        reverse=True,
    )
    if not measured:
        return [], []
    split = min(top_n, len(measured))
    strengths, attention = measured[:split], measured[split:]
    if not attention:  # fewer than 2*top_n values measured — do not double-report
        return strengths, []
    return strengths, attention


def ranking_contribution(kpi_row: pd.Series) -> dict:
    """Weighted contribution of each KPI, using the real RANKING_WEIGHTS.

    contribution = KPI score x its ranking weight. The sum is reported next to
    the engine's own ``composite_rank_score`` so the two can be compared; the
    weights are read from config and never redefined.
    """
    rows, total = [], 0.0
    for column, label, _ in KPI_DIMENSIONS:
        value = _as_float(kpi_row.get(column))
        weight_key = KPI_WEIGHT_KEYS[column]
        weight = float(RANKING_WEIGHTS[weight_key])
        if value is None:
            rows.append({
                "key": column, "label": label, "weight_key": weight_key,
                "weight": weight, "score": None, "contribution": None,
            })
            continue
        contribution = round(value * weight, 2)
        total += contribution
        rows.append({
            "key": column, "label": label, "weight_key": weight_key,
            "weight": weight, "score": value, "contribution": contribution,
        })

    composite = _as_float(kpi_row.get("composite_rank_score"))
    return {
        "rows": rows,
        "weights": {k: float(RANKING_WEIGHTS[v]) for k, v in KPI_WEIGHT_KEYS.items()},
        "weight_source": "config.settings.RANKING_WEIGHTS",
        "contribution_total": round(total, 2),
        "composite_rank_score": composite,
        "overall_performance_index": _as_float(kpi_row.get("overall_performance_index")),
        # RankingEngine sets composite_rank_score = KPIEngine.weighted_index(...),
        # so the two columns are the same computation by construction.
        "opi_is_composite": composite is not None
        and _as_float(kpi_row.get("overall_performance_index")) == composite,
    }


# ----------------------------------------------------------------- benchmarks --
def benchmark_rows(breakdown: list[dict], comparison: dict) -> list[dict]:
    """Institution vs national vs top-10 for each KPI the service actually covers.

    Only benchmark values present in the BenchmarkingService output are used.
    Missing coverage is reported as unavailable, never estimated.
    """
    national = comparison.get("national_benchmark") or {}
    top10 = comparison.get("top_performer_benchmark") or {}
    state = comparison.get("state_benchmark") or {}

    rows = []
    for kpi in breakdown:
        value = kpi["value"]
        nat_key = NATIONAL_BENCHMARK_KEYS.get(kpi["key"])
        top_key = TOP10_BENCHMARK_KEYS.get(kpi["key"])
        nat_val = _as_float(national.get(nat_key)) if nat_key else None
        top_val = _as_float(top10.get(top_key)) if top_key else None

        # State averages are raw metrics, not KPI scores. Only placement has a
        # genuinely same-unit state average (avg_placement is a percentage, and
        # placement_score is the placement percentage).
        state_val = None
        if kpi["key"] == "placement_score" and is_populated(state.get("avg_placement")):
            state_val = _as_float(state.get("avg_placement"))

        rows.append({
            "key": kpi["key"],
            "label": kpi["label"],
            "icon": kpi["icon"],
            "institution": value,
            "national": nat_val,
            "top10": top_val,
            "state": state_val,
            "institution_display": kpi["display"],
            "national_display": f"{nat_val:.2f}" if nat_val is not None else NOT_PROVIDED,
            "top10_display": f"{top_val:.2f}" if top_val is not None else NOT_PROVIDED,
            "state_display": f"{state_val:.2f}" if state_val is not None else None,
            "national_delta": _delta(value, nat_val),
            "top10_delta": _delta(value, top_val),
        })
    return rows


def _delta(value: Optional[float], benchmark: Optional[float]) -> Optional[float]:
    if value is None or benchmark is None:
        return None
    return round(value - benchmark, 2)


def benchmark_label(delta: Optional[float], band: float = BENCHMARK_NEAR_BAND) -> tuple[str, str]:
    """(tone, text) for a benchmark delta. Text always accompanies the colour."""
    if delta is None:
        return "neutral", "Not available"
    if delta > band:
        return "success", "Above benchmark"
    if delta < -band:
        return "critical", "Below benchmark"
    return "neutral", "At benchmark"


# ------------------------------------------------------------------ build ----
def build_profile(institution_name: str, data: dict) -> dict:
    """Assemble the full profile for one institution from already-loaded frames.

    ``data`` is the dict returned by ``app.ui_common.load_data()``.
    """
    inst_df: pd.DataFrame = data.get("institutions", pd.DataFrame())
    kpi_df: pd.DataFrame = data.get("kpis", pd.DataFrame())
    rec_df: pd.DataFrame = data.get("recommendations", pd.DataFrame())
    ml_df: Optional[pd.DataFrame] = data.get("predictions")
    if ml_df is None:
        ml_df = pd.DataFrame()

    if inst_df.empty or kpi_df.empty:
        return {"found": False, "institution_name": institution_name}

    inst_rows = inst_df[inst_df["institution_name"] == institution_name]
    kpi_rows = kpi_df[kpi_df["institution_name"] == institution_name]
    if inst_rows.empty or kpi_rows.empty:
        return {"found": False, "institution_name": institution_name}

    inst_row = inst_rows.iloc[0]
    kpi_row = kpi_rows.iloc[0]

    # Existing engines, reused as-is.
    comparison = BenchmarkingService.compare_institution(institution_name, inst_df, kpi_df)
    insights = InsightsService.generate_institution_insights(
        institution_name, inst_df, kpi_df, ml_df if not ml_df.empty else None
    )

    breakdown = kpi_breakdown(kpi_row)
    strengths, attention = classify_kpis(breakdown)

    recommendations = []
    if not rec_df.empty:
        subset = rec_df[rec_df["institution_name"] == institution_name]
        order = {"high": 0, "medium": 1, "low": 2}
        recommendations = [
            {
                "category": str(row.get("category", "")),
                "message": str(row.get("message", "")),
                "priority": str(row.get("priority", "")).lower(),
            }
            for _, row in subset.sort_values(
                "priority", key=lambda s: s.map(order).fillna(3)
            ).iterrows()
        ]

    ml_prediction = None
    if not ml_df.empty:
        ml_rows = ml_df[ml_df["institution_name"] == institution_name]
        if not ml_rows.empty:
            row = ml_rows.iloc[0]
            ml_prediction = {
                "predicted_performance_score": _as_float(row.get("predicted_performance_score")),
                "accreditation_readiness": str(row.get("accreditation_readiness", "") or "—"),
                "ranking_category_pred": str(row.get("ranking_category_pred", "") or "—"),
            }

    sources, provenance_kind = data_sources_for(institution_name)

    rank = kpi_row.get("institution_rank")
    return {
        "found": True,
        "institution_name": institution_name,
        "institution": {
            "id": inst_row.get("id"),
            "state": str(inst_row.get("state", "Unknown") or "Unknown"),
            "student_enrollment": _as_float(inst_row.get("student_enrollment")),
            "faculty_count": _as_float(inst_row.get("faculty_count")),
            "placement_percentage": _as_float(inst_row.get("placement_percentage")),
            "research_publications": _as_float(inst_row.get("research_publications")),
            "infrastructure_score": _as_float(inst_row.get("infrastructure_score")),
            "accreditation_grade": str(inst_row.get("accreditation_grade", "—") or "—"),
            "nirf_rank": _as_float(inst_row.get("nirf_rank")),
        },
        "kpis": breakdown,
        "strengths": strengths,
        "attention": attention,
        "benchmarks": benchmark_rows(breakdown, comparison) if comparison else [],
        "benchmarks_available": bool(comparison),
        "ranking": ranking_contribution(kpi_row),
        "institution_rank": int(rank) if is_populated(rank) else None,
        "ranking_category": str(kpi_row.get("ranking_category", "") or "—"),
        "recommendations": recommendations,
        "insights": [i for i in (insights or []) if i],
        "ml_prediction": ml_prediction,
        "completeness": field_completeness(inst_row),
        "data_sources": sources,
        "provenance_kind": provenance_kind,
        "using_sample": bool(data.get("using_sample")),
    }


def institution_choices(inst_df: pd.DataFrame) -> list[str]:
    """Sorted institution names for the selector — never a hardcoded list."""
    if inst_df is None or inst_df.empty or "institution_name" not in inst_df.columns:
        return []
    return sorted({str(n) for n in inst_df["institution_name"].dropna() if str(n).strip()})
