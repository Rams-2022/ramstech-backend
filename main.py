from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from datetime import datetime
import openai, os, uuid, json

app = FastAPI()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

JOBS, CUSTOMERS, INVOICES = {}, {}, {}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","logo":"🔧","labour_rate":450}

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

FAULT_CODES = {
    "P0101":{"code":"P0101","description":"Mass Air Flow Circuit","system":"Engine","severity":"Medium",
             "causes":["Dirty MAF","Air leaks","Clogged filter"],
             "steps":["Check filter","Inspect intake","Clean MAF"]},
    "P0300":{"code":"P0300","description":"Multiple Cylinder Misfire","system":"Engine","severity":"High",
             "causes":["Faulty plugs","Bad coils","Fuel issues"],
             "steps":["Scan cylinders","Check plugs","Test coils"]},
    "P0401":{"code":"P0401","description":"EGR Flow Insufficient","system":"Engine","severity":"Medium",
             "causes":["Clogged EGR","Blocked passages"],
             "steps":["Inspect EGR","Check passages"]},
    "P0700":{"code":"P0700","description":"Transmission Control","system":"Transmission","severity":"High",
             "causes":["Internal fault","TCM problem","Solenoid"],
             "steps":["Scan TCM","Check fluid"]},
    "P0087":{"code":"P0087","description":"Fuel Rail Pressure Low","system":"Diesel","severity":"High",
             "causes":["Faulty HP pump","Clogged filter"],
             "steps":["Check pressure","Inspect filter"]},
    "HYD-001":{"code":"HYD-001","description":"Low Hydraulic Pressure","system":"Hydraulic","severity":"High",
               "causes":["Worn pump","Leaks","Low fluid"],
               "steps":["Check fluid","Test pressure"]},
    "PNEU-001":{"code":"PNEU-001","description":"Air Compressor No Pressure","system":"Pneumatic","severity":"High",
                "causes":["Worn rings","Leaking valves"],
                "steps":["Check belt","Test output"]},
}

HTML = r"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RamsTech</title>
<style>
:root{--bg:#f0f2f5;--card:#fff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;--primary:#E65100}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);padding-bottom:80px}
.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:16px;text-align:center;border-bottom-left-radius:24px;border-bottom-right-radius:24px;box-shadow:0 6px 24px rgba(102,126,234,.35)}
.header h1{font-size:20px;font-weight:800}
.header p{font-size:11px;opacity:.9;margin-top:3px}
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block}
.panel-title{font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px}
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:16px;padding:20px 12px;cursor:pointer;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.tile:active{transform:scale(.95)}
.tile-icon{font-size:36px;margin-bottom:8px;display:block}
.tile-label{font-size:13px;font-weight:700}
.card{background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;font-weight:700}
.card p{margin:4px 0;font-size:13px;line-height:1.5}
.form-input{width:100%;padding:14px;border:1.5px solid var(--border);border-radius:12px;font-size:15px;margin-bottom:10px;background:#f9fafb;font-family:inherit}
.form-input:focus{outline:none;border-color:var(--primary)}
.btn{width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;box-shadow:0 4px 12px rgba(102,126,234,.3)}
.btn:active{transform:scale(.97)}
.btn-green{background:linear-gradient(135deg,#43e97b,#38f9d7)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-sm{padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;background:var(--primary);color:white}
.btn-sm.green{background:#10b981}.btn-sm.red{background:#ef4444}.btn-sm.blue{background:#3b82f6}.btn-sm.gray{background:#6b7280}.btn-sm.wa{background:#25D366}
.badge{display:inline-block;padding:3px 9px;border-radius:6px;font-size:11px;font-weight:700;color:white;margin-left:6px}
.badge.high{background:#ef4444}.badge.medium{background:#f59e0b}.badge.low,.badge.ok{background:#10b981}
.badge.new{background:#6b7280}.badge.inprogress{background:#f59e0b}.badge.completed{background:#10b981}
.list-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.list-item:last-child{border-bottom:none}
.chat-box{background:var(--card);border-radius:16px;padding:14px;height:calc(100vh - 300px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border)}
.msg{padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.45}
.msg.user{background:linear-gradient(135deg,#667eea,#764ba2);color:white;margin-left:auto}
.msg.ai{background:#f9fafb;border:1px solid var(--border)}
.input-row{display:flex;gap:8px}
.input-row input{flex:1;padding:14px 18px;border:1.5px solid var(--border);border-radius:25px;font-size:15px;outline:none}
.input-row button{padding:14px 16px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:50%;font-weight:bold;font-size:16px}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;padding:8px 4px;z-index:100}
.bnav{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px}
.bnav.active{background:rgba(230,81,0,.08)}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase}
.bnav.active .bnav-label{color:var(--primary)}
.loading{text-align:center;padding:20px;color:var(--text2);font-size:13px}
.status-online{background:linear-gradient(135deg,#10b981,#34d399);color:white;padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.status-offline{background:linear-gradient(135deg,#ef4444,#f87171);color:white;padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
</style>
</head><body>

<div class="header">
<h1>🔧 <span id="wsName">RAMSTECH</span></h1>
<p id="wsSub">AI Workshop Assistant</p>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking...</div></div>
<div class="tile-grid">
<div class="tile" onclick="showTab('chat',this)"><span class="tile-icon">🤖</span><div class="tile-label">AI Chat</div></div>
<div class="tile" onclick="showTab('codes',this)"><span class="tile-icon">📟</span><div class="tile-label">Fault Codes</div></div>
<div class="tile" onclick="showTab('jobs',this)"><span class="tile-icon">📋</span><div class="tile-label">Jobs</div></div>
<div class="tile" onclick="showTab('customers',this)"><span class="tile-icon">👥</span><div class="tile-label">Customers</div></div>
<div class="tile" onclick="showTab('invoices',this)"><span class="tile-icon">💰</span><div class="tile-label">Invoices</div></div>
<div class="tile" onclick="showTab('settings',this)"><span class="tile-icon">⚙️</span><div class="tile-label">Settings</div></div>
</div>
</div>

<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! Ask me about vehicle repairs, diagnostics, or tools.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()">
<button onclick="sendMsg()">➤</button>
</div>
</div>

<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<button class="btn btn-green" onclick="showForm('jobForm')">+ New Job</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jCustomer" placeholder="Customer name">
<input class="form-input" id="jPhone" placeholder="Phone">
<input class="form-input" id="jVehicle" placeholder="Vehicle">
<input class="form-input" id="jReg" placeholder="Registration">
<textarea class="form-input" id="jComplaint" placeholder="Complaint" rows="2"></textarea>
<button class="btn btn-green" onclick="createJob()">Save Job</button>
<button class="btn btn-dark" onclick="hideForm('jobForm')">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<div id="customers" class="panel">
<div class="panel-title">👥 Customers</div>
<button class="btn btn-green" onclick="showForm('custForm')">+ New Customer</button>
<div id="custForm" style="display:none">
<div class="card">
<input class="form-input" id="cName" placeholder="Name">
<input class="form-input" id="cPhone" placeholder="Phone">
<input class="form-input" id="cEmail" placeholder="Email">
<button class="btn btn-green" onclick="createCustomer()">Save</button>
<button class="btn btn-dark" onclick="hideForm('custForm')">Cancel</button>
</div>
</div>
<div id="custList"><div class="loading">Loading...</div></div>
</div>

<div id="invoices" class="panel">
<div class="panel-title">💰 Invoices</div>
<button class="btn btn-green" onclick="showForm('invForm')">+ New Invoice</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="iCustomer" placeholder="Customer">
<input class="form-input" id="iVehicle" placeholder="Vehicle">
<input class="form-input" id="iDesc" placeholder="Description">
<input class="form-input" id="iLabour" type="number" placeholder="Labour (R)">
<input class="form-input" id="iParts" type="number" placeholder="Parts (R)">
<button class="btn btn-green" onclick="createInvoice()">Save</button>
<button class="btn btn-dark" onclick="hideForm('invForm')">Cancel</button>
</div>
</div>
<div id="invList"><div class="loading">Loading...</div></div>
</div>

<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
<div class="card">
<h3>🏢 Workshop</h3>
<input class="form-input" id="sLogo" placeholder="🔧" maxlength="4">
<input class="form-input" id="sName" placeholder="Workshop name">
<input class="form-input" id="sPhone" placeholder="Phone">
<input class="form-input" id="sAddress" placeholder="Address">
<input class="form-input" id="sRate" type="number" placeholder="Labour rate R/hr">
<button class="btn btn-green" onclick="saveSettings()">Save</button>
</div>
</div>

<div class="bottom-nav">
<div class="bnav active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
<div class="bnav" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
<div class="bnav" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav" onclick="showTab('customers',this)"><div class="bnav-icon">👥</div><div class="bnav-label">Clients</div></div>
<div class="bnav" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>

<script>
async function jget(u){const r=await fetch(u);return r.json();}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
async function jput(u,b){const r=await fetch(u,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}

function showTab(name,el){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.bnav').forEach(t=>t.classList.remove('active'));
document.getElementById(name).classList.add('active');
if(el&&el.classList)el.classList.add('active');
window.scrollTo(0,0);
if(name==='codes'&&!document.getElementById('codeResults').dataset.loaded)searchCodes();
if(name==='jobs')loadJobs();
if(name==='customers')loadCust();
if(name==='invoices')loadInv();
if(name==='settings')loadSettings();
}
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}

async function checkStatus(){try{await fetch('/health');document.getElementById('status').innerHTML='<span class="status-online">✓ Backend Online</span>';}catch(e){document.getElementById('status').innerHTML='<span class="status-offline">✗ Backend Offline</span>';}}
checkStatus();

async function sendMsg(){
const i=document.getElementById('chatInput');const m=i.value.trim();if(!m)return;
const b=document.getElementById('chatBox');
b.innerHTML+='<div class="msg user">'+esc(m)+'</div>';i.value='';b.scrollTop=b.scrollHeight;
b.innerHTML+='<div class="msg ai" id="typ">Thinking...</div>';b.scrollTop=b.scrollHeight;
try{const d=await jpost('/api/chat',{message:m});document.getElementById('typ').outerHTML='<div class="msg ai">'+esc(d.reply)+'</div>';}
catch(e){document.getElementById('typ').outerHTML='<div class="msg ai">Error</div>';}
b.scrollTop=b.scrollHeight;
}

async function searchCodes(){
const q=document.getElementById('codeSearch').value;const c=document.getElementById('codeResults');
c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/fault-codes?search='+encodeURIComponent(q));c.dataset.loaded='1';
c.innerHTML=d.codes.length?d.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}

async function loadJobs(){
const c=document.getElementById('jobList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/jobs');
c.innerHTML=d.jobs.length?d.jobs.reverse().map(j=>'<div class="card"><h3>Job #'+j.id+' <span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+j.status+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p><p style="color:var(--text2)">'+esc(j.complaint)+'</p><p style="font-size:11px;color:var(--text2);margin-top:6px">'+esc(j.created)+'</p><div style="margin-top:8px"><button class="btn-sm blue" onclick="upJob(\''+j.id+'\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="upJob(\''+j.id+'\',\'Completed\')">Done</button><button class="btn-sm red" onclick="delJob(\''+j.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No jobs yet</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createJob(){
const c=document.getElementById('jCustomer').value.trim();
const v=document.getElementById('jVehicle').value.trim();
const comp=document.getElementById('jComplaint').value.trim();
if(!c||!v||!comp){alert('Fill customer, vehicle, complaint');return;}
await jpost('/api/jobs',{customer:c,phone:document.getElementById('jPhone').value,vehicle:v,registration:document.getElementById('jReg').value,complaint:comp});
['jCustomer','jPhone','jVehicle','jReg','jComplaint'].forEach(id=>document.getElementById(id).value='');
hideForm('jobForm');loadJobs();
}
async function upJob(id,s){await jput('/api/jobs/'+id,{status:s});loadJobs();}
async function delJob(id){if(!confirm('Delete?'))return;await fetch('/api/jobs/'+id,{method:'DELETE'});loadJobs();}

async function loadCust(){
const c=document.getElementById('custList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/customers');
c.innerHTML=d.customers.length?d.customers.reverse().map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+'<div style="margin-top:8px"><button class="btn-sm wa" onclick="waCust(\''+esc(x.phone)+'\')">📱 WhatsApp</button><button class="btn-sm red" onclick="delCust(\''+x.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No customers</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createCustomer(){
const n=document.getElementById('cName').value.trim();
const p=document.getElementById('cPhone').value.trim();
if(!n||!p){alert('Name and phone required');return;}
await jpost('/api/customers',{name:n,phone:p,email:document.getElementById('cEmail').value});
['cName','cPhone','cEmail'].forEach(id=>document.getElementById(id).value='');
hideForm('custForm');loadCust();
}
async function delCust(id){if(!confirm('Delete?'))return;await fetch('/api/customers/'+id,{method:'DELETE'});loadCust();}
function waCust(p){window.open('https://wa.me/'+p.replace(/\D/g,''),'_blank');}

async function loadInv(){
const c=document.getElementById('invList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/invoices');
c.innerHTML=d.invoices.length?d.invoices.reverse().map(i=>'<div class="card"><h3>Invoice #'+i.id+'</h3><p><strong>'+esc(i.customer)+'</strong></p><p>'+esc(i.description)+'</p><div class="list-item">Labour: R'+i.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+i.parts.toFixed(2)+'</div><div class="list-item"><strong>Total: R'+i.total.toFixed(2)+'</strong></div><button class="btn-sm red" onclick="delInv(\''+i.id+'\')">×</button></div>').join(''):'<div class="card"><p>No invoices</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createInvoice(){
const c=document.getElementById('iCustomer').value.trim();
const d=document.getElementById('iDesc').value.trim();
if(!c||!d){alert('Customer and description required');return;}
await jpost('/api/invoices',{customer:c,vehicle:document.getElementById('iVehicle').value,description:d,labour:parseFloat(document.getElementById('iLabour').value)||0,parts:parseFloat(document.getElementById('iParts').value)||0});
['iCustomer','iVehicle','iDesc','iLabour','iParts'].forEach(id=>document.getElementById(id).value='');
hideForm('invForm');loadInv();
}
async function delInv(id){if(!confirm('Delete?'))return;await fetch('/api/invoices/'+id,{method:'DELETE'});loadInv();}

async function loadSettings(){
try{const d=await jget('/api/workshop');
document.getElementById('sLogo').value=d.logo||'🔧';
document.getElementById('sName').value=d.name||'';
document.getElementById('sPhone').value=d.phone||'';
document.getElementById('sAddress').value=d.address||'';
document.getElementById('sRate').value=d.labour_rate||450;
applyBrand(d);
}catch(e){}
}
function applyBrand(d){
const logo=d.logo||'🔧';
const name=(d.name||'RAMSTECH').toUpperCase();
document.querySelector('.header h1').innerHTML=logo+' <span id="wsName">'+name+'</span>';
const sub=[d.phone,d.address].filter(Boolean).join(' • ');
document.getElementById('wsSub').textContent=sub||'AI Workshop Assistant';
}
async function saveSettings(){
const p={logo:document.getElementById('sLogo').value||'🔧',name:document.getElementById('sName').value,phone:document.getElementById('sPhone').value,address:document.getElementById('sAddress').value,labour_rate:parseFloat(document.getElementById('sRate').value)||450};
await jpost('/api/workshop',p);applyBrand(p);alert('Saved ✓');
}
loadSettings();
</script>
</body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home(): return HTML

@app.get("/health")
def health(): return {"status":"healthy"}

@app.get("/api/fault-codes")
def codes(search: str = None):
    r = list(FAULT_CODES.values())
    if search:
        q = search.lower()
        r = [c for c in r if q in c["code"].lower() or q in c["description"].lower()]
    return {"codes": r}

@app.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message","")
    if not msg: raise HTTPException(400,"Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured — set OPENAI_API_KEY in Render environment"}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, an expert mechanic assistant. Help with diagnostics, repairs, tools, and fault codes."},
                      {"role":"user","content":msg}], max_tokens=800, temperature=0.3)
        return {"reply": resp.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

@app.get("/api/jobs")
def list_jobs(): return {"jobs": list(JOBS.values())}

@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json()
    jid = str(uuid.uuid4())[:6]
    JOBS[jid] = {"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),
                 "vehicle":d.get("vehicle",""),"registration":d.get("registration",""),
                 "complaint":d.get("complaint",""),"status":"New","created":now()}
    return {"success":True,"job":JOBS[jid]}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d = await r.json()
    if jid in JOBS: JOBS[jid]["status"] = d.get("status", JOBS[jid]["status"])
    return {"success":True}

@app.delete("/api/jobs/{jid}")
def delete_job(jid: str):
    JOBS.pop(jid, None); return {"success":True}

@app.get("/api/customers")
def list_cust(): return {"customers": list(CUSTOMERS.values())}

@app.post("/api/customers")
async def create_cust(r: Request):
    d = await r.json()
    cid = str(uuid.uuid4())[:6]
    CUSTOMERS[cid] = {"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),
                      "email":d.get("email",""),"created":today()}
    return {"success":True,"customer":CUSTOMERS[cid]}

@app.delete("/api/customers/{cid}")
def delete_cust(cid: str):
    CUSTOMERS.pop(cid, None); return {"success":True}

@app.get("/api/invoices")
def list_inv(): return {"invoices": list(INVOICES.values())}

@app.post("/api/invoices")
async def create_inv(r: Request):
    d = await r.json()
    labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour + parts; vat = subtotal * 0.15; total = subtotal + vat
    iid = str(uuid.uuid4())[:6]
    INVOICES[iid] = {"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
                     "description":d.get("description",""),"labour":labour,"parts":parts,
                     "subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    return {"success":True,"invoice":INVOICES[iid]}

@app.delete("/api/invoices/{iid}")
def delete_inv(iid: str):
    INVOICES.pop(iid, None); return {"success":True}

@app.get("/api/workshop")
def get_ws(): return WORKSHOP

@app.post("/api/workshop")
async def save_ws(r: Request):
    d = await r.json(); WORKSHOP.update(d); return {"success":True,"workshop":WORKSHOP}
