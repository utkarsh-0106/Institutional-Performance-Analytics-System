"""Institution Intelligence Profile — a 360-degree view of one institution.

Presentation only. Every measured value on this page comes from
``services.institution_profile_service``, which in turn reuses the existing KPI,
ranking, benchmarking, recommendation and insight engines unchanged.

Editorial rules enforced here:
* no value is invented, estimated or substituted for a missing one;
* a genuine 0.0 is displayed as a score, never as "missing";
* the two identifiers of the same weighted computation (overall performance
  index and composite rank score) are labelled as one measurement;
* the mislabeled ``performance_gaps["placement_vs_state"]`` entry from the
  benchmarking service is deliberately not shown — the state comparison uses
  the service's real ``avg_placement`` instead;
* comparison wording stays descriptive, never causal.
"""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from app.components import ui
from app.components.charts import institution_radar_chart
from app.ui_common import load_data, show_data_banner, widget_key
from services.institution_profile_service import (
    BENCHMARK_NEAR_BAND,
    NOT_PROVIDED,
    benchmark_label,
    build_profile,
    institution_choices,
)

PAGE = "institution_profile"


# --------------------------------------------------------------- formatting --
def _num(value: Optional[float], unit: str = "", decimals: int = 0) -> str:
    """Format a real number, or an explicit unavailable label. Never a fake 0."""
    if value is None:
        return "Data unavailable"
    return f"{value:,.{decimals}f}{unit}"


def _ordinal(rank: Optional[int]) -> str:
    return f"#{rank}" if rank is not None else "Unranked"


# ------------------------------------------------------------------ sections --
def _identity_band(profile: dict) -> None:
    inst = profile["institution"]
    meta = [
        {"text": inst["state"], "icon_name": "map-pin"},
        {"text": profile["ranking_category"], "icon_name": "award"},
        {"text": f"NIRF {_num(inst['nirf_rank'])}", "icon_name": "trending-up"},
        {"text": f"Accreditation {inst['accreditation_grade']}", "icon_name": "shield"},
        {"text": f"Enrollment {_num(inst['student_enrollment'])}", "icon_name": "users"},
        {"text": f"Faculty {_num(inst['faculty_count'])}", "icon_name": "book"},
    ]
    ui.html(ui.monogram(profile["institution_name"], inst["state"], meta))
    st.markdown("")
    ui.stat_grid(
        [
            {
                "label": "National rank",
                "value": _ordinal(profile["institution_rank"]),
                "hint": f"of {profile['institution_count']} ranked institutions",
                "icon_name": "target",
            },
            {
                "label": "Overall performance index",
                "value": f"{profile['ranking']['overall_performance_index']:.2f}",
                "hint": "weighted composite, 0–100",
                "icon_name": "gauge",
            },
            {
                "label": "Placement rate",
                "value": _num(inst["placement_percentage"], "%", 2),
                "hint": "as recorded in the source data",
                "icon_name": "briefcase",
            },
        ],
        per_row=3,
    )


def _kpi_section(profile: dict) -> None:
    items = []
    for kpi in profile["kpis"]:
        items.append({
            "label": kpi["label"],
            "value": kpi["display"],
            "caption": "0–100 normalised score" if kpi["available"] else "no value on record",
            "icon_name": kpi["icon"],
            "show_meter": kpi["available"],
            "tone": ui.score_tone(kpi["value"]),
        })
    ui.kpi_grid(items, per_row=3)


def _radar_section(profile: dict) -> None:
    rows = profile["benchmarks"]
    dims = [(k["key"], k["label"], k["icon"]) for k in profile["kpis"]]
    fig = institution_radar_chart(
        dims,
        [k["value"] for k in profile["kpis"]],
        profile["institution_name"],
        national_values=[r["national"] for r in rows],
        top10_values=[r["top10"] for r in rows],
    )
    covered = sum(1 for r in rows if r["national"] is not None or r["top10"] is not None)
    ui.chart(
        fig,
        key=f"{PAGE}_radar",
        height=460,
        note_text=(
            f"Dashed reference lines appear only where the benchmarking service supplies a value "
            f"({covered} of {len(rows)} indicators have at least one benchmark). "
            "Gaps are absent data, not zero scores."
        ),
    )


def _strengths_section(profile: dict) -> None:
    left, right = st.columns(2, gap="large")

    with left:
        with ui.card("Highest three measured indicators", icon_name="trending-up"):
            if profile["strengths"]:
                for kpi in profile["strengths"]:
                    ui.html(
                        ui.meter(
                            kpi["value"],
                            ui.score_tone(kpi["value"]),
                            label=f"{kpi['label']} · {kpi['display']}",
                        )
                    )
                st.markdown("")
                ui.html(
                    ui.note(
                        "How this is chosen",
                        "The three highest of the six computed KPI scores. "
                        "It is a sort of existing values, not a judgement or a threshold.",
                        tone="info",
                        icon_name="info",
                    )
                )
            else:
                ui.empty_state(
                    "No measured indicators",
                    "None of the six KPI scores hold a value for this institution.",
                    icon_name="inbox",
                )

    with right:
        with ui.card("Lowest three measured indicators", icon_name="activity"):
            if profile["attention"]:
                for kpi in profile["attention"]:
                    ui.html(
                        ui.meter(
                            kpi["value"],
                            ui.score_tone(kpi["value"]),
                            label=f"{kpi['label']} · {kpi['display']}",
                        )
                    )
                st.markdown("")
                ui.html(
                    ui.note(
                        "How this is chosen",
                        "The three lowest of the six computed KPI scores. "
                        "No threshold is applied and no causal claim is implied.",
                        tone="info",
                        icon_name="info",
                    )
                )
            else:
                ui.empty_state(
                    "Nothing to flag",
                    "Fewer than four indicators hold a value, so a lowest three "
                    "cannot be formed without repeating a score.",
                    icon_name="check-circle",
                )


def _benchmark_section(profile: dict) -> None:
    rows = profile["benchmarks"]
    columns = [
        ("institution", "This institution"),
        ("national", "National average"),
        ("top10", "Top 10 performers"),
    ]
    state_row = next((r for r in rows if r.get("state") is not None), None)

    with ui.card("Benchmark comparison", icon_name="compare"):
        ui.html(
            ui.benchmark_table(
                rows,
                columns,
                {"national": benchmark_label, "top10": benchmark_label},
            )
        )
        st.markdown("")
        ui.html(
            ui.note(
                "Coverage and banding",
                f"“{NOT_PROVIDED}” means the benchmarking service holds no value for that "
                f"indicator — nothing is estimated to fill the gap. A position label counts as "
                f"“At benchmark” within ±{BENCHMARK_NEAR_BAND:.1f} point of the reference; "
                "every label is written out, never conveyed by colour alone.",
                tone="info",
                icon_name="info",
            )
        )

    if state_row is not None:
        gap = round(state_row["institution"] - state_row["state"], 2)
        tone, text = benchmark_label(gap)
        ui.html(
            ui.note(
                "State context",
                f"State average placement for {profile['institution']['state']} is "
                f"{state_row['state_display']}% against this institution's "
                f"{state_row['institution_display']}%.",
                tone="accent",
                icon_name="map-pin",
                meta=[
                    {"text": f"Difference {gap:+.2f} points", "tone": tone},
                    {"text": f"Position: {text}"},
                    {"text": "Source: state_benchmark.avg_placement"},
                ],
            )
        )
        st.markdown("")
        ui.html(ui.delta_badge(gap, text, tone))


def _ranking_section(profile: dict) -> None:
    ranking = profile["ranking"]

    left, right = st.columns([3, 2], gap="large")

    with left:
        with ui.card("What drives the composite score", icon_name="sliders"):
            parts = ['<div class="ipa-contrib">']
            for row in sorted(
                ranking["rows"],
                key=lambda r: (r["contribution"] is not None, r["contribution"] or 0),
                reverse=True,
            ):
                if row["contribution"] is None:
                    parts.append(
                        '<div class="ipa-contrib-row">'
                        f'<span class="ipa-contrib-name">{ui.esc(row["label"])}</span>'
                        '<span class="ipa-contrib-val">Data unavailable</span></div>'
                    )
                    continue
                parts.append(
                    '<div class="ipa-contrib-row">'
                    f'<span class="ipa-contrib-name">{ui.esc(row["label"])}'
                    f' <span class="ipa-contrib-w">{row["weight"] * 100:.0f}% weight</span></span>'
                    f'<span class="ipa-contrib-val">{row["contribution"]:.2f} pts</span>'
                    f'<span class="ipa-contrib-meta">{row["score"]:.2f} × {row["weight"] * 100:.0f}%</span>'
                    "</div>"
                )
            parts.append("</div>")
            ui.html("".join(parts))
            st.markdown("")
            ui.html(
                ui.note(
                    "Two names, one measurement",
                    "Overall performance index and composite rank score are both "
                    "produced by the same weighted index in the ranking engine, so they "
                    "carry identical values. They are shown as one measurement with two "
                    "labels, not as two independent metrics.",
                    tone="info",
                    icon_name="info",
                )
            )

    with right:
        with ui.card("Configured ranking weights", icon_name="sliders"):
            ui.weight_list(
                [(k.replace("_", " ").title(), v) for k, v in ranking["weights"].items()],
                suffix=" weight",
            )
            st.markdown("")
            ui.html(
                ui.note(
                    "Contribution vs composite",
                    f"Each KPI score multiplied by its configured weight sums to "
                    f"{ranking['contribution_total']:.2f}, which is the engine's own composite "
                    f"rank score of {ranking['composite_rank_score']:.2f}. Weights are read from "
                    f"{ranking['weight_source']} and are not redefined here.",
                    tone="success",
                    icon_name="check-circle",
                )
            )


def _recommendations_section(profile: dict) -> None:
    recs = profile["recommendations"]
    with ui.card(
        f"Existing recommendations · {len(recs)}",
        icon_name="lightbulb",
    ):
        if not recs:
            ui.empty_state(
                "No recommendations on record",
                "The recommendation engine has not produced any rules for this institution.",
                icon_name="inbox",
            )
            return
        cols = st.columns(2, gap="medium")
        for idx, rec in enumerate(recs):
            with cols[idx % 2]:
                ui.html(
                    ui.priority_card(
                        rec["priority"] or "medium",
                        rec["category"],
                        rec["message"],
                    )
                )
        st.markdown("")
        ui.html(
            ui.note(
                "Unchanged logic",
                "These are the recommendation engine's own rules and priorities for this "
                "institution, presented verbatim. No new rule is inferred on this page.",
                tone="info",
                icon_name="info",
            )
        )


def _insights_section(profile: dict) -> None:
    insights = profile["insights"]
    if not insights:
        with ui.card("Generated insights", icon_name="sparkles"):
            ui.empty_state(
                "No insights available",
                "The insights service returned nothing for this institution.",
                icon_name="inbox",
            )
        return

    with ui.card(f"Generated insights · {len(insights)}", icon_name="sparkles"):
        for text in insights:
            ui.html(ui.insight_card(text))
        st.markdown("")
        ui.html(
            ui.note(
                "Generated, not endorsed",
                "These statements are produced by the insights service from the same "
                "measured values shown above. They describe the data and do not assert causes.",
                tone="info",
                icon_name="info",
            )
        )


def _quality_section(profile: dict) -> None:
    quality = profile["completeness"]
    sources = profile["data_sources"]
    kind = profile["provenance_kind"]

    left, right = st.columns([3, 2], gap="large")

    with left:
        with ui.card("Data quality", icon_name="check-circle"):
            pct = quality["percent"]
            tone = "success" if pct == 100 else ("warning" if pct >= 80 else "critical")
            ui.html(ui.quality_indicator(tone, f"{pct:.0f}% of required fields populated"))
            st.markdown("")
            ui.html(f'<p class="ipa-formula">{ui.esc(quality["formula"])}</p>')
            st.markdown("")
            ui.html(
                ui.profile_fields([
                    (None, "Required fields populated", f"{quality['populated']} of {quality['total']}"),
                    (None, "Fields without a value", f"{len(quality['missing'])}"),
                    ("info", "Meaning", quality["meaning"]),
                ])
            )
            if quality["missing"]:
                st.markdown("")
                ui.html(
                    ui.note(
                        "Fields awaiting a value",
                        ", ".join(m["label"] for m in quality["missing"]),
                        tone="warning",
                        icon_name="alert-triangle",
                    )
                )
            else:
                st.markdown("")
                ui.html(
                    ui.note(
                        "Complete record",
                        "Every required field holds a value for this institution, so the "
                        "indicators above are computed from a full record.",
                        tone="success",
                        icon_name="check-circle",
                    )
                )

    with right:
        with ui.card("Data provenance", icon_name="database"):
            if kind == "per-institution":
                ui.html(
                    ui.profile_fields([(None, "Source", s) for s in sources])
                )
                st.markdown("")
                ui.html(
                    ui.note(
                        "Recorded for this institution",
                        "Taken from the data_sources column produced by the ETL stage. "
                        "The database does not store that column, so no schema change "
                        "was needed to display it.",
                        tone="accent",
                        icon_name="database",
                    )
                )
            else:
                ui.html(
                    ui.note(
                        "Dataset-level sources",
                        "The merged ETL output could not be read, so the pipeline's "
                        "configured sources are listed instead:",
                        tone="warning",
                        icon_name="alert-triangle",
                        meta=[{"text": f"{s} (dataset-level)"} for s in sources],
                    )
                )


def _source_data_section(profile: dict) -> None:
    inst = profile["institution"]
    rows = profile["kpis"]
    with st.expander("View recorded source data", expanded=False):
        st.markdown("**Record as stored**")
        ui.html(
            "<div class='ipa-pfields'>"
            + ui.profile_fields([
                ("map-pin", "Institution", profile["institution_name"]),
                ("map-pin", "State", inst["state"]),
                ("users", "Student enrollment", _num(inst["student_enrollment"])),
                ("book", "Faculty count", _num(inst["faculty_count"])),
                ("briefcase", "Placement percentage", _num(inst["placement_percentage"], "%", 2)),
                ("flask", "Research publications", _num(inst["research_publications"])),
                ("layers", "Infrastructure score", _num(inst["infrastructure_score"])),
                ("shield", "Accreditation grade", inst["accreditation_grade"]),
                ("trending-up", "NIRF rank", _num(inst["nirf_rank"])),
                ("target", "Institution rank", _ordinal(profile["institution_rank"])),
                ("award", "Ranking category", profile["ranking_category"]),
            ])
            + "</div>"
        )
        st.markdown("")
        st.markdown("**Computed indicators**")
        ui.html(
            "<div class='ipa-pfields'>"
            + ui.profile_fields(
                [(r["icon"], r["label"], r["display"]) for r in rows]
                + [
                    ("gauge", "Overall performance index",
                     f"{profile['ranking']['overall_performance_index']:.2f}"),
                    ("sliders", "Composite rank score",
                     f"{profile['ranking']['composite_rank_score']:.2f}"),
                ]
            )
            + "</div>"
        )
        if profile["ml_prediction"]:
            ml = profile["ml_prediction"]
            st.markdown("")
            st.markdown("**Existing model output**")
            ui.html(
                "<div class='ipa-pfields'>"
                + ui.profile_fields([
                    ("cpu", "Predicted performance score",
                     _num(ml["predicted_performance_score"], "", 2)),
                    ("shield", "Accreditation readiness", ml["accreditation_readiness"]),
                    ("target", "Predicted ranking category", ml["ranking_category_pred"]),
                ])
                + "</div>"
            )


# --------------------------------------------------------------------- page --
def render() -> None:
    data = load_data()
    show_data_banner(data)

    inst_df = data.get("institutions")
    choices = institution_choices(inst_df)

    if not choices:
        ui.page_header(
            "Institution Intelligence",
            "A single-institution view assembled from the existing analytics engines",
        )
        ui.empty_state(
            "No institutions available",
            "The dataset contains no institutions to profile yet. Run the ETL "
            "pipeline from Data Management to load records.",
            icon_name="inbox",
        )
        return

    linked = None
    user = st.session_state.get("user") or {}
    if isinstance(user, dict):
        linked = user.get("linked_institution")
    requested = st.session_state.get("institution_profile_selection")
    preferred = requested if requested in choices else linked
    default = choices.index(preferred) if preferred in choices else 0

    selected = st.selectbox(
        "Select an institution",
        choices,
        index=default,
        key=widget_key(PAGE, "institution"),
        help="All 165 institutions in the current dataset are selectable.",
    )

    ui.page_header(
        "Institution Intelligence",
        "A single-institution view assembled from the existing analytics engines",
        right=ui.badge(f"{len(choices)} institutions", "primary", "building"),
    )

    profile = build_profile(selected, data)
    if not profile.get("found"):
        ui.empty_state(
            "No matching record",
            f"{selected} is listed in the selector but has no institution or KPI record "
            "in the current dataset.",
            icon_name="alert-triangle",
        )
        return

    profile["institution_count"] = len(choices)
    rank_total = data.get("kpis")
    if rank_total is not None and not rank_total.empty:
        profile["institution_count"] = len(rank_total)

    _identity_band(profile)
    ui.divider()

    ui.html(ui.section_head("Performance indicators", "Six normalised scores, 0–100", "gauge"))
    _kpi_section(profile)
    st.markdown("")

    ui.html(ui.section_head("Indicator profile", "Institution against available benchmarks", "chart-bar"))
    _radar_section(profile)
    ui.divider()

    ui.html(
        ui.section_head(
            "Where this institution stands",
            "Ordered by the six measured indicator values",
            "trending-up",
        )
    )
    _strengths_section(profile)
    ui.divider()

    ui.html(
        ui.section_head(
            "Benchmark comparison",
            "Only indicators the benchmarking service covers are compared",
            "compare",
        )
    )
    _benchmark_section(profile)
    ui.divider()

    ui.html(
        ui.section_head(
            "Ranking contribution",
            "How the configured weights shape the composite score",
            "sliders",
        )
    )
    _ranking_section(profile)
    ui.divider()

    ui.html(
        ui.section_head(
            "Recommendations",
            "The recommendation engine's own output for this institution",
            "lightbulb",
        )
    )
    _recommendations_section(profile)
    ui.divider()

    ui.html(
        ui.section_head(
            "Generated insights",
            "Narrative produced by the insights service from the values above",
            "sparkles",
        )
    )
    _insights_section(profile)
    ui.divider()

    ui.html(
        ui.section_head(
            "Data quality and provenance",
            "Completeness of the record and where the data came from",
            "database",
        )
    )
    _quality_section(profile)
    ui.divider()

    _source_data_section(profile)
    st.markdown("")
    st.caption("Institutional Performance Analytics | Institution Intelligence Module")
