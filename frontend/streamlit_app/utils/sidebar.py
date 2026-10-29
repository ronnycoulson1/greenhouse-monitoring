from pathlib import Path

import streamlit as st

from .alerts import evaluate_humidity_alert, evaluate_temperature_alert
from .db import load_latest
from .layout import CELSIUS_UNIT
from .styles import get_current_theme_name
from .themes import THEMES
from .zone_config import ZONE1_AREAS

from .styles import get_current_theme_name, load_css

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LOGO_PATH = ASSETS_DIR / "logo3.png"


def _sidebar_status_snapshot():
    indoor_area = ZONE1_AREAS[0]
    indoor_latest = load_latest(indoor_area["collection"], indoor_area["schema"])
    outside_latest = load_latest("outside_weather_data", "pico")

    if not indoor_latest:
        return {
            "headline": "Waiting for greenhouse readings",
            "copy": "Once Zone 1 data arrives, the sidebar will summarize live canopy conditions here.",
            "detail": "Zone 1 status unavailable",
        }

    temp_alert = evaluate_temperature_alert(indoor_latest.get("temp_c"), zone="zone1")
    humidity_alert = evaluate_humidity_alert(indoor_latest.get("humidity_pct"), zone="zone1")

    if temp_alert or humidity_alert:
        if temp_alert and temp_alert["kind"] == "high":
            headline = "Zone 1 needs cooling attention"
        elif temp_alert and temp_alert["kind"] == "low":
            headline = "Zone 1 is running colder than target"
        elif humidity_alert and humidity_alert["kind"] == "high":
            headline = "Zone 1 humidity is above target"
        else:
            headline = "Zone 1 humidity is below target"
    else:
        headline = "Zone 1 climate is within target band"

    temp_value = indoor_latest.get("temp_c")
    humidity_value = indoor_latest.get("humidity_pct")
    outside_temp = outside_latest.get("temp_c") if outside_latest else None

    greenhouse_bits = []
    if temp_value is not None:
        greenhouse_bits.append(f"{temp_value:.1f}{CELSIUS_UNIT}")
    if humidity_value is not None:
        greenhouse_bits.append(f"{humidity_value:.0f}% RH")
    greenhouse_snapshot = " and ".join(greenhouse_bits) if greenhouse_bits else "partial greenhouse data"

    if outside_temp is not None:
        copy = (
            f"Upper canopy is reading {greenhouse_snapshot}. "
            f"Outside reference is {outside_temp:.1f}{CELSIUS_UNIT}."
        )
    else:
        copy = f"Upper canopy is reading {greenhouse_snapshot}."

    return {
        "headline": headline,
        "copy": copy,
        "detail": "Live snapshot from Zone 1 upper canopy",
    }


def render_sidebar():
    if "theme" not in st.session_state:
        st.session_state["theme"] = list(THEMES.keys())[0]

    load_css()

    snapshot = _sidebar_status_snapshot()

    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=110)

        st.markdown(
            f"""
            <div class="sidebar-card">
                <p class="sidebar-title">Greenhouse Console</p>
                <p class="sidebar-copy">{snapshot["headline"]}</p>
                <p class="sidebar-stat">{snapshot["copy"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<p class="section-label">Navigate</p>', unsafe_allow_html=True)
        if st.button("Home", use_container_width=True):
            st.switch_page("Home.py")
        if st.button("Zone 1 Dashboard", use_container_width=True):
            st.switch_page("pages/1_zone1.py")
        st.button("Zone 2", use_container_width=True, disabled=True)
        if st.button("Credits", use_container_width=True):
            st.switch_page("pages/credits.py")

        st.markdown('<p class="section-label">Controls</p>', unsafe_allow_html=True)
        if st.button("Alert Settings", use_container_width=True):
            st.switch_page("pages/settings.py")

        theme_names = list(THEMES.keys())
        current_theme = get_current_theme_name()
        selected_theme = st.selectbox(
            "Display theme",
            options=theme_names,
            index=theme_names.index(current_theme),
        )
        if selected_theme != current_theme:
            st.session_state["theme"] = selected_theme
            st.rerun()

        st.caption(snapshot["detail"])
