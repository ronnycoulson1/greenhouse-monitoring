import copy
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import streamlit as st

ALERT_SETTINGS_STATE_KEY = "zone_alert_thresholds"

DEFAULT_ZONE_ALERTS = {
    "zone1": {
        "enabled": True,
        "temp_min_c": 18.0,
        "temp_max_c": 28.0,
        "humidity_min_pct": 45.0,
        "humidity_max_pct": 80.0,
        "email_enabled": False,
        "email_to": "",
        "email_recipients": [],
        "email_cooldown_minutes": 30,
    },
    "zone2": {
        "enabled": True,
        "temp_min_c": 18.0,
        "temp_max_c": 28.0,
        "humidity_min_pct": 45.0,
        "humidity_max_pct": 80.0,
        "email_enabled": False,
        "email_to": "",
        "email_recipients": [],
        "email_cooldown_minutes": 30,
    },
}

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "alert_settings.json"
# Separate state file tracks last email timestamps for cooldown checks.
ALERT_STATE_FILE = DATA_DIR / "alert_email_state.json"


def _normalize_zone(zone: str) -> str:
    return (zone or "").strip().lower()


def _normalize_email_recipients(value) -> list[str]:
    # Accept CSV/newline/list input and return a deduplicated recipient list.
    if value is None:
        return []

    candidates = []
    if isinstance(value, str):
        text = value.replace(";", ",").replace("\n", ",")
        candidates = [part.strip() for part in text.split(",")]
    elif isinstance(value, list):
        candidates = [str(part).strip() for part in value]
    else:
        candidates = [str(value).strip()]

    seen = set()
    cleaned = []
    for email in candidates:
        key = email.lower()
        if not email or key in seen:
            continue
        seen.add(key)
        cleaned.append(email)
    return cleaned


def _build_settings(raw_settings: dict | None) -> dict:
    # Always start with defaults so missing or partial files remain safe.
    settings = copy.deepcopy(DEFAULT_ZONE_ALERTS)
    if not isinstance(raw_settings, dict):
        return settings

    for zone_key, zone_values in raw_settings.items():
        if not isinstance(zone_values, dict):
            continue

        normalized_zone = _normalize_zone(zone_key)
        defaults = settings.get(normalized_zone, copy.deepcopy(DEFAULT_ZONE_ALERTS["zone1"]))
        settings[normalized_zone] = {
            "enabled": bool(zone_values.get("enabled", defaults["enabled"])),
            "temp_min_c": float(zone_values.get("temp_min_c", defaults["temp_min_c"])),
            "temp_max_c": float(zone_values.get("temp_max_c", defaults["temp_max_c"])),
            "humidity_min_pct": float(zone_values.get("humidity_min_pct", defaults["humidity_min_pct"])),
            "humidity_max_pct": float(zone_values.get("humidity_max_pct", defaults["humidity_max_pct"])),
            "email_enabled": bool(zone_values.get("email_enabled", defaults["email_enabled"])),
            "email_to": str(zone_values.get("email_to", defaults["email_to"]))[:320].strip(),
            "email_recipients": _normalize_email_recipients(
                zone_values.get("email_recipients", zone_values.get("email_to", defaults["email_to"]))
            ),
            "email_cooldown_minutes": int(zone_values.get("email_cooldown_minutes", defaults["email_cooldown_minutes"])),
        }

    return settings


def _load_persisted_settings() -> dict:
    # If persistence is missing or invalid, gracefully fall back to defaults.
    if not SETTINGS_FILE.exists():
        return copy.deepcopy(DEFAULT_ZONE_ALERTS)

    try:
        raw_data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(DEFAULT_ZONE_ALERTS)

    return _build_settings(raw_data)


def _persist_settings(settings: dict) -> None:
    # Settings are stored on disk so thresholds survive app reruns/restarts.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def get_alert_settings() -> dict:
    if ALERT_SETTINGS_STATE_KEY not in st.session_state:
        st.session_state[ALERT_SETTINGS_STATE_KEY] = _load_persisted_settings()
    return st.session_state[ALERT_SETTINGS_STATE_KEY]


def get_zone_alert(zone: str) -> dict:
    zone_key = _normalize_zone(zone)
    settings = get_alert_settings()
    zone_defaults = DEFAULT_ZONE_ALERTS.get(zone_key, DEFAULT_ZONE_ALERTS["zone1"])

    if zone_key not in settings:
        settings[zone_key] = copy.deepcopy(zone_defaults)

    # Backfill newly introduced keys for old settings files.
    zone_settings = settings[zone_key]
    zone_settings.setdefault("enabled", zone_defaults["enabled"])
    zone_settings.setdefault("temp_min_c", zone_defaults["temp_min_c"])
    zone_settings.setdefault("temp_max_c", zone_defaults["temp_max_c"])
    zone_settings.setdefault("humidity_min_pct", zone_defaults["humidity_min_pct"])
    zone_settings.setdefault("humidity_max_pct", zone_defaults["humidity_max_pct"])
    zone_settings.setdefault("email_enabled", zone_defaults["email_enabled"])
    zone_settings.setdefault("email_to", zone_defaults["email_to"])
    # Keep legacy single-recipient data compatible with new recipient lists.
    zone_settings.setdefault("email_recipients", _normalize_email_recipients(zone_settings.get("email_to", "")))
    zone_settings.setdefault("email_cooldown_minutes", zone_defaults["email_cooldown_minutes"])
    return zone_settings


def update_zone_alert(
    zone: str,
    enabled: bool,
    temp_min_c: float,
    temp_max_c: float,
    humidity_min_pct: float | None = None,
    humidity_max_pct: float | None = None,
    email_enabled: bool | None = None,
    email_to: str | None = None,
    email_recipients: list[str] | None = None,
    email_cooldown_minutes: int | None = None,
) -> None:
    # Temperature and humidity ranges are validated independently.
    if temp_min_c >= temp_max_c:
        raise ValueError("Minimum temperature must be lower than maximum temperature.")

    zone_key = _normalize_zone(zone)
    current = get_zone_alert(zone_key)

    # Preserve existing email values unless explicit overrides are provided.
    cooldown = current.get("email_cooldown_minutes", 30) if email_cooldown_minutes is None else int(email_cooldown_minutes)
    if cooldown < 1:
        raise ValueError("Email cooldown must be at least 1 minute.")

    humidity_min = float(current.get("humidity_min_pct", 45.0) if humidity_min_pct is None else humidity_min_pct)
    humidity_max = float(current.get("humidity_max_pct", 80.0) if humidity_max_pct is None else humidity_max_pct)
    if humidity_min >= humidity_max:
        raise ValueError("Minimum humidity must be lower than maximum humidity.")

    if email_recipients is None:
        # Reuse existing recipients when caller does not provide a new list.
        recipients = _normalize_email_recipients(current.get("email_recipients", current.get("email_to", "")))
    else:
        recipients = _normalize_email_recipients(email_recipients)

    if email_to is not None:
        # Keep compatibility with older single-recipient input.
        recipients = _normalize_email_recipients(recipients + _normalize_email_recipients(email_to))

    settings = get_alert_settings()
    settings[zone_key] = {
        "enabled": bool(enabled),
        "temp_min_c": float(temp_min_c),
        "temp_max_c": float(temp_max_c),
        "humidity_min_pct": humidity_min,
        "humidity_max_pct": humidity_max,
        "email_enabled": bool(current.get("email_enabled", False) if email_enabled is None else email_enabled),
        # Keep email_to in sync for legacy readers that still expect one address.
        "email_to": (recipients[0] if recipients else ""),
        "email_recipients": recipients,
        "email_cooldown_minutes": cooldown,
    }
    _persist_settings(settings)


def evaluate_temperature_alert(temp_c: float, zone: str) -> dict | None:
    if temp_c is None:
        return None

    zone_settings = get_zone_alert(zone)
    if not zone_settings.get("enabled", True):
        return None

    temp_min = float(zone_settings["temp_min_c"])
    temp_max = float(zone_settings["temp_max_c"])
    temp_value = float(temp_c)

    # Alert thresholds are evaluated in Celsius regardless of display unit.
    if temp_value < temp_min:
        return {
            "kind": "low",
            "zone": _normalize_zone(zone),
            "temp_c": temp_value,
            "threshold_c": temp_min,
        }

    if temp_value > temp_max:
        return {
            "kind": "high",
            "zone": _normalize_zone(zone),
            "temp_c": temp_value,
            "threshold_c": temp_max,
        }

    return None


def evaluate_humidity_alert(humidity_pct: float, zone: str) -> dict | None:
    if humidity_pct is None:
        return None

    zone_settings = get_zone_alert(zone)
    if not zone_settings.get("enabled", True):
        return None

    # Humidity is evaluated in raw percent, so no unit conversion is required.
    humidity_min = float(zone_settings["humidity_min_pct"])
    humidity_max = float(zone_settings["humidity_max_pct"])
    humidity_value = float(humidity_pct)

    if humidity_value < humidity_min:
        return {
            "kind": "low",
            "zone": _normalize_zone(zone),
            "humidity_pct": humidity_value,
            "threshold_pct": humidity_min,
        }

    if humidity_value > humidity_max:
        return {
            "kind": "high",
            "zone": _normalize_zone(zone),
            "humidity_pct": humidity_value,
            "threshold_pct": humidity_max,
        }

    return None


def _load_email_state() -> dict:
    if not ALERT_STATE_FILE.exists():
        return {}
    try:
        state = json.loads(ALERT_STATE_FILE.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _persist_email_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ALERT_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def should_send_email_alert(zone: str, kind: str, cooldown_minutes: int, metric: str = "temperature") -> bool:
    normalized_zone = _normalize_zone(zone)
    alert_kind = (kind or "").strip().lower()
    if alert_kind not in {"low", "high"}:
        return False

    # Metric-qualified keys let temperature and humidity cooldowns run independently.
    metric_key = (metric or "temperature").strip().lower()
    state_key = f"{metric_key}_{alert_kind}"

    state = _load_email_state()
    zone_state = state.get(normalized_zone, {})
    last_sent = zone_state.get(state_key)

    if not last_sent:
        return True

    try:
        last_sent_dt = datetime.fromisoformat(last_sent)
    except ValueError:
        return True

    if last_sent_dt.tzinfo is None:
        last_sent_dt = last_sent_dt.replace(tzinfo=timezone.utc)

    wait_until = last_sent_dt + timedelta(minutes=max(1, int(cooldown_minutes)))
    return datetime.now(timezone.utc) >= wait_until


def mark_email_alert_sent(zone: str, kind: str, metric: str = "temperature") -> None:
    normalized_zone = _normalize_zone(zone)
    alert_kind = (kind or "").strip().lower()
    if alert_kind not in {"low", "high"}:
        return

    # Persist the send timestamp used by cooldown enforcement.
    metric_key = (metric or "temperature").strip().lower()
    state_key = f"{metric_key}_{alert_kind}"

    state = _load_email_state()
    state.setdefault(normalized_zone, {})
    state[normalized_zone][state_key] = datetime.now(timezone.utc).isoformat()
    _persist_email_state(state)