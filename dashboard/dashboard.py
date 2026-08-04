dashboard code:

"""
dashboard.py — Central Monitoring Station
Requires: pip install paho-mqtt flask
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
from flask import Flask, render_template_string, jsonify

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BROKER_IP       = "broker.hivemq.com"   # Public broker for easy cross-laptop testing
BROKER_PORT     = 1883
SUBSCRIBE_TOPIC = "drowsiness/#"        # Listens to ALL vehicles

# ─── SHARED STATE ─────────────────────────────────────────────────────────────
publishers  = {}       
state_lock  = threading.Lock()
pkt_count   = 0
last_seen_time = "--:--:--"

# ─── STATUS LOGIC ─────────────────────────────────────────────────────────────
def get_status(eye_count):
    if eye_count < 5: return "NORMAL"
    elif eye_count < 10: return "WARNING"
    elif eye_count < 20: return "ALERT"
    else: return "CRITICAL"

# ─── MQTT CALLBACKS ───────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to {BROKER_IP}")
        client.subscribe(SUBSCRIBE_TOPIC)
        print(f"[MQTT] Listening on: {SUBSCRIBE_TOPIC}")
    else:
        print(f"[MQTT] Connection failed (Code {rc})")

def on_message(client, userdata, msg):
    global pkt_count, last_seen_time
    try:
        data       = json.loads(msg.payload.decode())
        pub_ip     = data.get("publisher_ip", msg.topic.split("/")[-1])
        eye_count  = data.get("eye_count", 0)
        status     = get_status(eye_count)

        with state_lock:
            publishers[pub_ip] = {
                "publisher_ip" : pub_ip,
                "eye_count"    : eye_count,
                "buzzer_count" : data.get("buzzer_count", 0),
                "motor_count"  : data.get("motor_count",  0),
                "eye_closed"   : data.get("eye_closed",   False),
                "status"       : status,
                "last_seen"    : time.time()
            }
            pkt_count      += 1
            last_seen_time  = time.strftime("%H:%M:%S")

    except Exception as e:
        pass # Ignore malformed packets

# ─── START MQTT ──────────────────────────────────────────────────────────────
mqtt_client = mqtt.Client(client_id="fleet_dash_12345")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
mqtt_client.loop_start()

# ─── HTML DASHBOARD TEMPLATE ──────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Driver Drowsiness Dashboard</title>
  <meta http-equiv="refresh" content="1">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
    body { background: #f5f5f0; padding: 16px; }

    .header { display: flex; justify-content: space-between; align-items: center;
      padding: 14px 20px; background: #fff; border: 1px solid #e5e5e0;
      border-radius: 12px; margin-bottom: 14px; }
    .title  { font-size: 16px; font-weight: 600; color: #111; }
    .subtitle { font-size: 12px; color: #888; margin-top: 3px; }
    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
      background: #639922; margin-right: 6px; animation: pulse 1.2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
    .clock { font-size: 20px; font-weight: 600; text-align: right; }
    .upd   { font-size: 11px; color: #aaa; text-align: right; margin-top: 2px; }

    .summary { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 14px; }
    .scard  { background: #f0ede8; border-radius: 8px; padding: 12px; text-align: center; }
    .slabel { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .snum   { font-size: 28px; font-weight: 700; }
    .cn { color: #1D9E75; } .cw { color: #BA7517; }
    .ca { color: #D85A30; } .cc { color: #A32D2D; }

    .legend { display: flex; gap: 16px; align-items: center; padding: 7px 14px;
      background: #f0ede8; border-radius: 8px; margin-bottom: 12px;
      font-size: 12px; color: #666; }
    .ldot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: middle; }

    .table-card { background: #fff; border: 1px solid #e5e5e0; border-radius: 12px; overflow: hidden; margin-bottom: 14px; }
    .table-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; border-bottom: 1px solid #e5e5e0; }
    .table-title { font-size: 13px; font-weight: 600; color: #111; }
    .vpill { font-size: 11px; background: #e6f1fb; color: #0C447C; border-radius: 20px; padding: 2px 10px; font-weight: 500; }

    table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
    th { padding: 8px 16px; text-align: left; font-size: 11px; font-weight: 600; color: #888; background: #f8f8f5; border-bottom: 1px solid #e5e5e0; text-transform: uppercase; letter-spacing: 0.4px; }
    td { padding: 10px 16px; border-bottom: 1px solid #f0f0ec; color: #222; vertical-align: middle; }
    tr:last-child td { border-bottom: none; }
    tr.crit { background: rgba(162,45,45,0.06); animation: blink 1s infinite; }
    @keyframes blink { 0%,100% { background: rgba(162,45,45,0.06); } 50% { background: rgba(162,45,45,0.15); } }

    .ip-pill { font-family: Consolas, monospace; font-size: 12px; background: #f0ede8; border-radius: 4px; padding: 2px 8px; color: #444; }
    .cnt { display: flex; align-items: center; gap: 5px; }
    .cdot { display: inline-block; width: 9px; height: 9px; border-radius: 2px; }
    .cval { font-size: 13px; font-weight: 600; }
    .cunit { font-size: 11px; color: #aaa; }

    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
    .bn { background: #EAF3DE; color: #3B6D11; }
    .bw { background: #FAEEDA; color: #854F0B; }
    .ba { background: #FAECE7; color: #993C1D; }
    .bc { background: #FCEBEB; color: #A32D2D; }

    .waiting { text-align: center; padding: 30px; color: #aaa; font-size: 14px; }
    .net { display: flex; justify-content: space-between; align-items: center; padding: 9px 16px; background: #fff; border: 1px solid #e5e5e0; border-radius: 8px; font-size: 12px; }
    .mqtt-ok  { color: #3B6D11; font-weight: 600; }
    .pkt-pill { background: #f0ede8; border-radius: 20px; padding: 2px 10px; font-size: 11px; color: #666; }
  </style>
</head>
<body>

<div class="header">
  <div>
    <div class="title"><span class="dot"></span>Fleet Monitoring Command Center</div>
    <div class="subtitle">Live MQTT Telemetry</div>
  </div>
  <div>
    <div class="clock">{{ current_time }}</div>
    <div class="upd">Live feed connected</div>
  </div>
</div>

<div class="summary">
  <div class="scard"><div class="slabel">Normal</div>  <div class="snum cn">{{ counts.NORMAL   }}</div></div>
  <div class="scard"><div class="slabel">Warning</div> <div class="snum cw">{{ counts.WARNING  }}</div></div>
  <div class="scard"><div class="slabel">Alert</div>   <div class="snum ca">{{ counts.ALERT    }}</div></div>
  <div class="scard"><div class="slabel">Critical</div><div class="snum cc">{{ counts.CRITICAL }}</div></div>
</div>

<div class="legend">
  <strong style="color:#555;margin-right:4px;">Legend:</strong>
  <span><span class="ldot" style="background:#B5D4F4;"></span>Eye closed count</span>
  <span><span class="ldot" style="background:#FAC775;"></span>Buzzer triggers</span>
  <span><span class="ldot" style="background:#F5C4B3;"></span>Motor triggers</span>
</div>

<div class="table-card">
  <div class="table-header">
    <span class="table-title">Active Fleet Status</span>
    <span class="vpill">{{ publishers|length }} vehicle{{ 's' if publishers|length != 1 else '' }} connected</span>
  </div>

  {% if publishers %}
  <table>
    <thead>
      <tr>
        <th>Vehicle ID</th>
        <th>Eyes Closed (Duration)</th>
        <th>Buzzer Triggers</th>
        <th>Motor Triggers</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for ip, p in publishers.items() %}
      <tr class="{{ 'crit' if p.status == 'CRITICAL' else '' }}">
        <td><span class="ip-pill">{{ ip }}</span></td>
        <td>
          <div class="cnt">
            <span class="cdot" style="background:#B5D4F4;"></span>
            <span class="cval" style="color:#0C447C;">{{ p.eye_count }}</span>
            <span class="cunit">sec</span>
          </div>
        </td>
        <td>
          <div class="cnt">
            <span class="cdot" style="background:#FAC775;"></span>
            <span class="cval" style="color:#854F0B;">{{ p.buzzer_count }}</span>
            <span class="cunit">events</span>
          </div>
        </td>
        <td>
          <div class="cnt">
            <span class="cdot" style="background:#F5C4B3;"></span>
            <span class="cval" style="color:#712B13;">{{ p.motor_count }}</span>
            <span class="cunit">events</span>
          </div>
        </td>
        <td>
          {% if   p.status == 'NORMAL'   %}<span class="badge bn">NORMAL</span>
          {% elif p.status == 'WARNING'  %}<span class="badge bw">WARNING</span>
          {% elif p.status == 'ALERT'    %}<span class="badge ba">ALERT</span>
          {% else                        %}<span class="badge bc">CRITICAL</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="waiting">Waiting for vehicles to connect... Start a vehicle script to see data here.</div>
  {% endif %}
</div>

<div class="net">
  <span class="mqtt-ok"><span class="dot"></span>Broker: {{ broker_ip }}:1883</span>
  <span style="color:#888;">Last updated: <strong>{{ last_packet }}</strong></span>
  <span class="pkt-pill">Packets Received: {{ pkt_count }}</span>
</div>

</body>
</html>
"""

# ─── FLASK APP ────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def index():
    with state_lock:
        pubs_copy = dict(publishers)
        pkts      = pkt_count
        last_pkt  = last_seen_time

    counts = {"NORMAL": 0, "WARNING": 0, "ALERT": 0, "CRITICAL": 0}
    for p in pubs_copy.values():
        counts[p["status"]] += 1

    return render_template_string(
        HTML,
        publishers   = pubs_copy,
        counts       = counts,
        current_time = time.strftime("%H:%M:%S"),
        broker_ip    = BROKER_IP,
        last_packet  = last_pkt,
        pkt_count    = pkts
    )

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print(" 🚀 DASHBOARD RUNNING!")
    print(" 👉 Open your browser to: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    # use_reloader=False is critical so MQTT doesn't connect twice
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
