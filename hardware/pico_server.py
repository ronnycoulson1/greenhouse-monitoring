from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timezone 
import certifi
import os
import logging
from dotenv import load_dotenv

# -- Load env first --
load_dotenv()
# --------------------

# -- Start Log --
logging.getLogger("werkzeug").setLevel(logging.ERROR)
#----------------

# --------------------------------------------------
# App + DB init
# --------------------------------------------------



MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME   = os.getenv("DB_NAME", "greenhouse_db").strip()


app = Flask(__name__)
# --------------------------------------------------
# Node Registar
#
# All known nodes go here
# Sorted by collection -> sent to mongo
# Collection can be shared by multiple nodes
# --------------------------------------------------

NODE_REGISTRY = {
    "pico_prototype_1_dht22_upper": {
        "zone":       "zone1",
        "area":       "upper_plants",
        "collection": "zone1-upper", 
    },
    
    "pico_prototype_1_dht22_middle": {
        "zone":       "zone1",
        "area":       "upper_plants",
        "collection": "zone1-middle", 
    },
    
    "pico_prototype_1_dht22_low": {
        "zone":       "zone1",
        "area":       "upper_plants",
        "collection": "zone1-lower", 
    },
    
    "pico_prototype_1_dht22_outside": {
        "zone":       "zone1",
        "area":       "upper_plants",
        "collection": "outside_weather_data", 
    },
    #"Example_pico_ID": {
    #    "zone":       "zone 1/2/3 ...",
    #    "area":       "Up/mid/bot",
    #    "collection": "mongo collection",
    #},
    
}
try:
    client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    
    client.admin.command("ping")
    
    db = client[DB_NAME]
    _db_ok = True
except Exception as e:
    client = db = None
    _db_ok = False
    _db_err = str(e)


_connected_nodes: dict = {}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

# -- Timestamp
def _ts() -> str: # -- HH:MM:SS string for log
    return datetime.now().strftime("%H:%M:%S")


def _print_banner():
    width = 30
    print("┌" + "─" * width + "┐")
    print("│" + "  Greenhouse Pico W Server".center(width) + "│")
    print("├" + "─" * width + "┤")
 
    if _db_ok:
        print("│" + f"  DB    Connected to '{DB_NAME}'".ljust(width) + "│")
    else:
        print("│" + f"  DB    {_db_err}"[:width].ljust(width) + "│")
 
    print("├" + "─" * width + "┤")
    print("│" + f"  Registered nodes: {len(NODE_REGISTRY)}".ljust(width) + "│")
    for nid, cfg in NODE_REGISTRY.items():
        line = f"     {nid}    {cfg['zone']} / {cfg['area']}"
        print("│" + line[:width].ljust(width) + "│")
 
    print("└" + "─" * width + "┘")
 







# --------------------------------------------------
# Routes
# --------------------------------------------------

# -- NetworkRoutes
@app.route("/ping", methods=["GET"])
def ping():
    #Health-check - confirm 
    ip = request.remote_addr
    print(f"  [{_ts()}]  PING  -  {ip}")
    return jsonify({"status": "ok", "message": "Server is running"}), 200
    
@app.route("/nodes", methods=["GET"])
def list_nodes():
    #Returns a summary of all nodes that have connected this session.
    #http://<server-ip>:5000/nodes
    summary = {}
    for nid, state in _connected_nodes.items():
        cfg = NODE_REGISTRY.get(nid, {})
        summary[nid] = {
            "ip":            state["ip"],
            "zone":          cfg.get("zone", "unknown"),
            "area":          cfg.get("area", "unknown"),
            "first_seen":    state["first_seen"].isoformat(),
            "reading_count": state["reading_count"],
        }
    return jsonify({"connected_nodes": summary, "count": len(summary)}), 200

###############

# -- Data Routes
@app.route("/data", methods=["POST"])
def receive_data():
    """
    Accepts a JSON POST from the Pico W and saves it to MongoDB.

    Expected payload from Pico:
    {
        "node_id":        - Needs to match in registry
        "temperature_c":  - x.xx
        "humidity_rh":    - y.yy
    }
    """
    
    ip = request.remote_addr
    
    # ── 1. Parse incoming JSON 
    incoming = request.get_json(silent=True)

    if not incoming:
        print(f"  [{_ts()}]    Bad request from {ip} — no JSON body")
        return jsonify({"status":
                        "error", 
                        "message": 
                        "No JSON received"
                        }
                       ), 400

    #print(f"[POST /data] Received: {incoming}")         ------------------------------

    # -- Validate required fields
    required = ["node_id", "temperature_c", "humidity_rh"]
    missing  = [f for f in required if f not in incoming]

    if missing:
        print(f"  [{_ts()}] Bad request from {ip} — missing fields: {missing}")
        return jsonify({"status": "error",
                        "message": f"Missing fields: {missing}"
                        }
                       ), 400

    # -- Get sent node and log it
    node_id = incoming["node_id"] 
    
    # -- Validate in Node registry first
    if node_id not in NODE_REGISTRY:
        print(f"  [{_ts()}]    Unknown node '{node_id}' from {ip} — rejected")
        return jsonify({
            "status":  "error",
            "message": f"Unknown node_id '{node_id}'. Node not registered.",
        }), 403
 
    cfg             = NODE_REGISTRY[node_id]
    zone            = cfg["zone"]
    area            = cfg["area"]
    collection_name = cfg["collection"]
    
    
    #Successful new node connection print
    if node_id not in _connected_nodes:
        _connected_nodes[node_id] = {
            "ip":            ip,
            "first_seen":    datetime.now(),
            "reading_count": 0,
        }
        print(f"  [{_ts()}]  !  New device connected")
        print(f"             ID         : {node_id}")
        print(f"             IP         : {ip}")
        print(f"             Zone/Area  : {zone} / {area}")
        print(f"             Collection : {collection_name}")
        print(f"             {'─' * 38}") #draw ------
        
    
    # -- Log the Reading
    temp_c   = float(incoming["temperature_c"])
    humidity = float(incoming["humidity_rh"])
    print(
        f"  [{_ts()}]    {node_id}  "
        f"│  {temp_c:.1f}°C  "
        f"│  {humidity:.0f}% RH  "
        f"│  {ip}"
    )
    
    _connected_nodes[node_id]["reading_count"] += 1
    count = _connected_nodes[node_id]["reading_count"]
    
    print(
        f"  [{_ts()}]    {node_id}"
        f"  │  {temp_c:.1f}°C"
        f"  │  {humidity:.0f}% RH"
        f"  │  #{count}"
    )
    
    # -- Build the document package to send to mongo
    record = {
        "node_id":       incoming["node_id"],
        "zone":          incoming.get("zone", "zone1"),
        "area":          incoming.get("area", "upper_plants"),
        "source":        "pico_w",
        "temperature_c": float(incoming["temperature_c"]),
        "humidity_rh":   float(incoming["humidity_rh"]),
        "ts":            datetime.utcnow(),
    }

    # ── 4. Insert into MongoDB ──────────────────────────────────────────────
    if db is None:
        print(f"  [{_ts()}]     DB unavailable — reading from {node_id} not saved")
        return jsonify({"status": "error", "message": "Database unavailable"}), 503

    try:
        collection = db[collection_name]
        result     = collection.insert_one(record)
        print(f"  [{_ts()}]    Saved to '{collection_name}'        │  _id: {result.inserted_id}")
    except Exception as e:
        print(f"  [{_ts()}]     DB insert failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    # ── 5. Respond to Pico ──────────────────────────────────────────────────
    return jsonify({
        "status":  "success",
        "message": "Data saved",
        "id":      str(result.inserted_id)
    }), 200


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    # host='0.0.0.0' lets devices on the same Wi-Fi reach this server.
    # Change port if 5000 is taken.
    print("[Server] Starting on 0.0.0.0:5000 ...")
    
    _print_banner()
    
    app.run(host="0.0.0.0", port=5000, debug=False)