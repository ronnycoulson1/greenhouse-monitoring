import requests
import streamlit as st
from utils.config import API_KEY, CITY
from utils.conversion import fahrenheitToCelsius

@st.cache_data(ttl=300)
def fetch_weather_data(api_key: str = API_KEY, city: str = CITY):
    if not api_key:
        return None, None, None, {"error": "Missing OPENWEATHER_API_KEY"}

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=imperial&appid={api_key}"

    try:
        resp = requests.get(url, timeout=10)
        debug = {
            "url": url,
            "status_code": resp.status_code,
            "text_preview": resp.text[:300],
        }
        if resp.status_code != 200:
            return None, None, None, debug

        data = resp.json()
        main = data.get("main") or {}
        weather_arr = data.get("weather") or [{}]
        temp_f = main.get("temp")
        humidity = main.get("humidity")
        desc = (weather_arr[0] or {}).get("description")

        if temp_f is None or humidity is None or desc is None:
            debug["parse_error"] = "Missing expected fields in JSON"
            debug["json_keys"] = list(data.keys())
            return None, None, None, debug

        temp_c = fahrenheitToCelsius(temp_f)
        return temp_c, humidity, desc, debug

    except Exception as e:
        return None, None, None, {"error": str(e)}