from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import openai
import os
import json
import uuid

app = FastAPI(title="RamsTech")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ═══════════════════════════════════
# DATA STORES
# ═══════════════════════════════════
FAULT_CODES = {
    "P0101": {"code": "P0101", "description": "Mass Air Flow Circuit", "system": "Engine",
              "severity": "Medium",
              "causes": ["Dirty MAF", "Air leaks", "Clogged filter"],
              "symptoms": ["Poor economy", "Loss of power"],
              "steps": ["Check filter", "Inspect intake", "Clean MAF"]},
    "P0300": {"code": "P0300", "description": "Multiple Cylinder Misfire", "system": "Engine",
              "severity": "High",
              "causes": ["Faulty plugs", "Bad coils", "Fuel issues"],
              "symptoms": ["Engine shaking", "Loss of power"],
              "steps": ["Scan cylinders", "Check plugs", "Test coils"]},
    "P0401": {"code": "P0401", "description": "EGR Flow Insufficient", "system": "Engine",
              "severity": "Medium",
              "causes": ["Clogged EGR", "Blocked passages"],
              "symptoms": ["Check engine light"],
              "steps": ["Inspect EGR", "Check passages"]},
    "P0700": {"code": "P0700", "description": "Transmission Control System", "system": "Transmission",
              "severity": "High",
              "causes": ["Internal fault", "TCM problem"],
              "symptoms": ["Slipping", "Harsh shifting"],
              "steps": ["Scan TCM", "Check fluid"]},
    "P0087": {"code": "P0087", "description": "Fuel Rail Pressure Low", "system": "Diesel",
              "severity": "High",
              "causes": ["Faulty HP pump", "Clogged filter"],
              "symptoms": ["Won't start", "Loss of power"],
              "steps": ["Check pressure", "Inspect filter"]},
    "HYD-001": {"code": "HYD-001", "description": "Low Hydraulic Pressure", "system": "Hydraulic",
                "severity": "High",
                "causes": ["Worn pump", "Leaks", "Low fluid"],
                "symptoms": ["Slow operation", "Weak lifting"],
                "steps": ["Check fluid", "Test pressure"]},
    "PNEU-001": {"code": "PNEU-001", "description": "Air Compressor No Pressure", "system": "Pneumatic",
                 "severity": "High",
                 "causes": ["Worn rings", "Leaking valves"],
                 "symptoms": ["Low pressure"],
                 "steps": ["Check belt", "Test output"]},
}

WMI_DB = {
    "1HG": ("Honda", "USA"), "1FT": ("Ford", "USA"),
    "JHM": ("Honda", "Japan"), "JTD": ("Toyota", "Japan"),
    "JTM": ("Toyota", "Japan"), "KMH": ("Hyundai", "Korea"),
    "KNA": ("Kia", "Korea"), "WBA": ("BMW", "Germany"),
    "WDB": ("Mercedes-Benz", "Germany"), "WVW": ("Volkswagen", "Germany"),
    "AHT": ("Toyota SA", "South Africa"), "ADB": ("Mercedes SA", "South Africa"),
}

YEAR_CODES = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014,
    "F": 2015, "G": 2016, "H": 2017, "J": 2018, "K": 2019,
    "L": 2020, "M": 2021, "N": 2022, "P": 2023, "R": 2024,
    "Y": 2000, "1": 2001, "2": 2002, "3": 2003, "4": 2004,
}

TORQUE_SPECS = [
    {"size": "M6", "grade": "8.8", "nm": 10, "ftlb": 7.4, "use": "Small brackets"},
    {"size": "M8", "grade": "8.8", "nm": 25, "ftlb": 18.4, "use": "Engine brackets"},
    {"size": "M10", "grade": "8.8", "nm": 50, "ftlb": 37, "use": "Subframe bolts"},
    {"size": "M12", "grade": "8.8", "nm": 90, "ftlb": 66, "use": "Wheel hubs"},
    {"size": "M14", "grade": "8.8", "nm": 140, "ftlb": 103, "use": "Heavy brackets"},
    {"size": "M16", "grade": "8.8", "nm": 215, "ftlb": 159, "use": "Chassis bolts"},
    {"size": "M18", "grade": "8.8", "nm": 300, "ftlb": 221, "use": "Suspension pivots"},
    {"size": "M20", "grade": "8.8", "nm": 425, "ftlb": 313, "use": "Truck chassis"},
    {"size": "M8", "grade": "10.9", "nm": 35, "ftlb": 25.8, "use": "Cylinder head (small)"},
    {"size": "M10", "grade": "10.9", "nm": 70, "ftlb": 51.6, "use": "Cylinder head bolts"},
    {"size": "M12", "grade": "10.9", "nm": 120, "ftlb": 88.5, "use": "Head bolts / mains"},
    {"size": "M14", "grade": "10.9", "nm": 190, "ftlb": 140, "use": "Head bolts (diesel)"},
    {"size": "M16", "grade": "10.9", "nm": 295, "ftlb": 218, "use": "Heavy diesel heads"},
    {"size": "M12", "grade": "12.9", "nm": 145, "ftlb": 107, "use": "Racing / performance"},
    {"size": "M10", "grade": "12.9", "nm": 83, "ftlb": 61.2, "use": "High performance"},
    {"size": '1/4"', "grade": "Grade 5", "nm": 12, "ftlb": 8.8, "use": "General automotive"},
    {"size": '3/8"', "grade": "Grade 5", "nm": 45, "ftlb": 33, "use": "Suspension"},
    {"size": '1/2"', "grade": "Grade 5", "nm": 105, "ftlb": 77, "use": "Heavy suspension"},
    {"size": '3/8"', "grade": "Grade 8", "nm": 60, "ftlb": 44, "use": "High-stress"},
    {"size": '1/2"', "grade": "Grade 8", "nm": 150, "ftlb": 110, "use": "Tow bars / heavy"},
]

TORQUE_SEQUENCES = [
    {"component": "Cylinder Head — 4 Cyl", "pattern": "Star",
     "steps": ["Stage 1: 40 Nm", "Stage 2: 80 Nm", "Stage 3: +90°", "Stage 4: +90°"],
     "note": "Replace TTY bolts. Use angle gauge."},
    {"component": "Wheel Nuts — Car", "pattern": "Star (cross)",
     "steps": ["Stage 1: 60 Nm", "Final: 110 Nm"],
     "note": "Re-torque after 50-100 km."},
    {"component": "Wheel Nuts — Bakkie", "pattern": "Star",
     "steps": ["Stage 1: 100 Nm", "Final: 140 Nm"],
     "note": "Hilux, Ranger, Amarok."},
    {"component": "Wheel Nuts — Truck", "pattern": "Star",
     "steps": ["Stage 1: 400 Nm", "Stage 2: 500 Nm", "Final: 600 Nm"],
     "note": "10-stud wheels."},
    {"component": "Spark Plugs", "pattern": "Linear",
     "steps": ["Cast iron head: 25 Nm", "Aluminum head: 18 Nm"],
     "note": "Do NOT overtighten aluminum."},
    {"component": "Oil Drain Plug", "pattern": "Linear",
     "steps": ["Steel pan M12: 25 Nm", "Alum pan M12: 18 Nm", "Steel pan M14: 35 Nm"],
     "note": "Replace crush washer every change."},
    {"component": "Intake Manifold", "pattern": "Star",
     "steps": ["Stage 1: 10 Nm", "Stage 2: 20 Nm"],
     "note": "Avoid warping plastic manifolds."},
    {"component": "Turbo Mounting", "pattern": "Star",
     "steps": ["Stage 1: 25 Nm", "Stage 2: 45 Nm"],
     "note": "High-temp anti-seize on threads."},
]

PARTS_CATALOG = [
    {"number": "04152-YZZA1", "name": "Oil Filter", "brand": "Toyota", "category": "Engine", "price": 15},
    {"number": "17801-30060", "name": "Air Filter", "brand": "Toyota", "category": "Engine", "price": 25},
    {"number": "04465-YZZE8", "name": "Brake Pads Front", "brand": "Toyota", "category": "Brakes", "price": 55},
    {"number": "04466-YZZE8", "name": "Brake Pads Rear", "brand": "Toyota", "category": "Brakes", "price": 45},
    {"number": "23390-30020", "name": "Fuel Filter", "brand": "Toyota", "category": "Fuel", "price": 35},
    {"number": "90919-01253", "name": "Spark Plug", "brand": "Toyota", "category": "Ignition", "price": 12},
    {"number": "90915-YZZD2", "name": "Oil Filter (alt)", "brand": "Toyota", "category": "Engine", "price": 18},
    {"number": "28113-2P100", "name": "Air Filter", "brand": "Hyundai", "category": "Engine", "price": 22},
    {"number": "26300-35505", "name": "Oil Filter", "brand": "Hyundai", "category": "Engine", "price": 14},
    {"number": "58101-2EA00", "name": "Brake Pads", "brand": "Hyundai", "category": "Brakes", "price": 50},
    {"number": "BK-4E", "name": "Battery Terminal", "brand": "Universal", "category": "Electrical", "price": 8},
    {"number": "HF-1", "name": "Hydraulic Filter", "brand": "Universal", "category": "Hydraulic", "price": 45},
    {"number": "AF-220", "name": "Air Filter (heavyduty)", "brand": "Universal", "category": "Pneumatic", "price": 60},
    {"number": "WABCO-4324100202", "name": "Air Dryer Cartridge", "brand": "WABCO", "category": "Pneumatic", "price": 85},
    {"number": "BOSCH-F026T02025", "name": "Fuel Filter", "brand": "Bosch", "category": "Diesel", "price": 40},
    {"number": "MANN-WK940/20", "name": "Diesel Filter", "brand": "MANN", "category": "Diesel", "price": 38},
    {"number": "GATES-6PK1250", "name": "Serpentine Belt", "brand": "Gates", "category": "Engine", "price": 65},
    {"number": "NGK-BKR6EIX", "name": "Iridium Spark Plug", "brand": "NGK", "category": "Ignition", "price": 18},
    {"number": "DENSO-IK20", "name": "Iridium Plug", "brand": "Denso", "category": "Ignition", "price": 16},
    {"number": "DELPHI-CF1022", "name": "Fuel Pump", "brand": "Delphi", "category": "Fuel", "price": 220},
]

COMMON_PROBLEMS = [
    {"title": "Engine won't start (cranks)", "system": "Engine",
     "causes": ["No fuel", "No spark", "Low compression", "Faulty injectors"],
     "checks": ["Check fuel pressure", "Test for spark", "Compression test", "Scan codes"],
     "severity": "High"},
    {"title": "Engine cranks but no fire (diesel)", "system": "Diesel",
     "causes": ["Air in fuel system", "Glow plugs", "Low rail pressure", "Crank sensor"],
     "checks": ["Bleed fuel system", "Test glow plugs", "Check rail pressure", "Scan codes"],
     "severity": "High"},
    {"title": "Overheating", "system": "Cooling",
     "causes": ["Low coolant", "Thermostat stuck", "Water pump", "Radiator blocked"],
     "checks": ["Check coolant level", "Test thermostat", "Check pump flow", "Pressure test"],
     "severity": "Critical"},
    {"title": "Misfire at idle", "system": "Engine",
     "causes": ["Spark plugs", "Ignition coils", "Vacuum leak", "Injectors"],
     "checks": ["Scan for codes", "Check plugs", "Test coils", "Smoke test for leaks"],
     "severity": "Medium"},
    {"title": "White smoke (diesel)", "system": "Diesel",
     "causes": ["Injector timing", "Coolant leak", "Glow plugs", "Low compression"],
     "checks": ["Check coolant level", "Test injectors", "Compression test", "Check timing"],
     "severity": "High"},
    {"title": "Black smoke (diesel)", "system": "Diesel",
     "causes": ["Over-fuelling", "Air filter", "Turbo", "EGR issue"],
     "checks": ["Check air filter", "Test turbo boost", "Check injectors", "Check EGR"],
     "severity": "Medium"},
    {"title": "Transmission slipping", "system": "Transmission",
     "causes": ["Low fluid", "Worn clutches", "Solenoid", "Converter"],
     "checks": ["Check fluid level & color", "Scan TCM", "Test line pressure", "Check solenoids"],
     "severity": "High"},
    {"title": "Brake pedal soft", "system": "Brakes",
     "causes": ["Air in system", "Brake fluid leak", "Master cylinder", "Worn pads"],
     "checks": ["Bleed brakes", "Check for leaks", "Test master cylinder", "Inspect pads"],
     "severity": "Critical"},
    {"title": "ABS light on", "system": "Brakes",
     "causes": ["Wheel speed sensor", "Tone ring", "Wiring", "ABS module"],
     "checks": ["Scan ABS codes", "Check sensor resistance", "Inspect tone ring", "Test wiring"],
     "severity": "High"},
    {"title": "Battery drains overnight", "system": "Electrical",
     "causes": ["Parasitic draw", "Alternator", "Old battery", "Short circuit"],
     "checks": ["Check parasitic draw", "Test alternator output", "Load test battery", "Check for shorts"],
     "severity": "Medium"},
    {"title": "Low hydraulic power (plant)", "system": "Hydraulic",
     "causes": ["Low fluid", "Worn pump", "Internal leak", "Relief valve"],
     "checks": ["Check fluid level", "Test pressure", "Check for leaks", "Test relief valve"],
     "severity": "High"},
    {"title": "Air compressor no pressure", "system": "Pneumatic",
     "causes": ["Worn rings", "Leaking valves", "Belt slippage", "Air leaks"],
     "checks": ["Check belt tension", "Test output pressure", "Check for leaks", "Inspect valves"],
     "severity": "High"},
    {"title": "Rough idle", "system": "Engine",
     "causes": ["Vacuum leak", "Dirty throttle body", "MAF sensor", "Spark plugs"],
     "checks": ["Smoke test for vacuum leaks", "Clean throttle body", "Clean MAF", "Check plugs"],
     "severity": "Medium"},
    {"title": "Grinding when braking", "system": "Brakes",
     "causes": ["Worn pads", "Warped rotor", "Worn bearings", "Debris"],
     "checks": ["Inspect pads", "Check rotor thickness", "Check bearings", "Clean caliper"],
     "severity": "High"},
    {"title": "Stuck in limp mode", "system": "Transmission",
     "causes": ["Sensor fault", "Wiring", "TCM", "Mechanical fault"],
     "checks": ["Scan codes", "Check wiring", "Test sensors", "Check fluid"],
     "severity": "High"},
]

JOBS = {}
CUSTOMERS = {}
APPOINTMENTS = {}
INVOICES = {}

# ═══════════════════════════════════
# HTML FRONTEND
# ═══════════════════════════════════
HTML_PAGE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RamsTech</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#f5f5f5;color:#212121;padding-bottom:20px}
.header{background:#E65100;color:white;padding:16px;text-align:center}
.header h1{font-size:22px}
.header p{font-size:12px;opacity:.9;margin-top:4px}
.tabs{display:flex;background:white;border-bottom:1px solid #ddd;overflow-x:auto;position:sticky;top:0;z-index:99;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{padding:14px 12px;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap;font-size:12px}
.tab.active{color:#E65100;border-bottom-color:#E65100;font-weight:bold}
.panel{display:none;padding:16px;max-width:800px;margin:0 auto}
.panel.active{display:block}
.chat-box{background:white;border-radius:12px;padding:12px;height:400px;overflow-y:auto;margin-bottom:12px}
.msg{padding:10px 14px;margin:6px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.4}
.msg.user{background:#E65100;color:white;margin-left:auto}
.msg.ai{background:#f0f0f0}
.input-row{display:flex;gap:8px}
.input-row input{flex:1;padding:12px 16px;border:1px solid #ccc;border-radius:25px;font-size:14px;outline:none}
.input-row button{padding:12px 20px;background:#E65100;color:white;border:none;border-radius:25px;font-weight:bold;cursor:pointer}
.form-input{width:100%;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;margin-bottom:10px}
.btn{width:100%;padding:14px;background:#E65100;color:white;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;margin-bottom:12px}
.btn:active{background:#BF360C}
.btn-sm{padding:6px 10px;background:#E65100;color:white;border:none;border-radius:6px;font-size:12px;font-weight:bold;cursor:pointer;margin-right:6px}
.btn-sm.gray{background:#666}.btn-sm.green{background:#4CAF50}.btn-sm.red{background:#F44336}
.card{background:white;padding:16px;border-radius:12px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.card h3{color:#E65100;margin-bottom:8px;font-size:16px}
.card p{margin:4px 0;font-size:13px;line-height:1.4}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:white;margin-left:6px}
.badge.high{background:#F44336}.badge.medium{background:#FF9800}.badge.low{background:#4CAF50}
.badge.status{background:#2196F3}.badge.new{background:#666}.badge.progress{background:#FF9800}.badge.done{background:#4CAF50}
.list-item{padding:6px 0;border-bottom:1px solid #eee;font-size:13px}
.list-item:last-child{border-bottom:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.grid-item{background:white;padding:14px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08);cursor:pointer}
.grid-item:active{background:#f0f0f0}
.grid-item .icon{font-size:28px;margin-bottom:6px}
.grid-item .label{font-size:11px;font-weight:bold}
.img-preview{width:100%;border-radius:12px;margin-bottom:12px}
.swatch{height:80px;border-radius:12px;border:1px solid #ccc;margin-bottom:12px}
.status-online{background:#E8F5E9;color:#2E7D32;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.status-offline{background:#FFEBEE;color:#C62828;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.loading{text-align:center;padding:20px;color:#666}
.torque-table{width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:#E65100;color:white;padding:8px 6px;text-align:left}
.torque-table td{padding:8px 6px;border-bottom:1px solid #eee}
.torque-table tr:last-child td{border-bottom:none}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.stat-card{background:white;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.stat-card .num{font-size:28px;font-weight:bold;color:#E65100}
.stat-card .lbl{font-size:11px;color:#666;margin-top:4px}
.stat-card.green .num{color:#4CAF50}
.stat-card.red .num{color:#F44336}
.stat-card.blue .num{color:#2196F3}
</style>
</head>
<body>

<div class="header">
<h1>🔧 RAMSTECH</h1>
<p>AI Workshop Assistant v3.0</p>
</div>

<div class="tabs">
<div class="tab active" onclick="showTab('home',this)">🏠 Home</div>
<div class="tab" onclick="showTab('dashboard',this)">📊 Dash</div>
<div class="tab" onclick="showTab('chat',this)">🤖 AI</div>
<div class="tab" onclick="showTab('codes',this)">📟 Codes</div>
<div class="tab" onclick="showTab('problems',this)">📖 Problems</div>
<div class="tab" onclick="showTab('vin',this)">🔍 VIN</div>
<div class="tab" onclick="showTab('paint',this)">🎨 Paint</div>
<div class="tab" onclick="showTab('photo',this)">📸 Diag</div>
<div class="tab" onclick="showTab('jobs',this)">📋 Jobs</div>
<div class="tab" onclick="showTab('customers',this)">👥 Clients</div>
<div class="tab" onclick="showTab('appointments',this)">📅 Appts</div>
<div class="tab" onclick="showTab('invoices',this)">💰 Invoices</div>
<div class="tab" onclick="showTab('parts',this)">🔩 Parts</div>
<div class="tab" onclick="showTab('boltcalc',this)">🔧 Bolt Calc</div>
<div class="tab" onclick="showTab('torque',this)">⚙️ Torque</div>
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
<div class="grid-item" onclick="clickTab(13)"><div class="icon">🔧</div><div class="label">Bolt Calc</div></div>
<div class="grid-item" onclick="clickTab(14)"><div class="icon">⚙️</div><div class="label">Torque</div></div>
</div>
</div>

<div id="dashboard" class="panel">
<h3 style="margin-bottom:12px;color:#E65100">📊 Workshop Dashboard</h3>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>Today's Appointments</h3><div id="dashAppts"><div class="loading">Loading...</div></div></div>
<div class="card"><h3>Recent Jobs</h3><div id="dashJobs"><div class="loading">Loading...</div></div></div>
</div>

<div id="chat" class="panel">
<div class="chat-box" id="chatBox"><div class="msg ai">Welcome! Ask about repairs, diagnostics, or tools.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()">
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
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
</div>

<div id="photo" class="panel">
<div class="card"><p style="font-size:13px">Take photo of mechanical issue. AI diagnoses the problem.</p></div>
<input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>

<div id="jobs" class="panel">
<button class="btn" onclick="showJobForm()">+ New Job Card</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jobCustomer" placeholder="Customer name">
<input class="form-input" id="jobVehicle" placeholder="Vehicle (e.g. 2018 Toyota Hilux)">
<input class="form-input" id="jobComplaint" placeholder="Complaint">
<input class="form-input" id="jobVehicleReg" placeholder="Registration">
<button class="btn" onclick="createJob()">Create Job</button>
<button class="btn" style="background:#666" onclick="hideJobForm()">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<div id="customers" class="panel">
<button class="btn" onclick="showCustomerForm()">+ New Customer</button>
<div id="customerForm" style="display:none">
<div class="card">
<input class="form-input" id="custName" placeholder="Full name">
<input class="form-input" id="custPhone" placeholder="Phone number">
<input class="form-input" id="custEmail" placeholder="Email (optional)">
<input class="form-input" id="custAddress" placeholder="Address (optional)">
<button class="btn" onclick="createCustomer()">Save Customer</button>
<button class="btn" style="background:#666" onclick="hideCustomerForm()">Cancel</button>
</div>
</div>
<div id="customerList"><div class="loading">Loading...</div></div>
</div>

<div id="appointments" class="panel">
<button class="btn" onclick="showApptForm()">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="apptCustomer" placeholder="Customer name">
<input class="form-input" id="apptPhone" placeholder="Phone">
<input class="form-input" id="apptVehicle" placeholder="Vehicle">
<input class="form-input" id="apptService" placeholder="Service (e.g. Oil change)">
<input class="form-input" id="apptDate" type="date">
<input class="form-input" id="apptTime" type="time">
<button class="btn" onclick="createAppt()">Book Appointment</button>
<button class="btn" style="background:#666" onclick="hideApptForm()">Cancel</button>
</div>
</div>
<div id="apptList"><div class="loading">Loading...</div></div>
</div>

<div id="invoices" class="panel">
<button class="btn" onclick="showInvoiceForm()">+ New Invoice</button>
<div id="invoiceForm" style="display:none">
<div class="card">
<input class="form-input" id="invCustomer" placeholder="Customer name">
<input class="form-input" id="invVehicle" placeholder="Vehicle">
<input class="form-input" id="invDesc" placeholder="Description (e.g. Full service)">
<input class="form-input" id="invLabour" type="number" placeholder="Labour cost (R)">
<input class="form-input" id="invParts" type="number" placeholder="Parts cost (R)">
<button class="btn" onclick="createInvoice()">Generate Invoice</button>
<button class="btn" style="background:#666" onclick="hideInvoiceForm()">Cancel</button>
</div>
</div>
<div id="invoiceList"><div class="loading">Loading...</div></div>
</div>

<div id="parts" class="panel">
<input type="text" class="form-input" id="partsSearch" placeholder="Search part name or number..." oninput="filterParts()">
<div id="partsList"><div class="loading">Loading...</div></div>
</div>

<div id="boltcalc" class="panel">
<div class="card">
<h3>🔧 Bolt Torque Calculator</h3>
<p style="font-size:12px;color:#666;margin-bottom:12px">Calculate correct torque based on bolt size and grade.</p>
<label style="font-size:13px;font-weight:bold">Bolt Size</label>
<select class="form-input" id="boltSize">
<option>M6</option><option>M8</option><option selected>M10</option>
<option>M12</option><option>M14</option><option>M16</option>
<option>M18</option><option>M20</option>
</select>
<label style="font-size:13px;font-weight:bold">Grade</label>
<select class="form-input" id="boltGrade">
<option>8.8</option><option selected>10.9</option><option>12.9</option>
</select>
<label style="font-size:13px;font-weight:bold">Condition</label>
<select class="form-input" id="boltCondition">
<option value="dry">Dry</option>
<option value="oiled">Lightly oiled</option>
<option value="moly">Moly lubricated</option>
</select>
<button class="btn" onclick="calcTorque()">Calculate Torque</button>
<div id="boltResult"></div>
</div>
</div>

<div id="torque" class="panel">
<input type="text" class="form-input" id="torqueSearch" placeholder="Search size or grade..." oninput="filterTorque()">
<h3 style="margin-bottom:8px;font-size:15px">Bolt Torque</h3>
<div id="torqueTable"></div>
<h3 style="margin:16px 0 8px;font-size:15px">Torque Sequences</h3>
<div id="torqueSeq"></div>
</div>

<script>
function showTab(name,el){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(name).classList.add('active');
if(el)el.classList.add('active');
if(name==='codes'&&!document.getElementById('codeResults').dataset.loaded)searchCodes();
if(name==='problems'&&!document.getElementById('problemList').dataset.loaded)loadProblems();
if(name==='jobs')loadJobs();
if(name==='customers')loadCustomers();
if(name==='appointments')loadAppts();
if(name==='invoices')loadInvoices();
if(name==='parts'&&!document.getElementById('partsList').dataset.loaded)loadParts();
if(name==='torque')loadTorque();
if(name==='dashboard')loadDashboard();
}
function clickTab(i){showTab(document.querySelectorAll('.panel')[i].id,document.querySelectorAll('.tab')[i]);}

async function checkStatus(){
try{await fetch('/health');document.getElementById('status').innerHTML='<span class="status-online">✓ Backend Online</span>';}
catch(e){document.getElementById('status').innerHTML='<span class="status-offline">✗ Backend Offline</span>';}
}
checkStatus();
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}

async function sendMsg(){
const input=document.getElementById('chatInput');
const msg=input.value.trim();if(!msg)return;
const box=document.getElementById('chatBox');
box.innerHTML+='<div class="msg user">'+esc(msg)+'</div>';
input.value='';box.scrollTop=box.scrollHeight;
box.innerHTML+='<div class="msg ai" id="typing">Thinking...</div>';
box.scrollTop=box.scrollHeight;
try{
const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
const data=await res.json();
document.getElementById('typing').outerHTML='<div class="msg ai">'+esc(data.reply)+'</div>';
}catch(e){document.getElementById('typing').outerHTML='<div class="msg ai">Error: '+e.message+'</div>';}
box.scrollTop=box.scrollHeight;
}

async function searchCodes(){
const q=document.getElementById('codeSearch').value;
const c=document.getElementById('codeResults');
c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/fault-codes?search='+encodeURIComponent(q));
const data=await res.json();
c.dataset.loaded='true';
if(!data.codes.length){c.innerHTML='<div class="card"><p>No matches</p></div>';return}
c.innerHTML=data.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:#666;font-size:12px">'+esc(x.system)+'</p><p style="margin-top:8px"><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p style="margin-top:8px"><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

let problemsData=[];
async function loadProblems(){
try{
const res=await fetch('/api/problems');
const data=await res.json();
problemsData=data.problems;
document.getElementById('problemList').dataset.loaded='true';
renderProblems();
}catch(e){document.getElementById('problemList').innerHTML='<div class="card"><p>Error</p></div>'}
}
function filterProblems(){renderProblems();}
function renderProblems(){
const q=(document.getElementById('problemSearch').value||'').toLowerCase();
const filtered=problemsData.filter(x=>!q||x.title.toLowerCase().includes(q)||x.system.toLowerCase().includes(q));
if(!filtered.length){document.getElementById('problemList').innerHTML='<div class="card"><p>No matches</p></div>';return}
document.getElementById('problemList').innerHTML=filtered.map(x=>'<div class="card"><h3>'+esc(x.title)+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p style="color:#666;font-size:12px">'+esc(x.system)+'</p><p style="margin-top:8px"><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p style="margin-top:8px"><strong>Checks:</strong></p>'+x.checks.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join('');
}

async function decodeVin(){
const vin=document.getElementById('vinInput').value.trim().toUpperCase();
const c=document.getElementById('vinResult');
if(vin.length!==17){c.innerHTML='<div class="card"><p style="color:red">VIN must be 17 characters</p></div>';return}
c.innerHTML='<div class="loading">Decoding...</div>';
try{
const res=await fetch('/api/vin/'+vin);
const data=await res.json();
if(data.detail){c.innerHTML='<div class="card"><p style="color:red">'+data.detail+'</p></div>';return}
c.innerHTML='<div class="card"><h3>🔍 Vehicle Info</h3><p><strong>VIN:</strong> '+data.vin+'</p><p><strong>Manufacturer:</strong> '+data.manufacturer+'</p><p><strong>Country:</strong> '+data.country+'</p><p><strong>Year:</strong> '+data.year+'</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

let paintB64='';
function previewPaint(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=function(ev){paintB64=ev.target.result;document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+paintB64+'">';};r.readAsDataURL(f);}
async function matchPaint(){
const btn=document.getElementById('paintBtn');
const c=document.getElementById('paintResult');
if(!paintB64){c.innerHTML='<div class="card"><p style="color:red">Select an image</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';c.innerHTML='<div class="loading">Analyzing...</div>';
try{
const res=await fetch('/api/paint/match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:paintB64,vehicle_info:document.getElementById('paintVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else{const col=data.detected_colour;let h='<div class="card"><div class="swatch" style="background:'+col.hex_code+'"></div><h3>'+esc(col.name)+'</h3><p><strong>'+esc(col.finish)+'</strong> • '+esc(col.colour_family)+'</p><p style="font-family:monospace">'+col.hex_code+'</p><p>Confidence: <strong>'+data.confidence+'</strong></p></div>';if(data.brand_codes){h+='<div class="card"><h3>Brand Codes</h3>';data.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code)+' — '+esc(b.name)+'</div>'});h+='</div>'}if(data.mixing_formula){const m=data.mixing_formula;h+='<div class="card"><h3>Mixing Formula</h3><p><strong>Base:</strong> '+esc(m.base_colour)+'</p>';if(m.toners)m.toners.forEach(t=>{h+='<div class="list-item">• '+esc(t.name)+': '+esc(t.parts)+' parts</div>'});h+='<p><strong>Reducer:</strong> '+esc(m.reducer)+'</p></div>'}c.innerHTML=h;}
}catch(e){c.innerHTML='<div class="card"><p style="color:red">Error: '+e.message+'</p></div>'}
btn.disabled=false;btn.textContent='🎨 Match Paint Colour';
}

let diagB64='';
function previewDiag(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=function(ev){diagB64=ev.target.result;document.getElementById('photoPreview').innerHTML='<img class="img-preview" src="'+diagB64+'">';};r.readAsDataURL(f);}
async function diagnosePhoto(){
const btn=document.getElementById('photoBtn');
const c=document.getElementById('photoResult');
if(!diagB64){c.innerHTML='<div class="card"><p style="color:red">Select an image</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';c.innerHTML='<div class="loading">Analyzing...</div>';
try{
const res=await fetch('/api/diagnose/photo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:diagB64,vehicle_info:document.getElementById('photoVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else{let h='<div class="card"><h3>🔍 '+esc(data.problem||'Detected')+'</h3><p><strong>Confidence:</strong> '+data.confidence+'</p>';if(data.description)h+='<p style="margin-top:8px">'+esc(data.description)+'</p>';h+='</div>';if(data.possible_causes){h+='<div class="card"><h3>Possible Causes</h3>';data.possible_causes.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}if(data.diagnostic_steps){h+='<div class="card"><h3>Diagnostic Steps</h3>';data.diagnostic_steps.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}if(data.repair_suggestions){h+='<div class="card"><h3>Repair Suggestions</h3>';data.repair_suggestions.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}if(data.tools_needed){h+='<div class="card"><h3>Tools Needed</h3>';data.tools_needed.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}if(data.safety_warnings){h+='<div class="card" style="background:#FFEBEE"><h3 style="color:#C62828">⚠ Safety</h3>';data.safety_warnings.forEach(w=>{h+='<div class="list-item">⚠ '+esc(w)+'</div>'});h+='</div>'}c.innerHTML=h;}
}catch(e){c.innerHTML='<div class="card"><p style="color:red">Error: '+e.message+'</p></div>'}
btn.disabled=false;btn.textContent='📸 Analyze Photo';
}

// DASHBOARD
async function loadDashboard(){
try{
const res=await fetch('/api/stats');
const d=await res.json();
document.getElementById('dashStats').innerHTML='<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Total Jobs</div></div><div class="stat-card orange"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open Jobs</div></div><div class="stat-card green"><div class="num">'+d.jobs_completed+'</div><div class="lbl">Completed</div></div><div class="stat-card"><div class="num">'+d.customers+'</div><div class="lbl">Customers</div></div><div class="stat-card"><div class="num">'+d.appointments_today+'</div><div class="lbl">Appts Today</div></div><div class="stat-card green"><div class="num">R'+d.revenue+'</div><div class="lbl">Revenue</div></div></div>';
}catch(e){document.getElementById('dashStats').innerHTML='<div class="card"><p>Error loading stats</p></div>'}
// Appointments today
try{
const res=await fetch('/api/appointments');
const d=await res.json();
const today=new Date().toISOString().slice(0,10);
const todays=d.appointments.filter(a=>a.date===today);
if(!todays.length){document.getElementById('dashAppts').innerHTML='<p style="color:#666">No appointments today</p>';}
else{document.getElementById('dashAppts').innerHTML=todays.map(a=>'<div class="list-item">'+esc(a.time)+' - '+esc(a.customer)+' ('+esc(a.service)+')</div>').join('');}
}catch(e){}
// Recent jobs
try{
const res=await fetch('/api/jobs');
const d=await res.json();
const recent=d.jobs.slice(-3).reverse();
if(!recent.length){document.getElementById('dashJobs').innerHTML='<p style="color:#666">No jobs yet</p>';}
else{document.getElementById('dashJobs').innerHTML=recent.map(j=>'<div class="list-item"><strong>#'+j.id+'</strong> '+esc(j.customer)+' - '+esc(j.vehicle)+' <span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+esc(j.status)+'</span></div>').join('');}
}catch(e){}
}

// JOBS
function showJobForm(){document.getElementById('jobForm').style.display='block';}
function hideJobForm(){document.getElementById('jobForm').style.display='none';}
async function createJob(){
const customer=document.getElementById('jobCustomer').value.trim();
const vehicle=document.getElementById('jobVehicle').value.trim();
const complaint=document.getElementById('jobComplaint').value.trim();
const reg=document.getElementById('jobVehicleReg').value.trim();
if(!customer||!vehicle||!complaint){alert('Fill customer, vehicle, and complaint');return}
try{
await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer,vehicle,complaint,registration:reg})});
document.getElementById('jobCustomer').value='';document.getElementById('jobVehicle').value='';
document.getElementById('jobComplaint').value='';document.getElementById('jobVehicleReg').value='';
hideJobForm();loadJobs();
}catch(e){alert('Error: '+e.message)}
}
async function loadJobs(){
const c=document.getElementById('jobList');c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/jobs');
const data=await res.json();
if(!data.jobs.length){c.innerHTML='<div class="card"><p>No jobs yet. Tap "+ New Job Card".</p></div>';return}
c.innerHTML=data.jobs.reverse().map(j=>{
const statusClass=j.status.toLowerCase().replace(' ','');
return '<div class="card"><h3>Job #'+j.id+' <span class="badge '+statusClass+'">'+esc(j.status)+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p><p style="color:#666">'+esc(j.complaint)+'</p><p style="font-size:11px;color:#999">'+esc(j.created)+'</p><div style="margin-top:8px"><button class="btn-sm" onclick="updateJob(\''+j.id+'\',\'In Progress\')">In Progress</button><button class="btn-sm green" onclick="updateJob(\''+j.id+'\',\'Completed\')">Done</button></div></div>';
}).join('');
}catch(e){c.innerHTML='<div class="card"><p>Error loading jobs</p></div>'}
}
async function updateJob(id,status){
try{await fetch('/api/jobs/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});loadJobs();}catch(e){alert(e.message)}
}

// CUSTOMERS
function showCustomerForm(){document.getElementById('customerForm').style.display='block';}
function hideCustomerForm(){document.getElementById('customerForm').style.display='none';}
async function createCustomer(){
const name=document.getElementById('custName').value.trim();
const phone=document.getElementById('custPhone').value.trim();
if(!name||!phone){alert('Name and phone required');return}
try{
await fetch('/api/customers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,email:document.getElementById('custEmail').value,address:document.getElementById('custAddress').value})});
['custName','custPhone','custEmail','custAddress'].forEach(id=>document.getElementById(id).value='');
hideCustomerForm();loadCustomers();
}catch(e){alert('Error: '+e.message)}
}
async function loadCustomers(){
const c=document.getElementById('customerList');c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/customers');
const data=await res.json();
if(!data.customers.length){c.innerHTML='<div class="card"><p>No customers yet.</p></div>';return}
c.innerHTML=data.customers.reverse().map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+(x.address?'<p>📍 '+esc(x.address)+'</p>':'')+'</div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

// APPOINTMENTS
function showApptForm(){document.getElementById('apptForm').style.display='block';}
function hideApptForm(){document.getElementById('apptForm').style.display='none';}
async function createAppt(){
const customer=document.getElementById('apptCustomer').value.trim();
const phone=document.getElementById('apptPhone').value.trim();
const vehicle=document.getElementById('apptVehicle').value.trim();
const service=document.getElementById('apptService').value.trim();
const date=document.getElementById('apptDate').value;
const time=document.getElementById('apptTime').value;
if(!customer||!date||!time){alert('Customer, date, and time required');return}
try{
await fetch('/api/appointments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer,phone,vehicle,service,date,time})});
['apptCustomer','apptPhone','apptVehicle','apptService','apptDate','apptTime'].forEach(id=>document.getElementById(id).value='');
hideApptForm();loadAppts();
}catch(e){alert('Error: '+e.message)}
}
async function loadAppts(){
const c=document.getElementById('apptList');c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/appointments');
const data=await res.json();
if(!data.appointments.length){c.innerHTML='<div class="card"><p>No appointments yet.</p></div>';return}
const sorted=data.appointments.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));
c.innerHTML=sorted.map(a=>'<div class="card"><h3>📅 '+esc(a.date)+' at '+esc(a.time)+'</h3><p><strong>'+esc(a.customer)+'</strong></p>'+(a.phone?'<p>📞 '+esc(a.phone)+'</p>':'')+(a.vehicle?'<p>🚗 '+esc(a.vehicle)+'</p>':'')+(a.service?'<p style="color:#666">'+esc(a.service)+'</p>':'')+'<button class="btn-sm red" style="margin-top:8px" onclick="deleteAppt(\''+a.id+'\')">Delete</button></div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function deleteAppt(id){
if(!confirm('Delete this appointment?'))return;
try{await fetch('/api/appointments/'+id,{method:'DELETE'});loadAppts();}catch(e){alert(e.message)}
}

// INVOICES
function showInvoiceForm(){document.getElementById('invoiceForm').style.display='block';}
function hideInvoiceForm(){document.getElementById('invoiceForm').style.display='none';}
async function createInvoice(){
const customer=document.getElementById('invCustomer').value.trim();
const vehicle=document.getElementById('invVehicle').value.trim();
const desc=document.getElementById('invDesc').value.trim();
const labour=parseFloat(document.getElementById('invLabour').value)||0;
const parts=parseFloat(document.getElementById('invParts').value)||0;
if(!customer||!desc){alert('Customer and description required');return}
try{
await fetch('/api/invoices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer,vehicle,description:desc,labour,parts})});
['invCustomer','invVehicle','invDesc','invLabour','invParts'].forEach(id=>document.getElementById(id).value='');
hideInvoiceForm();loadInvoices();
}catch(e){alert('Error: '+e.message)}
}
async function loadInvoices(){
const c=document.getElementById('invoiceList');c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/invoices');
const data=await res.json();
if(!data.invoices.length){c.innerHTML='<div class="card"><p>No invoices yet.</p></div>';return}
c.innerHTML=data.invoices.reverse().map(i=>'<div class="card"><h3>Invoice #'+i.id+'</h3><p><strong>'+esc(i.customer)+'</strong></p>'+(i.vehicle?'<p>🚗 '+esc(i.vehicle)+'</p>':'')+'<p style="color:#666">'+esc(i.description)+'</p><div class="list-item">Labour: R'+i.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+i.parts.toFixed(2)+'</div><div class="list-item"><strong>Subtotal: R'+i.subtotal.toFixed(2)+'</strong></div><div class="list-item"><strong>VAT (15%): R'+i.vat.toFixed(2)+'</strong></div><div class="list-item" style="font-size:16px"><strong>TOTAL: R'+i.total.toFixed(2)+'</strong></div><p style="font-size:11px;color:#999">'+esc(i.created)+'</p><button class="btn-sm" style="margin-top:8px" onclick="shareInvoice(\''+i.id+'\')">Share</button></div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}
async function shareInvoice(id){
try{
const res=await fetch('/api/invoices/'+id);
const i=await res.json();
const txt='Invoice #'+i.id+'\n\nCustomer: '+i.customer+'\nVehicle: '+i.vehicle+'\nService: '+i.description+'\n\nLabour: R'+i.labour.toFixed(2)+'\nParts: R'+i.parts.toFixed(2)+'\nSubtotal: R'+i.subtotal.toFixed(2)+'\nVAT: R'+i.vat.toFixed(2)+'\nTOTAL: R'+i.total.toFixed(2)+'\n\nThank you!';
if(navigator.share){navigator.share({title:'Invoice #'+i.id,text:txt});}
else{navigator.clipboard.writeText(txt);alert('Copied to clipboard');}
}catch(e){alert(e.message)}
}

// PARTS
let partsData=[];
async function loadParts(){
try{
const res=await fetch('/api/parts');
const data=await res.json();
partsData=data.parts;
document.getElementById('partsList').dataset.loaded='true';
renderParts();
}catch(e){document.getElementById('partsList').innerHTML='<div class="card"><p>Error</p></div>'}
}
function filterParts(){renderParts();}
function renderParts(){
const q=(document.getElementById('partsSearch').value||'').toLowerCase();
const filtered=partsData.filter(x=>!q||x.name.toLowerCase().includes(q)||x.number.toLowerCase().includes(q)||x.brand.toLowerCase().includes(q));
if(!filtered.length){document.getElementById('partsList').innerHTML='<div class="card"><p>No matches</p></div>';return}
document.getElementById('partsList').innerHTML=filtered.map(p=>'<div class="card"><h3>'+esc(p.name)+'</h3><p style="font-family:monospace;font-size:12px">'+esc(p.number)+'</p><p>Brand: <strong>'+esc(p.brand)+'</strong> | '+esc(p.category)+'</p><p style="font-size:16px;color:#E65100"><strong>R'+p.price+'</strong></p></div>').join('');
}

// BOLT CALCULATOR
async function calcTorque(){
const size=document.getElementById('boltSize').value;
const grade=document.getElementById('boltGrade').value;
const condition=document.getElementById('boltCondition').value;
try{
const res=await fetch('/api/bolt-calc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({size,grade,condition})});
const d=await res.json();
document.getElementById('boltResult').innerHTML='<div class="card" style="background:#E65100;color:white"><h3 style="color:white">Recommended Torque</h3><p style="font-size:32px;font-weight:bold;color:white;margin:8px 0">'+d.nm.toFixed(1)+' Nm</p><p style="color:white">'+d.ftlb.toFixed(1)+' ft·lb</p></div><div class="card"><p><strong>Bolt:</strong> '+esc(d.size)+' grade '+esc(d.grade)+'</p><p><strong>Condition:</strong> '+esc(d.condition)+'</p><p><strong>Clamp force:</strong> '+d.clamp_kn.toFixed(1)+' kN</p><p style="font-size:11px;color:#666;margin-top:8px">⚠ Always verify against OEM specs</p></div>';
}catch(e){document.getElementById('boltResult').innerHTML='<div class="card"><p>Error</p></div>'}
}

// TORQUE
let torqueData=[];let seqData=[];
async function loadTorque(){
if(torqueData.length){renderTorque();return}
try{
const res=await fetch('/api/torque');
const data=await res.json();
torqueData=data.bolts;seqData=data.sequences;renderTorque();
}catch(e){document.getElementById('torqueTable').innerHTML='<div class="card"><p>Error</p></div>'}
}
function renderTorque(){
const q=(document.getElementById('torqueSearch').value||'').toLowerCase();
const filtered=torqueData.filter(x=>!q||x.size.toLowerCase().includes(q)||x.grade.toLowerCase().includes(q)||x.use.toLowerCase().includes(q));
let h='<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>';
filtered.forEach(x=>{h+='<tr><td><strong>'+esc(x.size)+'</strong></td><td>'+esc(x.grade)+'</td><td>'+x.nm+'</td><td>'+x.ftlb+'</td><td>'+esc(x.use)+'</td></tr>'});
h+='</table>';
document.getElementById('torqueTable').innerHTML=h;
document.getElementById('torqueSeq').innerHTML=seqData.map(s=>'<div class="card"><h3>'+esc(s.component)+'</h3><p style="font-size:11px;color:#666">Pattern: '+esc(s.pattern)+'</p>'+s.steps.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'<p style="font-size:12px;font-style:italic;margin-top:6px">'+esc(s.note)+'</p></div>').join('');
}
function filterTorque(){renderTorque();}
</script>
</body>
</html>"""

# ═══════════════════════════════════
# ROUTES
# ═══════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE

@app.get("/health")
def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

# STATS
@app.get("/api/stats")
def get_stats():
    jobs_total = len(JOBS)
    jobs_open = sum(1 for j in JOBS.values() if j["status"] != "Completed")
    jobs_completed = sum(1 for j in JOBS.values() if j["status"] == "Completed")
    today = datetime.now().strftime("%Y-%m-%d")
    appts_today = sum(1 for a in APPOINTMENTS.values() if a.get("date") == today)
    revenue = sum(i["total"] for i in INVOICES.values())
    return {
        "jobs_total": jobs_total, "jobs_open": jobs_open,
        "jobs_completed": jobs_completed, "customers": len(CUSTOMERS),
        "appointments_today": appts_today, "revenue": round(revenue, 2),
    }

# FAULT CODES
@app.get("/api/fault-codes")
def list_codes(search: str = None):
    results = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        results = [c for c in results if q in c["code"].lower() or q in c["description"].lower()]
    return {"count": len(results), "codes": results}

# PROBLEMS
@app.get("/api/problems")
def list_problems():
    return {"problems": COMMON_PROBLEMS}

# VIN
@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17:
        raise HTTPException(400, "VIN must be 17 characters")
    wmi = v[:3]
    mfr, country = WMI_DB.get(wmi, ("Unknown", "Unknown"))
    return {"vin": v, "manufacturer": mfr, "country": country, "year": YEAR_CODES.get(v[9], "Unknown")}

# CHAT
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("message", "")
    if not msg:
        raise HTTPException(400, "Message required")
    if not OPENAI_KEY:
        return {"reply": "AI not configured"}
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are RamsTech AI, an expert mechanic. Help with diagnostics, repairs, fault codes, tools. Be practical."},
                {"role": "user", "content": msg}
            ],
            max_tokens=800, temperature=0.3,
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

# PAINT
@app.post("/api/paint/match")
async def match_paint(request: Request):
    data = await request.json()
    img = data.get("image_base64", "")
    vehicle = data.get("vehicle_info", "")
    if not img:
        raise HTTPException(400, "Image required")
    if not OPENAI_KEY:
        return {"success": False, "error": "AI not configured"}
    if img.startswith("data:"):
        img = img.split(",", 1)[1]
    if len(img) > 7000000:
        return {"success": False, "error": "Image too large"}
    prompt = f"""You are an expert automotive paint technician. Vehicle: {vehicle or 'Not specified'}
Analyze paint colour. Respond ONLY with valid JSON:
{{"detected_colour":{{"name":"Name","hex_code":"#RRGGBB","rgb":[R,G,B],"finish":"Solid|Metallic|Pearl|Matte|Satin","colour_family":"White|Black|Red|Blue|Silver|Grey|Green|Yellow|Orange|Brown"}},"confidence":"High|Medium|Low","condition_notes":"Notes","brand_codes":[{{"brand":"DuPont","code":"Code","name":"Formula"}},{{"brand":"PPG","code":"Code","name":"Formula"}},{{"brand":"Sikkens","code":"Code","name":"Formula"}},{{"brand":"Glasurit","code":"Code","name":"Formula"}}],"mixing_formula":{{"base_colour":"Desc","toners":[{{"name":"Toner","parts":"X"}}],"reducer":"Ratio","total_parts":100}},"coverage_estimate":{{"base_coat_litres":"X.X","clear_coat_litres":"X.X"}},"application_notes":["Step 1"],"safety_warnings":["Warning 1"]}}"""
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000, temperature=0.2, response_format={"type":"json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        parsed["success"] = True
        return parsed
    except Exception as e:
        return {"success": False, "error": str(e)}

# PHOTO DIAG
@app.post("/api/diagnose/photo")
async def diagnose_photo(request: Request):
    data = await request.json()
    img = data.get("image_base64", "")
    vehicle = data.get("vehicle_info", "")
    if not img:
        raise HTTPException(400, "Image required")
    if not OPENAI_KEY:
        return {"success": False, "error": "AI not configured"}
    if img.startswith("data:"):
        img = img.split(",", 1)[1]
    if len(img) > 7000000:
        return {"success": False, "error": "Image too large"}
    prompt = f"""You are an expert mechanic analyzing a vehicle photo. Vehicle: {vehicle or 'Not specified'}
Identify visible problems (wear, damage, leaks, corrosion).
Respond ONLY with valid JSON:
{{"problem":"Short description","description":"What you see","confidence":"High|Medium|Low","possible_causes":["Cause 1"],"diagnostic_steps":["Step 1"],"repair_suggestions":["Repair 1"],"tools_needed":["Tool 1"],"safety_warnings":["Warning 1"]}}"""
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000, temperature=0.2, response_format={"type":"json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        parsed["success"] = True
        return parsed
    except Exception as e:
        return {"success": False, "error": str(e)}

# JOBS
@app.get("/api/jobs")
def list_jobs():
    return {"jobs": list(JOBS.values())}

@app.post("/api/jobs")
async def create_job(request: Request):
    data = await request.json()
    jid = str(len(JOBS) + 1).zfill(4)
    JOBS[jid] = {
        "id": jid, "customer": data.get("customer", ""),
        "vehicle": data.get("vehicle", ""), "registration": data.get("registration", ""),
        "complaint": data.get("complaint", ""), "status": "New",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return {"success": True, "job": JOBS[jid]}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, request: Request):
    data = await request.json()
    if jid not in JOBS:
        raise HTTPException(404, "Job not found")
    JOBS[jid]["status"] = data.get("status", JOBS[jid]["status"])
    return {"success": True, "job": JOBS[jid]}

# CUSTOMERS
@app.get("/api/customers")
def list_customers():
    return {"customers": list(CUSTOMERS.values())}

@app.post("/api/customers")
async def create_customer(request: Request):
    data = await request.json()
    cid = str(uuid.uuid4())[:8]
    CUSTOMERS[cid] = {
        "id": cid, "name": data.get("name", ""),
        "phone": data.get("phone", ""), "email": data.get("email", ""),
        "address": data.get("address", ""),
        "created": datetime.now().strftime("%Y-%m-%d"),
    }
    return {"success": True, "customer": CUSTOMERS[cid]}

# APPOINTMENTS
@app.get("/api/appointments")
def list_appts():
    return {"appointments": list(APPOINTMENTS.values())}

@app.post("/api/appointments")
async def create_appt(request: Request):
    data = await request.json()
    aid = str(uuid.uuid4())[:8]
    APPOINTMENTS[aid] = {
        "id": aid, "customer": data.get("customer", ""),
        "phone": data.get("phone", ""), "vehicle": data.get("vehicle", ""),
        "service": data.get("service", ""), "date": data.get("date", ""),
        "time": data.get("time", ""),
    }
    return {"success": True, "appointment": APPOINTMENTS[aid]}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str):
    if aid not in APPOINTMENTS:
        raise HTTPException(404, "Not found")
    del APPOINTMENTS[aid]
    return {"success": True}

# INVOICES
@app.get("/api/invoices")
def list_invoices():
    return {"invoices": list(INVOICES.values())}

@app.get("/api/invoices/{iid}")
def get_invoice(iid: str):
    if iid not in INVOICES:
        raise HTTPException(404, "Not found")
    return INVOICES[iid]

@app.post("/api/invoices")
async def create_invoice(request: Request):
    data = await request.json()
    labour = float(data.get("labour", 0))
    parts = float(data.get("parts", 0))
    subtotal = labour + parts
    vat = subtotal * 0.15
    total = subtotal + vat
    iid = str(len(INVOICES) + 1).zfill(4)
    INVOICES[iid] = {
        "id": iid, "customer": data.get("customer", ""),
        "vehicle": data.get("vehicle", ""), "description": data.get("description", ""),
        "labour": labour, "parts": parts, "subtotal": subtotal,
        "vat": vat, "total": total,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return {"success": True, "invoice": INVOICES[iid]}

# PARTS
@app.get("/api/parts")
def list_parts():
    return {"parts": PARTS_CATALOG}

# BOLT CALCULATOR
@app.post("/api/bolt-calc")
async def bolt_calc(request: Request):
    data = await request.json()
    size = data.get("size", "M8")
    grade = data.get("grade", "8.8")
    condition = data.get("condition", "dry")

    tensile_map = {"8.8": 800, "10.9": 1040, "12.9": 1220}
    area_map = {"M6": 20.1, "M8": 36.6, "M10": 58.0, "M12": 84.3,
                "M14": 115.0, "M16": 157.0, "M18": 192.0, "M20": 245.0}
    k_map = {"dry": 0.20, "oiled": 0.17, "moly": 0.14}

    tensile = tensile_map.get(grade, 800)
    area = area_map.get(size, 36.6)
    k = k_map.get(condition, 0.20)

    clamp_force = 0.75 * tensile * area
    d_m = float(size.replace("M", "")) / 1000.0
    torque_nm = k * d_m * clamp_force

    return {
        "size": size, "grade": grade, "condition": condition,
        "nm": torque_nm, "ftlb": torque_nm * 0.73756,
        "clamp_kn": clamp_force / 1000,
    }

# TORQUE
@app.get("/api/torque")
def get_torque():
    return {"bolts": TORQUE_SPECS, "sequences": TORQUE_SEQUENCES}
