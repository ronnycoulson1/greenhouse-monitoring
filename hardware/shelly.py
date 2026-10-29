from flask import Flask, jsonify
from pymongo import MongoClient
from datetime import datetime, timezone
import requests

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "")
client = MongoClient(MONGO_URI)
db = client["shelly_data"]
collection = db["ht_readings"]

SHELLY_IP = "172.20.10.5"


def get_shelly_data():
    url = f"http://{SHELLY_IP}/rpc/Shelly.GetStatus"
    res = requests.get(url, timeout=5)
    res.raise_for_status()
    data = res.json()

    temp = None
    humidity = None
    battery = None

    for key, value in data.items():
        if key.startswith("temperature") and isinstance(value, dict):
            temp = value.get("tC") or value.get("value")
        elif key.startswith("humidity") and isinstance(value, dict):
            humidity = value.get("rh") or value.get("value")
        elif key.startswith("devicepower") and isinstance(value, dict):
            battery_info = value.get("battery")
            if isinstance(battery_info, dict):
                battery = battery_info.get("percent")

    return {
        "sensor_id": "shelly_ht",
        "temperature": temp,
        "humidity": humidity,
        "battery": battery,
        "timestamp": datetime.now(timezone.utc)
    }


@app.route("/")
def home():
    return jsonify({"message": "Server is running. Use /api/shelly"}), 200


@app.route("/api/shelly", methods=["GET"])
def fetch_shelly():
    try:
        record = get_shelly_data()
        result = collection.insert_one(record)

        response_data = {
            "status": "success",
            "data": {
                "id": str(result.inserted_id),
                "sensor_id": record["sensor_id"],
                "temperature": record["temperature"],
                "humidity": record["humidity"],
                "battery": record["battery"],
                "timestamp": record["timestamp"].isoformat()
            }
        }

        print(f"Stored: {response_data['data']}")
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

