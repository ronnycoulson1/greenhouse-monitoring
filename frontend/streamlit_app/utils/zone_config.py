"""
Hardcoded per-zone area configuration.

Each zone page imports its own AREAS list. Areas within a zone can have
different underlying schemas (e.g. Pico W sensor data vs OpenWeather data),
so each entry carries a `schema` hint that tells db.py how to read it.

Schemas:
    "pico"    — temperature_c / humidity_rh / ts      (written by pico_server.py)
    "weather" — temp_c / humidity_pct / weather_desc / ts  (outside_weather_data)
"""

ZONE1_AREAS = [
    {
        "key":        "upper",
        "label":      "Upper canopy",
        "collection": "zone1-upper",
        "schema":     "pico",
    },
    {
        "key":        "middle",
        "label":      "Mid canopy",
        "collection": "zone1-middle",
        "schema":     "pico",
    },
    {
        "key":        "lower",
        "label":      "Root zone",
        "collection": "zone1-lower",
        "schema":     "pico",
    },
    {
        "key":        "outside",
        "label":      "Outside reference",
        "collection": "outside_weather_data",
        "schema":     "pico",
    },
]


def get_area(areas: list[dict], key: str) -> dict:
    """Look up an area config by its key. Falls back to the first entry."""
    for area in areas:
        if area["key"] == key:
            return area
    return areas[0]