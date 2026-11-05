import base64
from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.alerts import evaluate_humidity_alert, evaluate_temperature_alert
from utils.charts import apply_readable_layout, chart_axis
from utils.db import load_history, load_latest
from utils.layout import (
    CELSIUS_UNIT,
    render_overview_card,
    render_page_header,
    render_section_header,
    render_status_panel,
)
from utils.sidebar import render_sidebar
from utils.styles import load_css
from utils.zone_config import ZONE1_AREAS

PAGE_ICON = "\N{SEEDLING}"
SNAPSHOT_ICON = "\N{HERB}"
POSITION_ICON = "\N{POTTED PLANT}"
TREND_ICON = "\N{CHART WITH UPWARDS TREND}"
BASE_DIR = Path(__file__).resolve().parent
GREENHOUSE_IMAGE = BASE_DIR / "assets" / "greenhouse.jpg"

st.set_page_config(
    page_title="Greenhouse Overview",
    layout="wide",
    page_icon=PAGE_ICON,
    initial_sidebar_state="expanded",
)
load_css()
render_sidebar()



def _to_local_time(series: pd.Series) -> pd.Series:
    timestamps = pd.to_datetime(series)
    if getattr(timestamps.dt, "tz", None) is None:
        return timestamps.dt.tz_localize("UTC").dt.tz_convert("US/Eastern")
    return timestamps.dt.tz_convert("US/Eastern")


STALE_AFTER = pd.Timedelta(minutes=30)


def _age(latest: dict | None):
    ts = latest.get("ts") if latest else None
    if ts is None:
        return None
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return pd.Timestamp.now(tz="UTC") - ts


def _age_text(age) -> str:
    if age is None:
        return ""
    mins = int(age.total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    hours = mins // 60
    if hours < 48:
        return f"{hours} h ago"
    return f"{hours // 24} days ago"


def _alert_state_for_area(area: dict, latest: dict | None) -> tuple[str, str]:
    if not latest:
        return "neutral", "Waiting for data"

    if area["key"] == "outside":
        return "neutral", "Reference"

    age = _age(latest)
    if age is not None and age > STALE_AFTER:
        return "neutral", "No recent data"

    temp_alert = evaluate_temperature_alert(latest.get("temp_c"), zone="zone1")
    humidity_alert = evaluate_humidity_alert(latest.get("humidity_pct"), zone="zone1")

    if temp_alert or humidity_alert:
        if temp_alert and temp_alert["kind"] == "high":
            return "alert", "Too warm"
        if temp_alert and temp_alert["kind"] == "low":
            return "warn", "Running cool"
        if humidity_alert and humidity_alert["kind"] == "high":
            return "warn", "Humidity high"
        return "warn", "Humidity low"

    return "good", "Within target"

def _plot_card_start():
    st.markdown('<div class="plot-card">', unsafe_allow_html=True)


def _plot_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


snapshots = {}
for area in ZONE1_AREAS:
    snapshots[area["key"]] = load_latest(area["collection"], area["schema"])

zone1_latest = snapshots.get("upper")
outside_latest = snapshots.get("outside")

online_count = sum(1 for snapshot in snapshots.values() if snapshot)
healthy_count = 0
attention_count = 0
for area in ZONE1_AREAS[:3]:
    tone, _ = _alert_state_for_area(area, snapshots.get(area["key"]))
    if tone == "good":
        healthy_count += 1
    elif tone in {"warn", "alert"}:
        attention_count += 1

hero_pills = [
    f"{online_count}/{len(ZONE1_AREAS)} positions reporting",
    f"{healthy_count} canopy bands in target",
    f"{attention_count} positions need attention" if attention_count else "No active climate exceptions",
]

render_page_header(
    "Greenhouse Home",
    "A single place to watch canopy conditions, compare inside and outside climate, and spot issues before they stress the plants.",
    badge_text="Operations",
)


def _render_html(html: str):
    normalized = "\n".join(line.strip() for line in dedent(html).splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(normalized)
    else:
        st.markdown(normalized, unsafe_allow_html=True)

greenhouse_image_html = ""
if GREENHOUSE_IMAGE.exists():
    image_b64 = base64.b64encode(GREENHOUSE_IMAGE.read_bytes()).decode("ascii")
    greenhouse_image_html = dedent(
        f"""
        <div class="hero-visual">
            <img src="data:image/jpeg;base64,{image_b64}" alt="Greenhouse interior" />
            <div class="hero-visual-badge">
                <span class="hero-visual-badge-dot"></span>
                Kent State greenhouse
            </div>
        </div>
        """
    ).strip()

_render_html(
    f"""
    <div class="hero-panel">
        <div class="hero-split">
            <div>
                <div class="hero-eyebrow">Kent State Greenhouse</div>
                <div class="hero-title">Clean, fast climate awareness for daily greenhouse work.</div>
                <p class="hero-copy">
                    This home screen keeps the most important context above the fold: live indoor climate, outside reference conditions,
                    reporting sensor positions, and whether any area has drifted outside the configured plant-safe range.
                </p>
                <div class="hero-meta">
                    {''.join(f'<span class="hero-meta-pill">{pill}</span>' for pill in hero_pills)}
                </div>
            </div>
            {greenhouse_image_html}
        </div>
    </div>
    """
)

render_section_header("Current Snapshot", icon=SNAPSHOT_ICON)
top_cols = st.columns(4)
with top_cols[0]:
    zone_temp = f"{zone1_latest['temp_c']:.1f}{CELSIUS_UNIT}" if zone1_latest and zone1_latest.get("temp_c") is not None else "No data"
    render_overview_card("Zone 1 temperature", zone_temp, "Upper canopy live reading.")
with top_cols[1]:
    zone_humidity = f"{zone1_latest['humidity_pct']:.0f}% RH" if zone1_latest and zone1_latest.get("humidity_pct") is not None else "No data"
    render_overview_card("Zone 1 humidity", zone_humidity, "Relative humidity at the primary canopy monitor.")
with top_cols[2]:
    outside_temp = f"{outside_latest['temp_c']:.1f}{CELSIUS_UNIT}" if outside_latest and outside_latest.get("temp_c") is not None else "No data"
    render_overview_card("Outside reference", outside_temp, "Weather feed used as a greenhouse reference point.")
with top_cols[3]:
    alert_summary = "Clear" if attention_count == 0 else f"{attention_count} flagged"
    summary_copy = "All monitored indoor positions are inside the target band." if attention_count == 0 else "One or more indoor positions have drifted outside the configured range."
    render_overview_card("Attention", alert_summary, summary_copy)

render_section_header("Monitoring Positions", icon=POSITION_ICON)
status_items = []
for area in ZONE1_AREAS:
    latest = snapshots.get(area["key"])
    tone, state = _alert_state_for_area(area, latest)
    if latest and latest.get("temp_c") is not None and latest.get("humidity_pct") is not None:
        detail = f"{latest['temp_c']:.1f}{CELSIUS_UNIT} and {latest['humidity_pct']:.0f}% RH"
    elif latest and latest.get("temp_c") is not None:
        detail = f"{latest['temp_c']:.1f}{CELSIUS_UNIT}"
    else:
        detail = "No readings received yet."

    if area["schema"] == "weather" and latest and latest.get("weather_desc"):
        detail = f"{detail} | {str(latest['weather_desc']).title()}"
    if latest:
        detail = f"{detail} · updated {_age_text(_age(latest))}"

    status_items.append(
        {
            "label": "Position",
            "state": state,
            "title": area["label"],
            "detail": detail,
            "tone": tone,
        }
    )
render_status_panel(status_items)

render_section_header("Recent Climate Trend", icon=TREND_ICON)
history_cols = st.columns(2)

TREND_COLORS = ["#2E7D4F", "#C98A2B", "#7A5AA6", "#4C83C3"]
histories = []
for i, area in enumerate(ZONE1_AREAS):
    df = load_history(area["collection"], area["schema"], hours=24)
    if not df.empty and "ts" in df.columns:
        df["ts"] = _to_local_time(df["ts"])
        histories.append((area, df, TREND_COLORS[i % len(TREND_COLORS)]))


def _render_trend(field: str, title: str, unit: str, empty_msg: str):
    _plot_card_start()
    st.markdown(f"**{title}**")
    traces = [(a, df, c) for a, df, c in histories if field in df.columns]
    if not traces:
        st.info(empty_msg)
        _plot_card_end()
        return
    fig = go.Figure()
    for area, df, color in traces:
        is_outside = area["key"] == "outside"
        fig.add_trace(
            go.Scatter(
                x=df["ts"],
                y=df[field],
                mode="lines",
                name=area["label"],
                line=dict(color=color, width=2, dash="dash" if is_outside else "solid"),
            )
        )
    apply_readable_layout(
        fig,
        margin=dict(l=8, r=8, t=16, b=72),
        yaxis=chart_axis(title=unit, showgrid=True, gridcolor="rgba(99, 116, 106, 0.18)"),
        xaxis=chart_axis(showgrid=False, tickformat="%b %d\n%I:%M %p"),
    )
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, theme=None)
    _plot_card_end()


with history_cols[0]:
    _render_trend("temp_c", "Temperature, last 24 hours", CELSIUS_UNIT,
                  "Temperature history will appear here once data has been received.")

with history_cols[1]:
    _render_trend("humidity_pct", "Humidity, last 24 hours", "% RH",
                  "Humidity history will appear here once data has been received.")