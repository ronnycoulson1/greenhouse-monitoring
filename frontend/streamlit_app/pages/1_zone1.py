import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.alerts import (  # noqa: E402
    evaluate_humidity_alert,
    evaluate_temperature_alert,
    get_zone_alert,
    mark_email_alert_sent,
    should_send_email_alert,
)
from utils.charts import apply_readable_layout, chart_axis  # noqa: E402
from utils.db import load_history, load_latest, load_readings  # noqa: E402
from utils.emailer import (  # noqa: E402
    send_humidity_alert_email,
    send_temperature_alert_email,
)
from utils.layout import (  # noqa: E402
    CELSIUS_UNIT,
    FAHRENHEIT_UNIT,
    render_metrics_row,
    render_refresh_update,
    render_section_header,
    render_status_panel,
    render_zone1_top_controls,
    render_zone_header,
)
from utils.sidebar import render_sidebar  # noqa: E402
from utils.styles import load_css  # noqa: E402
from utils.zone_config import ZONE1_AREAS, get_area  # noqa: E402

POSITION_ICON = "\N{POTTED PLANT}"
CLIMATE_ICON = "\N{SEEDLING}"
HISTORY_ICON = "\N{CHART WITH UPWARDS TREND}"
TEMPERATURE_ICON = "\N{THERMOMETER}"
HUMIDITY_ICON = "\N{DROPLET}"
OUTSIDE_ICON = "\N{SUN BEHIND CLOUD}"
FEED_ICON = "\N{SATELLITE ANTENNA}"

st.set_page_config(page_title="Zone 1", layout="wide", initial_sidebar_state="expanded")
load_css()
render_sidebar()


def _to_local_time(series: pd.Series) -> pd.Series:
    timestamps = pd.to_datetime(series)
    if getattr(timestamps.dt, "tz", None) is None:
        return timestamps.dt.tz_localize("UTC").dt.tz_convert("US/Eastern")
    return timestamps.dt.tz_convert("US/Eastern")


def _format_temp(value_c: float | None, unit: str) -> str:
    if value_c is None:
        return "No data"
    if unit == FAHRENHEIT_UNIT:
        return f"{(value_c * 9.0 / 5.0) + 32.0:.1f}{FAHRENHEIT_UNIT}"
    return f"{value_c:.1f}{CELSIUS_UNIT}"


def _format_temp_html(value_c: float | None, unit: str) -> str:
    if value_c is None:
        return "No data"
    if unit == FAHRENHEIT_UNIT:
        return f"{(value_c * 9.0 / 5.0) + 32.0:.1f}<span class='metric-unit'>{FAHRENHEIT_UNIT}</span>"
    return f"{value_c:.1f}<span class='metric-unit'>{CELSIUS_UNIT}</span>"


def _trend_delta(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    valid = df[column].dropna()
    if len(valid) < 2:
        return None
    return float(valid.iloc[-1] - valid.iloc[0])


def _trend_text(delta: float | None, suffix: str, neutral_text: str = "Stable") -> tuple[str, str]:
    if delta is None:
        return "Awaiting trend", ""
    if abs(delta) < 0.15:
        return neutral_text, "trend-good"
    direction = "Up" if delta > 0 else "Down"
    css_class = "trend-warn" if abs(delta) >= 1 else "trend-good"
    return f"{direction} {abs(delta):.1f}{suffix} over the last 2 hours", css_class


def _status_for_metric(metric_name: str, value, alert, detail: str, disabled: bool = False) -> dict:
    if value is None:
        return {
            "label": metric_name,
            "state": "No data",
            "title": "Sensor feed",
            "detail": f"{detail} No current reading is available yet.",
            "tone": "neutral",
        }
    if disabled:
        return {
            "label": metric_name,
            "state": "Muted",
            "title": "Alerts disabled",
            "detail": detail,
            "tone": "neutral",
        }
    if not alert:
        return {
            "label": metric_name,
            "state": "In range",
            "title": "Plant-safe",
            "detail": detail,
            "tone": "good",
        }
    return {
        "label": metric_name,
        "state": "Attention",
        "title": "Threshold crossed",
        "detail": detail,
        "tone": "alert" if alert["kind"] == "high" and metric_name == "Temperature" else "warn",
    }


def _plot_card_start():
    st.markdown('<div class="plot-card">', unsafe_allow_html=True)


def _plot_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


render_zone_header("Zone 1")
render_refresh_update()

if "zone1_area_key" not in st.session_state:
    st.session_state["zone1_area_key"] = ZONE1_AREAS[0]["key"]

render_section_header("Monitoring Position", icon=POSITION_ICON)
area_cols = st.columns(len(ZONE1_AREAS))
for col, area in zip(area_cols, ZONE1_AREAS):
    is_selected = st.session_state["zone1_area_key"] == area["key"]
    with col:
        if st.button(
            area["label"],
            key=f"area_btn_{area['key']}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state["zone1_area_key"] = area["key"]
            st.rerun()

active_area = get_area(ZONE1_AREAS, st.session_state["zone1_area_key"])
active_collection = active_area["collection"]
active_schema = active_area["schema"]
is_reference_area = active_schema == "weather"

latest = load_latest(active_collection, active_schema)
outside_latest = None if is_reference_area else load_latest("outside_weather_data", "weather")
recent_history = load_history(active_collection, active_schema, hours=2)

temp = latest.get("temp_c") if latest else None
humidity = latest.get("humidity_pct") if latest else None
weather = latest.get("weather_desc") if latest else None

alerts_enabled = get_zone_alert("zone1").get("enabled", True)
temp_alert = None if is_reference_area else evaluate_temperature_alert(temp, zone="zone1")
humidity_alert = None if is_reference_area else evaluate_humidity_alert(humidity, zone="zone1")

if not latest:
    zone_summary_copy = f"{active_area['label']} has not reported any readings yet."
elif is_reference_area:
    zone_summary_copy = "Outside reference data is active. This feed is for comparison, not for indoor greenhouse alerting."
elif temp_alert or humidity_alert:
    zone_summary_copy = "One or more climate readings are outside the configured target range for Zone 1."
else:
    zone_summary_copy = "The selected position is inside the configured temperature and humidity range."

unit = render_zone1_top_controls(zone_summary_copy)

if latest and latest.get("ts"):
    local_ts = _to_local_time(pd.Series([latest["ts"]])).iloc[0]
    st.caption(f"{active_area['label']} last reported at {local_ts.strftime('%b %d, %Y %I:%M:%S %p')}")
else:
    st.caption(f"{active_area['label']} has not reported a reading yet.")

zone_alert_settings = get_zone_alert("zone1")
email_recipients = zone_alert_settings.get("email_recipients") or []
if not email_recipients and zone_alert_settings.get("email_to"):
    email_recipients = [zone_alert_settings.get("email_to")]
email_status_msgs = []

if temp_alert and zone_alert_settings.get("email_enabled", False) and email_recipients:
    cooldown = int(zone_alert_settings.get("email_cooldown_minutes", 30))
    if should_send_email_alert("zone1", temp_alert["kind"], cooldown_minutes=cooldown, metric="temperature"):
        sent_any = False
        for recipient in email_recipients:
            ok, msg = send_temperature_alert_email(
                recipient=recipient,
                zone="zone1",
                kind=temp_alert["kind"],
                temp_c=float(temp_alert["temp_c"]),
                threshold_c=float(temp_alert["threshold_c"]),
            )
            sent_any = sent_any or ok
            email_status_msgs.append(f"{recipient}: {msg}")
        if sent_any:
            mark_email_alert_sent("zone1", temp_alert["kind"], metric="temperature")

if humidity_alert and zone_alert_settings.get("email_enabled", False) and email_recipients:
    cooldown = int(zone_alert_settings.get("email_cooldown_minutes", 30))
    if should_send_email_alert("zone1", humidity_alert["kind"], cooldown_minutes=cooldown, metric="humidity"):
        sent_any = False
        for recipient in email_recipients:
            ok, msg = send_humidity_alert_email(
                recipient=recipient,
                zone="zone1",
                kind=humidity_alert["kind"],
                humidity_pct=float(humidity_alert["humidity_pct"]),
                threshold_pct=float(humidity_alert["threshold_pct"]),
            )
            sent_any = sent_any or ok
            email_status_msgs.append(f"{recipient}: {msg}")
        if sent_any:
            mark_email_alert_sent("zone1", humidity_alert["kind"], metric="humidity")

if unit == FAHRENHEIT_UNIT:
    threshold_min_display = zone_alert_settings["temp_min_c"] * 9.0 / 5.0 + 32.0
    threshold_max_display = zone_alert_settings["temp_max_c"] * 9.0 / 5.0 + 32.0
else:
    threshold_min_display = zone_alert_settings["temp_min_c"]
    threshold_max_display = zone_alert_settings["temp_max_c"]

temp_status_detail = (
    f"Target band is {threshold_min_display:.1f}{unit} to {threshold_max_display:.1f}{unit}."
    if not temp_alert
    else (
        f"Current reading is {_format_temp(temp_alert['temp_c'], unit)} and the threshold is "
        f"{_format_temp(temp_alert['threshold_c'], unit)}."
    )
)
humidity_min = float(zone_alert_settings.get("humidity_min_pct", 45.0))
humidity_max = float(zone_alert_settings.get("humidity_max_pct", 80.0))
humidity_status_detail = (
    f"Target band is {humidity_min:.0f}% RH to {humidity_max:.0f}% RH."
    if not humidity_alert
    else (
        f"Current reading is {humidity_alert['humidity_pct']:.0f}% RH and the threshold is "
        f"{humidity_alert['threshold_pct']:.0f}% RH."
    )
)
data_detail = "Reference feed only." if is_reference_area else (
    "Email notifications are enabled for threshold crossings." if zone_alert_settings.get("email_enabled", False)
    else "Email notifications are currently disabled."
)

render_status_panel(
    [
        _status_for_metric("Temperature", temp, temp_alert, temp_status_detail, disabled=(not alerts_enabled and not is_reference_area)),
        _status_for_metric("Humidity", humidity, humidity_alert, humidity_status_detail, disabled=(not alerts_enabled and not is_reference_area)),
        {
            "label": "Reporting",
            "state": "Reference" if is_reference_area else "Live",
            "title": active_area["label"],
            "detail": data_detail,
            "tone": "neutral" if is_reference_area else "good",
        },
    ]
)

for msg in email_status_msgs:
    st.caption(msg)

temp_delta = _trend_delta(recent_history, "temp_c")
humidity_delta = _trend_delta(recent_history, "humidity_pct")
temp_trend, temp_trend_class = _trend_text(temp_delta, CELSIUS_UNIT)
humidity_trend, humidity_trend_class = _trend_text(humidity_delta, "%", neutral_text="Humidity steady")

outside_temp_support = "Outside reference unavailable."
outside_temp_value = "No data"
if outside_latest and outside_latest.get("temp_c") is not None and temp is not None:
    gap_c = temp - outside_latest["temp_c"]
    gap_display = gap_c * 9.0 / 5.0 if unit == FAHRENHEIT_UNIT else gap_c
    gap_suffix = FAHRENHEIT_UNIT if unit == FAHRENHEIT_UNIT else CELSIUS_UNIT
    outside_temp_value = f"{gap_display:+.1f}<span class='metric-unit'>{gap_suffix}</span>"
    outside_temp_support = "Difference between this indoor reading and the outside reference."
elif outside_latest and outside_latest.get("temp_c") is not None:
    outside_temp_value = _format_temp_html(outside_latest["temp_c"], unit)

metrics = [
    {
        "title": "Temperature",
        "value": _format_temp_html(temp, unit),
        "chip_class": "chip-green",
        "icon": TEMPERATURE_ICON,
        "support": f"{active_area['label']} live reading",
        "trend": temp_trend,
        "trend_class": temp_trend_class,
    },
    {
        "title": "Humidity",
        "value": f"{humidity:.0f}<span class='metric-unit'>% RH</span>" if humidity is not None else "No data",
        "chip_class": "chip-blue",
        "icon": HUMIDITY_ICON,
        "support": "Relative humidity at the selected position",
        "trend": humidity_trend,
        "trend_class": humidity_trend_class,
    },
    {
        "title": "Indoor vs outside",
        "value": outside_temp_value,
        "chip_class": "chip-amber",
        "icon": OUTSIDE_ICON,
        "support": outside_temp_support,
        "trend": "Reference comparison" if outside_latest else "No outside reference",
        "trend_class": "trend-good" if outside_latest else "",
    },
    {
        "title": "Feed type",
        "value": "Reference" if is_reference_area else "Sensor",
        "chip_class": "chip-gray",
        "icon": FEED_ICON,
        "support": weather.title() if weather else ("Outside weather condition" if is_reference_area else active_area["label"]),
        "trend": "Weather feed" if is_reference_area else "Greenhouse position",
        "trend_class": "trend-good",
    },
]

render_section_header("Current Climate", icon=CLIMATE_ICON)
render_metrics_row(metrics)

render_section_header("Climate History", icon=HISTORY_ICON)
st.markdown("**Range filter**")
col_radio, col_date = st.columns([1, 2])

with col_radio:
    time_mode = st.radio(
        "Range Type",
        ["Last 24 Hours", "Last 7 Days", "Custom Range"],
        label_visibility="collapsed",
    )

start_time = None
end_time = None
hours = 24

with col_date:
    if time_mode == "Last 24 Hours":
        hours = 24
        st.markdown("<p class='control-caption'>Showing the most recent 24 hours of readings.</p>", unsafe_allow_html=True)
    elif time_mode == "Last 7 Days":
        hours = 168
        st.markdown("<p class='control-caption'>Showing a 7-day greenhouse history window.</p>", unsafe_allow_html=True)
    else:
        today = pd.Timestamp.now("US/Eastern").date()
        date_range = st.date_input("Select Date Range", (today - pd.Timedelta(days=2), today))
        if len(date_range) == 2:
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                start_t = st.time_input("Start Time", value=pd.Timestamp("00:00:00").time())
            with t_col2:
                end_t = st.time_input("End Time", value=pd.Timestamp("23:59:59").time())

            start_combined = pd.to_datetime(f"{date_range[0]} {start_t}")
            end_combined = pd.to_datetime(f"{date_range[1]} {end_t}")
            start_time = start_combined.tz_localize("US/Eastern").tz_convert("UTC").to_pydatetime()
            end_time = end_combined.tz_localize("US/Eastern").tz_convert("UTC").to_pydatetime()
            hours = None

chart_df = load_history(
    active_collection,
    active_schema,
    hours=hours,
    start_ts=start_time,
    end_ts=end_time,
)
if not chart_df.empty and "ts" in chart_df.columns:
    chart_df["ts"] = _to_local_time(chart_df["ts"])

display_temp_col = "temp_display"
if not chart_df.empty and "temp_c" in chart_df.columns:
    if unit == FAHRENHEIT_UNIT:
        chart_df[display_temp_col] = chart_df["temp_c"] * 9.0 / 5.0 + 32.0
    else:
        chart_df[display_temp_col] = chart_df["temp_c"]

_plot_card_start()
st.markdown(f"**{active_area['label']} climate history**")
if not chart_df.empty and {"temp_c", "humidity_pct"}.issubset(chart_df.columns):
    combined_fig = go.Figure()
    combined_fig.add_trace(
        go.Scatter(
            x=chart_df["ts"],
            y=chart_df[display_temp_col],
            mode="lines+markers",
            name=f"Temperature ({unit})",
            line=dict(color="#4F8B63", width=3),
            marker=dict(size=4),
            yaxis="y1",
        )
    )
    combined_fig.add_trace(
        go.Scatter(
            x=chart_df["ts"],
            y=chart_df["humidity_pct"],
            mode="lines+markers",
            name="Humidity (% RH)",
            line=dict(color="#4C83C3", width=2, dash="dot"),
            marker=dict(size=4),
            yaxis="y2",
        )
    )
    apply_readable_layout(
        combined_fig,
        margin=dict(l=8, r=8, t=18, b=48),
        xaxis=chart_axis(showgrid=False, tickformat="%b %d\n%I:%M %p"),
        yaxis=chart_axis(
            title=unit,
            showgrid=True,
            gridcolor="rgba(99, 116, 106, 0.18)",
        ),
        yaxis2=chart_axis(
            title="% RH",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
    )
    st.plotly_chart(combined_fig, use_container_width=True, config={"displayModeBar": False}, theme=None)
else:
    st.info("Combined history will appear here after enough temperature and humidity readings arrive for this position.")
_plot_card_end()

with st.expander("Open detailed charts"):
    detail_cols = st.columns(2)
    with detail_cols[0]:
        if not chart_df.empty and "temp_c" in chart_df.columns:
            temp_fig = go.Figure()
            temp_fig.add_trace(
                go.Scatter(
                    x=chart_df["ts"],
                    y=chart_df[display_temp_col],
                    mode="lines",
                    line=dict(color="#4F8B63", width=3),
                    name="Temperature",
                )
            )
            apply_readable_layout(
                temp_fig,
                margin=dict(l=8, r=8, t=20, b=48),
                showlegend=False,
                yaxis=chart_axis(title=unit, showgrid=True, gridcolor="rgba(99, 116, 106, 0.18)"),
                xaxis=chart_axis(showgrid=False, tickformat="%b %d\n%I:%M %p"),
            )
            st.plotly_chart(temp_fig, use_container_width=True, config={"displayModeBar": False}, theme=None)
        else:
            st.info("No temperature history yet.")

    with detail_cols[1]:
        if not chart_df.empty and "humidity_pct" in chart_df.columns:
            humidity_fig = go.Figure()
            humidity_fig.add_trace(
                go.Scatter(
                    x=chart_df["ts"],
                    y=chart_df["humidity_pct"],
                    mode="lines",
                    line=dict(color="#4C83C3", width=3),
                    name="Humidity",
                )
            )
            apply_readable_layout(
                humidity_fig,
                margin=dict(l=8, r=8, t=20, b=48),
                showlegend=False,
                yaxis=chart_axis(title="% RH", showgrid=True, gridcolor="rgba(99, 116, 106, 0.18)"),
                xaxis=chart_axis(showgrid=False, tickformat="%b %d\n%I:%M %p"),
            )
            st.plotly_chart(humidity_fig, use_container_width=True, config={"displayModeBar": False}, theme=None)
        else:
            st.info("No humidity history yet.")

with st.expander("Open raw readings"):
    show_latest_only = st.toggle("Show latest reading only", value=True)
    limit = 1 if show_latest_only else st.slider("Rows", min_value=1, max_value=90, value=20, step=1)
    docs = load_readings(active_collection, active_schema, limit=limit)
    table_df = pd.DataFrame(docs)
    if table_df.empty:
        st.info("No readings found yet.")
    else:
        if "ts" in table_df.columns:
            table_df["ts"] = _to_local_time(table_df["ts"])
        st.dataframe(table_df, use_container_width=True)
