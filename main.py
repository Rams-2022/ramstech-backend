from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import openai
import os
import json

app = FastAPI(title="RamsTech")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ═══════════════════════════════════
# DATA
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
# HTML FRONTEND
# ═══════════════════════════════════
HTML_PAGE = """<!DOCTYPE html>
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
.tabs{display:flex;background:white;border-bottom:1px solid #ddd;overflow-x:auto;position:sticky;top:0;z-index:99}
.tab{padding:14px 16px;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap;font-size:13px}
.tab.active{color:#E65100;border-bottom-color:#E65100;font-weight:bold}
.panel{display:none;padding:16px;max-width:800px;margin:0 auto}
.panel.active{display:block}
.chat-box{background:white;border-radius:12px;padding:12px;height:400px;overflow-y:auto;margin-bottom:12px}
.msg{padding:10px 14px;margin:6px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.4}
.msg.user{background:#E65100;color:white;margin-left:auto}
.msg.ai{background:#f0f0f0}
.input-row{display:flex;gap:8px}
.input-row input{flex:1;padding:12px 16px;border:1px solid #ccc;border-radius:25px;font-size:14px}
.input-row button{padding:12px 20px;background:#E65100;color:white;border:none;border-radius:25px;font-weight:bold;cursor:pointer}
.form-input{width:100%;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;margin-bottom:12px}
.btn{width:100%;padding:14px;background:#E65100;color:white;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;margin-bottom:12px}
.btn:active{background:#BF360C}
.card{background:white;padding:16px;border-radius:12px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.card h3{color:#E65100;margin-bottom:8px;font-size:16px}
.card p{margin:4px 0;font-size:13px;line-height:1.4}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:white;margin-left:6px}
.badge.high{background:#F44336}.badge.medium{background:#FF9800}
.list-item{padding:6px 0;border-bottom:1px solid #eee;font-size:13px}
.list-item:last-child{border-bottom:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.grid-item{background:white;padding:20px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08);cursor:pointer}
.grid-item:active{background:#f0f0f0}
.grid-item .icon{font-size:36px;margin-bottom:8px}
.grid-item .label{font-size:13px;font-weight:bold}
.img-preview{width:100%;border-radius:12px;margin-bottom:12px}
.swatch{height:80px;border-radius:12px;border:1px solid #ccc;margin-bottom:12px}
.status-online{background:#E8F5E9;color:#2E7D32;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.status-offline{background:#FFEBEE;color:#C62828;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.loading{text-align:center;padding:20px;color:#666}
</style>
</head>
<body>

<div class="header">
<h1>🔧 RAMSTECH</h1>
<p>AI Workshop Assistant</p>
</div>

<div class="tabs">
<div class="tab active" onclick="showTab('home',this)">🏠 Home</div>
<div class="tab" onclick="showTab('chat',this)">🤖 AI Chat</div>
<div class="tab" onclick="showTab('codes',this)">📟 Codes</div>
<div class="tab" onclick="showTab('vin',this)">🔍 VIN</div>
<div class="tab" onclick="showTab('paint',this)">🎨 Paint</div>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking backend...</div></div>
<div class="grid">
<div class="grid-item" onclick="showTab('chat',document.querySelectorAll('.tab')[1])">
<div class="icon">🤖</div><div class="label">AI Assistant</div></div>
<div class="grid-item" onclick="showTab('codes',document.querySelectorAll('.tab')[2])">
<div class="icon">📟</div><div class="label">Fault Codes</div></div>
<div class="grid-item" onclick="showTab('vin',document.querySelectorAll('.tab')[3])">
<div class="icon">🔍</div><div class="label">VIN Decoder</div></div>
<div class="grid-item" onclick="showTab('paint',document.querySelectorAll('.tab')[4])">
<div class="icon">🎨</div><div class="label">Paint Match</div></div>
</div>
</div>

<div id="chat" class="panel">
<div class="chat-box" id="chatBox">
<div class="msg ai">Welcome to RamsTech! 🔧<br>Ask about repairs, diagnostics, fault codes, or tools.</div>
</div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()">
<button onclick="sendMsg()">Send</button>
</div>
</div>

<div id="codes" class="panel">
<input type="text" class="form-input" id="codeSearch" placeholder="Search code or description..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<div id="vin" class="panel">
<input type="text" class="form-input" id="vinInput" placeholder="Enter 17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<div id="paint" class="panel">
<div class="card"><p style="font-size:13px">Take a photo of a vehicle panel in good natural light. AI will identify the colour and provide paint codes and mixing formulas.</p></div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info (optional) - e.g. 2018 Toyota Hilux">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewImage(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
</div>

<script>
function showTab(name,el){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(name).classList.add('active');
if(el)el.classList.add('active');
if(name==='codes'&&!document.getElementById('codeResults').dataset.loaded)searchCodes();
}

async function checkStatus(){
const el=document.getElementById('status');
try{
await fetch('/health');
el.innerHTML='<span class="status-online">✓ Backend Online</span>';
}catch(e){
el.innerHTML='<span class="status-offline">✗ Backend Offline</span>';
}
}
checkStatus();

function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}

async function sendMsg(){
const input=document.getElementById('chatInput');
const msg=input.value.trim();
if(!msg)return;
const box=document.getElementById('chatBox');
box.innerHTML+='<div class="msg user">'+esc(msg)+'</div>';
input.value='';
box.scrollTop=box.scrollHeight;
box.innerHTML+='<div class="msg ai" id="typing">Thinking...</div>';
box.scrollTop=box.scrollHeight;
try{
const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
const data=await res.json();
document.getElementById('typing').outerHTML='<div class="msg ai">'+esc(data.reply)+'</div>';
}catch(e){
document.getElementById('typing').outerHTML='<div class="msg ai">Error: '+e.message+'</div>';
}
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
if(!data.codes.length){c.innerHTML='<div class="card"><p>No matches found</p></div>';return}
c.innerHTML=data.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:#666;font-size:12px">System: '+esc(x.system)+'</p><p style="margin-top:10px"><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p style="margin-top:10px"><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join('');
}catch(e){c.innerHTML='<div class="card"><p>Error: '+e.message+'</p></div>'}
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
}catch(e){c.innerHTML='<div class="card"><p>Error: '+e.message+'</p></div>'}
}

let imgB64='';
function previewImage(e){
const f=e.target.files[0];
if(!f)return;
const r=new FileReader();
r.onload=function(ev){
imgB64=ev.target.result;
document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+imgB64+'">';
};
r.readAsDataURL(f);
}

async function matchPaint(){
const btn=document.getElementById('paintBtn');
const c=document.getElementById('paintResult');
if(!imgB64){c.innerHTML='<div class="card"><p style="color:red">Please select an image first</p></div>';return}
btn.disabled=true;btn.textContent='Analyzing...';
c.innerHTML='<div class="loading">AI is analyzing the paint colour...</div>';
try{
const res=await fetch('/api/paint/match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_base64:imgB64,vehicle_info:document.getElementById('paintVehicle').value})});
const data=await res.json();
if(!data.success){c.innerHTML='<div class="card"><p style="color:red">'+(data.error||'Failed')+'</p></div>'}
else renderPaint(data);
}catch(e){c.innerHTML='<div class="card"><p style="color:red">Error: '+e.message+'</p></div>'}
btn.disabled=false;btn.textContent='🎨 Match Paint Colour';
}

function renderPaint(data){
const col=data.detected_colour;
let h='<div class="card"><div class="swatch" style="background:'+col.hex_code+'"></div><h3>'+esc(col.name)+'</h3><p><strong>'+esc(col.finish)+'</strong> • '+esc(col.colour_family)+'</p><p style="font-family:monospace">'+col.hex_code+'</p><p>Confidence: <strong>'+data.confidence+'</strong></p></div>';
if(data.brand_codes){h+='<div class="card"><h3>Brand Codes</h3>';data.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code)+' — '+esc(b.name)+'</div>'});h+='</div>'}
if(data.mixing_formula){const m=data.mixing_formula;h+='<div class="card"><h3>Mixing Formula</h3><p><strong>Base:</strong> '+esc(m.base_colour)+'</p>';if(m.toners)m.toners.forEach(t=>{h+='<div class="list-item">• '+esc(t.name)+': '+esc(t.parts)+' parts</div>'});h+='<p><strong>Reducer:</strong> '+esc(m.reducer)+'</p></div>'}
if(data.application_notes){h+='<div class="card"><h3>Application</h3>';data.application_notes.forEach(n=>{h+='<div class="list-item">• '+esc(n)+'</div>'});h+='</div>'}
if(data.safety_warnings){h+='<div class="card" style="background:#FFEBEE"><h3 style="color:#C62828">⚠ Safety</h3>';data.safety_warnings.forEach(w=>{h+='<div class="list-item">⚠ '+esc(w)+'</div>'});h+='</div>'}
document.getElementById('paintResult').innerHTML=h;
}
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

@app.get("/api/fault-codes")
def list_codes(search: str = None):
    results = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        results = [c for c in results if q in c["code"].lower() or q in c["description"].lower()]
    return {"count": len(results), "codes": results}

@app.get("/api/fault-codes/{code}")
def get_code(code: str):
    c = FAULT_CODES.get(code.upper())
    if not c:
        raise HTTPException(404, "Code not found")
    return c

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17:
        raise HTTPException(400, "VIN must be 17 characters")
    wmi = v[:3]
    mfr, country = WMI_DB.get(wmi, ("Unknown", "Unknown"))
    return {
        "vin": v, "manufacturer": mfr, "country": country,
        "year": YEAR_CODES.get(v[9], "Unknown"),
    }

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("message", "")
    if not msg:
        raise HTTPException(400, "Message required")
    if not OPENAI_KEY:
        return {"reply": "AI not configured. Contact admin."}
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
        return {"success": False, "error": "Image too large (max 5MB)"}

    prompt = f"""You are an expert automotive paint technician.
Vehicle: {vehicle or 'Not specified'}

Analyze the paint colour. Respond ONLY with valid JSON:
{{
    "detected_colour": {{
        "name": "Colour name",
        "hex_code": "#RRGGBB",
        "rgb": [R,G,B],
        "finish": "Solid|Metallic|Pearl|Matte|Satin",
        "colour_family": "White|Black|Red|Blue|Silver|Grey|Green|Yellow|Orange|Brown"
    }},
    "confidence": "High|Medium|Low",
    "condition_notes": "Paint condition",
    "brand_codes": [
        {{"brand": "DuPont", "code": "Code", "name": "Formula"}},
        {{"brand": "PPG", "code": "Code", "name": "Formula"}},
        {{"brand": "Sikkens", "code": "Code", "name": "Formula"}},
        {{"brand": "Glasurit", "code": "Code", "name": "Formula"}}
    ],
    "mixing_formula": {{
        "base_colour": "Description",
        "toners": [{{"name": "Toner", "parts": "X"}}],
        "reducer": "Ratio",
        "total_parts": 100
    }},
    "coverage_estimate": {{
        "base_coat_litres": "X.X",
        "clear_coat_litres": "X.X"
    }},
    "application_notes": ["Step 1", "Step 2"],
    "safety_warnings": ["Warning 1"]
}}"""

    try:
        client = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img}",
                        "detail": "high"
                    }}
                ]
            }],
            max_tokens=2000,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        parsed["success"] = True
        return parsed
    except Exception as e:
        return {"success": False, "error": str(e)}
