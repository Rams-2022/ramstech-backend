from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
import openai, os, uuid

app = FastAPI()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# ═══════════════════════════════════
# DATABASE
# ═══════════════════════════════════
_db = None
DB_READY = False

def init_db():
    global _db, DB_READY
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[db] Memory mode")
        return
    try:
        from supabase import create_client
        _db = create_client(SUPABASE_URL, SUPABASE_KEY)
        _db.table("workshop").select("id").limit(1).execute()
        DB_READY = True
        print("[db] Supabase connected")
    except Exception as e:
        print(f"[db] Failed: {e}")

init_db()

MEM = {"jobs":{}, "customers":{}, "invoices":{}, "quotes":{}, "appointments":{}}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","logo":"🔧","labour_rate":450}

def db_list(table):
    if DB_READY:
        try: return _db.table(table).select("*").execute().data or []
        except Exception as e: print(f"[db] list {table}: {e}")
    return list(MEM[table].values())

def db_get(table, id_val):
    if DB_READY:
        try:
            r = _db.table(table).select("*").eq("id", id_val).execute()
            return r.data[0] if r.data else None
        except Exception as e: print(f"[db] get {table}: {e}")
    return MEM[table].get(id_val)

def db_save(table, id_val, row):
    if DB_READY:
        try:
            if db_get(table, id_val):
                _db.table(table).update(row).eq("id", id_val).execute()
            else:
                _db.table(table).insert(row).execute()
            return row
        except Exception as e: print(f"[db] save {table}: {e}")
    MEM[table][id_val] = row
    return row

def db_del(table, id_val):
    if DB_READY:
        try: _db.table(table).delete().eq("id", id_val).execute(); return True
        except Exception as e: print(f"[db] del {table}: {e}"); return False
    MEM[table].pop(id_val, None); return True

def ws_get():
    if DB_READY:
        try:
            r = _db.table("workshop").select("*").eq("id", 1).execute()
            if r.data: return r.data[0]
        except Exception as e: print(f"[db] ws: {e}")
    return WORKSHOP

def ws_save(d):
    if DB_READY:
        try: _db.table("workshop").update(d).eq("id", 1).execute(); return d
        except Exception as e: print(f"[db] ws save: {e}")
    WORKSHOP.update(d); return WORKSHOP

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
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
.btn{width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:linear-gradient(135deg,#667eea,#764ba2);color:white}
.btn:active{transform:scale(.97)}
.btn-green{background:linear-gradient(135deg,#43e97b,#38f9d7)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-sm{padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;background:var(--primary);color:white}
.btn-sm.green{background:#10b981}.btn-sm.red{background:#ef4444}.btn-sm.blue{background:#3b82f6}.btn-sm.gray{background:#6b7280}.btn-sm.wa{background:#25D366}.btn-sm.purple{background:#8b5cf6}
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
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{background:var(--card);padding:16px 12px;border-radius:16px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.stat-card .num{font-size:22px;font-weight:800;color:var(--primary)}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:4px;font-weight:600;text-transform:uppercase}
.stat-card.green .num{color:#10b981}
.stat-card.red .num{color:#ef4444}
.stat-card.blue .num{color:#3b82f6}
.stat-card.purple .num{color:#8b5cf6}
canvas{max-height:220px}
</style>
</head><body>

<div class="header">
<h1>🔧 <span id="wsName">RAMSTECH</span></h1>
<p id="wsSub">AI Workshop Assistant</p>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking...</div></div>
<div class="tile-grid">
<div class="tile" onclick="showTab('dashboard',this)"><span class="tile-icon">📊</span><div class="tile-label">Dashboard</div></div>
<div class="tile" onclick="showTab('chat',this)"><span class="tile-icon">🤖</span><div class="tile-label">AI Chat</div></div>
<div class="tile" onclick="showTab('codes',this)"><span class="tile-icon">📟</span><div class="tile-label">Fault Codes</div></div>
<div class="tile" onclick="showTab('jobs',this)"><span class="tile-icon">📋</span><div class="tile-label">Jobs</div></div>
<div class="tile" onclick="showTab('quotes',this)"><span class="tile-icon">💬</span><div class="tile-label">Quotes</div></div>
<div class="tile" onclick="showTab('appointments',this)"><span class="tile-icon">📅</span><div class="tile-label">Appointments</div></div>
<div class="tile" onclick="showTab('customers',this)"><span class="tile-icon">👥</span><div class="tile-label">Customers</div></div>
<div class="tile" onclick="showTab('invoices',this)"><span class="tile-icon">💰</span><div class="tile-label">Invoices</div></div>
<div class="tile" onclick="showTab('settings',this)"><span class="tile-icon">⚙️</span><div class="tile-label">Settings</div></div>
</div>
</div>

<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
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

<div id="quotes" class="panel">
<div class="panel-title">💬 Quotes</div>
<button class="btn btn-green" onclick="showForm('quoteForm')">+ New Quote</button>
<div id="quoteForm" style="display:none">
<div class="card">
<input class="form-input" id="qCustomer" placeholder="Customer name">
<input class="form-input" id="qVehicle" placeholder="Vehicle">
<textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea>
<input class="form-input" id="qLabour" type="number" placeholder="Labour (R)" value="0">
<input class="form-input" id="qParts" type="number" placeholder="Parts (R)" value="0">
<button class="btn btn-green" onclick="createQuote()">Save Quote</button>
<button class="btn btn-dark" onclick="hideForm('quoteForm')">Cancel</button>
</div>
</div>
<div id="quoteList"><div class="loading">Loading...</div></div>
</div>

<div id="appointments" class="panel">
<div class="panel-title">📅 Appointments</div>
<button class="btn btn-green" onclick="showForm('apptForm')">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="aCustomer" placeholder="Customer name">
<input class="form-input" id="aPhone" placeholder="Phone">
<input class="form-input" id="aVehicle" placeholder="Vehicle">
<input class="form-input" id="aService" placeholder="Service type">
<input class="form-input" id="aDate" type="date">
<input class="form-input" id="aTime" type="time">
<button class="btn btn-green" onclick="createAppt()">Book</button>
<button class="btn btn-dark" onclick="hideForm('apptForm')">Cancel</button>
</div>
</div>
<div id="apptList"><div class="loading">Loading...</div></div>
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
<div class="bnav" onclick="showTab('dashboard',this)"><div class="bnav-icon">📊</div><div class="bnav-label">Dash</div></div>
<div class="bnav" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav" onclick="showTab('quotes',this)"><div class="bnav-icon">💬</div><div class="bnav-label">Quotes</div></div>
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
if(name==='quotes')loadQuotes();
if(name==='appointments')loadAppts();
if(name==='customers')loadCust();
if(name==='invoices')loadInv();
if(name==='settings')loadSettings();
if(name==='dashboard')loadDash();
}
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}
async function checkStatus(){
try{const r=await fetch('/health');const d=await r.json();
const db=d.database==='supabase'?' ✓ DB':' ⚠ Memory';
document.getElementById('status').innerHTML='<span class="status-online">Backend Online'+db+'</span>';
}catch(e){document.getElementById('status').innerHTML='<span class="status-offline">Offline</span>';}}
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

// ═══ DASHBOARD ═══
let rC=null,jC=null;
async function loadDash(){
try{const d=await jget('/api/stats');
document.getElementById('dashStats').innerHTML='<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Jobs</div></div><div class="stat-card purple"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open</div></div><div class="stat-card green"><div class="num">'+d.jobs_completed+'</div><div class="lbl">Done</div></div><div class="stat-card"><div class="num">'+d.customers+'</div><div class="lbl">Customers</div></div><div class="stat-card green"><div class="num">R'+d.revenue+'</div><div class="lbl">Revenue</div></div><div class="stat-card red"><div class="num">'+d.appointments_today+'</div><div class="lbl">Today</div></div></div>';
if(rC)rC.destroy();const c1=document.getElementById('revenueChart');
if(c1)rC=new Chart(c1,{type:'line',data:{labels:d.revenue_labels,datasets:[{data:d.revenue_data,borderColor:'#667eea',backgroundColor:'rgba(102,126,234,.15)',tension:.4,fill:true,borderWidth:3}]},options:{responsive:true,plugins:{legend:{display:false}}}});
if(jC)jC.destroy();const c2=document.getElementById('jobChart');
if(c2)jC=new Chart(c2,{type:'doughnut',data:{labels:['New','Progress','Done'],datasets:[{data:[d.jobs_new,d.jobs_progress,d.jobs_completed],backgroundColor:['#6b7280','#f59e0b','#10b981'],borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'bottom'}}}});
}catch(e){}
}

// ═══ CODES ═══
async function searchCodes(){
const q=document.getElementById('codeSearch').value;const c=document.getElementById('codeResults');
c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/fault-codes?search='+encodeURIComponent(q));c.dataset.loaded='1';
c.innerHTML=d.codes.length?d.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}

// ═══ JOBS ═══
async function loadJobs(){
const c=document.getElementById('jobList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/jobs');
c.innerHTML=d.jobs.length?d.jobs.map(j=>'<div class="card"><h3>Job #'+j.id+' <span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+j.status+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p><p style="color:var(--text2)">'+esc(j.complaint)+'</p><p style="font-size:11px;color:var(--text2);margin-top:6px">'+esc(j.created)+'</p><div style="margin-top:8px"><button class="btn-sm blue" onclick="upJob(\''+j.id+'\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="upJob(\''+j.id+'\',\'Completed\')">Done</button><button class="btn-sm wa" onclick="waJob(\''+j.id+'\')">📱</button><button class="btn-sm red" onclick="delJob(\''+j.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No jobs yet</p></div>';
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
function waJob(id){jget('/api/jobs').then(d=>{const j=d.jobs.find(x=>x.id==id);if(!j)return;const txt='🔧 *Job #'+j.id+'*\n'+j.customer+'\n'+j.vehicle+'\nIssue: '+j.complaint+'\nStatus: '+j.status;window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// ═══ QUOTES ═══
async function loadQuotes(){
const c=document.getElementById('quoteList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/quotes');
c.innerHTML=d.quotes.length?d.quotes.map(q=>'<div class="card"><h3>💬 Quote #'+q.id+'</h3><p><strong>'+esc(q.customer)+'</strong></p><p>'+esc(q.description)+'</p><div class="list-item">Labour: R'+q.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+q.parts.toFixed(2)+'</div><div class="list-item"><strong>Total: R'+q.total.toFixed(2)+'</strong></div><div style="margin-top:10px"><button class="btn-sm green" onclick="acceptQuote(\''+q.id+'\')">→ Invoice</button><button class="btn-sm wa" onclick="waQuote(\''+q.id+'\')">📱</button><button class="btn-sm red" onclick="delQuote(\''+q.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No quotes</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createQuote(){
const c=document.getElementById('qCustomer').value.trim();
const d=document.getElementById('qDesc').value.trim();
if(!c||!d){alert('Customer and description required');return;}
await jpost('/api/quotes',{customer:c,vehicle:document.getElementById('qVehicle').value,description:d,labour:parseFloat(document.getElementById('qLabour').value)||0,parts:parseFloat(document.getElementById('qParts').value)||0});
['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id=>document.getElementById(id).value='');
hideForm('quoteForm');loadQuotes();
}
async function acceptQuote(id){
if(!confirm('Convert to invoice?'))return;
const r=await jpost('/api/quotes/'+id+'/accept',{});
if(r.success){alert('Converted to invoice ✓');loadQuotes();}
}
async function delQuote(id){if(!confirm('Delete?'))return;await fetch('/api/quotes/'+id,{method:'DELETE'});loadQuotes();}
function waQuote(id){jget('/api/quotes').then(d=>{const q=d.quotes.find(x=>x.id==id);if(!q)return;const txt='💬 *Quote #'+q.id+'*\n'+q.customer+'\n'+q.description+'\nLabour: R'+q.labour.toFixed(2)+'\nParts: R'+q.parts.toFixed(2)+'\nTotal: R'+q.total.toFixed(2);window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// ═══ APPOINTMENTS ═══
async function loadAppts(){
const c=document.getElementById('apptList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/appointments');
const s=d.appointments.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));
c.innerHTML=s.length?s.map(a=>'<div class="card"><h3>📅 '+esc(a.date)+' at '+esc(a.time)+'</h3><p><strong>'+esc(a.customer)+'</strong></p>'+(a.phone?'<p>📞 '+esc(a.phone)+'</p>':'')+(a.vehicle?'<p>🚗 '+esc(a.vehicle)+'</p>':'')+(a.service?'<p style="color:var(--text2)">'+esc(a.service)+'</p>':'')+'<div style="margin-top:8px"><button class="btn-sm wa" onclick="waAppt(\''+a.id+'\')">📱</button><button class="btn-sm red" onclick="delAppt(\''+a.id+'\')">Delete</button></div></div>').join(''):'<div class="card"><p>No appointments</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createAppt(){
const c=document.getElementById('aCustomer').value.trim();
const d=document.getElementById('aDate').value;
const t=document.getElementById('aTime').value;
if(!c||!d||!t){alert('Customer, date, and time required');return;}
await jpost('/api/appointments',{customer:c,phone:document.getElementById('aPhone').value,vehicle:document.getElementById('aVehicle').value,service:document.getElementById('aService').value,date:d,time:t});
['aCustomer','aPhone','aVehicle','aService','aDate','aTime'].forEach(id=>document.getElementById(id).value='');
hideForm('apptForm');loadAppts();
}
async function delAppt(id){if(!confirm('Delete?'))return;await fetch('/api/appointments/'+id,{method:'DELETE'});loadAppts();}
function waAppt(id){jget('/api/appointments').then(d=>{const a=d.appointments.find(x=>x.id==id);if(!a)return;const txt='📅 *Appointment Confirmation*\n\nCustomer: '+a.customer+'\nVehicle: '+(a.vehicle||'N/A')+'\nService: '+(a.service||'General')+'\nDate: '+a.date+'\nTime: '+a.time+'\n\nSee you soon!';window.open('https://wa.me/'+(a.phone?a.phone.replace(/\D/g,'')+'?text=':'?text=')+encodeURIComponent(txt),'_blank');});}

// ═══ CUSTOMERS ═══
async function loadCust(){
const c=document.getElementById('custList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/customers');
c.innerHTML=d.customers.length?d.customers.map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+'<div style="margin-top:8px"><button class="btn-sm wa" onclick="waCust(\''+esc(x.phone)+'\')">📱 WhatsApp</button><button class="btn-sm red" onclick="delCust(\''+x.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No customers</p></div>';
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

// ═══ INVOICES ═══
async function loadInv(){
const c=document.getElementById('invList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/invoices');
c.innerHTML=d.invoices.length?d.invoices.map(i=>'<div class="card"><h3>Invoice #'+i.id+'</h3><p><strong>'+esc(i.customer)+'</strong></p><p>'+esc(i.description)+'</p><div class="list-item">Labour: R'+i.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+i.parts.toFixed(2)+'</div><div class="list-item"><strong>Total: R'+i.total.toFixed(2)+'</strong></div><div style="margin-top:8px"><button class="btn-sm wa" onclick="waInv(\''+i.id+'\')">📱</button><button class="btn-sm red" onclick="delInv(\''+i.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No invoices</p></div>';
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
function waInv(id){jget('/api/invoices').then(d=>{const i=d.invoices.find(x=>x.id==id);if(!i)return;const txt='💰 *Invoice #'+i.id+'*\n'+i.customer+'\n'+i.description+'\nLabour: R'+i.labour.toFixed(2)+'\nParts: R'+i.parts.toFixed(2)+'\nVAT: R'+i.vat.toFixed(2)+'\nTotal: R'+i.total.toFixed(2);window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// ═══ SETTINGS ═══
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
def health(): return {"status":"healthy","database":"supabase" if DB_READY else "memory"}

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
    if not OPENAI_KEY: return {"reply":"AI not configured"}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, an expert mechanic assistant."},
                      {"role":"user","content":msg}], max_tokens=800, temperature=0.3)
        return {"reply": resp.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

@app.get("/api/stats")
def stats():
    jobs = db_list("jobs"); invs = db_list("invoices"); custs = db_list("customers")
    appts = db_list("appointments")
    total = len(jobs)
    done = sum(1 for j in jobs if j.get("status")=="Completed")
    open_j = sum(1 for j in jobs if j.get("status")!="Completed")
    new_j = sum(1 for j in jobs if j.get("status")=="New")
    prog = sum(1 for j in jobs if j.get("status")=="In Progress")
    rev = sum(float(i.get("total",0)) for i in invs)
    today_str = today()
    appts_today = sum(1 for a in appts if a.get("date")==today_str)
    labels,data = [],[]
    for i in range(6,-1,-1):
        day = (datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])
        data.append(round(sum(float(x.get("total",0)) for x in invs if (x.get("created") or "").startswith(day)),2))
    return {"jobs_total":total,"jobs_open":open_j,"jobs_completed":done,
            "jobs_new":new_j,"jobs_progress":prog,"customers":len(custs),
            "appointments_today":appts_today,"revenue":round(rev,2),
            "revenue_labels":labels,"revenue_data":data}

# ═══ JOBS ═══
@app.get("/api/jobs")
def list_jobs(): return {"jobs": db_list("jobs")}

@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json()
    jid = str(uuid.uuid4())[:6]
    row = {"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),
           "vehicle":d.get("vehicle",""),"registration":d.get("registration",""),
           "complaint":d.get("complaint",""),"status":"New","created":now()}
    db_save("jobs", jid, row)
    return {"success":True,"job":row}

@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d = await r.json()
    job = db_get("jobs", jid)
    if job:
        job["status"] = d.get("status", job["status"])
        db_save("jobs", jid, job)
    return {"success":True}

@app.delete("/api/jobs/{jid}")
def delete_job(jid: str):
    db_del("jobs", jid); return {"success":True}

# ═══ QUOTES ═══
@app.get("/api/quotes")
def list_quotes(): return {"quotes": db_list("quotes")}

@app.post("/api/quotes")
async def create_quote(r: Request):
    d = await r.json()
    labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour + parts; vat = subtotal * 0.15; total = subtotal + vat
    qid = str(uuid.uuid4())[:6]
    row = {"id":qid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
           "description":d.get("description",""),"labour":labour,"parts":parts,
           "subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("quotes", qid, row)
    return {"success":True,"quote":row}

@app.post("/api/quotes/{qid}/accept")
async def accept_quote(qid: str):
    q = db_get("quotes", qid)
    if not q: raise HTTPException(404,"Quote not found")
    iid = str(uuid.uuid4())[:6]
    inv = {"id":iid,"customer":q["customer"],"vehicle":q["vehicle"],
           "description":q["description"],"labour":q["labour"],"parts":q["parts"],
           "subtotal":q["subtotal"],"vat":q["vat"],"total":q["total"],"created":now()}
    db_save("invoices", iid, inv)
    db_del("quotes", qid)
    return {"success":True,"invoice":inv}

@app.delete("/api/quotes/{qid}")
def delete_quote(qid: str):
    db_del("quotes", qid); return {"success":True}

# ═══ APPOINTMENTS ═══
@app.get("/api/appointments")
def list_appts(): return {"appointments": db_list("appointments")}

@app.post("/api/appointments")
async def create_appt(r: Request):
    d = await r.json()
    aid = str(uuid.uuid4())[:6]
    row = {"id":aid,"customer":d.get("customer",""),"phone":d.get("phone",""),
           "vehicle":d.get("vehicle",""),"service":d.get("service",""),
           "date":d.get("date",""),"time":d.get("time",""),"created":now()}
    db_save("appointments", aid, row)
    return {"success":True,"appointment":row}

@app.delete("/api/appointments/{aid}")
def delete_appt(aid: str):
    db_del("appointments", aid); return {"success":True}

# ═══ CUSTOMERS ═══
@app.get("/api/customers")
def list_cust(): return {"customers": db_list("customers")}

@app.post("/api/customers")
async def create_cust(r: Request):
    d = await r.json()
    cid = str(uuid.uuid4())[:6]
    row = {"id":cid,"name":d.get("name",""),"phone":d.get("phone",""),
           "email":d.get("email",""),"created":today()}
    db_save("customers", cid, row)
    return {"success":True,"customer":row}

@app.delete("/api/customers/{cid}")
def delete_cust(cid: str):
    db_del("customers", cid); return {"success":True}

# ═══ INVOICES ═══
@app.get("/api/invoices")
def list_inv(): return {"invoices": db_list("invoices")}

@app.post("/api/invoices")
async def create_inv(r: Request):
    d = await r.json()
    labour = float(d.get("labour",0)); parts = float(d.get("parts",0))
    subtotal = labour + parts; vat = subtotal * 0.15; total = subtotal + vat
    iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"customer":d.get("customer",""),"vehicle":d.get("vehicle",""),
           "description":d.get("description",""),"labour":labour,"parts":parts,
           "subtotal":subtotal,"vat":vat,"total":total,"created":now()}
    db_save("invoices", iid, row)
    return {"success":True,"invoice":row}

@app.delete("/api/invoices/{iid}")
def delete_inv(iid: str):
    db_del("invoices", iid); return {"success":True}

# ═══ WORKSHOP ═══
@app.get("/api/workshop")
def get_ws(): return ws_get()

@app.post("/api/workshop")
async def save_ws(r: Request):
    d = await r.json(); ws_save(d); return {"success":True,"workshop":ws_get()}
