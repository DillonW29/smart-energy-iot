# Release 2 – UDP Service + Dashboard

## What this release adds
- Structured JSON messages from the simulated sensor
- A separate UDP “service” that processes messages (rolling average + alerts)
- A basic Flask dashboard that visualises latest values

## How to run
1. Start Packet Tracer and run the sensor script (UDP sender)
2. Terminal 1:
   - cd release2/service
   - python udp_service.py
3. Terminal 2:
   - cd release2/dashboard
   - python app.py
4. Open http://127.0.0.1:8000

## Message schema
{
  "device_id": "room1-temp",
  "type": "temperature",
  "value": 23.4,
  "unit": "C",
  "ts": 1730000000
}
