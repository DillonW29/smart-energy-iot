from flask import Flask, jsonify, render_template_string
import json
import os

app = Flask(__name__)

# Path to latest.json written by udp_service.py
DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "service",
    "latest.json"
)

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Release 2 IoT Dashboard</title>
  <meta http-equiv="refresh" content="2">
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    .card {
      padding: 16px;
      border: 1px solid #ddd;
      border-radius: 10px;
      max-width: 520px;
      margin-bottom: 16px;
    }
    .big { font-size: 36px; margin: 6px 0; }
    .warn { color: #b00020; font-weight: bold; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>Release 2 IoT Dashboard</h1>

  {% if temp %}
  <div class="card">
    <h2>Temperature</h2>
    <div>Device: <code>{{ temp.device_id }}</code></div>
    <div class="big">{{ temp.value }} °C</div>
    <div>Avg (last 10): {{ temp.avg_window }} °C</div>
    {% if temp.alerts and temp.alerts|length > 0 %}
      <div class="warn">Alerts: {{ temp.alerts }}</div>
    {% else %}
      <div>Status: Normal</div>
    {% endif %}
  </div>
  {% else %}
    <p>Waiting for temperature data...</p>
  {% endif %}

  {% if power %}
  <div class="card">
    <h2>Power Usage</h2>
    <div>Device: <code>{{ power.device_id }}</code></div>
    <div class="big">{{ power.value }} W</div>
    {% if power.alerts and power.alerts|length > 0 %}
      <div class="warn">Alerts: {{ power.alerts }}</div>
    {% else %}
      <div>Status: Normal</div>
    {% endif %}
  </div>
  {% else %}
    <p>Waiting for power data...</p>
  {% endif %}

</body>
</html>
"""

def read_latest():
    """Read latest sensor values written by udp_service.py"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

@app.route("/")
def home():
    latest = read_latest()
    return render_template_string(
        HTML,
        temp=latest.get("temperature"),
        power=latest.get("power")
    )

@app.route("/api/latest")
def api_latest():
    return jsonify(read_latest())

if __name__ == "__main__":
     app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)
