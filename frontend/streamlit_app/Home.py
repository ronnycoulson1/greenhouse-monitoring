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


def _alert_state_for_area(area: dict, latest: dict | None) -> tuple[str, str]:
    if not latest:
        return "neutral", "Waiting for data"

    if area["schema"] == "pico":
        return "neutral", "Outside reference"

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

outside_history = load_history("outside_weather_data", "pico", hours=24)

if not outside_history.empty and "ts" in outside_history.columns:
    outside_history["ts"] = _to_local_time(outside_history["ts"])

_has_temp = not outside_history.empty and "temp_c" in outside_history.columns
_has_humidity = not outside_history.empty and "humidity_pct" in outside_history.columns

with history_cols[0]:
    _plot_card_start()
    st.markdown("**Temperature, last 24 hours**")
    if _has_temp:
        temp_fig = go.Figure()
        temp_fig.add_trace(
            go.Scatter(
                x=outside_history["ts"],
                y=outside_history["temp_c"],
                mode="lines",
                name="Outside",
                line=dict(color="#4C83C3", width=2),
            )
        )
        apply_readable_layout(
            temp_fig,
            margin=dict(l=8, r=8, t=16, b=48),
            yaxis=chart_axis(title=CELSIUS_UNIT, showgrid=True, gridcolor="rgba(99, 116, 106, 0.18)"),
            xaxis=chart_axis(showgrid=False, tickformat="%b %d\n%I:%M %p"),
        )
        st.plotly_chart(temp_fig, use_container_width=True, config={"displayModeBar": False}, theme=None)
    else:
        st.info("Outside temperature history will appear here once data has been received.")
    _plot_card_end()

with history_cols[1]:
    _plot_card_start()
    st.markdown("**Humidity, last 24 hours**")
    if _has_humidity:
        humidity_fig = go.Figure()
        humidity_fig.add_trace(
            go.Scatter(
                x=outside_history["ts"],
                y=outside_history["humidity_pct"],
                mode="lines",
                name="Outside",
                line=dict(color="#4C83C3", width=2),
            )
        )
        apply_readable_layout(
            humidity_fig,
            margin=dict(l=8, r=8, t=16, b=48),
            yaxis=chart_axis(title="% RH", showgrid=True, gridcolor="rgba(99, 116, 106, 0.18)"),
            xaxis=chart_axis(showgrid=False, tickformat="%b %d\n%I:%M %p"),
        )
        st.plotly_chart(humidity_fig, use_container_width=True, config={"displayModeBar": False}, theme=None)
    else:
        st.info("Outside humidity history will appear here once data has been received.")
    _plot_card_end()