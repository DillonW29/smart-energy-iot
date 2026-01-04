import socket, json, time, os
from collections import deque

PORT = 5000
WINDOW = 10
TEMP_HIGH = 26.0
POWER_SPIKE = 600.0
# Always write latest.json in the SAME folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_PATH = os.path.join(BASE_DIR, "latest.json")
latest = {}  # latest reading by type
temp_history = deque(maxlen=WINDOW)

def process(msg: dict) -> dict:
    """Add derived metrics + alerts."""
    if msg.get("type") == "temperature":
        temp = float(msg["value"])
        temp_history.append(temp)
        avg = sum(temp_history) / len(temp_history)

        alerts = []
        if temp >= TEMP_HIGH:
            alerts.append("TEMP_HIGH")

        msg["avg_window"] = round(avg, 2)
        msg["alerts"] = alerts
    if msg.get("type") == "power":
        power = float(msg["value"])
        alerts = []
        if power >= POWER_SPIKE:
            alerts.append("POWER_SPIKE")
            msg["alerts"] = alerts

    msg["received_ts"] = int(time.time())
    return msg

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    print(f"[service] Listening UDP on {PORT}...")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            msg = json.loads(data.decode())
        except Exception:
            print("[service] Bad JSON from", addr, data[:80])
            continue

        msg = process(msg)
        latest[msg.get("type", "unknown")] = msg
        print("[service]", msg)
        
        with open(LATEST_PATH, "w") as f:
            json.dump(latest, f)


if __name__ == "__main__":
    run()
