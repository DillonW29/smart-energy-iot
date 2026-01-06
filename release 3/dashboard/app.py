from flask import Flask, jsonify, render_template_string
import sqlite3, os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "ingest", "iot.db"))

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Release 3 Dashboard</title>
  <meta http-equiv="refresh" content="10">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    .row { display: flex; gap: 24px; flex-wrap: wrap; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 16px; width: 520px; }
    .big { font-size: 36px; margin: 6px 0; }
    .warn { color: #b00020; font-weight: bold; }
  </style>
</head>
<body>
  <h1>Release 3 Dashboard (History + Alerts)</h1>

  <div class="row">
    <div class="card">
      <h2>Latest Temperature</h2>
      <div class="big" id="tempLatest">—</div>
      <div id="tempAlerts"></div>
    </div>

    <div class="card">
      <h2>Latest Power</h2>
      <div class="big" id="powerLatest">—</div>
      <div id="powerAlerts"></div>
    </div>
  </div>

  <h2>Temperature History (last 50)</h2>
  <canvas id="tempChart" width="1100" height="300"></canvas>

  <h2>Power History (last 50)</h2>
  <canvas id="powerChart" width="1100" height="300"></canvas>

  <script>
    async function load() {
      const latestRes = await fetch("/api/latest");
      const latest = await latestRes.json();

      if (latest.temperature) {
        document.getElementById("tempLatest").textContent =
          `${latest.temperature.value} °C (avg: ${latest.temperature.avg_window ?? "—"})`;
        document.getElementById("tempAlerts").innerHTML =
          latest.temperature.alerts?.length ? `<span class="warn">Alerts: ${latest.temperature.alerts}</span>` : "Status: Normal";
      }

      if (latest.power) {
        document.getElementById("powerLatest").textContent = `${latest.power.value} W`;
        document.getElementById("powerAlerts").innerHTML =
          latest.power.alerts?.length ? `<span class="warn">Alerts: ${latest.power.alerts}</span>` : "Status: Normal";
      }

      const histRes = await fetch("/api/history");
      const hist = await histRes.json();

      const tempLabels = hist.temperature.map(x => new Date(x.received_ts*1000).toLocaleTimeString());
      const tempValues = hist.temperature.map(x => x.value);

      const powerLabels = hist.power.map(x => new Date(x.received_ts*1000).toLocaleTimeString());
      const powerValues = hist.power.map(x => x.value);

      new Chart(document.getElementById("tempChart"), {
        type: "line",
        data: { labels: tempLabels, datasets: [{ label: "°C", data: tempValues }] }
      });

      new Chart(document.getElementById("powerChart"), {
        type: "line",
        data: { labels: powerLabels, datasets: [{ label: "W", data: powerValues }] }
      });
    }
    load();
  </script>
</body>
</html>
"""

def q(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/history")
def api_history():
    temp = q("SELECT value, received_ts FROM readings WHERE type='temperature' ORDER BY id DESC LIMIT 50")
    power = q("SELECT value, received_ts FROM readings WHERE type='power' ORDER BY id DESC LIMIT 50")
    temp.reverse(); power.reverse()
    return jsonify({"temperature": temp, "power": power})

@app.route("/api/latest")
def api_latest():
    # latest = highest id per type
    temp = q("SELECT * FROM readings WHERE type='temperature' ORDER BY id DESC LIMIT 1")
    power = q("SELECT * FROM readings WHERE type='power' ORDER BY id DESC LIMIT 1")
    # alerts column stored as JSON string
    def normalize(rowlist):
        if not rowlist:
            return None
        row = rowlist[0]
        try:
            import json
            row["alerts"] = json.loads(row.get("alerts") or "[]")
        except:
            row["alerts"] = []
        return row
    return jsonify({"temperature": normalize(temp), "power": normalize(power)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=False)
