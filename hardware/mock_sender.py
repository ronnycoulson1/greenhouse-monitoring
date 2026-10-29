"""
dummy_sender.py
---------------
Runs on PC 
Simulates a Pico W sensor node by generating dummy data and POSTing
it to the Flask server every INTERVAL seconds.

Usage:
    python dummy_sender.py

Make sure pico_server.py is already running in another terminal first.
"""

import time
import requests
from mock_sensor import MockSensorNode

# --------------------------------------------------
# Config — change SERVER_URL to match your machine's
# local IP if running on a different device.
# --------------------------------------------------

SERVER_URL = "http://192.168.1.147:5000/data"
INTERVAL   = 5   # seconds between each reading


# --------------------------------------------------
# Main loop
# --------------------------------------------------

def main():
    sensor = MockSensorNode(
        node_id="pico_prototype_1_dht22_upper",
        zone="zone1",
        area="upper_plants",
    )
    
    sensor2 = MockSensorNode(
        node_id="pico_prototype_1_dht22_middle",
        zone="zone1",
        area="upper_plants",
    )
    
    sensor3 = MockSensorNode(
        node_id="pico_prototype_1_dht22_low",
        zone="zone1",
        area="upper_plants",
    )
    
    sensor4 = MockSensorNode(
        node_id="pico_prototype_1_dht22_outside",
        zone="zone1",
        area="upper_plants",
    )

    print(f"[Dummy Sender] Starting — POSTing to {SERVER_URL} every {INTERVAL}s")
    print("[Dummy Sender] Press Ctrl+C to stop.\n")

    while True:
        #===================================
        # 1. Generate a fake reading
        payload = sensor.get_readings()
        print(f"[Reading] {payload}")

        # 2. POST to the Flask server
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=5)
            data     = response.json()

            if response.status_code == 200:
                print(f"[Server] Saved  — id: {data.get('id')}")
            else:
                print(f"[Server] Error  — {data.get('message')}")

        except requests.exceptions.ConnectionError:
            print("[Server] Could not connect — is pico_server.py running?")
        except Exception as e:
            print(f"[Error] {e}")

        print(f"[Waiting] Next reading in {INTERVAL}s...\n")
        time.sleep(INTERVAL)
        
        #===================================
        # 1. Generate a fake reading
        payload = sensor4.get_readings()
        print(f"[Reading] {payload}")

        # 2. POST to the Flask server
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=5)
            data     = response.json()

            if response.status_code == 200:
                print(f"[Server] Saved  — id: {data.get('id')}")
            else:
                print(f"[Server] Error  — {data.get('message')}")

        except requests.exceptions.ConnectionError:
            print("[Server] Could not connect — is pico_server.py running?")
        except Exception as e:
            print(f"[Error] {e}")

        print(f"[Waiting] Next reading in {INTERVAL}s...\n")
        time.sleep(INTERVAL)
        
        payload = sensor4.get_readings()
        print(f"[Reading] {payload}")

        # 2. POST to the Flask server
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=5)
            data     = response.json()

            if response.status_code == 200:
                print(f"[Server] Saved  — id: {data.get('id')}")
            else:
                print(f"[Server] Error  — {data.get('message')}")

        except requests.exceptions.ConnectionError:
            print("[Server] Could not connect — is pico_server.py running?")
        except Exception as e:
            print(f"[Error] {e}")

        print(f"[Waiting] Next reading in {INTERVAL}s...\n")
        time.sleep(INTERVAL)
        
        #===================================
        # 1. Generate a fake reading
        payload = sensor2.get_readings()
        print(f"[Reading] {payload}")

        # 2. POST to the Flask server
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=5)
            data     = response.json()

            if response.status_code == 200:
                print(f"[Server] Saved  — id: {data.get('id')}")
            else:
                print(f"[Server] Error  — {data.get('message')}")

        except requests.exceptions.ConnectionError:
            print("[Server] Could not connect — is pico_server.py running?")
        except Exception as e:
            print(f"[Error] {e}")

        print(f"[Waiting] Next reading in {INTERVAL}s...\n")
        time.sleep(INTERVAL)
        
        #===================================
        # 1. Generate a fake reading
        payload = sensor3.get_readings()
        print(f"[Reading] {payload}")

        # 2. POST to the Flask server
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=5)
            data     = response.json()

            if response.status_code == 200:
                print(f"[Server] Saved  — id: {data.get('id')}")
            else:
                print(f"[Server] Error  — {data.get('message')}")

        except requests.exceptions.ConnectionError:
            print("[Server] Could not connect — is pico_server.py running?")
        except Exception as e:
            print(f"[Error] {e}")

        print(f"[Waiting] Next reading in {INTERVAL}s...\n")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()