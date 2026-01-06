import os
import json
import time
import socket
import sqlite3
from collections import deque

import paho.mqtt.client as mqtt

# -----------------------------
# Config
# -----------------------------
UDP_PORT = 5000

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883  # if you run: mosquitto -v -p 1884 then set this to 1884

WINDOW = 10
TEMP_HIGH = 26.0
POWER_SPIKE = 600.0

# -----------------------------
# State
# -----------------------------
temp_history = deque(maxlen=WINDOW)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "iot.db")

# -----------------------------
# SQLite
# -----------------------------
def init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            type TEXT,
            value REAL,
            unit TEXT,
            ts INTEGER,
            received_ts INTEGER,
            avg_window REAL,
            alerts TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            type TEXT,
            alert TEXT,
            value REAL,
            received_ts INTEGER
        )
        """
    )

    con.commit()
    con.close()

def store_reading(msg: dict) -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO readings (device_id, type, value, unit, ts, received_ts, avg_window, alerts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            msg.get("device_id"),
            msg.get("type"),
            float(msg.get("value")),
            msg.get("unit"),
            int(msg.get("ts", 0)),
            int(msg.get("received_ts", 0)),
            msg.get("avg_window"),  # may be None for non-temperature
            json.dumps(msg.get("alerts", [])),
        ),
    )
    con.commit()
    con.close()

def store_alerts(msg: dict) -> None:
    alerts = msg.get("alerts") or []
    if not alerts:
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    for a in alerts:
        cur.execute(
            """
            INSERT INTO alerts (device_id, type, alert, value, received_ts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                msg.get("device_id"),
                msg.get("type"),
                a,
                float(msg.get("value")),
                int(msg.get("received_ts", 0)),
            ),
        )
    con.commit()
    con.close()

# -----------------------------
# Processing
# -----------------------------
def process(msg: dict) -> dict:
    msg_type = msg.get("type")
    alerts = []

    if msg_type == "temperature":
        temp = float(msg["value"])
        temp_history.append(temp)
        avg = sum(temp_history) / len(temp_history)
        msg["avg_window"] = round(avg, 2)

        if temp >= TEMP_HIGH:
            alerts.append("TEMP_HIGH")

    elif msg_type == "power":
        power = float(msg["value"])
        if power >= POWER_SPIKE:
            alerts.append("POWER_SPIKE")

    # Add more sensors later (humidity, motion, etc.) if you want.

    msg["alerts"] = alerts
    msg["received_ts"] = int(time.time())
    return msg

# -----------------------------
# MQTT
# -----------------------------
def mqtt_connect() -> mqtt.Client:
    client = mqtt.Client()

    def on_connect(c, userdata, flags, rc):
        print(f"[mqtt] connected rc={rc} host={MQTT_HOST} port={MQTT_PORT}")

    def on_disconnect(c, userdata, rc):
        print(f"[mqtt] disconnected rc={rc}")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client

def publish_reading(client: mqtt.Client, msg: dict) -> None:
    device_id = msg.get("device_id", "unknown")
    msg_type = msg.get("type", "unknown")
    topic = f"home/{device_id}/{msg_type}"
    client.publish(topic, json.dumps(msg))

def publish_alerts(client: mqtt.Client, msg: dict) -> None:
    # Publish full message when it contains alerts
    if msg.get("alerts"):
        client.publish("home/alerts", json.dumps(msg))

# -----------------------------
# Main
# -----------------------------
def run() -> None:
    init_db()
    mqtt_client = mqtt_connect()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))

    print(f"[ingest] UDP listening on {UDP_PORT}")
    print(f"[ingest] SQLite DB: {DB_PATH}")
    print(f"[ingest] MQTT broker: {MQTT_HOST}:{MQTT_PORT}")
    print("[ingest] Waiting for UDP packets...")

    while True:
        data, addr = sock.recvfrom(4096)

        try:
            msg = json.loads(data.decode(errors="strict"))
        except Exception as e:
            print("[ingest] Bad JSON from", addr, "error:", e, "raw:", data[:120])
            continue

        # Minimal validation to avoid crashes
        if "type" not in msg or "value" not in msg:
            print("[ingest] Missing fields from", addr, "msg:", msg)
            continue

        # Ensure these exist (helps consistency)
        msg.setdefault("device_id", "unknown")
        msg.setdefault("unit", "")
        msg.setdefault("ts", 0)

        msg = process(msg)

        # Persist
        store_reading(msg)
        store_alerts(msg)

        # Publish
        publish_reading(mqtt_client, msg)
        publish_alerts(mqtt_client, msg)

        print("[ingest]", msg)

if __name__ == "__main__":
    run()
