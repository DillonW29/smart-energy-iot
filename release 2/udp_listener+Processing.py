import socket, json, time
from collections import deque

PORT = 5000
WINDOW = 10
TEMP_HIGH = 26.0

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

if __name__ == "__main__":
    run()
