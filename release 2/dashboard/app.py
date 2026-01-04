import socket, json, time
from collections import deque
from flask import Flask, jsonify, render_template_string

PORT = 5000
WINDOW = 10
TEMP_HIGH = 26.0

latest = {}
temp_history = deque(maxlen=WINDOW)

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Release 2 Dashboard</title>
  <meta http-equiv="refresh" content="3">
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    .card { padding: 16px; border: 1px solid #ddd; border-radius: 10px; max-width: 520px; }
    .big { font-size: 36px; }
    .warn { color: #b00020; font-weight: bold; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>Release 2 IoT Dashboard</h1>
  {% if temp %}
  <div class="card">
    <div>Device: <code>{{ temp.device_id }}</code></div>
    <div class="big">{{ temp.value }}°C</div>
    <div>Avg (last {{ window }}): {{ temp.avg_window }}°C</div>
    <div>Updated: {{ temp.received_ts }}</div>
    {% if temp.alerts and temp.alerts|length > 0 %}
      <div class="warn">Alerts: {{ temp.alerts }}</div>
    {% else %}
      <div>Status: Normal</div>
    {% endif %}
  </div>
  {% else %}
    <p>Waiting for temperature data...</p>
  {% endif %}
</body>
</html>
"""

def process(msg: dict) -> dict:
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

def udp_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    print(f"[dashboard] Listening UDP on {PORT}...")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            msg = json.loads(data.decode())
        except Exception:
            print("[dashboard] Bad JSON from", addr)
            continue
        msg = process(msg)
        latest[msg.get("type", "unknown")] = msg

@app.route("/")
def home():
    temp = latest.get("temperature")
    return render_template_string(HTML, temp=temp, window=WINDOW)

@app.route("/api/latest")
def api_latest():
    return jsonify(latest)

if __name__ == "__main__":
    # Run UDP receiver in background thread
    import threading
    threading.Thread(target=udp_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
   
