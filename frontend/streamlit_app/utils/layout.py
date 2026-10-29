from datetime import datetime
from textwrap import dedent

import streamlit as st

CELSIUS_UNIT = "\u00b0C"
FAHRENHEIT_UNIT = "\u00b0F"
BULLET = "\u2022"


def _render_html(html: str):
    normalized = "\n".join(line.strip() for line in dedent(html).splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(normalized)
    else:
        st.markdown(normalized, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, badge_text: str = "Monitoring"):
    _render_html(
        f"""
        <div class="page-header">
            <div>
                <p class="page-title">{title}</p>
                <p class="page-subtitle">{subtitle}</p>
            </div>
            <div class="live-badge">
                <div class="live-badge-dot"></div>
                {badge_text}
            </div>
        </div>
        """
    )


def render_zone_header(zone_name: str):
    render_page_header(
        zone_name,
        "Live climate conditions, alerts, and recent sensor history for this greenhouse zone.",
        badge_text="Live feed",
    )


def render_refresh_update(label: str = "Last synced"):
    now = datetime.now().strftime("%b %d, %Y %I:%M:%S %p")
    col_time, col_btn = st.columns([5, 1])
    with col_time:
        st.markdown(f'<p class="control-caption">{label}: {now}</p>', unsafe_allow_html=True)
    with col_btn:
        if st.button("Refresh", use_container_width=True):
            st.session_state["last_update"] = datetime.now()
            st.cache_data.clear()
            st.rerun()


def render_zone1_top_controls(alert_copy: str):
    if "temp_unit" not in st.session_state:
        st.session_state["temp_unit"] = CELSIUS_UNIT

    col_controls, col_alerts = st.columns([1.3, 1.7])

    with col_controls:
        with st.container(border=True):
            st.markdown("**Display unit**")
            unit = st.radio(
                "Temperature Unit",
                [CELSIUS_UNIT, FAHRENHEIT_UNIT],
                horizontal=True,
                label_visibility="collapsed",
                key="temp_unit",
            )
            st.markdown(
                "<p class='control-caption'>Switches dashboard temperature labels only. Alert thresholds stay stored in Celsius.</p>",
                unsafe_allow_html=True,
            )

    with col_alerts:
        with st.container(border=True):
            st.markdown("**Zone summary**")
            st.markdown(f"<p class='control-caption'>{alert_copy}</p>", unsafe_allow_html=True)

    return unit


def render_metric_card(
    title: str,
    value: str,
    chip_class: str,
    icon: str,
    support: str = "",
    trend: str = "",
    trend_class: str = "",
):
    support_html = f'<div class="metric-support">{support}</div>' if support else ""
    trend_html = f'<div class="metric-trend {trend_class}">{trend}</div>' if trend else ""
    _render_html(
        f"""
        <div class="metric-card">
            <div class="metric-icon-chip {chip_class}">{icon}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {support_html}
            {trend_html}
        </div>
        """
    )



def render_metrics_row(metrics: list[dict]):
    columns = st.columns(len(metrics))
    for column, metric in zip(columns, metrics):
        with column:
            render_metric_card(
                title=metric["title"],
                value=metric["value"],
                chip_class=metric.get("chip_class", "chip-gray"),
                icon=metric.get("icon", BULLET),
                support=metric.get("support", ""),
                trend=metric.get("trend", ""),
                trend_class=metric.get("trend_class", ""),
            )


def render_status_panel(items: list[dict]):
    blocks = []
    for item in items:
        tone = item.get("tone", "neutral")
        chip_class = {
            "good": "status-chip-good",
            "warn": "status-chip-warn",
            "alert": "status-chip-alert",
            "neutral": "status-chip-neutral",
        }.get(tone, "status-chip-neutral")
        blocks.append(
            f"""
            <div class="status-block">
                <div class="status-block-label">{item.get("label", "Status")}</div>
                <div class="status-block-title">
                    <span class="status-chip {chip_class}">
                        <span class="status-chip-dot"></span>
                        {item.get("state", "Checking")}
                    </span>
                    <span class="status-block-name">{item.get("title", "")}</span>
                </div>
                <div class="status-block-copy">{item.get("detail", "")}</div>
            </div>
            """
        )

    _render_html(
        f"""
        <div class="status-panel">
            <div class="status-grid">
                {''.join(blocks)}
            </div>
        </div>
        """
    )


def render_overview_card(label: str, value: str, copy: str):
    _render_html(
        f"""
        <div class="overview-card">
            <div class="overview-label">{label}</div>
            <div class="overview-value">{value}</div>
            <div class="overview-copy">{copy}</div>
        </div>
        """
    )


def render_section_header(title: str, icon: str | None = None):
    icon_html = f'<span style="font-size:1rem;">{icon}</span>' if icon else ""
    _render_html(
        f"""
        <div>
            <div class="section-title-container">
                {icon_html}<h2 class="section-title">{title}</h2>
            </div>
            <div class="section-divider"></div>
        </div>
        """
    )
