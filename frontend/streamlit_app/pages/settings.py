import streamlit as st

from utils.alerts import (
    evaluate_humidity_alert,
    evaluate_temperature_alert,
    get_zone_alert,
    update_zone_alert,
)
from utils.db import load_latest
from utils.emailer import is_email_configured
from utils.layout import (
    CELSIUS_UNIT,
    FAHRENHEIT_UNIT,
    render_page_header,
    render_section_header,
    render_status_panel,
)
from utils.sidebar import render_sidebar
from utils.styles import load_css

PREVIEW_ICON = "\N{LEFT-POINTING MAGNIFYING GLASS}"
THRESHOLD_ICON = "\N{GEAR}"
CONFIG_ICON = "\N{CLIPBOARD}"


def c_to_f(temp_c: float) -> float:
    return (temp_c * 9.0 / 5.0) + 32.0


def f_to_c(temp_f: float) -> float:
    return (temp_f - 32.0) * 5.0 / 9.0


st.set_page_config(page_title="Alert Settings", layout="wide", initial_sidebar_state="expanded")
load_css()
render_sidebar()

render_page_header(
    "Alert Settings",
    "Tune the target range for Zone 1 so the dashboard flags conditions that can stress plants before they become real problems.",
    badge_text="Configuration",
)

zone_key = "zone1"
zone_label = "Zone 1"
zone_settings = get_zone_alert(zone_key)

if "temp_unit" not in st.session_state:
    st.session_state["temp_unit"] = CELSIUS_UNIT

unit = st.radio(
    "Temperature Unit",
    [CELSIUS_UNIT, FAHRENHEIT_UNIT],
    horizontal=True,
    key="temp_unit",
)

current_recipients = zone_settings.get("email_recipients") or []
if not current_recipients and zone_settings.get("email_to"):
    current_recipients = [zone_settings.get("email_to")]

min_c = float(zone_settings.get("temp_min_c", 18.0))
max_c = float(zone_settings.get("temp_max_c", 28.0))
humidity_min_pct = float(zone_settings.get("humidity_min_pct", 45.0))
humidity_max_pct = float(zone_settings.get("humidity_max_pct", 80.0))

if unit == FAHRENHEIT_UNIT:
    default_min = round(c_to_f(min_c), 1)
    default_max = round(c_to_f(max_c), 1)
    input_min, input_max = 14.0, 140.0
else:
    default_min = round(min_c, 1)
    default_max = round(max_c, 1)
    input_min, input_max = -10.0, 60.0

preview_doc = load_latest("zone1-upper", "pico")
live_temp = preview_doc.get("temp_c") if preview_doc else None
live_humidity = preview_doc.get("humidity_pct") if preview_doc else None
temp_alert_preview = evaluate_temperature_alert(live_temp, zone=zone_key)
humidity_alert_preview = evaluate_humidity_alert(live_humidity, zone=zone_key)

temp_min_display = c_to_f(min_c) if unit == FAHRENHEIT_UNIT else min_c
temp_max_display = c_to_f(max_c) if unit == FAHRENHEIT_UNIT else max_c
temp_value_display = c_to_f(live_temp) if (unit == FAHRENHEIT_UNIT and live_temp is not None) else live_temp

render_section_header("Live Preview", icon=PREVIEW_ICON)
render_status_panel(
    [
        {
            "label": "Temperature",
            "state": "Attention" if temp_alert_preview else "In range" if live_temp is not None else "No data",
            "title": zone_label,
            "detail": (
                f"Live reading {temp_value_display:.1f}{unit}; configured band {temp_min_display:.1f}{unit} to {temp_max_display:.1f}{unit}."
                if live_temp is not None
                else "No live temperature reading is available yet."
            ),
            "tone": "warn" if temp_alert_preview else "good" if live_temp is not None else "neutral",
        },
        {
            "label": "Humidity",
            "state": "Attention" if humidity_alert_preview else "In range" if live_humidity is not None else "No data",
            "title": zone_label,
            "detail": (
                f"Live reading {float(live_humidity):.0f}% RH; configured band {humidity_min_pct:.0f}% RH to {humidity_max_pct:.0f}% RH."
                if live_humidity is not None
                else "No live humidity reading is available yet."
            ),
            "tone": "warn" if humidity_alert_preview else "good" if live_humidity is not None else "neutral",
        },
        {
            "label": "Email delivery",
            "state": "Enabled" if zone_settings.get("email_enabled", False) else "Off",
            "title": "Notification routing",
            "detail": (
                f"{len(current_recipients)} recipient(s) configured. Cooldown is {int(zone_settings.get('email_cooldown_minutes', 30))} minutes."
                if zone_settings.get("email_enabled", False)
                else "Email alerts are currently disabled for this zone."
            ),
            "tone": "good" if zone_settings.get("email_enabled", False) else "neutral",
        },
    ]
)

render_section_header("Thresholds", icon=THRESHOLD_ICON)
with st.form("zone1_alert_form"):
    alerts_enabled = st.toggle(
        "Enable Zone 1 alerts",
        value=bool(zone_settings.get("enabled", True)),
    )

    col_min, col_max = st.columns(2)
    with col_min:
        temp_min_input = st.number_input(
            f"Minimum temperature ({unit})",
            min_value=input_min,
            max_value=input_max,
            value=default_min,
            step=0.5,
        )
    with col_max:
        temp_max_input = st.number_input(
            f"Maximum temperature ({unit})",
            min_value=input_min,
            max_value=input_max,
            value=default_max,
            step=0.5,
        )

    humidity_cols = st.columns(2)
    with humidity_cols[0]:
        humidity_min_input = st.number_input(
            "Minimum humidity (% RH)",
            min_value=0.0,
            max_value=100.0,
            value=round(humidity_min_pct, 1),
            step=1.0,
        )
    with humidity_cols[1]:
        humidity_max_input = st.number_input(
            "Maximum humidity (% RH)",
            min_value=0.0,
            max_value=100.0,
            value=round(humidity_max_pct, 1),
            step=1.0,
        )

    st.markdown("**Email notifications**")
    email_enabled = st.toggle(
        "Send email when an alert triggers",
        value=bool(zone_settings.get("email_enabled", False)),
    )
    email_add_input = st.text_input(
        "Add recipient email(s)",
        value="",
        placeholder="name@example.com or comma-separated list",
    )
    emails_to_remove = st.multiselect(
        "Remove recipient email(s)",
        options=current_recipients,
        default=[],
    )
    email_cooldown_minutes = st.number_input(
        "Cooldown between repeated emails (minutes)",
        min_value=1,
        max_value=720,
        value=int(zone_settings.get("email_cooldown_minutes", 30)),
        step=1,
    )

    save = st.form_submit_button("Save Zone 1 alert settings", use_container_width=True)

if save:
    try:
        temp_min_c = f_to_c(temp_min_input) if unit == FAHRENHEIT_UNIT else temp_min_input
        temp_max_c = f_to_c(temp_max_input) if unit == FAHRENHEIT_UNIT else temp_max_input

        new_recipients = [email for email in current_recipients if email not in emails_to_remove]
        if email_add_input.strip():
            add_parts = [part.strip() for part in email_add_input.replace(";", ",").replace("\n", ",").split(",")]
            for address in add_parts:
                if address and address.lower() not in {existing.lower() for existing in new_recipients}:
                    new_recipients.append(address)

        update_zone_alert(
            zone=zone_key,
            enabled=alerts_enabled,
            temp_min_c=temp_min_c,
            temp_max_c=temp_max_c,
            humidity_min_pct=humidity_min_input,
            humidity_max_pct=humidity_max_input,
            email_enabled=email_enabled,
            email_recipients=new_recipients,
            email_cooldown_minutes=int(email_cooldown_minutes),
        )
        st.success("Zone 1 alert settings were saved.")
    except ValueError as exc:
        st.error(str(exc))

render_section_header("Current Configuration", icon=CONFIG_ICON)
active_settings = get_zone_alert(zone_key)
active_min_c = float(active_settings["temp_min_c"])
active_max_c = float(active_settings["temp_max_c"])

if unit == FAHRENHEIT_UNIT:
    active_min = c_to_f(active_min_c)
    active_max = c_to_f(active_max_c)
else:
    active_min = active_min_c
    active_max = active_max_c

st.info(
    f"{zone_label} temperature band: {active_min:.1f}{unit} to {active_max:.1f}{unit}. "
    + ("Alerts are enabled." if active_settings.get("enabled", True) else "Alerts are disabled.")
)
st.info(
    f"{zone_label} humidity band: {float(active_settings.get('humidity_min_pct', 45.0)):.0f}% RH "
    f"to {float(active_settings.get('humidity_max_pct', 80.0)):.0f}% RH."
)

if active_settings.get("email_enabled", False):
    active_recipients = active_settings.get("email_recipients") or []
    if not active_recipients and active_settings.get("email_to"):
        active_recipients = [active_settings.get("email_to")]
    recipients_label = ", ".join(active_recipients) if active_recipients else "not set"
    st.caption(
        f"Email alerts are on for {recipients_label}. Cooldown is {int(active_settings.get('email_cooldown_minutes', 30))} minutes."
    )
else:
    st.caption("Email alerts are currently off for Zone 1.")

st.caption("Zone 2 settings stay hidden for now so the UI matches the rest of the dashboard and only exposes live greenhouse features.")

if not is_email_configured():
    st.warning(
        "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, and SMTP_FROM "
        "in your environment to enable email delivery."
    )
