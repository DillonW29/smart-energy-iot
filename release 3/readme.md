# Release 3 – Smart Energy & Environment Monitoring System

## Overview
Release 3 extends the IoT system by introducing message brokering, data persistence,
historical visualisation, and automation. Simulated IoT devices in Cisco Packet Tracer
generate sensor data which is transmitted via UDP, processed on a PC, stored in a
database, published to MQTT topics, and visualised through a web dashboard.

This release demonstrates a realistic end-to-end IoT architecture using
industry-standard protocols.

---

## Architecture

Packet Tracer IoT Devices (Temperature Monitor, Appliance)
        |
        |  UDP (JSON)
        v
Ingest Service (Python)
- Data validation and processing
- Rolling averages and alert detection
- SQLite persistence
- MQTT publishing
        |
        +---------------------+
        |                     |
     SQLite DB             MQTT Broker
    (iot.db)             (Mosquitto)
        |                     |
        v                     v
Flask Dashboard        MQTT Subscribers
(History + Graphs)     (Alerts)

---

## Technologies Used
- Cisco Packet Tracer
- Python 3
- UDP sockets
- MQTT (Mosquitto)
- SQLite
- Flask
- Chart.js

---

## Folder Structure

release3/
├── packet_tracer/
│   └── smart_energy_release3.pkt
├── ingest/
│   ├── ingest.py
│   └── iot.db
├── dashboard/
│   └── app.py
├── docs/
│   └── architecture.txt
└── README.md

---

## Data Flow
1. Packet Tracer devices generate temperature and power readings
2. Readings are sent via UDP as JSON
3. Ingest service processes data and generates alerts
4. Data is stored in SQLite for persistence
5. Messages are published to MQTT topics
6. Dashboard displays live and historical data
7. Alerts are delivered via MQTT

---

## MQTT Topics
- home/<device_id>/temperature
- home/<device_id>/power
- home/alerts

---

## Database Schema

readings table:
- device_id
- type
- value
- unit
- ts
- received_ts
- avg_window
- alerts

alerts table:
- device_id
- type
- alert
- value
- received_ts

---

## How to Run

1. Start the MQTT broker:
   mosquitto -v

2. Start the ingest service:
   cd release3/ingest
   python ingest.py

3. Start the dashboard:
   cd release3/dashboard
   python app.py

4. Open the dashboard in a browser:
   http://127.0.0.1:8001

5. Run the Packet Tracer simulation

---

## Alert Rules
- TEMP_HIGH: temperature ≥ 26 °C
- POWER_SPIKE: power ≥ 600 W

Alerts are stored in the database and published to MQTT.

---

## Status
Release 3 complete.
