# Environment-backed settings used across API, DB, and alert email features.
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

API_KEY   = (os.getenv("OPENWEATHER_API_KEY") or "").strip()
MONGO_URI = (os.getenv("MONGO_URI") or "").strip()
DB_NAME   = (os.getenv("DB_NAME") or "").strip()

SMTP_HOST = (os.getenv("SMTP_HOST") or "").strip()
SMTP_PORT = int((os.getenv("SMTP_PORT") or "587").strip())
SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
SMTP_PASS = (os.getenv("SMTP_PASS") or "").strip()
# Use SMTP_USER as the default sender when SMTP_FROM is not explicitly set.
SMTP_FROM = (os.getenv("SMTP_FROM") or SMTP_USER).strip()
SMTP_USE_TLS = (os.getenv("SMTP_USE_TLS") or "true").strip().lower() in {"1", "true", "yes", "on"}

CITY = "Akron,US"