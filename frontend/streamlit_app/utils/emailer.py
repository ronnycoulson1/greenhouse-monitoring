import smtplib
from email.message import EmailMessage

from utils.config import SMTP_FROM, SMTP_HOST, SMTP_PASS, SMTP_PORT, SMTP_USE_TLS, SMTP_USER


def is_email_configured() -> bool:
    # Delivery is enabled only when all required SMTP settings are present.
    return bool(SMTP_HOST and SMTP_PORT and SMTP_FROM and SMTP_USER and SMTP_PASS)


def send_environment_alert_email(
    recipient: str,
    zone: str,
    metric: str,
    kind: str,
    current_value: float,
    threshold_value: float,
    unit: str,
    alt_value_text: str = "",
    alt_threshold_text: str = "",
) -> tuple[bool, str]:
    # Generic sender used by both temperature and humidity alert wrappers.
    if not recipient:
        return False, "Missing recipient email."

    if not is_email_configured():
        return False, "SMTP is not configured."

    zone_label = (zone or "").replace("_", " ").title()
    kind_label = "LOW" if kind == "low" else "HIGH"
    metric_label = (metric or "Metric").replace("_", " ").title()

    msg = EmailMessage()
    msg["Subject"] = f"[{zone_label}] {metric_label} {kind_label} Alert"
    msg["From"] = SMTP_FROM
    msg["To"] = recipient
    current_line = f"Current {metric_label.lower()}: {current_value:.1f} {unit}"
    threshold_line = f"Threshold: {threshold_value:.1f} {unit}"
    if alt_value_text:
        current_line += f" / {alt_value_text}"
    if alt_threshold_text:
        threshold_line += f" / {alt_threshold_text}"

    msg.set_content(
        f"{metric_label} alert triggered.\n\n"
        f"Zone: {zone_label}\n"
        f"Alert type: {kind_label}\n"
        f"{current_line}\n"
        f"{threshold_line}\n"
    )

    # SMTP connection/login/send are handled in one block so failures return cleanly.
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as exc:
        return False, f"Email send failed: {exc}"

    return True, "Email notification sent."


def send_temperature_alert_email(
    recipient: str,
    zone: str,
    kind: str,
    temp_c: float,
    threshold_c: float,
) -> tuple[bool, str]:
    # Temperature emails include both Celsius and Fahrenheit for readability.
    temp_f = (temp_c * 9.0 / 5.0) + 32.0
    threshold_f = (threshold_c * 9.0 / 5.0) + 32.0
    return send_environment_alert_email(
        recipient=recipient,
        zone=zone,
        metric="temperature",
        kind=kind,
        current_value=temp_c,
        threshold_value=threshold_c,
        unit="C",
        alt_value_text=f"{temp_f:.1f} F",
        alt_threshold_text=f"{threshold_f:.1f} F",
    )


def send_humidity_alert_email(
    recipient: str,
    zone: str,
    kind: str,
    humidity_pct: float,
    threshold_pct: float,
) -> tuple[bool, str]:
    # Humidity uses percent units, so no alternate-unit text is needed.
    return send_environment_alert_email(
        recipient=recipient,
        zone=zone,
        metric="humidity",
        kind=kind,
        current_value=humidity_pct,
        threshold_value=threshold_pct,
        unit="%",
    )