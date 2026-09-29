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
# DATA STORES (in-memory — resets on restart)
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

# ═══════════════════════════════════
# TORQUE SPECS
# ═══════════════════════════════════
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
    {"size": "1/4\"", "grade": "Grade 5", "nm": 12, "ftlb": 8.8, "use": "General automotive"},
    {"size": "3/8\"", "grade": "Grade 5", "nm": 45, "ftlb": 33, "use": "Suspension"},
    {"size": "1/2\"", "grade": "Grade 5", "nm": 105, "ftlb": 77, "use": "Heavy suspension"},
    {"size": "3/8\"", "grade": "Grade 8", "nm": 60, "ftlb": 44, "use": "High-stress"},
    {"size": "1/2\"", "grade": "Grade 8", "nm": 150, "ftlb": 110, "use": "Tow bars / heavy"},
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
     "note": "10-stud wheels. Check hub spec."},
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

JOBS = {}
CUSTOMERS = {}

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
.tab{padding:14px 14px;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap;font-size:13px}
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
.btn-sm{padding:8px 12px;background:#E65100;color:white;border:none;border-radius:6px;font-size:13px;font-weight:bold;cursor:pointer;margin-right:6px}
.btn-sm.gray{background:#666}
.card{background:white;padding:16px;border-radius:12px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.card h3{color:#E65100;margin-bottom:8px;font-size:16px}
.card p{margin:4px 0;font-size:13px;line-height:1.4}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:white;margin-left:6px}
.badge.high{background:#F44336}.badge.medium{background:#FF9800}.badge.low{background:#4CAF50}
.badge.status{background:#2196F3}
.list-item{padding:6px 0;border-bottom:1px solid #eee;font-size:13px}
.list-item:last-child{border-bottom:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.grid-item{background:white;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08);cursor:pointer}
.grid-item:active{background:#f0f0f0}
.grid-item .icon{font-size:32px;margin-bottom:6px}
.grid-item .label{font-size:12px;font-weight:bold}
.img-preview{width:100%;border-radius:12px;margin-bottom:12px}
.swatch{height:80px;border-radius:12px;border:1px solid #ccc;margin-bottom:12px}
.status-online{background:#E8F5E9;color:#2E7D32;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.status-offline{background:#FFEBEE;color:#C62828;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.loading{text-align:center;padding:20px;color:#666}
.torque-table{width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden;font-size:12px}
.torque-table th{background:#E65100;color:white;padding:8px 6px;text-align:left}
.torque-table td{padding:8px 6px;border-bottom:1px solid #eee}
.torque-table tr:last-child td{border-bottom:none}
</style>
</head>
<body>

<div class="header">
<h1>🔧 RAMSTECH</h1>
<p>AI Workshop Assistant</p>
</div>

<div class="tabs">
<div class="tab active" onclick="showTab('home',this)">🏠 Home</div>
<div class="tab" onclick="showTab('chat',this)">🤖 AI</div>
<div class="tab" onclick="showTab('codes',this)">📟 Codes</div>
<div class="tab" onclick="showTab('vin',this)">🔍 VIN</div>
<div class="tab" onclick="showTab('paint',this)">🎨 Paint</div>
<div class="tab" onclick="showTab('photo',this)">📸 Diag</div>
<div class="tab" onclick="showTab('jobs',this)">📋 Jobs</div>
<div class="tab" onclick="showTab('customers',this)">👥 Clients</div>
<div class="tab" onclick="showTab('torque',this)">⚙️ Torque</div>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking backend...</div></div>
<div class="grid">
<div class="grid-item" onclick="clickTab(1)"><div class="icon">🤖</div><div class="label">AI Chat</div></div>
<div class="grid-item" onclick="clickTab(2)"><div class="icon">📟</div><div class="label">Fault Codes</div></div>
<div class="grid-item" onclick="clickTab(3)"><div class="icon">🔍</div><div class="label">VIN Decoder</div></div>
<div class="grid-item" onclick="clickTab(4)"><div class="icon">🎨</div><div class="label">Paint Match</div></div>
<div class="grid-item" onclick="clickTab(5)"><div class="icon">📸</div><div class="label">Photo Diag</div></div>
<div class="grid-item" onclick="clickTab(6)"><div class="icon">📋</div><div class="label">Job Cards</div></div>
<div class="grid-item" onclick="clickTab(7)"><div class="icon">👥</div><div class="label">Customers</div></div>
<div class="grid-item" onclick="clickTab(8)"><div class="icon">⚙️</div><div class="label">Torque Specs</div></div>
</div>
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
<div class="card"><p style="font-size:13px">Take photo of mechanical issue (leak, wear, damage). AI diagnoses the problem.</p></div>
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
if(name==='jobs')loadJobs();
if(name==='customers')loadCustomers();
if(name==='torque')loadTorque();
}
function clickTab(i){showTab(document.querySelectorAll('.panel')[i].id,document.querySelectorAll('.tab')[i]);}

async function checkStatus(){
try{await fetch('/health');document.getElementById('status').innerHTML='<span class="status-online">✓ Backend Online</span>';}
catch(e){document.getElementById('status').innerHTML='<span class="status-offline">✗ Backend Offline</span>';}
}
checkStatus();
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}

// CHAT
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

// CODES
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

// VIN
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

// PAINT
let paintB64='';
function previewPaint(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=function(ev){paintB64=ev.target.result;document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+paintB64+'">';};r.readAsDataURL(f);}
async function matchPaint(){
const btn=document.getElementById('paintBtn');
const c=document.getElementById('paintResult');
if(!paintB64){c.innerHTML='<div class="card"><p style="color:red">Select an image</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';
c.innerHTML='<div class="loading">Analyzing...</div>';
try{
const res=await fetch('/api/paint/match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:paintB64,vehicle_info:document.getElementById('paintVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else{const col=data.detected_colour;let h='<div class="card"><div class="swatch" style="background:'+col.hex_code+'"></div><h3>'+esc(col.name)+'</h3><p><strong>'+esc(col.finish)+'</strong> • '+esc(col.colour_family)+'</p><p style="font-family:monospace">'+col.hex_code+'</p><p>Confidence: <strong>'+data.confidence+'</strong></p></div>';if(data.brand_codes){h+='<div class="card"><h3>Brand Codes</h3>';data.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code)+' — '+esc(b.name)+'</div>'});h+='</div>'}if(data.mixing_formula){const m=data.mixing_formula;h+='<div class="card"><h3>Mixing Formula</h3><p><strong>Base:</strong> '+esc(m.base_colour)+'</p>';if(m.toners)m.toners.forEach(t=>{h+='<div class="list-item">• '+esc(t.name)+': '+esc(t.parts)+' parts</div>'});h+='<p><strong>Reducer:</strong> '+esc(m.reducer)+'</p></div>'}c.innerHTML=h;}
}catch(e){c.innerHTML='<div class="card"><p style="color:red">Error: '+e.message+'</p></div>'}
btn.disabled=false;btn.textContent='🎨 Match Paint Colour';
}

// PHOTO DIAGNOSIS
let diagB64='';
function previewDiag(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=function(ev){diagB64=ev.target.result;document.getElementById('photoPreview').innerHTML='<img class="img-preview" src="'+diagB64+'">';};r.readAsDataURL(f);}
async function diagnosePhoto(){
const btn=document.getElementById('photoBtn');
const c=document.getElementById('photoResult');
if(!diagB64){c.innerHTML='<div class="card"><p style="color:red">Select an image</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';
c.innerHTML='<div class="loading">Analyzing...</div>';
try{
const res=await fetch('/api/diagnose/photo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:diagB64,vehicle_info:document.getElementById('photoVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else{
let h='<div class="card"><h3>🔍 '+esc(data.problem||'Detected')+'</h3><p><strong>Confidence:</strong> '+data.confidence+'</p>';
if(data.description)h+='<p style="margin-top:8px">'+esc(data.description)+'</p>';
h+='</div>';
if(data.possible_causes){h+='<div class="card"><h3>Possible Causes</h3>';data.possible_causes.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}
if(data.diagnostic_steps){h+='<div class="card"><h3>Diagnostic Steps</h3>';data.diagnostic_steps.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}
if(data.repair_suggestions){h+='<div class="card"><h3>Repair Suggestions</h3>';data.repair_suggestions.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}
if(data.tools_needed){h+='<div class="card"><h3>Tools Needed</h3>';data.tools_needed.forEach(x=>{h+='<div class="list-item">• '+esc(x)+'</div>'});h+='</div>'}
if(data.safety_warnings){h+='<div class="card" style="background:#FFEBEE"><h3 style="color:#C62828">⚠ Safety</h3>';data.safety_warnings.forEach(w=>{h+='<div class="list-item">⚠ '+esc(w)+'</div>'});h+='</div>'}
c.innerHTML=h;
}
}catch(e){c.innerHTML='<div class="card"><p style="color:red">Error: '+e.message+'</p></div>'}
btn.disabled=false;btn.textContent='📸 Analyze Photo';
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
document.getElementById('jobCustomer').value='';
document.getElementById('jobVehicle').value='';
document.getElementById('jobComplaint').value='';
document.getElementById('jobVehicleReg').value='';
hideJobForm();loadJobs();
}catch(e){alert('Error: '+e.message)}
}
async function loadJobs(){
const c=document.getElementById('jobList');
c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/jobs');
const data=await res.json();
if(!data.jobs.length){c.innerHTML='<div class="card"><p>No jobs yet. Tap "+ New Job Card".</p></div>';return}
c.innerHTML=data.jobs.reverse().map(j=>'<div class="card"><h3>Job #'+j.id+' <span class="badge status">'+esc(j.status)+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p><p style="color:#666">'+esc(j.complaint)+'</p><p style="font-size:11px;color:#999">'+esc(j.created)+'</p><div style="margin-top:8px"><button class="btn-sm" onclick="updateJob(\''+j.id+'\',\'In Progress\')">In Progress</button><button class="btn-sm" onclick="updateJob(\''+j.id+'\',\'Completed\')">Completed</button></div></div>').join('');
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
document.getElementById('custName').value='';
document.getElementById('custPhone').value='';
document.getElementById('custEmail').value='';
document.getElementById('custAddress').value='';
hideCustomerForm();loadCustomers();
}catch(e){alert('Error: '+e.message)}
}
async function loadCustomers(){
const c=document.getElementById('customerList');
c.innerHTML='<div class="loading">Loading...</div>';
try{
const res=await fetch('/api/customers');
const data=await res.json();
if(!data.customers.length){c.innerHTML='<div class="card"><p>No customers yet.</p></div>';return}
c.innerHTML=data.customers.reverse().map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+(x.address?'<p>📍 '+esc(x.address)+'</p>':'')+'</div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}
}

// TORQUE
let torqueData=[];
let seqData=[];
async function loadTorque(){
if(torqueData.length){renderTorque();return}
try{
const res=await fetch('/api/torque');
const data=await res.json();
torqueData=data.bolts;
seqData=data.sequences;
renderTorque();
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

# FAULT CODES
@app.get("/api/fault-codes")
def list_codes(search: str = None):
    results = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        results = [c for c in results if q in c["code"].lower() or q in c["description"].lower()]
    return {"count": len(results), "codes": results}

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
            max_tokens=800,
            temperature=0.3,
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

# PHOTO DIAGNOSIS
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
Identify visible problems (wear, damage, leaks, corrosion, broken parts).
Respond ONLY with valid JSON:
{{"problem":"Short description of main issue","description":"Detailed what you see","confidence":"High|Medium|Low","possible_causes":["Cause 1","Cause 2"],"diagnostic_steps":["Step 1","Step 2"],"repair_suggestions":["Repair 1","Repair 2"],"tools_needed":["Tool 1","Tool 2"],"safety_warnings":["Warning 1"]}}"""
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
        "id": jid,
        "customer": data.get("customer", ""),
        "vehicle": data.get("vehicle", ""),
        "registration": data.get("registration", ""),
        "complaint": data.get("complaint", ""),
        "status": "New",
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
        "id": cid,
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "address": data.get("address", ""),
        "created": datetime.now().strftime("%Y-%m-%d"),
    }
    return {"success": True, "customer": CUSTOMERS[cid]}

# TORQUE
@app.get("/api/torque")
def get_torque():
    return {"bolts": TORQUE_SPECS, "sequences": TORQUE_SEQUENCES}
