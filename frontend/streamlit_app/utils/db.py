from pymongo import MongoClient
import certifi
import streamlit as st
import pandas as pd
from utils.config import MONGO_URI, DB_NAME


# --------------------------------------------------
# Shared connection
# --------------------------------------------------

@st.cache_resource
def init_connection():
    if not MONGO_URI or not DB_NAME:
        return None, None
    #client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    if MONGO_URI.startswith("mongodb+srv://"):
        client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    else:
        client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return client, db


# --------------------------------------------------
# Schema normalization
# --------------------------------------------------
#
# The app supports multiple collection schemas (Pico W sensor inserts vs
# the outside_weather_data collection written by the external WeatherAPI
# pipeline). All public loaders below normalize results to a canonical
# shape so the rest of the app sees the same field names regardless of
# which collection it's reading from:
#
#     ts            -> datetime
#     temp_c        -> float   (Celsius)
#     humidity_pct  -> float   (0-100)
#     weather_desc  -> str     (only present for "weather" schema)
#     node_id       -> str     (only present for "pico"    schema)
#
# Source field mapping per schema:
#
#     "pico":    temperature_c -> temp_c, humidity_rh -> humidity_pct
#     "weather": temp_c passthrough,      humidity_pct passthrough
#

# Canonical projections we need to pull from each schema.
_PROJECTIONS = {
    "pico": {
        "_id": 0,
        "ts": 1,
        "temperature_c": 1,
        "humidity_rh": 1,
        "node_id": 1,
    },
    "weather": {
        "_id": 0,
        "ts": 1,
        "temp_c": 1,
        "humidity_pct": 1,
        "weather_desc": 1,
    },
}


def _normalize_doc(doc: dict, schema: str) -> dict:
    """Rewrite a raw Mongo doc into the canonical shape."""
    if doc is None:
        return None
    if schema == "pico":
        out = {
            "ts":           doc.get("ts"),
            "temp_c":       doc.get("temperature_c"),
            "humidity_pct": doc.get("humidity_rh"),
        }
        if "node_id" in doc:
            out["node_id"] = doc["node_id"]
        return out
    # schema == "weather" (or unknown — return as-is with canonical fields)
    return {
        "ts":           doc.get("ts"),
        "temp_c":       doc.get("temp_c"),
        "humidity_pct": doc.get("humidity_pct"),
        "weather_desc": doc.get("weather_desc"),
    }


def _normalize_df(df: pd.DataFrame, schema: str) -> pd.DataFrame:
    """Rename DataFrame columns to the canonical shape."""
    if df is None or df.empty:
        return df
    if schema == "pico":
        df = df.rename(columns={
            "temperature_c": "temp_c",
            "humidity_rh":   "humidity_pct",
        })
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"])
    return df


# --------------------------------------------------
# Public loaders (collection + schema driven)
# --------------------------------------------------

@st.cache_data(ttl=15)
def load_latest(collection: str, schema: str):
    """Return the most recent document from a collection, normalized."""
    _, db = init_connection()
    if db is None:
        return None
    doc = db[collection].find_one({}, sort=[("ts", -1)])
    return _normalize_doc(doc, schema)


@st.cache_data(ttl=60)
def load_history(
    collection: str,
    schema: str,
    hours: int | None = 24,
    start_ts=None,
    end_ts=None,
) -> pd.DataFrame:
    """
    Return a normalized DataFrame of readings from a collection, either for
    the last `hours` hours or for a specific [start_ts, end_ts] UTC window.
    """
    _, db = init_connection()
    if db is None:
        return pd.DataFrame()

    if start_ts and end_ts:
        ts_query = {"$gte": start_ts, "$lte": end_ts}
    elif hours is not None:
        since = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)
        ts_query = {"$gte": since.to_pydatetime()}
    else:
        ts_query = None

    query = {"ts": ts_query} if ts_query is not None else {}
    projection = _PROJECTIONS.get(schema, _PROJECTIONS["weather"])

    docs = list(
        db[collection]
        .find(query, projection)
        .sort("ts", 1)
    )

    df = pd.DataFrame(docs)
    return _normalize_df(df, schema)


@st.cache_data(ttl=30)
def load_readings(collection: str, schema: str, limit: int = 50) -> list[dict]:
    """Return the latest `limit` documents from a collection, normalized."""
    _, db = init_connection()
    if db is None:
        return []
    projection = _PROJECTIONS.get(schema, _PROJECTIONS["weather"])
    docs = list(
        db[collection]
        .find({}, projection)
        .sort("ts", -1)
        .limit(limit)
    )
    return [_normalize_doc(d, schema) for d in docs]