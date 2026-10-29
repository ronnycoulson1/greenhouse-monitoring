import os
import random
from datetime import datetime, timedelta, timezone

import certifi
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

client = MongoClient(os.environ["MONGO_URI"], tlsCAFile=certifi.where())
db = client[os.environ["DB_NAME"]]

# collection: (base temp C, base humidity %)
PICO = {"zone1-upper": (24, 62), "zone1-middle": (22, 65), "zone1-lower": (20, 70)}
OUTSIDE = ("outside_weather_data", (12, 70))
STEP = timedelta(minutes=5)
BACKFILL = timedelta(hours=48)
KEEP = timedelta(days=7)
now = datetime.now(timezone.utc)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def pending_times(coll):
    """Timestamps from the last reading (or 48h ago) up to now, every 5 min."""
    last = coll.find_one({}, sort=[("ts", -1)])
    start = now - BACKFILL
    if last and "ts" in last:
        last_ts = last["ts"].replace(tzinfo=timezone.utc)
        if last_ts > start:
            start = last_ts + STEP
    times, t = [], start
    while t <= now:
        times.append(t)
        t += STEP
    return times, last


def walk(temp, hum, t0, h0):
    temp = clamp(temp + random.uniform(-0.4, 0.4), t0 - 5, t0 + 5)
    hum = clamp(hum + random.uniform(-1.5, 1.5), h0 - 15, h0 + 15)
    return round(temp, 1), round(hum, 1)


for name, (t0, h0) in PICO.items():
    coll = db[name]
    times, last = pending_times(coll)
    temp = (last or {}).get("temperature_c", t0)
    hum = (last or {}).get("humidity_rh", h0)
    docs = []
    for t in times:
        temp, hum = walk(temp, hum, t0, h0)
        docs.append({"ts": t, "temperature_c": temp, "humidity_rh": hum, "node_id": name})
    if docs:
        coll.insert_many(docs)
    coll.delete_many({"ts": {"$lt": now - KEEP}})
    print(f"{name}: +{len(docs)}")

name, (t0, h0) = OUTSIDE
coll = db[name]
times, last = pending_times(coll)
temp = (last or {}).get("temp_c", t0)
hum = (last or {}).get("humidity_pct", h0)
docs = []
for t in times:
    temp, hum = walk(temp, hum, t0, h0)
    docs.append({
        "ts": t,
        "temp_c": temp, "humidity_pct": hum,
        "temperature_c": temp, "humidity_rh": hum,  # Home.py reads this with the pico schema
        "weather_desc": random.choice(["Clear", "Cloudy", "Light rain"]),
    })
if docs:
    coll.insert_many(docs)
coll.delete_many({"ts": {"$lt": now - KEEP}})
print(f"{name}: +{len(docs)}")