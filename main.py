from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import openai, os, json, uuid, csv, io

app = FastAPI(title="RamsTech")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ═══════════════════════════════════
# STATIC DATA
# ═══════════════════════════════════
FAULT_CODES = {
    "P0101": {"code":"P0101","description":"Mass Air Flow Circuit","system":"Engine","severity":"Medium",
              "causes":["Dirty MAF","Air leaks","Clogged filter"],"symptoms":["Poor economy","Loss of power"],
              "steps":["Check filter","Inspect intake","Clean MAF"]},
    "P0300": {"code":"P0300","description":"Multiple Cylinder Misfire","system":"Engine","severity":"High",
              "causes":["Faulty plugs","Bad coils","Fuel issues"],"symptoms":["Engine shaking","Loss of power"],
              "steps":["Scan cylinders","Check plugs","Test coils"]},
    "P0401": {"code":"P0401","description":"EGR Flow Insufficient","system":"Engine","severity":"Medium",
              "causes":["Clogged EGR","Blocked passages"],"symptoms":["Check engine light"],
              "steps":["Inspect EGR","Check passages"]},
    "P0700": {"code":"P0700","description":"Transmission Control System","system":"Transmission","severity":"High",
              "causes":["Internal fault","TCM problem"],"symptoms":["Slipping","Harsh shifting"],
              "steps":["Scan TCM","Check fluid"]},
    "P0087": {"code":"P0087","description":"Fuel Rail Pressure Low","system":"Diesel","severity":"High",
              "causes":["Faulty HP pump","Clogged filter"],"symptoms":["Won't start","Loss of power"],
              "steps":["Check pressure","Inspect filter"]},
    "HYD-001": {"code":"HYD-001","description":"Low Hydraulic Pressure","system":"Hydraulic","severity":"High",
                "causes":["Worn pump","Leaks","Low fluid"],"symptoms":["Slow operation","Weak lifting"],
                "steps":["Check fluid","Test pressure"]},
    "PNEU-001": {"code":"PNEU-001","description":"Air Compressor No Pressure","system":"Pneumatic","severity":"High",
                 "causes":["Worn rings","Leaking valves"],"symptoms":["Low pressure"],
                 "steps":["Check belt","Test output"]},
}

WMI_DB = {"1HG":("Honda","USA"),"1FT":("Ford","USA"),"JHM":("Honda","Japan"),
          "JTD":("Toyota","Japan"),"JTM":("Toyota","Japan"),"KMH":("Hyundai","Korea"),
          "KNA":("Kia","Korea"),"WBA":("BMW","Germany"),"WDB":("Mercedes-Benz","Germany"),
          "WVW":("Volkswagen","Germany"),"AHT":("Toyota SA","South Africa"),"ADB":("Mercedes SA","South Africa")}

YEAR_CODES = {"A":2010,"B":2011,"C":2012,"D":2013,"E":2014,"F":2015,"G":2016,"H":2017,
              "J":2018,"K":2019,"L":2020,"M":2021,"N":2022,"P":2023,"R":2024,
              "Y":2000,"1":2001,"2":2002,"3":2003,"4":2004}

TORQUE_SPECS = [
    {"size":"M6","grade":"8.8","nm":10,"ftlb":7.4,"use":"Small brackets"},
    {"size":"M8","grade":"8.8","nm":25,"ftlb":18.4,"use":"Engine brackets"},
    {"size":"M10","grade":"8.8","nm":50,"ftlb":37,"use":"Subframe bolts"},
    {"size":"M12","grade":"8.8","nm":90,"ftlb":66,"use":"Wheel hubs"},
    {"size":"M14","grade":"8.8","nm":140,"ftlb":103,"use":"Heavy brackets"},
    {"size":"M16","grade":"8.8","nm":215,"ftlb":159,"use":"Chassis bolts"},
    {"size":"M20","grade":"8.8","nm":425,"ftlb":313,"use":"Truck chassis"},
    {"size":"M8","grade":"10.9","nm":35,"ftlb":25.8,"use":"Cylinder head (small)"},
    {"size":"M10","grade":"10.9","nm":70,"ftlb":51.6,"use":"Cylinder head bolts"},
    {"size":"M12","grade":"10.9","nm":120,"ftlb":88.5,"use":"Head bolts"},
    {"size":"M14","grade":"10.9","nm":190,"ftlb":140,"use":"Head (diesel)"},
    {"size":"M16","grade":"10.9","nm":295,"ftlb":218,"use":"Heavy diesel"},
    {"size":"M12","grade":"12.9","nm":145,"ftlb":107,"use":"Racing"},
    {"size":"M10","grade":"12.9","nm":83,"ftlb":61.2,"use":"Performance"},
]

TORQUE_SEQUENCES = [
    {"component":"Cylinder Head — 4 Cyl","pattern":"Star",
     "steps":["Stage 1: 40 Nm","Stage 2: 80 Nm","Stage 3: +90°","Stage 4: +90°"],
     "note":"Replace TTY bolts."},
    {"component":"Wheel Nuts — Car","pattern":"Star",
     "steps":["Stage 1: 60 Nm","Final: 110 Nm"],"note":"Re-torque after 50-100 km."},
    {"component":"Wheel Nuts — Bakkie","pattern":"Star",
     "steps":["Stage 1: 100 Nm","Final: 140 Nm"],"note":"Hilux, Ranger, Amarok."},
    {"component":"Wheel Nuts — Truck","pattern":"Star",
     "steps":["Stage 1: 400 Nm","Stage 2: 500 Nm","Final: 600 Nm"],"note":"10-stud."},
    {"component":"Spark Plugs","pattern":"Linear",
     "steps":["Cast iron: 25 Nm","Aluminum: 18 Nm"],"note":"Do NOT overtighten."},
    {"component":"Oil Drain Plug","pattern":"Linear",
     "steps":["Steel M12: 25 Nm","Alum M12: 18 Nm"],"note":"Replace washer."},
]

PARTS_CATALOG = [
    {"number":"04152-YZZA1","name":"Oil Filter","brand":"Toyota","category":"Engine","price":15},
    {"number":"17801-30060","name":"Air Filter","brand":"Toyota","category":"Engine","price":25},
    {"number":"04465-YZZE8","name":"Brake Pads Front","brand":"Toyota","category":"Brakes","price":55},
    {"number":"04466-YZZE8","name":"Brake Pads Rear","brand":"Toyota","category":"Brakes","price":45},
    {"number":"23390-30020","name":"Fuel Filter","brand":"Toyota","category":"Fuel","price":35},
    {"number":"90919-01253","name":"Spark Plug","brand":"Toyota","category":"Ignition","price":12},
    {"number":"26300-35505","name":"Oil Filter","brand":"Hyundai","category":"Engine","price":14},
    {"number":"58101-2EA00","name":"Brake Pads","brand":"Hyundai","category":"Brakes","price":50},
    {"number":"BK-4E","name":"Battery Terminal","brand":"Universal","category":"Electrical","price":8},
    {"number":"HF-1","name":"Hydraulic Filter","brand":"Universal","category":"Hydraulic","price":45},
    {"number":"AF-220","name":"Air Filter (heavy)","brand":"Universal","category":"Pneumatic","price":60},
    {"number":"WABCO-4324100202","name":"Air Dryer Cartridge","brand":"WABCO","category":"Pneumatic","price":85},
    {"number":"BOSCH-F026T02025","name":"Fuel Filter","brand":"Bosch","category":"Diesel","price":40},
    {"number":"MANN-WK940/20","name":"Diesel Filter","brand":"MANN","category":"Diesel","price":38},
    {"number":"GATES-6PK1250","name":"Serpentine Belt","brand":"Gates","category":"Engine","price":65},
    {"number":"NGK-BKR6EIX","name":"Iridium Plug","brand":"NGK","category":"Ignition","price":18},
    {"number":"DELPHI-CF1022","name":"Fuel Pump","brand":"Delphi","category":"Fuel","price":220},
]

COMMON_PROBLEMS = [
    {"title":"Engine won't start (cranks)","system":"Engine","severity":"High",
     "causes":["No fuel","No spark","Low compression"],"checks":["Check fuel pressure","Test spark","Compression test"]},
    {"title":"Overheating","system":"Cooling","severity":"Critical",
     "causes":["Low coolant","Thermostat","Water pump","Radiator"],"checks":["Check coolant","Test thermostat","Check pump"]},
    {"title":"Misfire at idle","system":"Engine","severity":"Medium",
     "causes":["Spark plugs","Coils","Vacuum leak"],"checks":["Scan codes","Check plugs","Smoke test"]},
    {"title":"White smoke (diesel)","system":"Diesel","severity":"High",
     "causes":["Injector timing","Coolant leak","Glow plugs"],"checks":["Check coolant","Test injectors","Compression"]},
    {"title":"Black smoke (diesel)","system":"Diesel","severity":"Medium",
     "causes":["Over-fuelling","Air filter","Turbo"],"checks":["Check air filter","Test turbo","Injectors"]},
    {"title":"Transmission slipping","system":"Transmission","severity":"High",
     "causes":["Low fluid","Worn clutches","Solenoid"],"checks":["Check fluid","Scan TCM","Test pressure"]},
    {"title":"Brake pedal soft","system":"Brakes","severity":"Critical",
     "causes":["Air in system","Fluid leak","Master cylinder"],"checks":["Bleed brakes","Check leaks","Test master"]},
    {"title":"ABS light on","system":"Brakes","severity":"High",
     "causes":["Wheel speed sensor","Tone ring","Wiring"],"checks":["Scan codes","Check sensors","Inspect ring"]},
    {"title":"Battery drains overnight","system":"Electrical","severity":"Medium",
     "causes":["Parasitic draw","Alternator","Old battery"],"checks":["Check draw","Test alternator","Load test"]},
    {"title":"Low hydraulic power","system":"Hydraulic","severity":"High",
     "causes":["Low fluid","Worn pump","Internal leak"],"checks":["Check fluid","Test pressure","Check leaks"]},
    {"title":"Air compressor no pressure","system":"Pneumatic","severity":"High",
     "causes":["Worn rings","Leaking valves","Air leaks"],"checks":["Check belt","Test pressure","Check leaks"]},
    {"title":"Rough idle","system":"Engine","severity":"Medium",
     "causes":["Vacuum leak","Dirty throttle","MAF"],"checks":["Smoke test","Clean throttle","Clean MAF"]},
    {"title":"Grinding when braking","system":"Brakes","severity":"High",
     "causes":["Worn pads","Warped rotor","Worn bearings"],"checks":["Inspect pads","Check rotor","Check bearings"]},
    {"title":"Stuck in limp mode","system":"Transmission","severity":"High",
     "causes":["Sensor fault","Wiring","TCM"],"checks":["Scan codes","Check wiring","Test sensors"]},
]

WIRING_LIBRARY = [
    {"id":"WD001","name":"Charging System","system":"Charging",
     "description":"Alternator, battery, warning light circuit",
     "components":["Battery 12V","Alternator (B+, D+, S, W)","Ignition switch","Charge warning light","Chassis ground"],
     "connections":[
        "Battery + → Alternator B+ (Red, 6mm²)",
        "Battery - → Ground (Black, 10mm²)",
        "Alternator D+ → Warning light (Blue, 1.5mm²)",
        "Warning light → Ignition 15 (Black, 1.5mm²)",
        "Alternator S → Battery + (Yellow, 1.5mm²)"],
     "notes":["Output: 13.8-14.4V when running","Warning light ON with engine off is normal","Light stays on = alternator fault"]},
    {"id":"WD002","name":"Starting System","system":"Starting",
     "description":"Starter motor, relay, ignition switch",
     "components":["Battery","Ignition switch","Starter relay (30/85/86/87)","Starter motor (30, 50)","Engine ground"],
     "connections":[
        "Battery + → Starter 30 (Red, 25mm²)",
        "Battery + → Relay 30 (Red, 4mm²)",
        "Ignition 50 → Relay 86 (Yellow, 1.5mm²)",
        "Relay 87 → Starter 50 (Brown, 4mm²)",
        "Relay 85 → Ground (Black, 1.5mm²)"],
     "notes":["Don't hold starter over 10 sec","Check battery voltage first (12.6V+)","Click but no crank = check battery/starter"]},
    {"id":"WD003","name":"Engine Sensors","system":"Engine Mgmt",
     "description":"MAF, MAP, TPS, Coolant, O2 to ECU",
     "components":["ECU (multiple pins)","MAF sensor (4-pin)","MAP sensor (3-pin)","TPS (3-pin)","ECT (2-pin)","O2 sensor (4-pin)"],
     "connections":[
        "ECU → MAF: signal + ground + power + IAT",
        "ECU → MAP: signal + ground + 5V ref",
        "ECU → TPS: 5V + signal + ground",
        "ECU → ECT: signal + ground",
        "ECU → O2: signal + ground + heater +/-"],
     "notes":["Reference voltage: 4.9-5.1V","MAF output: 0.5-4.5V","Never unplug ECU with ignition ON"]},
    {"id":"WD004","name":"Headlight Relay Circuit","system":"Lighting",
     "description":"Relay-controlled headlights with high/low beam",
     "components":["Battery","Headlight switch (30/56/56a)","Low beam relay","High beam relay","Left + Right headlights"],
     "connections":[
        "Battery + → Relay 30 (Red, 4mm²)",
        "Switch 56 → Low relay 86 (Yellow, 1.5mm²)",
        "Relay 87 → Headlight + (Yellow, 2.5mm²)",
        "Headlight - → Ground (Black, 2.5mm²)"],
     "notes":["Voltage drop < 0.5V","One side dim: check ground","HID = high voltage warning"]},
    {"id":"WD005","name":"ABS Wheel Sensors","system":"ABS",
     "description":"4-channel wheel speed sensors",
     "components":["ABS ECU","FL/FR/RL/RR wheel sensors","ABS pump motor"],
     "connections":[
        "ABS ECU → FL sensor (White + Black)",
        "ABS ECU → FR sensor (Yellow + Green)",
        "ABS ECU → RL sensor (Blue + Grey)",
        "ABS ECU → RR sensor (Brown + Purple)",
        "ABS ECU → Pump motor (Red + Black)"],
     "notes":["Sensor resistance: 800-1400Ω","Air gap: 0.5-1.5mm","Tone ring must be clean"]},
    {"id":"WD006","name":"Diesel Glow Plugs","system":"Diesel",
     "description":"Glow plug relay and circuit",
     "components":["Battery","Ignition switch","Glow relay (30/85/86/87)","Glow plugs 1-4"],
     "connections":[
        "Battery + → Relay 30 (Red, 6mm²)",
        "Ignition 15 → Relay 86 (Blue, 1.5mm²)",
        "Relay 87 → All glow plugs (Brown, 4mm²)"],
     "notes":["Glow plug resistance: 0.5-2Ω","Glow time: 5-15 sec","After-glow: 2-5 min"]},
    {"id":"WD007","name":"Transmission Control","system":"Transmission",
     "description":"TCM, solenoids, speed sensors",
     "components":["TCM","Shift solenoids A/B/C","Line pressure solenoid","Input/output speed sensors"],
     "connections":[
        "TCM → Shift Sol A (Red)","TCM → Shift Sol B (Blue)",
        "TCM → Line pressure (Yellow)","TCM → ISS (White)","TCM → OSS (Brown)"],
     "notes":["Solenoid resistance: 10-15Ω","Speed sensors: 300-1500Ω","Must relearn after replacement"]},
    {"id":"WD008","name":"Petrol Fuel Injection","system":"Fuel Injection",
     "description":"Injectors and fuel pump circuit",
     "components":["ECU","Injectors 1-4","Fuel pump relay","Fuel pump"],
     "connections":[
        "ECU → Injector 1-4 drivers","ECU → Common 12V to injectors",
        "ECU → Fuel relay 86","Relay 87 → Fuel pump"],
     "notes":["Injector: 12-16Ω (saturated)","Fuel pump: 4-8A draw","Relieve pressure before service"]},
    {"id":"WD009","name":"CAN Bus Network","system":"Network",
     "description":"Multi-module communication bus",
     "components":["ECM","TCM","BCM","ABS","Diagnostic Link Connector"],
     "connections":[
        "All modules: CAN High (Yellow) twisted pair",
        "All modules: CAN Low (Green) twisted pair",
        "DLC pin 6 = CAN-H, pin 14 = CAN-L"],
     "notes":["CAN-H ~2.5-3.5V idle","CAN-L ~1.5-2.5V idle","Termination: 60Ω between pin 6-14","Twisted pair — never untwist >50mm"]},
    {"id":"WD010","name":"Immobilizer System","system":"Security",
     "description":"Key transponder and immobilizer circuit",
     "components":["Immobilizer ECU","Key reader antenna","Status LED","ECM"],
     "connections":[
        "IMMO → Antenna (White + Black)","IMMO → ECM (CAN bus)","IMMO → Status LED (Orange)"],
     "notes":["Never disconnect IMMO with ignition ON","Antenna resistance: 5-20Ω","Lost key = dealer reprogram"]},
]

# ═══════════════════════════════════
# IN-MEMORY STORES
# ═══════════════════════════════════
JOBS = {}
CUSTOMERS = {}
APPOINTMENTS = {}
INVOICES = {}
STAFF = {}
INVENTORY = {}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","email":"","logo":"🔧","labour_rate":450}

# ═══════════════════════════════════
# HTML
# ═══════════════════════════════════
HTML_PAGE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f5f5f5;--card:#fff;--text:#212121;--text2:#666;--border:#ddd;--primary:#E65100;--input-bg:#fff}
body.dark{--bg:#121212;--card:#1e1e1e;--text:#e0e0e0;--text2:#999;--border:#333;--input-bg:#2a2a2a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);padding-bottom:20px}
.header{background:var(--primary);color:white;padding:14px;text-align:center;position:relative}
.header h1{font-size:20px;display:flex;align-items:center;justify-content:center;gap:8px}
.header h1 .logo{font-size:26px}
.header p{font-size:11px;opacity:.9;margin-top:2px}
.top-btns{position:absolute;right:8px;top:8px;display:flex;gap:4px}
.top-btns button{background:rgba(255,255,255,.2);border:none;color:white;padding:6px 9px;border-radius:8px;font-size:15px;cursor:pointer}
.tabs{display:flex;background:var(--card);border-bottom:1px solid var(--border);overflow-x:auto;position:sticky;top:0;z-index:99;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{padding:12px 11px;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap;font-size:11px;color:var(--text)}
.tab.active{color:var(--primary);border-bottom-color:var(--primary);font-weight:bold}
.panel{display:none;padding:14px;max-width:800px;margin:0 auto}
.panel.active{display:block}
.chat-box{background:var(--card);border-radius:12px;padding:12px;height:400px;overflow-y:auto;margin-bottom:12px}
.msg{padding:10px 14px;margin:6px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.4}
.msg.user{background:var(--primary);color:white;margin-left:auto}
.msg.ai{background:var(--border)}
.input-row{display:flex;gap:6px}
.input-row input{flex:1;padding:12px 16px;border:1px solid var(--border);border-radius:25px;font-size:14px;outline:none;background:var(--input-bg);color:var(--text)}
.input-row button{padding:12px 15px;background:var(--primary);color:white;border:none;border-radius:25px;font-weight:bold;cursor:pointer}
.mic-btn{background:#4CAF50!important}
.mic-btn.recording{background:#F44336!important;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.form-input{width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;margin-bottom:10px;background:var(--input-bg);color:var(--text)}
textarea.form-input{font-family:inherit;resize:vertical}
.btn{width:100%;padding:13px;background:var(--primary);color:white;border:none;border-radius:8px;font-size:15px;font-weight:bold;cursor:pointer;margin-bottom:10px}
.btn-sm{padding:6px 10px;background:var(--primary);color:white;border:none;border-radius:6px;font-size:12px;font-weight:bold;cursor:pointer;margin-right:5px;margin-bottom:4px}
.btn-sm.gray{background:#666}.btn-sm.green{background:#4CAF50}.btn-sm.red{background:#F44336}.btn-sm.blue{background:#2196F3}.btn-sm.whatsapp{background:#25D366}
.card{background:var(--card);padding:14px;border-radius:12px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px}
.card p{margin:4px 0;font-size:13px;line-height:1.4;color:var(--text)}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:white;margin-left:6px}
.badge.high,.badge.critical{background:#F44336}
.badge.medium{background:#FF9800}
.badge.low{background:#4CAF50}
.badge.new{background:#666}.badge.inprogress{background:#FF9800}.badge.completed{background:#4CAF50}
.badge.warn{background:#F44336}.badge.ok{background:#4CAF50}
.list-item{padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.list-item:last-child{border-bottom:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.grid-item{background:var(--card);padding:14px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08);cursor:pointer}
.grid-item .icon{font-size:26px;margin-bottom:6px}
.grid-item .label{font-size:11px;font-weight:bold}
.img-preview{width:100%;border-radius:12px;margin-bottom:12px}
.thumb-row{display:flex;gap:8px;overflow-x:auto;margin-top:8px;padding-bottom:4px}
.thumb{width:80px;height:80px;object-fit:cover;border-radius:8px;border:1px solid var(--border)}
.thumb-wrap{position:relative}
.thumb-del{position:absolute;top:-6px;right:-6px;background:#F44336;color:white;border:none;border-radius:50%;width:20px;height:20px;font-size:11px;cursor:pointer;line-height:1}
.swatch{height:80px;border-radius:12px;border:1px solid var(--border);margin-bottom:12px}
.status-online{background:#E8F5E9;color:#2E7D32;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.status-offline{background:#FFEBEE;color:#C62828;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.loading{text-align:center;padding:20px;color:var(--text2)}
.torque-table{width:100%;border-collapse:collapse;background:var(--card);border-radius:8px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:var(--primary);color:white;padding:8px 6px;text-align:left}
.torque-table td{padding:8px 6px;border-bottom:1px solid var(--border);color:var(--text)}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.stat-card{background:var(--card);padding:14px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.stat-card .num{font-size:22px;font-weight:bold;color:var(--primary)}
.stat-card .lbl{font-size:11px;color:var(--text2);margin-top:4px}
.stat-card.green .num{color:#4CAF50}
.stat-card.red .num{color:#F44336}
.stat-card.blue .num{color:#2196F3}
canvas{max-height:220px}
@media print{.header,.tabs,.no-print,button,.btn,.btn-sm{display:none!important}.panel{display:block!important;padding:0}.panel:not(.active){display:none!important}body{background:white;color:black}.card{box-shadow:none;border:1px solid #ccc;page-break-inside:avoid}}
</style>
</head>
<body>

<div class="header">
<h1><span class="logo" id="logoDisplay">🔧</span> <span id="wsNameDisplay">RAMSTECH</span></h1>
<p id="wsSubtitle">AI Workshop Assistant v6.0</p>
<div class="top-btns">
<button onclick="toggleTheme()" id="themeBtn">🌙</button>
</div>
</div>

<div class="tabs no-print">
<div class="tab active" onclick="showTab('home',this)">🏠</div>
<div class="tab" onclick="showTab('dashboard',this)">📊</div>
<div class="tab" onclick="showTab('chat',this)">🤖</div>
<div class="tab" onclick="showTab('codes',this)">📟</div>
<div class="tab" onclick="showTab('problems',this)">📖</div>
<div class="tab" onclick="showTab('vin',this)">🔍</div>
<div class="tab" onclick="showTab('paint',this)">🎨</div>
<div class="tab" onclick="showTab('photo',this)">📸</div>
<div class="tab" onclick="showTab('jobs',this)">📋</div>
<div class="tab" onclick="showTab('customers',this)">👥</div>
<div class="tab" onclick="showTab('appointments',this)">📅</div>
<div class="tab" onclick="showTab('invoices',this)">💰</div>
<div class="tab" onclick="showTab('parts',this)">🔩</div>
<div class="tab" onclick="showTab('inventory',this)">📦</div>
<div class="tab" onclick="showTab('staff',this)">👷</div>
<div class="tab" onclick="showTab('wiring',this)">🔌</div>
<div class="tab" onclick="showTab('boltcalc',this)">🔧</div>
<div class="tab" onclick="showTab('torque',this)">⚙️</div>
<div class="tab" onclick="showTab('history',this)">🚗</div>
<div class="tab" onclick="showTab('analytics',this)">📈</div>
<div class="tab" onclick="showTab('settings',this)">⚙</div>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking backend...</div></div>
<div class="grid">
<div class="grid-item" onclick="clickTab(1)"><div class="icon">📊</div><div class="label">Dashboard</div></div>
<div class="grid-item" onclick="clickTab(2)"><div class="icon">🤖</div><div class="label">AI Chat</div></div>
<div class="grid-item" onclick="clickTab(3)"><div class="icon">📟</div><div class="label">Codes</div></div>
<div class="grid-item" onclick="clickTab(4)"><div class="icon">📖</div><div class="label">Problems</div></div>
<div class="grid-item" onclick="clickTab(5)"><div class="icon">🔍</div><div class="label">VIN</div></div>
<div class="grid-item" onclick="clickTab(6)"><div class="icon">🎨</div><div class="label">Paint</div></div>
<div class="grid-item" onclick="clickTab(7)"><div class="icon">📸</div><div class="label">Photo Diag</div></div>
<div class="grid-item" onclick="clickTab(8)"><div class="icon">📋</div><div class="label">Jobs</div></div>
<div class="grid-item" onclick="clickTab(9)"><div class="icon">👥</div><div class="label">Customers</div></div>
<div class="grid-item" onclick="clickTab(10)"><div class="icon">📅</div><div class="label">Appointments</div></div>
<div class="grid-item" onclick="clickTab(11)"><div class="icon">💰</div><div class="label">Invoices</div></div>
<div class="grid-item" onclick="clickTab(12)"><div class="icon">🔩</div><div class="label">Parts</div></div>
<div class="grid-item" onclick="clickTab(13)"><div class="icon">📦</div><div class="label">Inventory</div></div>
<div class="grid-item" onclick="clickTab(14)"><div class="icon">👷</div><div class="label">Staff</div></div>
<div class="grid-item" onclick="clickTab(15)"><div class="icon">🔌</div><div class="label">Wiring</div></div>
<div class="grid-item" onclick="clickTab(16)"><div class="icon">🔧</div><div class="label">Bolt Calc</div></div>
<div class="grid-item" onclick="clickTab(17)"><div class="icon">⚙️</div><div class="label">Torque</div></div>
<div class="grid-item" onclick="clickTab(18)"><div class="icon">🚗</div><div class="label">History</div></div>
<div class="grid-item" onclick="clickTab(19)"><div class="icon">📈</div><div class="label">Analytics</div></div>
<div class="grid-item" onclick="clickTab(20)"><div class="icon">⚙</div><div class="label">Settings</div></div>
</div>
</div>

<div id="dashboard" class="panel">
<h3 style="margin-bottom:12px;color:var(--primary)">📊 Dashboard</h3>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>Low Stock Alerts</h3><div id="dashLowStock"></div></div>
</div>

<div id="chat" class="panel">
<div class="chat-box" id="chatBox"><div class="msg ai">Welcome! Ask about repairs, diagnostics, or tools.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendMsg()">
<button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
<button onclick="sendMsg()">Send</button>
</div>
</div>

<div id="codes" class="panel">
<input type="text" class="form-input" id="codeSearch" placeholder="Search code..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<div id="problems" class="panel">
<input type="text" class="form-input" id="problemSearch" placeholder="Search problems..." oninput="filterProblems()">
<div id="problemList"><div class="loading">Loading...</div></div>
</div>

<div id="vin" class="panel">
<input type="text" class="form-input" id="vinInput" placeholder="Enter 17-char VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<div id="paint" class="panel">
<div class="card"><p style="font-size:13px">Take photo of a vehicle panel. AI identifies colour and provides paint codes.</p></div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
</div>

<div id="photo" class="panel">
<div class="card"><p style="font-size:13px">Take photo of mechanical issue. AI diagnoses the problem.</p></div>
<input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>

<div id="jobs" class="panel">
<button class="btn no-print" onclick="showJobForm()">+ New Job Card</button>
<button class="btn no-print" style="background:#2196F3" onclick="exportJobsCSV()">📥 Export CSV</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jobCustomer" placeholder="Customer name">
<input class="form-input" id="jobVehicle" placeholder="Vehicle">
<input class="form-input" id="jobVehicleReg" placeholder="Registration">
<textarea class="form-input" id="jobComplaint" placeholder="Complaint / issue" rows="2"></textarea>
<label style="font-size:12px;font-weight:bold;display:block;margin-bottom:6px">Assign to</label>
<select class="form-input" id="jobAssigned"><option value="">— Unassigned —</option></select>
<label style="font-size:12px;font-weight:bold;display:block;margin-bottom:6px">📸 Photos</label>
<input type="file" id="jobPhotos" accept="image/*" multiple capture="environment" class="form-input" onchange="addJobPhotos(event)">
<div class="thumb-row" id="jobPhotoThumbs"></div>
<button class="btn" style="margin-top:10px" onclick="createJob()">Create Job</button>
<button class="btn" style="background:#666" onclick="hideJobForm()">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<div id="customers" class="panel">
<button class="btn no-print" onclick="showCustomerForm()">+ New Customer</button>
<button class="btn no-print" style="background:#2196F3" onclick="exportCustomersCSV()">📥 Export CSV</button>
<div id="customerForm" style="display:none">
<div class="card">
<input class="form-input" id="custName" placeholder="Full name">
<input class="form-input" id="custPhone" placeholder="Phone">
<input class="form-input" id="custEmail" placeholder="Email">
<input class="form-input" id="custAddress" placeholder="Address">
<button class="btn" onclick="createCustomer()">Save</button>
<button class="btn" style="background:#666" onclick="hideCustomerForm()">Cancel</button>
</div>
</div>
<div id="customerList"><div class="loading">Loading...</div></div>
</div>

<div id="appointments" class="panel">
<button class="btn no-print" onclick="showApptForm()">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="apptCustomer" placeholder="Customer">
<input class="form-input" id="apptPhone" placeholder="Phone">
<input class="form-input" id="apptVehicle" placeholder="Vehicle">
<input class="form-input" id="apptService" placeholder="Service">
<input class="form-input" id="apptDate" type="date">
<input class="form-input" id="apptTime" type="time">
<button class="btn" onclick="createAppt()">Book</button>
<button class="btn" style="background:#666" onclick="hideApptForm()">Cancel</button>
</div>
</div>
<div id="apptList"><div class="loading">Loading...</div></div>
</div>

<div id="invoices" class="panel">
<button class="btn no-print" onclick="showInvoiceForm()">+ New Invoice</button>
<div id="invoiceForm" style="display:none">
<div class="card">
<input class="form-input" id="invCustomer" placeholder="Customer">
<input class="form-input" id="invVehicle" placeholder="Vehicle">
<input class="form-input" id="invDesc" placeholder="Description">
<input class="form-input" id="invLabour" type="number" placeholder="Labour (R)">
<input class="form-input" id="invParts" type="number" placeholder="Parts (R)">
<button class="btn" onclick="createInvoice()">Generate</button>
<button class="btn" style="background:#666" onclick="hideInvoiceForm()">Cancel</button>
</div>
</div>
<div id="invoiceList"><div class="loading">Loading...</div></div>
</div>

<div id="parts" class="panel">
<input type="text" class="form-input" id="partsSearch" placeholder="Search part..." oninput="filterParts()">
<div id="partsList"><div class="loading">Loading...</div></div>
</div>

<div id="inventory" class="panel">
<button class="btn no-print" onclick="showInvForm()">+ Add Stock Item</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="invPartNum" placeholder="Part number">
<input class="form-input" id="invPartName" placeholder="Part name">
<input class="form-input" id="invCategory" placeholder="Category">
<input class="form-input" id="invQty" type="number" placeholder="Quantity">
<input class="form-input" id="invMinQty" type="number" placeholder="Minimum quantity (low-stock alert)">
<input class="form-input" id="invCostPrice" type="number" placeholder="Cost price (R)">
<input class="form-input" id="invSellPrice" type="number" placeholder="Sell price (R)">
<input class="form-input" id="invSupplier" placeholder="Supplier">
<button class="btn" onclick="addInventory()">Save</button>
<button class="btn" style="background:#666" onclick="hideInvForm()">Cancel</button>
</div>
</div>
<div id="inventoryList"><div class="loading">Loading...</div></div>
</div>

<div id="staff" class="panel">
<button class="btn no-print" onclick="showStaffForm()">+ Add Staff</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="staffName" placeholder="Full name">
<input class="form-input" id="staffRole" placeholder="Role (e.g. Mechanic)">
<input class="form-input" id="staffPhone" placeholder="Phone">
<input class="form-input" id="staffEmail" placeholder="Email">
<button class="btn" onclick="addStaff()">Save</button>
<button class="btn" style="background:#666" onclick="hideStaffForm()">Cancel</button>
</div>
</div>
<div id="staffList"><div class="loading">Loading...</div></div>
</div>

<div id="wiring" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🔌 Wiring Library</h3>
<input type="text" class="form-input" id="wiringSearch" placeholder="Search circuits..." oninput="filterWiring()">
<div id="wiringList"><div class="loading">Loading...</div></div>
</div>

<div id="boltcalc" class="panel">
<div class="card">
<h3>🔧 Bolt Torque Calculator</h3>
<label style="font-size:13px;font-weight:bold">Bolt Size</label>
<select class="form-input" id="boltSize">
<option>M6</option><option>M8</option><option selected>M10</option><option>M12</option>
<option>M14</option><option>M16</option><option>M18</option><option>M20</option>
</select>
<label style="font-size:13px;font-weight:bold">Grade</label>
<select class="form-input" id="boltGrade">
<option>8.8</option><option selected>10.9</option><option>12.9</option>
</select>
<label style="font-size:13px;font-weight:bold">Condition</label>
<select class="form-input" id="boltCondition">
<option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly</option>
</select>
<button class="btn" onclick="calcTorque()">Calculate</button>
<div id="boltResult"></div>
</div>
</div>

<div id="torque" class="panel">
<input type="text" class="form-input" id="torqueSearch" placeholder="Search..." oninput="filterTorque()">
<h3 style="margin-bottom:8px;font-size:14px">Bolt Torque</h3>
<div id="torqueTable"></div>
<h3 style="margin:16px 0 8px;font-size:14px">Sequences</h3>
<div id="torqueSeq"></div>
</div>

<div id="history" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🚗 Vehicle History</h3>
<input type="text" class="form-input" id="vehicleSearch" placeholder="Search reg or vehicle..." oninput="searchVehicleHistory()">
<div id="vehicleHistory"><div class="loading">Enter search term</div></div>
</div>

<div id="analytics" class="panel">
<h3 style="margin-bottom:12px;color:var(--primary)">📈 Analytics</h3>
<div id="analyticsContent"><div class="loading">Loading...</div></div>
</div>

<div id="settings" class="panel">
<div class="card">
<h3>🏢 Branding</h3>
<input class="form-input" id="wsLogo" placeholder="🔧" maxlength="4" value="🔧">
<input class="form-input" id="wsName" placeholder="Workshop name">
<input class="form-input" id="wsPhone" placeholder="Phone">
<input class="form-input" id="wsAddress" placeholder="Address">
<input class="form-input" id="wsEmail" placeholder="Email">
<input class="form-input" id="wsRate" type="number" placeholder="Default labour rate (R/hr)" value="450">
<button class="btn" onclick="saveSettings()">Save</button>
</div>
</div>

<script>
function showTab(name,el){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(name).classList.add('active');
if(el)el.classList.add('active');
if(name==='codes'&&!document.getElementById('codeResults').dataset.loaded)searchCodes();
if(name==='problems'&&!document.getElementById('problemList').dataset.loaded)loadProblems();
if(name==='jobs'){loadJobs();loadStaffDropdown();}
if(name==='customers')loadCustomers();
if(name==='appointments')loadAppts();
if(name==='invoices')loadInvoices();
if(name==='parts'&&!document.getElementById('partsList').dataset.loaded)loadParts();
if(name==='inventory')loadInventory();
if(name==='staff')loadStaff();
if(name==='wiring')loadWiring();
if(name==='torque')loadTorque();
if(name==='dashboard')loadDashboard();
if(name==='analytics')loadAnalytics();
if(name==='settings')loadSettings();
}
function clickTab(i){showTab(document.querySelectorAll('.panel')[i].id,document.querySelectorAll('.tab')[i]);}

function toggleTheme(){
document.body.classList.toggle('dark');
const d=document.body.classList.contains('dark');
localStorage.setItem('theme',d?'dark':'light');
document.getElementById('themeBtn').textContent=d?'☀️':'🌙';
}
if(localStorage.getItem('theme')==='dark'){document.body.classList.add('dark');document.getElementById('themeBtn').textContent='☀️';}

async function checkStatus(){
try{await fetch('/health');document.getElementById('status').innerHTML='<span class="status-online">✓ Online</span>';}
catch(e){document.getElementById('status').innerHTML='<span class="status-offline">✗ Offline</span>';}
}
checkStatus();
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}

let recognition=null,recording=false;
function toggleMic(){
if(!('webkitSpeechRecognition'in window)&&!('SpeechRecognition'in window)){alert('Voice not supported');return}
if(!recognition){
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
recognition=new SR();recognition.lang='en-ZA';
recognition.onresult=e=>{document.getElementById('chatInput').value=e.results[0][0].transcript;reset();sendMsg();};
recognition.onerror=reset;recognition.onend=reset;
}
function reset(){recording=false;document.getElementById('micBtn').classList.remove('recording');document.getElementById('micBtn').textContent='🎤';}
if(recording){recognition.stop();reset();}
else{try{recognition.start();recording=true;document.getElementById('micBtn').classList.add('recording');document.getElementById('micBtn').textContent='⏹';}catch(e){alert(e.message);}}
}

async function sendMsg(){
const input=document.getElementById('chatInput');const msg=input.value.trim();if(!msg)return;
const box=document.getElementById('chatBox');
box.innerHTML+='<div class="msg user">'+esc(msg)+'</div>';
input.value='';box.scrollTop=box.scrollHeight;
box.innerHTML+='<div class="msg ai" id="typing">...</div>';box.scrollTop=box.scrollHeight;
try{const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
const data=await res.json();
document.getElementById('typing').outerHTML='<div class="msg ai">'+esc(data.reply)+'</div>';
}catch(e){document.getElementById('typing').outerHTML='<div class="msg ai">Error</div>';}
box.scrollTop=box.scrollHeight;
}

// DASHBOARD
let revChart=null,jobChart=null;
async function loadDashboard(){
try{const res=await fetch('/api/stats');const d=await res.json();
document.getElementById('dashStats').innerHTML='<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Jobs</div></div><div class="stat-card"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open</div></div><div class="stat-card green"><div class="num">'+d.jobs_completed+'</div><div class="lbl">Done</div></div><div class="stat-card"><div class="num">'+d.customers+'</div><div class="lbl">Customers</div></div><div class="stat-card"><div class="num">'+d.staff+'</div><div class="lbl">Staff</div></div><div class="stat-card green"><div class="num">R'+d.revenue+'</div><div class="lbl">Revenue</div></div></div>';
if(revChart)revChart.destroy();
const c1=document.getElementById('revenueChart');
if(c1)revChart=new Chart(c1,{type:'line',data:{labels:d.revenue_labels,datasets:[{label:'R',data:d.revenue_data,borderColor:'#E65100',backgroundColor:'rgba(230,81,0,.15)',tension:.3,fill:true}]},options:{responsive:true,plugins:{legend:{display:false}}}});
if(jobChart)jobChart.destroy();
const c2=document.getElementById('jobChart');
if(c2)jobChart=new Chart(c2,{type:'doughnut',data:{labels:['New','Progress','Done'],datasets:[{data:[d.jobs_new,d.jobs_progress,d.jobs_completed],backgroundColor:['#666','#FF9800','#4CAF50']}]},options:{responsive:true}});
// Low stock
const lsRes=await fetch('/api/inventory/low-stock');
const ls=await lsRes.json();
document.getElementById('dashLowStock').innerHTML=ls.items.length?ls.items.map(i=>'<div class="list-item"><strong>'+esc(i.name)+'</strong> — '+i.qty+' left (min '+i.min+')</div>').join(''):'<p style="color:var(--text2)">All stock OK</p>';
}catch(e){}
}

// CODES
async function searchCodes(){
const q=document.getElementById('codeSearch').value;const c=document.getElementById('codeResults');
c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/fault-codes?search='+encodeURIComponent(q));const data=await res.json();
c.dataset.loaded='true';
if(!data.codes.length){c.innerHTML='<div class="card"><p>No matches</p></div>';return}
c.innerHTML=data.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p style="margin-top:8px"><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p style="margin-top:8px"><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

let problemsData=[];
async function loadProblems(){
try{const res=await fetch('/api/problems');const data=await res.json();
problemsData=data.problems;document.getElementById('problemList').dataset.loaded='true';renderProblems();
}catch(e){}
}
function filterProblems(){renderProblems();}
function renderProblems(){
const q=(document.getElementById('problemSearch').value||'').toLowerCase();
const f=problemsData.filter(x=>!q||x.title.toLowerCase().includes(q)||x.system.toLowerCase().includes(q));
document.getElementById('problemList').innerHTML=f.length?f.map(x=>'<div class="card"><h3>'+esc(x.title)+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p style="margin-top:8px"><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p style="margin-top:8px"><strong>Checks:</strong></p>'+x.checks.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>';
}

async function decodeVin(){
const vin=document.getElementById('vinInput').value.trim().toUpperCase();const c=document.getElementById('vinResult');
if(vin.length!==17){c.innerHTML='<div class="card"><p style="color:red">VIN must be 17 chars</p></div>';return}
c.innerHTML='<div class="loading">Decoding...</div>';
try{const res=await fetch('/api/vin/'+vin);const data=await res.json();
if(data.detail){c.innerHTML='<div class="card"><p style="color:red">'+data.detail+'</p></div>';return}
c.innerHTML='<div class="card"><h3>🔍 Info</h3><p><strong>VIN:</strong> '+data.vin+'</p><p><strong>Manufacturer:</strong> '+data.manufacturer+'</p><p><strong>Country:</strong> '+data.country+'</p><p><strong>Year:</strong> '+data.year+'</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

let paintB64='';
function previewPaint(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=ev=>{paintB64=ev.target.result;document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+paintB64+'">';};r.readAsDataURL(f);}
async function matchPaint(){
const btn=document.getElementById('paintBtn');const c=document.getElementById('paintResult');
if(!paintB64){c.innerHTML='<div class="card"><p style="color:red">Select image</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';c.innerHTML='<div class="loading">Analyzing...</div>';
try{const res=await fetch('/api/paint/match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:paintB64,vehicle_info:document.getElementById('paintVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else{const col=data.detected_colour;let h='<div class="card"><div class="swatch" style="background:'+col.hex_code+'"></div><h3>'+esc(col.name)+'</h3><p><strong>'+esc(col.finish)+'</strong> • '+esc(col.colour_family)+'</p><p style="font-family:monospace">'+col.hex_code+'</p><p>Confidence: <strong>'+data.confidence+'</strong></p></div>';if(data.brand_codes){h+='<div class="card"><h3>Brand Codes</h3>';data.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code)+'</div>'});h+='</div>'}c.innerHTML=h;}
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
btn.disabled=false;btn.textContent='🎨 Match Paint Colour';
}

let diagB64='';
function previewDiag(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=ev=>{diagB64=ev.target.result;document.getElementById('photoPreview').innerHTML='<img class="img-preview" src="'+diagB64+'">';};r.readAsDataURL(f);}
async function diagnosePhoto(){
const btn=document.getElementById('photoBtn');const c=document.getElementById('photoResult');
if(!diagB64){c.innerHTML='<div class="card"><p style="color:red">Select image</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';c.innerHTML='<div class="loading">Analyzing...</div>';
try{const res=await fetch('/api/diagnose/photo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:diagB64,vehicle_info:document.getElementById('photoVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else{let h='<div class="card"><h3>🔍 '+esc(data.problem||'Detected')+'</h3><p><strong>Confidence:</strong> '+data.confidence+'</p>';if(data.description)h+='<p style="margin-top:8px">'+esc(data.description)+'</p>';h+='</div>';if(data.possible_causes){h+='<div class="card"><h3>Possible Causes</h3>';data.possible_causes.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}if(data.diagnostic_steps){h+='<div class="card"><h3>Steps</h3>';data.diagnostic_steps.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}if(data.safety_warnings){h+='<div class="card" style="background:#FFEBEE"><h3 style="color:#C62828">⚠ Safety</h3>';data.safety_warnings.forEach(w=>{h+='<div class="list-item">⚠ '+esc(w)+'</div>'});h+='</div>'}c.innerHTML=h;}
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
btn.disabled=false;btn.textContent='📸 Analyze Photo';
}

// JOBS
let jobPhotos=[];
function addJobPhotos(e){Array.from(e.target.files).forEach(f=>{const r=new FileReader();r.onload=ev=>{jobPhotos.push(ev.target.result);renderJobThumbs();};r.readAsDataURL(f);});}
function renderJobThumbs(){document.getElementById('jobPhotoThumbs').innerHTML=jobPhotos.map((p,i)=>'<div class="thumb-wrap"><img class="thumb" src="'+p+'"><button class="thumb-del" onclick="removeJobPhoto('+i+')">×</button></div>').join('');}
function removeJobPhoto(i){jobPhotos.splice(i,1);renderJobThumbs();}
function showJobForm(){document.getElementById('jobForm').style.display='block';}
function hideJobForm(){document.getElementById('jobForm').style.display='none';jobPhotos=[];renderJobThumbs();}
async function loadStaffDropdown(){
try{const res=await fetch('/api/staff');const d=await res.json();
const sel=document.getElementById('jobAssigned');
sel.innerHTML='<option value="">— Unassigned —</option>'+d.staff.map(s=>'<option value="'+esc(s.name)+'">'+esc(s.name)+'</option>').join('');
}catch(e){}
}
async function createJob(){
const c=document.getElementById('jobCustomer').value.trim();
const v=document.getElementById('jobVehicle').value.trim();
const comp=document.getElementById('jobComplaint').value.trim();
if(!c||!v||!comp){alert('Fill customer, vehicle, complaint');return}
try{
await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
customer:c,vehicle:v,registration:document.getElementById('jobVehicleReg').value,
complaint:comp,assigned_to:document.getElementById('jobAssigned').value,photos:jobPhotos})});
['jobCustomer','jobVehicle','jobComplaint','jobVehicleReg'].forEach(id=>document.getElementById(id).value='');
hideJobForm();loadJobs();
}catch(e){alert(e.message)}
}
async function loadJobs(){
const c=document.getElementById('jobList');c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/jobs');const data=await res.json();
if(!data.jobs.length){c.innerHTML='<div class="card"><p>No jobs yet.</p></div>';return}
c.innerHTML=data.jobs.reverse().map(j=>{
const s=j.status.toLowerCase().replace(' ','');
let photos=j.photos&&j.photos.length?'<div class="thumb-row">'+j.photos.map(p=>'<img class="thumb" src="'+p+'">').join('')+'</div>':'';
let costing=j.total?'<div style="margin-top:8px;padding:8px;background:var(--bg);border-radius:6px;font-size:12px"><strong>Cost:</strong> Labour R'+(j.labour_cost||0).toFixed(2)+' + Parts R'+(j.parts_cost||0).toFixed(2)+' + VAT = <strong>R'+j.total.toFixed(2)+'</strong></div>':'';
let assigned=j.assigned_to?'<p style="color:var(--text2);font-size:12px">👷 '+esc(j.assigned_to)+'</p>':'';
let timeline=j.timeline&&j.timeline.length?'<div style="margin-top:8px"><strong style="font-size:12px">Timeline:</strong>'+j.timeline.slice(-3).map(t=>'<div style="font-size:11px;color:var(--text2);padding:2px 0">• '+esc(t)+'</div>').join('')+'</div>':'';
return '<div class="card" id="job-'+j.id+'"><h3>Job #'+j.id+' <span class="badge '+s+'">'+esc(j.status)+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p>'+assigned+'<p style="color:var(--text2)">'+esc(j.complaint)+'</p>'+photos+costing+timeline+'<p style="font-size:11px;color:var(--text2);margin-top:6px">'+esc(j.created)+'</p><div class="no-print" style="margin-top:8px"><button class="btn-sm" onclick="updateJob(\''+j.id+'\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="updateJob(\''+j.id+'\',\'Completed\')">Done</button><button class="btn-sm blue" onclick="addJobNote(\''+j.id+'\')">+ Note</button><button class="btn-sm" onclick="setJobCost(\''+j.id+'\')">💰 Cost</button><button class="btn-sm whatsapp" onclick="shareJobWA(\''+j.id+'\')">📱</button><button class="btn-sm gray" onclick="printJob(\''+j.id+'\')">🖨</button></div></div>';
}).join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function updateJob(id,status){
try{
await fetch('/api/jobs/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status,note:'Status → '+status})});
loadJobs();}catch(e){alert(e.message)}
}
async function addJobNote(id){
const note=prompt('Add note to job #'+id+':');
if(!note)return;
try{await fetch('/api/jobs/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({note})});loadJobs();}catch(e){alert(e.message)}
}
async function setJobCost(id){
const rate=await getLabourRate();
const hours=prompt('Labour hours:', '1');
if(hours===null)return;
const parts=prompt('Parts cost (R):','0');
if(parts===null)return;
try{await fetch('/api/jobs/'+id+'/cost',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({labour_hours:parseFloat(hours),labour_rate:rate,parts_cost:parseFloat(parts)})});loadJobs();}catch(e){alert(e.message)}
}
async function getLabourRate(){
try{const r=await fetch('/api/workshop');const d=await r.json();return d.labour_rate||450;}catch(e){return 450;}
}
function shareJobWA(id){
fetch('/api/jobs').then(r=>r.json()).then(d=>{
const j=d.jobs.find(x=>x.id==id);
if(!j)return;
const txt='🔧 *Job #'+j.id+'*\nCustomer: '+j.customer+'\nVehicle: '+j.vehicle+'\n'+(j.registration?'Reg: '+j.registration+'\n':'')+'Issue: '+j.complaint+'\nStatus: '+j.status+(j.total?'\nTotal: R'+j.total.toFixed(2):'');
const phone=j.customer_phone||'';
const url=phone?'https://wa.me/'+phone.replace(/\D/g,'')+'?text='+encodeURIComponent(txt):'https://wa.me/?text='+encodeURIComponent(txt);
window.open(url,'_blank');
});
}
function printJob(id){
const el=document.getElementById('job-'+id);
const w=window.open('','','width=800,height=600');
w.document.write('<html><head><title>Job #'+id+'</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}</style></head><body>');
w.document.write('<h1>'+document.getElementById('logoDisplay').textContent+' '+document.getElementById('wsNameDisplay').textContent+' — Job #'+id+'</h1>');
w.document.write(el.innerHTML.replace(/<div class="no-print".*?<\/div>/gs,''));
w.document.write('</body></html>');w.document.close();setTimeout(()=>w.print(),500);
}

// CUSTOMERS
function showCustomerForm(){document.getElementById('customerForm').style.display='block';}
function hideCustomerForm(){document.getElementById('customerForm').style.display='none';}
async function createCustomer(){
const name=document.getElementById('custName').value.trim();
const phone=document.getElementById('custPhone').value.trim();
if(!name||!phone){alert('Name and phone required');return}
try{await fetch('/api/customers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,email:document.getElementById('custEmail').value,address:document.getElementById('custAddress').value})});
['custName','custPhone','custEmail','custAddress'].forEach(id=>document.getElementById(id).value='');
hideCustomerForm();loadCustomers();}catch(e){alert(e.message)}
}
async function loadCustomers(){
const c=document.getElementById('customerList');c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/customers');const data=await res.json();
c.innerHTML=data.customers.length?data.customers.reverse().map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+'<button class="btn-sm whatsapp" onclick="waCustomer(\''+esc(x.phone)+'\',\''+esc(x.name)+'\')">📱 WhatsApp</button></div>').join(''):'<div class="card"><p>No customers yet.</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
function waCustomer(phone,name){
const url='https://wa.me/'+phone.replace(/\D/g,'')+'?text='+encodeURIComponent('Hi '+name+', ');
window.open(url,'_blank');
}

// APPOINTMENTS
function showApptForm(){document.getElementById('apptForm').style.display='block';}
function hideApptForm(){document.getElementById('apptForm').style.display='none';}
async function createAppt(){
const c=document.getElementById('apptCustomer').value.trim();
const d=document.getElementById('apptDate').value;
const t=document.getElementById('apptTime').value;
if(!c||!d||!t){alert('Customer, date, time required');return}
try{await fetch('/api/appointments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer:c,phone:document.getElementById('apptPhone').value,vehicle:document.getElementById('apptVehicle').value,service:document.getElementById('apptService').value,date:d,time:t})});
['apptCustomer','apptPhone','apptVehicle','apptService','apptDate','apptTime'].forEach(id=>document.getElementById(id).value='');
hideApptForm();loadAppts();}catch(e){alert(e.message)}
}
async function loadAppts(){
const c=document.getElementById('apptList');c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/appointments');const data=await res.json();
const s=data.appointments.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));
c.innerHTML=s.length?s.map(a=>'<div class="card"><h3>📅 '+esc(a.date)+' '+esc(a.time)+'</h3><p><strong>'+esc(a.customer)+'</strong></p>'+(a.vehicle?'<p>🚗 '+esc(a.vehicle)+'</p>':'')+(a.service?'<p style="color:var(--text2)">'+esc(a.service)+'</p>':'')+'<button class="btn-sm red" onclick="deleteAppt(\''+a.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>No appointments.</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function deleteAppt(id){if(!confirm('Delete?'))return;try{await fetch('/api/appointments/'+id,{method:'DELETE'});loadAppts();}catch(e){alert(e.message)}}

// INVOICES
function showInvoiceForm(){document.getElementById('invoiceForm').style.display='block';}
function hideInvoiceForm(){document.getElementById('invoiceForm').style.display='none';}
async function createInvoice(){
const c=document.getElementById('invCustomer').value.trim();
const d=document.getElementById('invDesc').value.trim();
if(!c||!d){alert('Customer, description required');return}
try{await fetch('/api/invoices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer:c,vehicle:document.getElementById('invVehicle').value,description:d,labour:parseFloat(document.getElementById('invLabour').value)||0,parts:parseFloat(document.getElementById('invParts').value)||0})});
['invCustomer','invVehicle','invDesc','invLabour','invParts'].forEach(id=>document.getElementById(id).value='');
hideInvoiceForm();loadInvoices();}catch(e){alert(e.message)}
}
async function loadInvoices(){
const c=document.getElementById('invoiceList');c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/invoices');const data=await res.json();
c.innerHTML=data.invoices.length?data.invoices.reverse().map(i=>'<div class="card" id="inv-'+i.id+'"><h3>Invoice #'+i.id+'</h3><p><strong>'+esc(i.customer)+'</strong></p>'+(i.vehicle?'<p>🚗 '+esc(i.vehicle)+'</p>':'')+'<p style="color:var(--text2)">'+esc(i.description)+'</p><div class="list-item">Labour: R'+i.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+i.parts.toFixed(2)+'</div><div class="list-item"><strong>Subtotal: R'+i.subtotal.toFixed(2)+'</strong></div><div class="list-item"><strong>VAT: R'+i.vat.toFixed(2)+'</strong></div><div class="list-item" style="font-size:16px"><strong>TOTAL: R'+i.total.toFixed(2)+'</strong></div><div class="no-print" style="margin-top:8px"><button class="btn-sm whatsapp" onclick="shareInvoiceWA(\''+i.id+'\')">📱</button><button class="btn-sm blue" onclick="printInvoice(\''+i.id+'\')">🖨</button></div></div>').join(''):'<div class="card"><p>No invoices.</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function shareInvoiceWA(id){
try{const res=await fetch('/api/invoices/'+id);const i=await res.json();
const txt='🔧 *'+document.getElementById('wsNameDisplay').textContent+'*\nInvoice #'+i.id+'\n\nCustomer: '+i.customer+'\nVehicle: '+i.vehicle+'\nService: '+i.description+'\n\nLabour: R'+i.labour.toFixed(2)+'\nParts: R'+i.parts.toFixed(2)+'\nVAT: R'+i.vat.toFixed(2)+'\n*TOTAL: R'+i.total.toFixed(2)+'*\n\nThank you!';
const url='https://wa.me/?text='+encodeURIComponent(txt);
window.open(url,'_blank');
}catch(e){alert(e.message)}
}
function printInvoice(id){
const el=document.getElementById('inv-'+id);
const w=window.open('','','width=800,height=600');
w.document.write('<html><head><title>Invoice #'+id+'</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}</style></head><body>');
w.document.write('<h1>'+document.getElementById('logoDisplay').textContent+' '+document.getElementById('wsNameDisplay').textContent+' — Invoice #'+id+'</h1>');
w.document.write(el.innerHTML.replace(/<div class="no-print".*?<\/div>/gs,''));
w.document.write('</body></html>');w.document.close();setTimeout(()=>w.print(),500);
}

// PARTS
let partsData=[];
async function loadParts(){
try{const res=await fetch('/api/parts');const data=await res.json();
partsData=data.parts;document.getElementById('partsList').dataset.loaded='true';renderParts();
}catch(e){}
}
function filterParts(){renderParts();}
function renderParts(){
const q=(document.getElementById('partsSearch').value||'').toLowerCase();
const f=partsData.filter(x=>!q||x.name.toLowerCase().includes(q)||x.number.toLowerCase().includes(q)||x.brand.toLowerCase().includes(q));
document.getElementById('partsList').innerHTML=f.length?f.map(p=>'<div class="card"><h3>'+esc(p.name)+'</h3><p style="font-family:monospace;font-size:12px">'+esc(p.number)+'</p><p>Brand: <strong>'+esc(p.brand)+'</strong> | '+esc(p.category)+'</p><p style="font-size:16px;color:var(--primary)"><strong>R'+p.price+'</strong></p></div>').join(''):'<div class="card"><p>No matches</p></div>';
}

// INVENTORY
function showInvForm(){document.getElementById('invForm').style.display='block';}
function hideInvForm(){document.getElementById('invForm').style.display='none';}
async function addInventory(){
const name=document.getElementById('invPartName').value.trim();
if(!name){alert('Part name required');return}
try{await fetch('/api/inventory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
part_number:document.getElementById('invPartNum').value,name:name,
category:document.getElementById('invCategory').value,
qty:parseInt(document.getElementById('invQty').value)||0,
min_qty:parseInt(document.getElementById('invMinQty').value)||5,
cost_price:parseFloat(document.getElementById('invCostPrice').value)||0,
sell_price:parseFloat(document.getElementById('invSellPrice').value)||0,
supplier:document.getElementById('invSupplier').value})});
['invPartNum','invPartName','invCategory','invQty','invMinQty','invCostPrice','invSellPrice','invSupplier'].forEach(id=>document.getElementById(id).value='');
hideInvForm();loadInventory();}catch(e){alert(e.message)}
}
async function loadInventory(){
const c=document.getElementById('inventoryList');c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/inventory');const data=await res.json();
if(!data.items.length){c.innerHTML='<div class="card"><p>No stock items.</p></div>';return}
c.innerHTML=data.items.map(i=>{
const cls=i.qty<=i.min_qty?'warn':'ok';
return '<div class="card"><h3>'+esc(i.name)+' <span class="badge '+cls+'">'+i.qty+' in stock</span></h3><p style="font-family:monospace;font-size:12px">'+esc(i.part_number||'-')+'</p><p>'+esc(i.category||'-')+' | Supplier: '+esc(i.supplier||'-')+'</p><p>Cost: R'+i.cost_price.toFixed(2)+' | Sell: R'+i.sell_price.toFixed(2)+'</p>'+(i.qty<=i.min_qty?'<p style="color:#F44336;font-size:12px;font-weight:bold">⚠ Low stock (min '+i.min_qty+')</p>':'')+'<div style="margin-top:8px"><button class="btn-sm green" onclick="adjustStock(\''+i.id+'\',1)">+1</button><button class="btn-sm red" onclick="adjustStock(\''+i.id+'\',-1)">-1</button><button class="btn-sm gray" onclick="deleteInvItem(\''+i.id+'\')">Delete</button></div></div>';
}).join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function adjustStock(id,d){try{await fetch('/api/inventory/'+id+'/adjust',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({delta:d})});loadInventory();}catch(e){alert(e.message)}}
async function deleteInvItem(id){if(!confirm('Delete?'))return;try{await fetch('/api/inventory/'+id,{method:'DELETE'});loadInventory();}catch(e){alert(e.message)}}

// STAFF
function showStaffForm(){document.getElementById('staffForm').style.display='block';}
function hideStaffForm(){document.getElementById('staffForm').style.display='none';}
async function addStaff(){
const name=document.getElementById('staffName').value.trim();
if(!name){alert('Name required');return}
try{await fetch('/api/staff',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,role:document.getElementById('staffRole').value,phone:document.getElementById('staffPhone').value,email:document.getElementById('staffEmail').value})});
['staffName','staffRole','staffPhone','staffEmail'].forEach(id=>document.getElementById(id).value='');
hideStaffForm();loadStaff();}catch(e){alert(e.message)}
}
async function loadStaff(){
const c=document.getElementById('staffList');c.innerHTML='<div class="loading">Loading...</div>';
try{const res=await fetch('/api/staff');const data=await res.json();
c.innerHTML=data.staff.length?data.staff.map(s=>'<div class="card"><h3>👷 '+esc(s.name)+'</h3><p>'+esc(s.role||'-')+'</p>'+(s.phone?'<p>📞 '+esc(s.phone)+'</p>':'')+(s.email?'<p>📧 '+esc(s.email)+'</p>':'')+'<button class="btn-sm red" onclick="deleteStaff(\''+s.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>No staff yet.</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function deleteStaff(id){if(!confirm('Delete?'))return;try{await fetch('/api/staff/'+id,{method:'DELETE'});loadStaff();}catch(e){alert(e.message)}}

// WIRING
let wiringData=[];
async function loadWiring(){
try{const res=await fetch('/api/wiring');const data=await res.json();
wiringData=data.circuits;renderWiring();
}catch(e){}
}
function filterWiring(){renderWiring();}
function renderWiring(){
const q=(document.getElementById('wiringSearch').value||'').toLowerCase();
const f=wiringData.filter(x=>!q||x.name.toLowerCase().includes(q)||x.system.toLowerCase().includes(q));
document.getElementById('wiringList').innerHTML=f.length?f.map(w=>'<div class="card"><h3>🔌 '+esc(w.name)+'</h3><p style="font-size:12px;color:var(--text2)">'+esc(w.system)+' — '+esc(w.description)+'</p><p style="margin-top:8px"><strong>Components:</strong></p>'+w.components.map(c=>'<div class="list-item">• '+esc(c)+'</div>').join('')+'<p style="margin-top:8px"><strong>Connections:</strong></p>'+w.connections.map(c=>'<div class="list-item" style="font-family:monospace;font-size:11px">'+esc(c)+'</div>').join('')+'<p style="margin-top:8px"><strong>Notes:</strong></p>'+w.notes.map(n=>'<div class="list-item">• '+esc(n)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>';
}

// BOLT CALC
async function calcTorque(){
try{const res=await fetch('/api/bolt-calc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({size:document.getElementById('boltSize').value,grade:document.getElementById('boltGrade').value,condition:document.getElementById('boltCondition').value})});
const d=await res.json();
document.getElementById('boltResult').innerHTML='<div class="card" style="background:var(--primary);color:white"><h3 style="color:white">Recommended</h3><p style="font-size:30px;font-weight:bold;color:white;margin:8px 0">'+d.nm.toFixed(1)+' Nm</p><p style="color:white">'+d.ftlb.toFixed(1)+' ft·lb</p></div><div class="card"><p><strong>Clamp:</strong> '+d.clamp_kn.toFixed(1)+' kN</p></div>';
}catch(e){}
}

// TORQUE
let torqueData=[],seqData=[];
async function loadTorque(){
if(torqueData.length){renderTorque();return}
try{const res=await fetch('/api/torque');const data=await res.json();
torqueData=data.bolts;seqData=data.sequences;renderTorque();}catch(e){}
}
function renderTorque(){
const q=(document.getElementById('torqueSearch').value||'').toLowerCase();
const f=torqueData.filter(x=>!q||x.size.toLowerCase().includes(q)||x.grade.toLowerCase().includes(q)||x.use.toLowerCase().includes(q));
let h='<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>';
f.forEach(x=>{h+='<tr><td><strong>'+esc(x.size)+'</strong></td><td>'+esc(x.grade)+'</td><td>'+x.nm+'</td><td>'+x.ftlb+'</td><td>'+esc(x.use)+'</td></tr>'});
h+='</table>';
document.getElementById('torqueTable').innerHTML=h;
document.getElementById('torqueSeq').innerHTML=seqData.map(s=>'<div class="card"><h3>'+esc(s.component)+'</h3><p style="font-size:11px;color:var(--text2)">Pattern: '+esc(s.pattern)+'</p>'+s.steps.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'<p style="font-size:12px;font-style:italic;margin-top:6px">'+esc(s.note)+'</p></div>').join('');
}
function filterTorque(){renderTorque();}

// HISTORY
async function searchVehicleHistory(){
const q=document.getElementById('vehicleSearch').value.trim().toLowerCase();
const c=document.getElementById('vehicleHistory');
if(!q){c.innerHTML='<div class="loading">Enter search term</div>';return}
try{const res=await fetch('/api/jobs');const data=await res.json();
const m=data.jobs.filter(j=>j.vehicle.toLowerCase().includes(q)||(j.registration||'').toLowerCase().includes(q));
c.innerHTML=m.length?'<p style="margin-bottom:12px;color:var(--text2)">'+m.length+' record(s)</p>'+m.reverse().map(j=>'<div class="card"><h3>Job #'+j.id+'</h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p><p style="color:var(--text2)">'+esc(j.complaint)+'</p><p><span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+esc(j.status)+'</span></p><p style="font-size:11px;color:var(--text2)">'+esc(j.created)+'</p></div>').join(''):'<div class="card"><p>No history</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

// ANALYTICS
async function loadAnalytics(){
try{const res=await fetch('/api/analytics');const d=await res.json();
let h='<div class="stats-row"><div class="stat-card blue"><div class="num">R'+d.avg_invoice.toFixed(0)+'</div><div class="lbl">Avg Invoice</div></div><div class="stat-card green"><div class="num">R'+d.total_revenue.toFixed(0)+'</div><div class="lbl">Total Revenue</div></div></div>';
if(d.top_services.length)h+='<div class="card"><h3>🔥 Top Services</h3>'+d.top_services.map(s=>'<div class="list-item"><strong>'+esc(s.name)+'</strong> — '+s.count+'×</div>').join('')+'</div>';
if(d.top_customers.length)h+='<div class="card"><h3>⭐ Top Customers</h3>'+d.top_customers.map(x=>'<div class="list-item"><strong>'+esc(x.name)+'</strong> — R'+x.total.toFixed(0)+'</div>').join('')+'</div>';
document.getElementById('analyticsContent').innerHTML=h;
}catch(e){}
}

// SETTINGS
async function loadSettings(){
try{const res=await fetch('/api/workshop');const d=await res.json();
document.getElementById('wsLogo').value=d.logo||'🔧';
document.getElementById('wsName').value=d.name||'';
document.getElementById('wsPhone').value=d.phone||'';
document.getElementById('wsAddress').value=d.address||'';
document.getElementById('wsEmail').value=d.email||'';
document.getElementById('wsRate').value=d.labour_rate||450;
applyBranding(d);
}catch(e){}
}
function applyBranding(d){
document.getElementById('logoDisplay').textContent=d.logo||'🔧';
document.getElementById('wsNameDisplay').textContent=(d.name||'RAMSTECH').toUpperCase();
const sub=[d.phone,d.address].filter(Boolean).join(' • ');
document.getElementById('wsSubtitle').textContent=sub||'AI Workshop Assistant v6.0';
}
async function saveSettings(){
try{const p={logo:document.getElementById('wsLogo').value||'🔧',name:document.getElementById('wsName').value,phone:document.getElementById('wsPhone').value,address:document.getElementById('wsAddress').value,email:document.getElementById('wsEmail').value,labour_rate:parseFloat(document.getElementById('wsRate').value)||450};
await fetch('/api/workshop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
applyBranding(p);alert('Saved');}catch(e){alert(e.message)}
}
loadSettings();

function exportJobsCSV(){window.location.href='/api/export/jobs';}
function exportCustomersCSV(){window.location.href='/api/export/customers';}
</script>
</body>
</html>"""

# ═══════════════════════════════════
# ROUTES
# ═══════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def home(): return HTML_PAGE

@app.get("/health")
def health(): return {"status":"healthy","time":datetime.now().isoformat()}

@app.get("/api/stats")
def get_stats():
    from datetime import timedelta
    total=len(JOBS)
    open_j=sum(1 for j in JOBS.values() if j["status"]!="Completed")
    done=sum(1 for j in JOBS.values() if j["status"]=="Completed")
    new=sum(1 for j in JOBS.values() if j["status"]=="New")
    prog=sum(1 for j in JOBS.values() if j["status"]=="In Progress")
    rev=sum(i["total"] for i in INVOICES.values())
    labels,data=[],[]
    for i in range(6,-1,-1):
        day=(datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])
        data.append(round(sum(inv["total"] for inv in INVOICES.values() if inv.get("created","").startswith(day)),2))
    return {"jobs_total":total,"jobs_open":open_j,"jobs_completed":done,"jobs_new":new,"jobs_progress":prog,
            "customers":len(CUSTOMERS),"staff":len(STAFF),"revenue":round(rev,2),
            "revenue_labels":labels,"revenue_data":data}

@app.get("/api/analytics")
def get_analytics():
    tr=sum(i["total"] for i in INVOICES.values())
    avg=tr/len(INVOICES) if INVOICES else 0
    services={}
    for j in JOBS.values():
        c=j.get("complaint","").strip()[:30]
        if c: services[c]=services.get(c,0)+1
    top_services=[{"name":k,"count":v} for k,v in sorted(services.items(),key=lambda x:-x[1])[:5]]
    cr={}
    for i in INVOICES.values():
        n=i.get("customer","")
        if n:
            if n not in cr: cr[n]={"total":0,"jobs":0}
            cr[n]["total"]+=i["total"]; cr[n]["jobs"]+=1
    top_customers=[{"name":k,"total":v["total"]} for k,v in sorted(cr.items(),key=lambda x:-x[1]["total"])[:5]]
    return {"total_revenue":tr,"avg_invoice":avg,"top_services":top_services,"top_customers":top_customers}

@app.get("/api/workshop")
def get_workshop(): return WORKSHOP

@app.post("/api/workshop")
async def save_workshop(request: Request):
    d=await request.json(); WORKSHOP.update(d); return {"success":True,"workshop":WORKSHOP}

@app.get("/api/fault-codes")
def list_codes(search: str = None):
    r=list(FAULT_CODES.values())
    if search:
        q=search.lower(); r=[c for c in r if q in c["code"].lower() or q in c["description"].lower()]
    return {"count":len(r),"codes":r}

@app.get("/api/problems")
def list_problems(): return {"problems":COMMON_PROBLEMS}

@app.get("/api/wiring")
def list_wiring(): return {"circuits":WIRING_LIBRARY}

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v=vin.strip().upper()
    if len(v)!=17: raise HTTPException(400,"VIN must be 17 characters")
    m,c=WMI_DB.get(v[:3],("Unknown","Unknown"))
    return {"vin":v,"manufacturer":m,"country":c,"year":YEAR_CODES.get(v[9],"Unknown")}

@app.post("/api/chat")
async def chat(request: Request):
    d=await request.json(); msg=d.get("message","")
    if not msg: raise HTTPException(400,"Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured"}
    try:
        c=openai.OpenAI(api_key=OPENAI_KEY)
        r=c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, an expert mechanic."},
                      {"role":"user","content":msg}],max_tokens=800,temperature=0.3)
        return {"reply":r.choices[0].message.content}
    except Exception as e: return {"reply":f"Error: {str(e)}"}

@app.post("/api/paint/match")
async def match_paint(request: Request):
    d=await request.json(); img=d.get("image_base64",""); vehicle=d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img=img.split(",",1)[1]
    if len(img)>7000000: return {"success":False,"error":"Image too large"}
    prompt=f"""Expert paint technician. Vehicle: {vehicle or 'Not specified'}
Respond ONLY valid JSON:
{{"detected_colour":{{"name":"N","hex_code":"#RRGGBB","rgb":[R,G,B],"finish":"Solid|Metallic|Pearl","colour_family":"White|Black|Red|Blue|Silver|Grey"}},"confidence":"High|Medium|Low","brand_codes":[{{"brand":"DuPont","code":"C","name":"F"}},{{"brand":"PPG","code":"C","name":"F"}}],"mixing_formula":{{"base_colour":"D","toners":[{{"name":"T","parts":"X"}}],"reducer":"R"}},"safety_warnings":["W"]}}"""
    try:
        c=openai.OpenAI(api_key=OPENAI_KEY,timeout=60.0)
        r=c.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000,temperature=0.2,response_format={"type":"json_object"})
        p=json.loads(r.choices[0].message.content); p["success"]=True; return p
    except Exception as e: return {"success":False,"error":str(e)}

@app.post("/api/diagnose/photo")
async def diagnose_photo(request: Request):
    d=await request.json(); img=d.get("image_base64",""); vehicle=d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img=img.split(",",1)[1]
    if len(img)>7000000: return {"success":False,"error":"Image too large"}
    prompt=f"""Expert mechanic. Vehicle: {vehicle or 'Not specified'}
Respond ONLY valid JSON:
{{"problem":"S","description":"D","confidence":"High|Medium|Low","possible_causes":["C"],"diagnostic_steps":["S"],"safety_warnings":["W"]}}"""
    try:
        c=openai.OpenAI(api_key=OPENAI_KEY,timeout=60.0)
        r=c.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000,temperature=0.2,response_format={"type":"json_object"})
        p=json.loads(r.choices[0].message.content); p["success"]=True; return p
    except Exception as e: return {"success":False,"error":str(e)}

# JOBS
@app.get("/api/jobs")
def list_jobs(): return {"jobs":list(JOBS.values())}

@app.post("/api/jobs")
async def create_job(request: Request):
    d=await request.json()
    jid=str(len(JOBS)+1).zfill(4)
    JOBS[jid]={"id":jid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
               "registration":d.get("registration",""),"complaint":d.get("complaint",""),
               "assigned_to":d.get("assigned_to",""),"photos":d.get("photos",[])[:5],
               "status":"New","timeline":[datetime.now().strftime("%Y-%m-%d %H:%M")+" — Job created"],
               "labour_hours":0,"labour_rate":WORKSHOP.get("labour_rate",450),"parts_cost":0,
               "labour_cost":0,"subtotal":0,"vat":0,"total":0,
               "created":datetime.now().strftime("%Y-%m-%d %H:%M")}
    return {"success":True,"job":JOBS[jid]}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, request: Request):
    d=await request.json()
    if jid not in JOBS: raise HTTPException(404,"Not found")
    if "status" in d: JOBS[jid]["status"]=d["status"]
    if "note" in d:
        JOBS[jid].setdefault("timeline",[]).append(
            datetime.now().strftime("%Y-%m-%d %H:%M")+" — "+d["note"])
    return {"success":True,"job":JOBS[jid]}

@app.post("/api/jobs/{jid}/cost")
async def set_job_cost(jid: str, request: Request):
    d=await request.json()
    if jid not in JOBS: raise HTTPException(404,"Not found")
    hours=float(d.get("labour_hours",0))
    rate=float(d.get("labour_rate",WORKSHOP.get("labour_rate",450)))
    parts=float(d.get("parts_cost",0))
    labour=hours*rate
    subtotal=labour+parts
    vat=subtotal*0.15
    total=subtotal+vat
    JOBS[jid].update({"labour_hours":hours,"labour_rate":rate,"parts_cost":parts,
                      "labour_cost":labour,"subtotal":subtotal,"vat":vat,"total":total})
    JOBS[jid].setdefault("timeline",[]).append(
        datetime.now().strftime("%Y-%m-%d %H:%M")+f" — Cost set: {hours}h × R{rate} + parts R{parts} = R{total:.2f}")
    return {"success":True,"job":JOBS[jid]}

# CUSTOMERS
@app.get("/api/customers")
def list_customers(): return {"customers":list(CUSTOMERS.values())}

@app.post("/api/customers")
async def create_customer(request: Request):
    d=await request.json()
    cid=str(uuid.uuid4())[:8]
    CUSTOMERS[cid]={"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),
                    "email":d.get("email",""),"address":d.get("address",""),
                    "created":datetime.now().strftime("%Y-%m-%d")}
    return {"success":True,"customer":CUSTOMERS[cid]}

# APPOINTMENTS
@app.get("/api/appointments")
def list_appts(): return {"appointments":list(APPOINTMENTS.values())}

@app.post("/api/appointments")
async def create_appt(request: Request):
    d=await request.json()
    aid=str(uuid.uuid4())[:8]
    APPOINTMENTS[aid]={"id":aid,"customer":d.get("customer",""),"phone":d.get("phone",""),
                       "vehicle":d.get("vehicle",""),"service":d.get("service",""),
                       "date":d.get("date",""),"time":d.get("time","")}
    return {"success":True,"appointment":APPOINTMENTS[aid]}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str):
    if aid not in APPOINTMENTS: raise HTTPException(404,"Not found")
    del APPOINTMENTS[aid]; return {"success":True}

# INVOICES
@app.get("/api/invoices")
def list_invoices(): return {"invoices":list(INVOICES.values())}

@app.get("/api/invoices/{iid}")
def get_invoice(iid: str):
    if iid not in INVOICES: raise HTTPException(404,"Not found")
    return INVOICES[iid]

@app.post("/api/invoices")
async def create_invoice(request: Request):
    d=await request.json()
    labour=float(d.get("labour",0)); parts=float(d.get("parts",0))
    subtotal=labour+parts; vat=subtotal*0.15; total=subtotal+vat
    iid=str(len(INVOICES)+1).zfill(4)
    INVOICES[iid]={"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
                   "description":d.get("description",""),"labour":labour,"parts":parts,
                   "subtotal":subtotal,"vat":vat,"total":total,
                   "created":datetime.now().strftime("%Y-%m-%d %H:%M")}
    return {"success":True,"invoice":INVOICES[iid]}

# PARTS
@app.get("/api/parts")
def list_parts(): return {"parts":PARTS_CATALOG}

# INVENTORY
@app.get("/api/inventory")
def list_inventory(): return {"items":list(INVENTORY.values())}

@app.get("/api/inventory/low-stock")
def low_stock():
    items=[{"id":k,"name":v["name"],"qty":v["qty"],"min":v["min_qty"]}
           for k,v in INVENTORY.items() if v["qty"]<=v["min_qty"]]
    return {"items":items}

@app.post("/api/inventory")
async def add_inventory(request: Request):
    d=await request.json()
    iid=str(uuid.uuid4())[:8]
    INVENTORY[iid]={"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),
                    "category":d.get("category",""),"qty":int(d.get("qty",0)),
                    "min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),
                    "sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),
                    "created":datetime.now().strftime("%Y-%m-%d")}
    return {"success":True,"item":INVENTORY[iid]}

@app.post("/api/inventory/{iid}/adjust")
async def adjust_inventory(iid: str, request: Request):
    d=await request.json()
    if iid not in INVENTORY: raise HTTPException(404,"Not found")
    INVENTORY[iid]["qty"]=max(0,INVENTORY[iid]["qty"]+int(d.get("delta",0)))
    return {"success":True,"item":INVENTORY[iid]}

@app.delete("/api/inventory/{iid}")
def delete_inventory(iid: str):
    if iid not in INVENTORY: raise HTTPException(404,"Not found")
    del INVENTORY[iid]; return {"success":True}

# STAFF
@app.get("/api/staff")
def list_staff(): return {"staff":list(STAFF.values())}

@app.post("/api/staff")
async def add_staff(request: Request):
    d=await request.json()
    sid=str(uuid.uuid4())[:8]
    STAFF[sid]={"id":sid,"name":d.get("name",""),"role":d.get("role",""),
                "phone":d.get("phone",""),"email":d.get("email",""),
                "created":datetime.now().strftime("%Y-%m-%d")}
    return {"success":True,"staff":STAFF[sid]}

@app.delete("/api/staff/{sid}")
def delete_staff(sid: str):
    if sid not in STAFF: raise HTTPException(404,"Not found")
    del STAFF[sid]; return {"success":True}

# BOLT CALC
@app.post("/api/bolt-calc")
async def bolt_calc(request: Request):
    d=await request.json()
    size=d.get("size","M8"); grade=d.get("grade","8.8"); condition=d.get("condition","dry")
    tm={"8.8":800,"10.9":1040,"12.9":1220}
    am={"M6":20.1,"M8":36.6,"M10":58.0,"M12":84.3,"M14":115.0,"M16":157.0,"M18":192.0,"M20":245.0}
    km={"dry":0.20,"oiled":0.17,"moly":0.14}
    ts=tm.get(grade,800); a=am.get(size,36.6); k=km.get(condition,0.20)
    cf=0.75*ts*a; d_m=float(size.replace("M",""))/1000.0
    nm=k*d_m*cf
    return {"size":size,"grade":grade,"condition":condition,"nm":nm,"ftlb":nm*0.73756,"clamp_kn":cf/1000}

@app.get("/api/torque")
def get_torque(): return {"bolts":TORQUE_SPECS,"sequences":TORQUE_SEQUENCES}

# CSV
@app.get("/api/export/jobs")
def export_jobs():
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Job ID","Customer","Vehicle","Reg","Complaint","Assigned","Status","Total","Created"])
    for j in JOBS.values():
        w.writerow([j["id"],j["customer"],j["vehicle"],j.get("registration",""),
                    j["complaint"],j.get("assigned_to",""),j["status"],
                    j.get("total",0),j["created"]])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=jobs.csv"})

@app.get("/api/export/customers")
def export_customers():
    o=io.StringIO(); w=csv.writer(o)
    w.writerow(["Name","Phone","Email","Address","Created"])
    for c in CUSTOMERS.values():
        w.writerow([c["name"],c["phone"],c.get("email",""),c.get("address",""),c["created"]])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]),media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=customers.csv"})
