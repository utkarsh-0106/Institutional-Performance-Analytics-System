"""Reusable presentation primitives for the Institutional Intelligence UI.

Everything in this module is presentation-only: it renders HTML/CSS through
Streamlit and never touches data, KPIs, rankings, models or the database.

The card pattern relies on a zero-height marker element rendered inside a
``st.container()``. ``app/theme.css`` uses ``:has()`` to turn that container
into a card surface, which keeps Streamlit's own widgets as real, interactive
children (no hand-rolled wrapper divs).
"""
from __future__ import annotations

import base64
import html as _html
import inspect
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = APP_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
ICONS_DIR = ASSETS_DIR / "icons"
THEME_CSS_PATH = APP_DIR / "theme.css"

CARD_MARK_CLASS = "ipa-card-mark"

TONES = ("primary", "accent", "success", "warning", "critical", "neutral")

# Mirrors of the CSS tokens, for Python-side use (chart colours, aria text).
COLORS = {
    "ink": "#0b1f3a",
    "primary": "#1e4e8c",
    "primary_600": "#2f6fad",
    "primary_400": "#5b8fc7",
    "accent": "#2aa7b8",
    "success": "#0f8a5f",
    "warning": "#b45309",
    "critical": "#b91c1c",
    "text": "#0f1b2d",
    "muted": "#5b6b7c",
    "grid": "#e8edf3",
    "surface": "#ffffff",
    "canvas": "#f4f6fa",
}

# Tones for a 0-100 score. Purely presentational banding of an existing value.
SCORE_TONES = ((75, "success"), (55, "primary"), (40, "warning"), (0, "critical"))


def score_tone(value: Optional[float]) -> str:
    """Map an existing 0-100 score to a semantic tone (no value is altered)."""
    if value is None:
        return "neutral"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "neutral"
    for threshold, tone in SCORE_TONES:
        if v >= threshold:
            return tone
    return "critical"


# ----------------------------------------------------------------- assets --
def asset_path(filename: str) -> str:
    """Resolve an asset, preferring an optimised WebP derivative when present."""
    stem = Path(filename).stem
    for candidate in (IMAGES_DIR / f"{stem}.webp", IMAGES_DIR / filename, ASSETS_DIR / filename):
        if candidate.exists():
            return str(candidate)
    return str(ASSETS_DIR / filename)


@lru_cache(maxsize=256)
def _read_icon(name: str) -> str:
    path = ICONS_DIR / f"{name}.svg"
    if not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8")
    return svg.replace('width="24" height="24"', "").strip()


def icon(name: str, size: int = 18, css_class: str = "") -> str:
    """Inline SVG for a local icon. Returns '' when the icon is unknown."""
    svg = _read_icon(name)
    if not svg:
        return ""
    cls = f' class="{css_class}"' if css_class else ""
    return svg.replace("<svg ", f'<svg{cls} width="{size}" height="{size}" ', 1)


@lru_cache(maxsize=64)
def _encode_image(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    mime = "image/webp" if path.suffix.lower() == ".webp" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def image_data_uri(filename: str) -> str:
    """Base64 data URI for a local image (memoised — no re-encode per rerun)."""
    return _encode_image(asset_path(filename))


# ------------------------------------------------------------------- html --
def esc(value: Any) -> str:
    return _html.escape("" if value is None else str(value), quote=True)


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def _tone(value: Optional[str], default: str = "neutral") -> str:
    return value if value in TONES else default


def _pick(func, options: Mapping[str, Any]) -> dict:
    """Drop unknown keys so a stray field in a view cannot crash a page."""
    allowed = set(inspect.signature(func).parameters)
    return {k: v for k, v in dict(options).items() if k in allowed}


# ----------------------------------------------------------------- layout --
def _card_mark(variant: str = "default") -> str:
    attr = "" if variant == "default" else f' data-card="{esc(variant)}"'
    return f'<div class="{CARD_MARK_CLASS}"{attr} style="height:0"></div>'


@contextmanager
def card(
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    kicker_text: Optional[str] = None,
    icon_name: Optional[str] = None,
    variant: str = "default",
    right: Optional[str] = None,
) -> Iterator[Any]:
    """A titled card surface that contains real Streamlit widgets.

    Use as a context manager; everything rendered inside stays interactive.
    """
    with st.container() as container:
        html(_card_mark(variant))
        if title or right:
            html(section_head(title or "", subtitle=subtitle, icon_name=icon_name,
                              kicker_text=kicker_text, right=right))
        yield container


def section_head(
    title: str,
    subtitle: Optional[str] = None,
    icon_name: Optional[str] = None,
    kicker_text: Optional[str] = None,
    right: Optional[str] = None,
) -> str:
    """HTML for a section heading (icon + title, optional kicker/description)."""
    ic = icon(icon_name, 17) if icon_name else ""
    head = f'<div class="ipa-section-head"><div><h3>{ic}<span>{esc(title)}</span></h3>'
    if subtitle:
        head += f"<p>{esc(subtitle)}</p>"
    head += "</div>"
    if right:
        head += f'<div class="ipa-row">{right}</div>'
    head += "</div>"
    if kicker_text:
        head = f'<div class="ipa-kicker">{esc(kicker_text)}</div>' + head
    return head


def page_header(
    title: str,
    subtitle: str = "",
    kicker_text: Optional[str] = None,
    right: Optional[str] = None,
) -> None:
    """Standard page header: kicker, title, description, optional right slot."""
    parts = ['<div class="ipa-page-header"><div>']
    if kicker_text:
        parts.append(f'<div class="ipa-kicker">{esc(kicker_text)}</div>')
    parts.append(f"<h1>{esc(title)}</h1>")
    if subtitle:
        parts.append(f"<p>{esc(subtitle)}</p>")
    parts.append("</div>")
    if right:
        parts.append(f'<div class="ipa-row">{right}</div>')
    parts.append("</div>")
    html("".join(parts))


def divider(tight: bool = False) -> None:
    html('<hr class="ipa-divider' + (" ipa-divider--tight" if tight else "") + '"/>')


def hero(
    title: str,
    description: str = "",
    image_file: Optional[str] = None,
    kicker_text: str = "Institutional Intelligence",
    min_height: int = 320,
) -> None:
    """Full-bleed image hero with a legibility scrim."""
    uri = image_data_uri(image_file) if image_file else ""
    background = (
        f"linear-gradient(90deg, rgba(6,15,30,.90) 0%, rgba(11,31,58,.74) 46%, rgba(11,31,58,.30) 100%), url('{uri}')"
        if uri
        else "linear-gradient(135deg, #0b1f3a, #1e4e8c)"
    )
    html(
        f'<div class="ipa-hero" style="background-image:{background};background-size:cover;'
        f'background-position:center;min-height:{min_height}px">'
        f'<div class="ipa-hero-overlay">'
        f'<div class="ipa-kicker">{esc(kicker_text)}</div>'
        f"<h1>{esc(title)}</h1>"
        + (f"<p>{esc(description)}</p>" if description else "")
        + "</div></div>"
    )


# ------------------------------------------------------------------ tiles --
def meter(pct: float, tone: str = "primary", label: str = "") -> str:
    """Labelled progress meter. Text label keeps it accessible (not colour-only)."""
    try:
        value = max(0.0, min(100.0, float(pct)))
    except (TypeError, ValueError):
        value = 0.0
    aria = f' role="meter" aria-valuenow="{value:.0f}" aria-valuemin="0" aria-valuemax="100"'
    if label:
        aria += f' aria-label="{esc(label)}"'
    return (
        f'<div class="ipa-meter" data-tone="{_tone(tone, "primary")}"{aria}>'
        f'<span style="width:{value:.1f}%"></span></div>'
    )


def stat_tile(
    label: str,
    value: Any,
    unit: str = "",
    hint: str = "",
    delta: str = "",
    tone: str = "primary",
    icon_name: Optional[str] = None,
) -> str:
    ic = icon(icon_name, 14) if icon_name else ""
    unit_html = f"<small>{esc(unit)}</small>" if unit else ""
    parts = [
        f'<div class="ipa-stat" data-tone="{_tone(tone)}">',
        f'<div class="ipa-stat-label">{ic}<span>{esc(label)}</span></div>',
        f'<div class="ipa-stat-value">{esc(value)}{unit_html}</div>',
    ]
    if delta:
        parts.append(f'<div class="ipa-stat-delta" data-tone="{_tone(tone, "neutral")}">{esc(delta)}</div>')
    if hint:
        parts.append(f'<div class="ipa-stat-hint">{esc(hint)}</div>')
    parts.append("</div>")
    return "".join(parts)


def stat_grid(items: Sequence[Mapping[str, Any]], per_row: Optional[int] = None) -> None:
    """Responsive grid of stat tiles (auto-fits, so no fixed widths)."""
    if not items:
        return
    html('<div class="ipa-stat-grid">' + "".join(stat_tile(**_pick(stat_tile, i)) for i in items) + "</div>")


def kpi_tile(
    label: str,
    value: Any,
    maximum: float = 100.0,
    unit: str = "",
    caption: str = "",
    tone: Optional[str] = None,
    icon_name: Optional[str] = None,
    show_meter: bool = True,
) -> str:
    """KPI card: label, value, interpretation and a progress visualisation."""
    try:
        pct = (float(value) / float(maximum)) * 100.0 if float(maximum) else 0.0
    except (TypeError, ValueError, ZeroDivisionError):
        pct = 0.0
    resolved = _tone(tone, score_tone(pct)) if tone else score_tone(pct)
    ic = icon(icon_name, 15) if icon_name else ""
    unit_html = f"<small>{esc(unit)}</small>" if unit else ""
    parts = [
        '<div class="ipa-kpi">',
        f'<div class="ipa-kpi-head">{ic}<span>{esc(label)}</span></div>',
        f'<div class="ipa-kpi-value">{esc(value)}{unit_html}</div>',
    ]
    if show_meter:
        parts.append(meter(pct, resolved, label=f"{label} — share of maximum"))
    if caption:
        parts.append(f'<div class="ipa-stat-hint">{esc(caption)}</div>')
    parts.append("</div>")
    return "".join(parts)


def kpi_grid(items: Sequence[Mapping[str, Any]], per_row: Optional[int] = None) -> None:
    """Grid of KPI tiles; falls back to a plain responsive two-column grid."""
    if not items:
        return
    html('<div class="ipa-two-col">' + "".join(kpi_tile(**_pick(kpi_tile, i)) for i in items) + "</div>")


def weight_list(rows: Iterable[Sequence[Any]], suffix: str = "") -> None:
    """Horizontal weight bars, e.g. the live ranking weights from config."""
    parts = ['<div class="ipa-weights">']
    for row in rows:
        label, value = row[0], row[1]
        try:
            pct = max(0.0, min(100.0, float(value) * 100.0))
        except (TypeError, ValueError):
            pct = 0.0
        parts.append(
            '<div class="ipa-weight">'
            f'<span class="ipa-weight-name">{esc(label)}</span>'
            f'<span class="ipa-weight-val">{pct:.0f}%{esc(suffix)}</span>'
            + meter(pct, "primary", label=f"{label} weight")
            + "</div>"
        )
    parts.append("</div>")
    html("".join(parts))


# ------------------------------------------------------- content surfaces --
def badge(text: str, tone: str = "neutral", icon_name: Optional[str] = None) -> str:
    ic = icon(icon_name, 12) if icon_name else ""
    return f'<span class="ipa-badge" data-tone="{_tone(tone)}">{ic}{esc(text)}</span>'


def badges(items: Sequence[Mapping[str, Any]]) -> str:
    return "".join(badge(**_pick(badge, i)) for i in items)


def note(
    title: str = "",
    body: str = "",
    tone: str = "info",
    icon_name: Optional[str] = None,
    meta: Sequence[Mapping[str, Any]] = (),
) -> str:
    """Bordered content card with an icon rail, title, body and meta badges."""
    ic = icon(icon_name or {"info": "info", "accent": "sparkles"}.get(tone, "info"), 16)
    parts = [f'<div class="ipa-note" data-tone="{esc(tone)}">', f'<div class="ipa-note-icon">{ic}</div>', '<div class="ipa-note-body">']
    if title:
        parts.append(f'<div class="ipa-note-title">{esc(title)}</div>')
    if body:
        parts.append(f'<p class="ipa-note-text">{body}</p>')
    if meta:
        parts.append('<div class="ipa-note-meta">' + badges(meta) + "</div>")
    parts.append("</div></div>")
    return "".join(parts)


def insight_card(text: str, label: str = "Insight", tone: str = "accent", icon_name: str = "sparkles") -> str:
    """One AI/narrative insight. The text is passed through unchanged."""
    return note(title="", body=esc(text), tone=tone, icon_name=icon_name,
                meta=[{"text": label, "tone": "neutral"}])


def priority_card(priority: str, category: str, message: str, icon_name: Optional[str] = None) -> str:
    """Recommendation card. Priority drives tone and is always spelled out."""
    p = str(priority or "").strip().lower()
    tone = {"high": "high", "medium": "medium", "low": "low"}.get(p, "info")
    default_icon = {"high": "alert-triangle", "medium": "info", "low": "check-circle"}.get(p, "lightbulb")
    return note(
        title=esc(category),
        body=esc(message),
        tone=tone,
        icon_name=icon_name or default_icon,
        meta=[{"text": f"{p.title() if p else 'Unrated'} priority", "tone": {"high": "critical", "medium": "warning", "low": "success"}.get(tone, "neutral")}],
    )


def monogram(name: str, subtitle: str = "", meta: Sequence[Mapping[str, Any]] = ()) -> str:
    """Data-driven institution tile (initials + state + rank). No photography."""
    words = [w for w in str(name).replace(".", " ").split() if w]
    initials = "".join(w[0] for w in words[:3]).upper() or "—"
    if len(initials) > 3:
        initials = initials[:3]
    parts = [
        '<div class="ipa-monogram">',
        f'<div class="ipa-monogram-mark" aria-hidden="true">{esc(initials)}</div>',
        '<div class="ipa-monogram-body">',
        f'<p class="ipa-monogram-name">{esc(name)}</p>',
    ]
    chips = ([{"text": subtitle, "tone": "primary"}] if subtitle else []) + [_pick(badge, m) for m in meta]
    if chips:
        parts.append(f'<div class="ipa-monogram-meta">{badges(chips)}</div>')
    parts.append("</div></div>")
    return "".join(parts)


def definition_list(rows: Iterable[Sequence[Any]]) -> str:
    """Term/description rows. Descriptions may contain <code> and light markup."""
    parts = ['<dl class="ipa-defs">']
    for row in rows:
        term, description = row[0], row[1]
        source = row[2] if len(row) > 2 else ""
        parts.append(
            "<div class='ipa-def'>"
            f"<dt>{esc(term)}</dt>"
            f"<dd>{description}"
            + (f"<br><span class='ipa-source'>{esc(source)}</span>" if source else "")
            + "</dd></div>"
        )
    parts.append("</dl>")
    return "".join(parts)


def quality_indicator(tone: str, label: str) -> str:
    """Dot + text label, so status is never communicated by colour alone."""
    return f'<span class="ipa-quality" data-tone="{_tone(tone, "neutral")}"><i></i>{esc(label)}</span>'


# ----------------------------------------------------------------- states --
def empty_state(
    title: str,
    body: str = "",
    icon_name: str = "inbox",
    eyebrow: str = "",
) -> None:
    """Designed empty state — never a blank region or a raw Streamlit info box."""
    ic = icon(icon_name, 22)
    eyebrow_html = f'<div class="ipa-kicker">{esc(eyebrow)}</div>' if eyebrow else ""
    html(
        f'<div class="ipa-empty">{eyebrow_html}<div class="ipa-empty-icon">{ic}</div>'
        f"<h4>{esc(title)}</h4>"
        + (f"<p>{esc(body)}</p>" if body else "")
        + "</div>"
    )


def error_state(
    title: str = "Unable to load this analytics view",
    body: str = "Please verify the dataset and try again.",
    exc: Optional[BaseException] = None,
    detail: str = "",
) -> None:
    """Friendly failure card that still surfaces the real technical detail."""
    html(
        '<div class="ipa-fault">'
        '<div class="ipa-fault-eyebrow">Data unavailable</div>'
        f"<h4>{esc(title)}</h4><p>{esc(body)}</p></div>"
    )
    if exc is not None or detail:
        text = detail or f"{type(exc).__name__}: {exc}"
        with st.expander("Technical details"):
            st.code(text, language="text")


# ------------------------------------------------------------------- data --
_PY_TYPES = {
    "number": st.column_config.NumberColumn,
    "text": st.column_config.TextColumn,
    "progress": st.column_config.ProgressColumn,
    "bar": st.column_config.BarChartColumn,
    "date": st.column_config.DateColumn,
}


def styled_dataframe(
    df: pd.DataFrame,
    spec: Optional[Mapping[str, Mapping[str, Any]]] = None,
    height: Optional[int] = None,
    key: Optional[str] = None,
    hide_index: bool = True,
    columns: Optional[Sequence[str]] = None,
) -> None:
    """``st.dataframe`` with real column configuration.

    ``spec`` maps column name -> {label, type, format, help, width}. Only
    columns present in the frame are used, so callers can pass a superset.
    """
    if df is None or df.empty:
        empty_state(
            "No rows to display",
            "Adjust the filters or load institutional data to populate this table.",
            icon_name="inbox",
        )
        return

    frame = df[list(columns)] if columns else df
    config = {}
    for name, options in (spec or {}).items():
        if name not in frame.columns:
            continue
        options = dict(options)
        kind = options.pop("type", "number")
        column = _PY_TYPES.get(kind, st.column_config.NumberColumn)
        label = options.pop("label", None) or name.replace("_", " ").title()
        config[name] = column(label, **options)

    st.dataframe(
        frame,
        width="stretch",
        hide_index=hide_index,
        height=height,
        column_config=config or None,
        key=key,
    )


def chart(
    fig: Any,
    key: Optional[str] = None,
    note_text: str = "",
    height: Optional[int] = None,
) -> None:
    """Render a Plotly figure full-width with an optional truthful caption."""
    st.plotly_chart(fig, width="stretch", key=key)
    if note_text:
        html(f'<p class="ipa-chart-note">{esc(note_text)}</p>')


# ------------------------------------------------------------------- theme --
@lru_cache(maxsize=1)
def theme_css() -> str:
    return THEME_CSS_PATH.read_text(encoding="utf-8") if THEME_CSS_PATH.exists() else ""


def inject_theme_css() -> None:
    """Inject the design system. Idempotent — Streamlit re-runs the script."""
    st.markdown(f"<style>{theme_css()}</style>", unsafe_allow_html=True)
