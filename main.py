from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import datetime, timedelta
import openai, os, uuid, csv, io, json

app = FastAPI()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

_db = None
DB_READY = False

def init_db():
    global _db, DB_READY
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[db] Memory mode"); return
    try:
        from supabase import create_client
        _db = create_client(SUPABASE_URL, SUPABASE_KEY)
        _db.table("workshop").select("id").limit(1).execute()
        DB_READY = True; print("[db] Supabase connected")
    except Exception as e: print(f"[db] Failed: {e}")

init_db()

MEM = {"jobs":{}, "customers":{}, "invoices":{}, "quotes":{}, "appointments":{},
       "inventory":{}, "staff":{}, "expenses":{}}
WORKSHOP = {"name":"My Workshop","phone":"","address":"","logo":"🔧","labour_rate":450}

def db_list(table):
    if DB_READY:
        try: return _db.table(table).select("*").execute().data or []
        except Exception as e: print(f"[db] {table}: {e}")
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
    "P0101":{"code":"P0101","description":"Mass Air Flow Circuit","system":"Engine","severity":"Medium","causes":["Dirty MAF","Air leaks","Clogged filter"],"steps":["Check filter","Inspect intake","Clean MAF"]},
    "P0300":{"code":"P0300","description":"Multiple Cylinder Misfire","system":"Engine","severity":"High","causes":["Faulty plugs","Bad coils","Fuel issues"],"steps":["Scan cylinders","Check plugs","Test coils"]},
    "P0401":{"code":"P0401","description":"EGR Flow Insufficient","system":"Engine","severity":"Medium","causes":["Clogged EGR","Blocked passages"],"steps":["Inspect EGR","Check passages"]},
    "P0700":{"code":"P0700","description":"Transmission Control","system":"Transmission","severity":"High","causes":["Internal fault","TCM problem","Solenoid"],"steps":["Scan TCM","Check fluid"]},
    "P0087":{"code":"P0087","description":"Fuel Rail Pressure Low","system":"Diesel","severity":"High","causes":["Faulty HP pump","Clogged filter"],"steps":["Check pressure","Inspect filter"]},
    "HYD-001":{"code":"HYD-001","description":"Low Hydraulic Pressure","system":"Hydraulic","severity":"High","causes":["Worn pump","Leaks","Low fluid"],"steps":["Check fluid","Test pressure"]},
    "PNEU-001":{"code":"PNEU-001","description":"Air Compressor No Pressure","system":"Pneumatic","severity":"High","causes":["Worn rings","Leaking valves"],"steps":["Check belt","Test output"]},
}

WMI_DB = {"1HG":("Honda","USA"),"1FT":("Ford","USA"),"JHM":("Honda","Japan"),
          "JTD":("Toyota","Japan"),"JTM":("Toyota","Japan"),"KMH":("Hyundai","Korea"),
          "KNA":("Kia","Korea"),"WBA":("BMW","Germany"),"WDB":("Mercedes-Benz","Germany"),
          "WVW":("Volkswagen","Germany"),"YV1":("Volvo","Sweden"),"ZFA":("Fiat","Italy"),
          "AAV":("VW South Africa","South Africa"),"AHT":("Toyota SA","South Africa"),
          "AFA":("Ford SA","South Africa"),"ADB":("Mercedes SA","South Africa")}

YEAR_CODES = {"A":2010,"B":2011,"C":2012,"D":2013,"E":2014,"F":2015,"G":2016,"H":2017,
              "J":2018,"K":2019,"L":2020,"M":2021,"N":2022,"P":2023,"R":2024,
              "Y":2000,"1":2001,"2":2002,"3":2003,"4":2004,"5":2005,"6":2006,"7":2007,"8":2008,"9":2009}

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
.badge.high{background:#ef4444}.badge.medium{background:#f59e0b}.badge.low,.badge.ok{background:#10b981}.badge.warn{background:#ef4444}
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
.stat-card.green .num{color:#10b981}.stat-card.red .num{color:#ef4444}.stat-card.blue .num{color:#3b82f6}.stat-card.purple .num{color:#8b5cf6}
canvas{max-height:220px}
.img-preview{width:100%;border-radius:14px;margin-bottom:12px}
.swatch{height:90px;border-radius:14px;border:2px solid var(--border);margin-bottom:12px}
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
<div class="tile" onclick="showTab('vin',this)"><span class="tile-icon">🔍</span><div class="tile-label">VIN Decoder</div></div>
<div class="tile" onclick="showTab('photo',this)"><span class="tile-icon">📸</span><div class="tile-label">Photo Diag</div></div>
<div class="tile" onclick="showTab('paint',this)"><span class="tile-icon">🎨</span><div class="tile-label">Paint Match</div></div>
<div class="tile" onclick="showTab('jobs',this)"><span class="tile-icon">📋</span><div class="tile-label">Jobs</div></div>
<div class="tile" onclick="showTab('quotes',this)"><span class="tile-icon">💬</span><div class="tile-label">Quotes</div></div>
<div class="tile" onclick="showTab('appointments',this)"><span class="tile-icon">📅</span><div class="tile-label">Appointments</div></div>
<div class="tile" onclick="showTab('customers',this)"><span class="tile-icon">👥</span><div class="tile-label">Customers</div></div>
<div class="tile" onclick="showTab('invoices',this)"><span class="tile-icon">💰</span><div class="tile-label">Invoices</div></div>
<div class="tile" onclick="showTab('inventory',this)"><span class="tile-icon">📦</span><div class="tile-label">Inventory</div></div>
<div class="tile" onclick="showTab('staff',this)"><span class="tile-icon">👷</span><div class="tile-label">Staff</div></div>
<div class="tile" onclick="showTab('expenses',this)"><span class="tile-icon">💸</span><div class="tile-label">Expenses</div></div>
<div class="tile" onclick="showTab('analytics',this)"><span class="tile-icon">📈</span><div class="tile-label">Analytics</div></div>
<div class="tile" onclick="showTab('warranty',this)"><span class="tile-icon">🎁</span><div class="tile-label">Warranty</div></div>
<div class="tile" onclick="showTab('tax',this)"><span class="tile-icon">🧾</span><div class="tile-label">Tax</div></div>
<div class="tile" onclick="showTab('settings',this)"><span class="tile-icon">⚙️</span><div class="tile-label">Settings</div></div>
</div>
</div>

<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock Alerts</h3><div id="dashLowStock"></div></div>
</div>

<div id="analytics" class="panel">
<div class="panel-title">📈 Analytics</div>
<div id="analyticsContent"><div class="loading">Loading...</div></div>
</div>

<div id="warranty" class="panel">
<div class="panel-title">🎁 Warranty Tracker</div>
<div id="warrantyList"><div class="loading">Loading...</div></div>
</div>

<div id="tax" class="panel">
<div class="panel-title">🧾 Tax & Reports</div>
<div class="card">
<h3>📅 Tax Report Period</h3>
<input class="form-input" id="taxFrom" type="date">
<input class="form-input" id="taxTo" type="date">
<button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV Report</button>
</div>
<div class="card">
<h3>💼 Business Card</h3>
<div id="bizCard" style="padding:20px;background:white;color:black;border-radius:12px;border:2px solid #E65100;text-align:center">
<div id="bcLogo" style="font-size:48px">🔧</div>
<h2 id="bcName" style="color:#E65100;margin:8px 0">My Workshop</h2>
<p id="bcPhone" style="font-size:14px">Phone</p>
<p id="bcAddress" style="font-size:12px;color:#666">Address</p>
</div>
<button class="btn" style="margin-top:12px" onclick="printBizCard()">🖨 Print Card</button>
</div>
</div>

<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<div class="card">
<p style="font-size:13px;color:var(--text2);margin-bottom:10px">Enter the 17-character VIN from the vehicle. It's usually on the driver-side door frame, engine bay, or windshield base.</p>
<input class="form-input" id="vinInput" placeholder="e.g. AHTFR22G50XXXXXXX" maxlength="17" style="text-transform:uppercase">
<button class="btn btn-green" onclick="decodeVin()">🔍 Decode VIN</button>
<div id="vinResult"></div>
</div>
</div>

<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card">
<p style="font-size:13px;color:var(--text2);margin-bottom:10px">📸 Take a photo of the mechanical issue — leak, worn part, damage, warning light, etc. AI will analyze it and give you diagnostic steps.</p>
<input class="form-input" id="photoVehicle" placeholder="Vehicle info (optional) e.g. 2018 Toyota Hilux">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn btn-green" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>
</div>

<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card">
<p style="font-size:13px;color:var(--text2);margin-bottom:10px">🎨 Take a clear photo of the vehicle panel in good natural light. AI identifies the colour and provides paint codes.</p>
<input class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn btn-green" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
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
<select class="form-input" id="jAssigned"><option value="">— Assign staff —</option></select>
<input class="form-input" id="jWarranty" type="number" placeholder="Warranty (months)" value="6">
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

<div id="inventory" class="panel">
<div class="panel-title">📦 Inventory</div>
<button class="btn btn-green" onclick="showForm('invItemForm')">+ Add Stock Item</button>
<div id="invItemForm" style="display:none">
<div class="card">
<input class="form-input" id="pNumber" placeholder="Part number">
<input class="form-input" id="pName" placeholder="Part name">
<input class="form-input" id="pCategory" placeholder="Category">
<input class="form-input" id="pQty" type="number" placeholder="Quantity">
<input class="form-input" id="pMinQty" type="number" placeholder="Min qty" value="5">
<input class="form-input" id="pCost" type="number" placeholder="Cost price (R)">
<input class="form-input" id="pSell" type="number" placeholder="Sell price (R)">
<input class="form-input" id="pSupplier" placeholder="Supplier">
<button class="btn btn-green" onclick="addInventory()">Save Item</button>
<button class="btn btn-dark" onclick="hideForm('invItemForm')">Cancel</button>
</div>
</div>
<div id="inventoryList"><div class="loading">Loading...</div></div>
</div>

<div id="staff" class="panel">
<div class="panel-title">👷 Staff</div>
<button class="btn btn-green" onclick="showForm('staffForm')">+ Add Staff Member</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="stName" placeholder="Full name">
<input class="form-input" id="stRole" placeholder="Role">
<input class="form-input" id="stPhone" placeholder="Phone">
<input class="form-input" id="stEmail" placeholder="Email">
<input class="form-input" id="stRate" type="number" placeholder="Hourly rate (R)" value="150">
<button class="btn btn-green" onclick="addStaff()">Save Staff</button>
<button class="btn btn-dark" onclick="hideForm('staffForm')">Cancel</button>
</div>
</div>
<div id="staffList"><div class="loading">Loading...</div></div>
</div>

<div id="expenses" class="panel">
<div class="panel-title">💸 Expenses</div>
<button class="btn btn-green" onclick="showForm('expForm')">+ Add Expense</button>
<div id="expForm" style="display:none">
<div class="card">
<select class="form-input" id="exCat">
<option>Rent</option><option>Utilities</option><option>Tools</option>
<option>Parts</option><option>Salaries</option><option>Fuel</option>
<option>Marketing</option><option>Other</option>
</select>
<input class="form-input" id="exAmount" type="number" placeholder="Amount (R)">
<input class="form-input" id="exDate" type="date">
<textarea class="form-input" id="exNote" placeholder="Note" rows="2"></textarea>
<button class="btn btn-green" onclick="addExpense()">Save Expense</button>
<button class="btn btn-dark" onclick="hideForm('expForm')">Cancel</button>
</div>
</div>
<div id="expenseList"><div class="loading">Loading...</div></div>
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
<div class="bnav" onclick="showTab('photo',this)"><div class="bnav-icon">📸</div><div class="bnav-label">Photo</div></div>
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
if(name==='jobs'){loadJobs();loadStaffDropdown();}
if(name==='quotes')loadQuotes();
if(name==='appointments')loadAppts();
if(name==='customers')loadCust();
if(name==='invoices')loadInv();
if(name==='inventory')loadInventory();
if(name==='staff')loadStaff();
if(name==='expenses')loadExpenses();
if(name==='settings')loadSettings();
if(name==='dashboard')loadDash();
if(name==='analytics')loadAnalytics();
if(name==='warranty')loadWarranty();
if(name==='tax')loadTax();
}
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}
async function checkStatus(){
try{const r=await fetch('/health');const d=await r.json();
const db=d.database==='supabase'?' ✓ DB':' ⚠ Memory';
document.getElementById('status').innerHTML='<span class="status-online">Backend Online'+db+'</span>';
}catch(e){document.getElementById('status').innerHTML='<span class="status-offline">Offline</span>';}}
checkStatus();

// ═══ IMAGE COMPRESSION ═══
function compressImage(file,maxWidth,quality){
return new Promise((resolve)=>{
const reader=new FileReader();
reader.onload=(e)=>{
const img=new Image();
img.onload=()=>{
const canvas=document.createElement('canvas');
let{width,height}=img;
if(width>maxWidth){height=(height*maxWidth)/width;width=maxWidth;}
canvas.width=width;canvas.height=height;
canvas.getContext('2d').drawImage(img,0,0,width,height);
resolve(canvas.toDataURL('image/jpeg',quality));
};
img.src=e.target.result;
};
reader.readAsDataURL(file);
});}

// ═══ VIN DECODER ═══
async function decodeVin(){
const vin=document.getElementById('vinInput').value.trim().toUpperCase();
const c=document.getElementById('vinResult');
if(vin.length!==17){c.innerHTML='<div class="card" style="background:#fef2f2"><p style="color:#ef4444">⚠ VIN must be exactly 17 characters</p></div>';return;}
c.innerHTML='<div class="loading">Decoding VIN...</div>';
try{const d=await jget('/api/vin/'+vin);
if(d.detail){c.innerHTML='<div class="card" style="background:#fef2f2"><p style="color:#ef4444">'+d.detail+'</p></div>';return;}
c.innerHTML='<div class="card"><h3>🔍 Vehicle Information</h3><div class="list-item"><strong>VIN:</strong> <span style="font-family:monospace">'+d.vin+'</span></div><div class="list-item"><strong>Manufacturer:</strong> '+d.manufacturer+'</div><div class="list-item"><strong>Country:</strong> '+d.country+'</div><div class="list-item"><strong>Year:</strong> '+d.year+'</div><div class="list-item"><strong>Plant:</strong> '+d.plant+'</div><div class="list-item"><strong>Serial:</strong> '+d.serial+'</div></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error decoding VIN</p></div>';}
}

// ═══ PHOTO DIAG ═══
let diagB64='';
async function previewDiag(e){
const f=e.target.files[0];if(!f)return;
diagB64=await compressImage(f,1200,0.75);
document.getElementById('photoPreview').innerHTML='<img class="img-preview" src="'+diagB64+'">';
}
async function diagnosePhoto(){
const btn=document.getElementById('photoBtn');
const c=document.getElementById('photoResult');
if(!diagB64){c.innerHTML='<div class="card" style="background:#fef2f2"><p style="color:#ef4444">Select a photo first</p></div>';return;}
btn.disabled=true;btn.textContent='📸 Analyzing...';
c.innerHTML='<div class="loading">AI is analyzing your photo...</div>';
try{
const d=await jpost('/api/diagnose/photo',{image_base64:diagB64,vehicle_info:document.getElementById('photoVehicle').value});
if(!d.success){c.innerHTML='<div class="card" style="background:#fef2f2"><p style="color:#ef4444">'+(d.error||'Analysis failed')+'</p></div>';}
else{
let h='<div class="card"><h3>🔍 '+(d.problem?esc(d.problem):'Detected')+'</h3><p><strong>Confidence:</strong> '+(d.confidence||'?')+'</p>'+(d.description?'<p style="margin-top:8px">'+esc(d.description)+'</p>':'')+'</div>';
if(d.possible_causes&&d.possible_causes.length){h+='<div class="card"><h3>Possible Causes</h3>'+d.possible_causes.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>';}
if(d.diagnostic_steps&&d.diagnostic_steps.length){h+='<div class="card"><h3>Diagnostic Steps</h3>'+d.diagnostic_steps.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>';}
if(d.safety_warnings&&d.safety_warnings.length){h+='<div class="card" style="background:#fef2f2;border-color:#fecaca"><h3 style="color:#dc2626">⚠️ Safety</h3>'+d.safety_warnings.map(x=>'<div class="list-item">⚠ '+esc(x)+'</div>').join('')+'</div>';}
c.innerHTML=h;
}
}catch(e){c.innerHTML='<div class="card"><p>Error analyzing photo</p></div>';}
btn.disabled=false;btn.textContent='📸 Analyze Photo';
}

// ═══ PAINT MATCH ═══
let paintB64='';
async function previewPaint(e){
const f=e.target.files[0];if(!f)return;
paintB64=await compressImage(f,1200,0.75);
document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+paintB64+'">';
}
async function matchPaint(){
const btn=document.getElementById('paintBtn');
const c=document.getElementById('paintResult');
if(!paintB64){c.innerHTML='<div class="card" style="background:#fef2f2"><p style="color:#ef4444">Select a photo first</p></div>';return;}
btn.disabled=true;btn.textContent='🎨 Analyzing...';
c.innerHTML='<div class="loading">AI is matching the paint colour...</div>';
try{
const d=await jpost('/api/paint/match',{image_base64:paintB64,vehicle_info:document.getElementById('paintVehicle').value});
if(!d.success){c.innerHTML='<div class="card" style="background:#fef2f2"><p style="color:#ef4444">'+(d.error||'Analysis failed')+'</p></div>';}
else{
const col=d.detected_colour||{};
let h='<div class="card"><div class="swatch" style="background:'+(col.hex_code||'#ccc')+'"></div><h3>'+esc(col.name||'Unknown')+'</h3><p><strong>'+esc(col.finish||'')+'</strong>'+(col.colour_family?' • '+esc(col.colour_family):'')+'</p><p style="font-family:monospace;margin-top:6px">'+(col.hex_code||'')+'</p><p>Confidence: <strong>'+(d.confidence||'?')+'</strong></p></div>';
if(d.brand_codes&&d.brand_codes.length){h+='<div class="card"><h3>🏷️ Brand Codes</h3>';d.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code||'?')+(b.name?' — '+esc(b.name):'')+'</div>';});h+='</div>';}
if(d.mixing_formula){const m=d.mixing_formula;h+='<div class="card"><h3>🧪 Mixing Formula</h3>';if(m.base_colour)h+='<div class="list-item"><strong>Base:</strong> '+esc(m.base_colour)+'</div>';if(m.toners&&m.toners.length){m.toners.forEach(t=>{h+='<div class="list-item">• '+esc(t.name)+': '+esc(t.parts)+' parts</div>';});}if(m.reducer)h+='<div class="list-item"><strong>Reducer:</strong> '+esc(m.reducer)+'</div>';h+='</div>';}
if(d.safety_warnings&&d.safety_warnings.length){h+='<div class="card" style="background:#fef2f2"><h3 style="color:#dc2626">⚠️ Safety</h3>'+d.safety_warnings.map(x=>'<div class="list-item">⚠ '+esc(x)+'</div>').join('')+'</div>';}
c.innerHTML=h;
}
}catch(e){c.innerHTML='<div class="card"><p>Error matching paint</p></div>';}
btn.disabled=false;btn.textContent='🎨 Match Paint Colour';
}

async function sendMsg(){
const i=document.getElementById('chatInput');const m=i.value.trim();if(!m)return;
const b=document.getElementById('chatBox');
b.innerHTML+='<div class="msg user">'+esc(m)+'</div>';i.value='';b.scrollTop=b.scrollHeight;
b.innerHTML+='<div class="msg ai" id="typ">Thinking...</div>';b.scrollTop=b.scrollHeight;
try{const d=await jpost('/api/chat',{message:m});document.getElementById('typ').outerHTML='<div class="msg ai">'+esc(d.reply)+'</div>';}
catch(e){document.getElementById('typ').outerHTML='<div class="msg ai">Error</div>';}
b.scrollTop=b.scrollHeight;
}

// DASHBOARD
let rC=null,jC=null;
async function loadDash(){
try{const d=await jget('/api/stats');
document.getElementById('dashStats').innerHTML='<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Jobs</div></div><div class="stat-card purple"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open</div></div><div class="stat-card green"><div class="num">'+d.jobs_completed+'</div><div class="lbl">Done</div></div><div class="stat-card"><div class="num">'+d.customers+'</div><div class="lbl">Customers</div></div><div class="stat-card green"><div class="num">R'+d.revenue+'</div><div class="lbl">Revenue</div></div><div class="stat-card red"><div class="num">R'+d.expenses+'</div><div class="lbl">Expenses</div></div></div>';
if(rC)rC.destroy();const c1=document.getElementById('revenueChart');
if(c1)rC=new Chart(c1,{type:'line',data:{labels:d.revenue_labels,datasets:[{data:d.revenue_data,borderColor:'#667eea',backgroundColor:'rgba(102,126,234,.15)',tension:.4,fill:true,borderWidth:3}]},options:{responsive:true,plugins:{legend:{display:false}}}});
if(jC)jC.destroy();const c2=document.getElementById('jobChart');
if(c2)jC=new Chart(c2,{type:'doughnut',data:{labels:['New','Progress','Done'],datasets:[{data:[d.jobs_new,d.jobs_progress,d.jobs_completed],backgroundColor:['#6b7280','#f59e0b','#10b981'],borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'bottom'}}}});
const ls=await jget('/api/inventory/low-stock');
document.getElementById('dashLowStock').innerHTML=ls.items.length?ls.items.map(i=>'<div class="list-item">⚠️ <strong>'+esc(i.name)+'</strong> — '+i.qty+' left</div>').join(''):'<p style="color:var(--text2)">✓ All stock OK</p>';
}catch(e){}
}

// ANALYTICS
async function loadAnalytics(){
try{const d=await jget('/api/analytics');
let h='<div class="stats-row"><div class="stat-card blue"><div class="num">R'+d.avg_invoice.toFixed(0)+'</div><div class="lbl">Avg Invoice</div></div><div class="stat-card green"><div class="num">R'+d.total_revenue.toFixed(0)+'</div><div class="lbl">Revenue</div></div></div>';
h+='<div class="stats-row"><div class="stat-card purple"><div class="num">'+d.invoices_count+'</div><div class="lbl">Invoices</div></div><div class="stat-card"><div class="num">'+d.jobs_count+'</div><div class="lbl">Jobs</div></div></div>';
if(d.top_services.length){h+='<div class="card"><h3>🔥 Top Job Types</h3>';d.top_services.forEach(s=>{h+='<div class="list-item"><strong>'+esc(s.name)+'</strong> <span style="color:var(--text2);float:right">'+s.count+'×</span></div>';});h+='</div>';}
if(d.top_customers.length){h+='<div class="card"><h3>⭐ Top Customers</h3>';d.top_customers.forEach(x=>{h+='<div class="list-item"><strong>'+esc(x.name)+'</strong> <span style="color:#10b981;float:right">R'+x.total.toFixed(0)+'</span></div>';});h+='</div>';}
h+='<div class="card"><h3>💼 This Month</h3><div class="list-item">Revenue: <strong>R'+d.month_revenue.toFixed(2)+'</strong></div><div class="list-item">Jobs: <strong>'+d.month_jobs+'</strong></div></div>';
document.getElementById('analyticsContent').innerHTML=h;
}catch(e){document.getElementById('analyticsContent').innerHTML='<div class="card"><p>Error</p></div>';}
}

// WARRANTY
async function loadWarranty(){
const c=document.getElementById('warrantyList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/warranty');
c.innerHTML=d.warranties.length?d.warranties.map(w=>{const cls=w.status==='active'?'ok':'warn';return '<div class="card"><h3>🎁 '+esc(w.vehicle)+' <span class="badge '+cls+'">'+w.status.toUpperCase()+'</span></h3><p><strong>'+esc(w.customer)+'</strong></p>'+(w.phone?'<p>📞 '+esc(w.phone)+'</p>':'')+'<div class="list-item">Expires: <strong>'+esc(w.expiry)+'</strong></div><div class="list-item">'+(w.days_left>0?'<span style="color:#10b981">'+w.days_left+' days remaining</span>':'<span style="color:#ef4444">Expired</span>')+'</div>'+(w.phone?'<div style="margin-top:8px"><button class="btn-sm wa" onclick="waWarranty(\''+esc(w.phone)+'\',\''+esc(w.customer)+'\',\''+esc(w.vehicle)+'\')">📱</button></div>':'')+'</div>';}).join(''):'<div class="card"><p>No warranties.</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
function waWarranty(phone,name,vehicle){const txt='Hi '+name+', your '+vehicle+' has an active warranty.';window.open('https://wa.me/'+phone.replace(/\D/g,'')+'?text='+encodeURIComponent(txt),'_blank');}

// TAX
async function loadTax(){
try{const d=await jget('/api/workshop');
document.getElementById('bcLogo').textContent=d.logo||'🔧';
document.getElementById('bcName').textContent=d.name||'My Workshop';
document.getElementById('bcPhone').textContent=d.phone||'(no phone set)';
document.getElementById('bcAddress').textContent=d.address||'(no address set)';
const n=new Date();const f=new Date(n.getFullYear(),n.getMonth(),1);
document.getElementById('taxFrom').value=f.toISOString().slice(0,10);
document.getElementById('taxTo').value=n.toISOString().slice(0,10);
}catch(e){}
}
function downloadTax(){const f=document.getElementById('taxFrom').value;const t=document.getElementById('taxTo').value;if(!f||!t){alert('Select both dates');return;}window.location.href='/api/export/tax?from_date='+f+'&to_date='+t;}
function printBizCard(){const w=window.open('','','width=600,height=400');w.document.write('<html><head><title>Card</title></head><body style="padding:20px;display:flex;justify-content:center;align-items:center;min-height:90vh">'+document.getElementById('bizCard').outerHTML+'</body></html>');w.document.close();setTimeout(()=>w.print(),500);}

// CODES
async function searchCodes(){
const q=document.getElementById('codeSearch').value;const c=document.getElementById('codeResults');
c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/fault-codes?search='+encodeURIComponent(q));c.dataset.loaded='1';
c.innerHTML=d.codes.length?d.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}

// JOBS
async function loadStaffDropdown(){
try{const d=await jget('/api/staff');
const sel=document.getElementById('jAssigned');
if(sel)sel.innerHTML='<option value="">— Assign staff —</option>'+d.staff.map(s=>'<option value="'+esc(s.name)+'">'+esc(s.name)+'</option>').join('');
}catch(e){}
}
async function loadJobs(){
const c=document.getElementById('jobList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/jobs');
c.innerHTML=d.jobs.length?d.jobs.map(j=>'<div class="card"><h3>Job #'+j.id+' <span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+j.status+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p>'+(j.assigned_to?'<p style="color:var(--text2);font-size:12px">👷 '+esc(j.assigned_to)+'</p>':'')+'<p style="color:var(--text2)">'+esc(j.complaint)+'</p><div style="margin-top:8px"><button class="btn-sm blue" onclick="upJob(\''+j.id+'\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="upJob(\''+j.id+'\',\'Completed\')">Done</button><button class="btn-sm wa" onclick="waJob(\''+j.id+'\')">📱</button><button class="btn-sm red" onclick="delJob(\''+j.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No jobs yet</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createJob(){
const c=document.getElementById('jCustomer').value.trim();
const v=document.getElementById('jVehicle').value.trim();
const comp=document.getElementById('jComplaint').value.trim();
if(!c||!v||!comp){alert('Fill customer, vehicle, complaint');return;}
await jpost('/api/jobs',{customer:c,phone:document.getElementById('jPhone').value,vehicle:v,registration:document.getElementById('jReg').value,complaint:comp,assigned_to:document.getElementById('jAssigned').value,warranty_months:parseInt(document.getElementById('jWarranty').value)||6});
['jCustomer','jPhone','jVehicle','jReg','jComplaint'].forEach(id=>document.getElementById(id).value='');
hideForm('jobForm');loadJobs();
}
async function upJob(id,s){await jput('/api/jobs/'+id,{status:s});loadJobs();}
async function delJob(id){if(!confirm('Delete?'))return;await fetch('/api/jobs/'+id,{method:'DELETE'});loadJobs();}
function waJob(id){jget('/api/jobs').then(d=>{const j=d.jobs.find(x=>x.id==id);if(!j)return;const txt='🔧 *Job #'+j.id+'*\n'+j.customer+'\n'+j.vehicle+'\nIssue: '+j.complaint+'\nStatus: '+j.status;window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// QUOTES
async function loadQuotes(){
const c=document.getElementById('quoteList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/quotes');
c.innerHTML=d.quotes.length?d.quotes.map(q=>'<div class="card"><h3>💬 Quote #'+q.id+'</h3><p><strong>'+esc(q.customer)+'</strong></p><p>'+esc(q.description)+'</p><div class="list-item"><strong>Total: R'+q.total.toFixed(2)+'</strong></div><div style="margin-top:10px"><button class="btn-sm green" onclick="acceptQuote(\''+q.id+'\')">→ Invoice</button><button class="btn-sm wa" onclick="waQuote(\''+q.id+'\')">📱</button><button class="btn-sm red" onclick="delQuote(\''+q.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No quotes</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createQuote(){
const c=document.getElementById('qCustomer').value.trim();
const d=document.getElementById('qDesc').value.trim();
if(!c||!d){alert('Required');return;}
await jpost('/api/quotes',{customer:c,vehicle:document.getElementById('qVehicle').value,description:d,labour:parseFloat(document.getElementById('qLabour').value)||0,parts:parseFloat(document.getElementById('qParts').value)||0});
['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id=>document.getElementById(id).value='');
hideForm('quoteForm');loadQuotes();
}
async function acceptQuote(id){if(!confirm('Convert to invoice?'))return;const r=await jpost('/api/quotes/'+id+'/accept',{});if(r.success){alert('Converted ✓');loadQuotes();}}
async function delQuote(id){if(!confirm('Delete?'))return;await fetch('/api/quotes/'+id,{method:'DELETE'});loadQuotes();}
function waQuote(id){jget('/api/quotes').then(d=>{const q=d.quotes.find(x=>x.id==id);if(!q)return;const txt='💬 *Quote #'+q.id+'*\n'+q.customer+'\nTotal: R'+q.total.toFixed(2);window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// APPOINTMENTS
async function loadAppts(){
const c=document.getElementById('apptList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/appointments');
const s=d.appointments.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));
c.innerHTML=s.length?s.map(a=>'<div class="card"><h3>📅 '+esc(a.date)+' at '+esc(a.time)+'</h3><p><strong>'+esc(a.customer)+'</strong></p>'+(a.vehicle?'<p>🚗 '+esc(a.vehicle)+'</p>':'')+'<div style="margin-top:8px"><button class="btn-sm wa" onclick="waAppt(\''+a.id+'\')">📱</button><button class="btn-sm red" onclick="delAppt(\''+a.id+'\')">Delete</button></div></div>').join(''):'<div class="card"><p>No appointments</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createAppt(){
const c=document.getElementById('aCustomer').value.trim();
const d=document.getElementById('aDate').value;
const t=document.getElementById('aTime').value;
if(!c||!d||!t){alert('Required');return;}
await jpost('/api/appointments',{customer:c,phone:document.getElementById('aPhone').value,vehicle:document.getElementById('aVehicle').value,service:document.getElementById('aService').value,date:d,time:t});
['aCustomer','aPhone','aVehicle','aService','aDate','aTime'].forEach(id=>document.getElementById(id).value='');
hideForm('apptForm');loadAppts();
}
async function delAppt(id){if(!confirm('Delete?'))return;await fetch('/api/appointments/'+id,{method:'DELETE'});loadAppts();}
function waAppt(id){jget('/api/appointments').then(d=>{const a=d.appointments.find(x=>x.id==id);if(!a)return;const txt='📅 Appointment\n'+a.customer+'\nDate: '+a.date+' at '+a.time;window.open('https://wa.me/'+(a.phone?a.phone.replace(/\D/g,'')+'?text=':'?text=')+encodeURIComponent(txt),'_blank');});}

// CUSTOMERS
async function loadCust(){
const c=document.getElementById('custList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/customers');
c.innerHTML=d.customers.length?d.customers.map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+'<div style="margin-top:8px"><button class="btn-sm wa" onclick="waCust(\''+esc(x.phone)+'\')">📱</button><button class="btn-sm red" onclick="delCust(\''+x.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No customers</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createCustomer(){
const n=document.getElementById('cName').value.trim();
const p=document.getElementById('cPhone').value.trim();
if(!n||!p){alert('Required');return;}
await jpost('/api/customers',{name:n,phone:p,email:document.getElementById('cEmail').value});
['cName','cPhone','cEmail'].forEach(id=>document.getElementById(id).value='');
hideForm('custForm');loadCust();
}
async function delCust(id){if(!confirm('Delete?'))return;await fetch('/api/customers/'+id,{method:'DELETE'});loadCust();}
function waCust(p){window.open('https://wa.me/'+p.replace(/\D/g,''),'_blank');}

// INVOICES
async function loadInv(){
const c=document.getElementById('invList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/invoices');
c.innerHTML=d.invoices.length?d.invoices.map(i=>'<div class="card"><h3>Invoice #'+i.id+'</h3><p><strong>'+esc(i.customer)+'</strong></p><p>'+esc(i.description)+'</p><div class="list-item"><strong>Total: R'+i.total.toFixed(2)+'</strong></div><div style="margin-top:8px"><button class="btn-sm wa" onclick="waInv(\''+i.id+'\')">📱</button><button class="btn-sm red" onclick="delInv(\''+i.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No invoices</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function createInvoice(){
const c=document.getElementById('iCustomer').value.trim();
const d=document.getElementById('iDesc').value.trim();
if(!c||!d){alert('Required');return;}
await jpost('/api/invoices',{customer:c,vehicle:document.getElementById('iVehicle').value,description:d,labour:parseFloat(document.getElementById('iLabour').value)||0,parts:parseFloat(document.getElementById('iParts').value)||0});
['iCustomer','iVehicle','iDesc','iLabour','iParts'].forEach(id=>document.getElementById(id).value='');
hideForm('invForm');loadInv();
}
async function delInv(id){if(!confirm('Delete?'))return;await fetch('/api/invoices/'+id,{method:'DELETE'});loadInv();}
function waInv(id){jget('/api/invoices').then(d=>{const i=d.invoices.find(x=>x.id==id);if(!i)return;const txt='💰 Invoice #'+i.id+'\n'+i.customer+'\nTotal: R'+i.total.toFixed(2);window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank');});}

// INVENTORY
async function loadInventory(){
const c=document.getElementById('inventoryList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/inventory');
c.innerHTML=d.items.length?d.items.map(i=>{const cls=i.qty<=i.min_qty?'warn':'ok';return '<div class="card"><h3>'+esc(i.name)+' <span class="badge '+cls+'">'+i.qty+'</span></h3><p style="font-family:monospace;font-size:12px">'+esc(i.part_number||'-')+'</p><div class="list-item">Cost: R'+i.cost_price.toFixed(2)+' | Sell: R'+i.sell_price.toFixed(2)+'</div>'+(i.qty<=i.min_qty?'<p style="color:#ef4444;font-size:12px;font-weight:700">⚠ Low stock</p>':'')+'<div style="margin-top:10px"><button class="btn-sm green" onclick="adjInv(\''+i.id+'\',1)">+1</button><button class="btn-sm red" onclick="adjInv(\''+i.id+'\',-1)">-1</button><button class="btn-sm gray" onclick="delInvItem(\''+i.id+'\')">Delete</button></div></div>';}).join(''):'<div class="card"><p>No inventory</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function addInventory(){
const n=document.getElementById('pName').value.trim();
if(!n){alert('Name required');return;}
await jpost('/api/inventory',{part_number:document.getElementById('pNumber').value,name:n,category:document.getElementById('pCategory').value,qty:parseInt(document.getElementById('pQty').value)||0,min_qty:parseInt(document.getElementById('pMinQty').value)||5,cost_price:parseFloat(document.getElementById('pCost').value)||0,sell_price:parseFloat(document.getElementById('pSell').value)||0,supplier:document.getElementById('pSupplier').value});
['pNumber','pName','pCategory','pQty','pMinQty','pCost','pSell','pSupplier'].forEach(id=>document.getElementById(id).value='');
hideForm('invItemForm');loadInventory();
}
async function adjInv(id,d){await jpost('/api/inventory/'+id+'/adjust',{delta:d});loadInventory();}
async function delInvItem(id){if(!confirm('Delete?'))return;await fetch('/api/inventory/'+id,{method:'DELETE'});loadInventory();}

// STAFF
async function loadStaff(){
const c=document.getElementById('staffList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/staff');
c.innerHTML=d.staff.length?d.staff.map(s=>'<div class="card"><h3>👷 '+esc(s.name)+'</h3>'+(s.role?'<p><strong>'+esc(s.role)+'</strong></p>':'')+(s.phone?'<p>📞 '+esc(s.phone)+'</p>':'')+'<p>Rate: R'+s.hourly_rate.toFixed(2)+'/hr</p><button class="btn-sm red" onclick="delStaff(\''+s.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>No staff</p></div>';
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function addStaff(){
const n=document.getElementById('stName').value.trim();
if(!n){alert('Name required');return;}
await jpost('/api/staff',{name:n,role:document.getElementById('stRole').value,phone:document.getElementById('stPhone').value,email:document.getElementById('stEmail').value,hourly_rate:parseFloat(document.getElementById('stRate').value)||150});
['stName','stRole','stPhone','stEmail'].forEach(id=>document.getElementById(id).value='');
hideForm('staffForm');loadStaff();
}
async function delStaff(id){if(!confirm('Delete?'))return;await fetch('/api/staff/'+id,{method:'DELETE'});loadStaff();}

// EXPENSES
async function loadExpenses(){
const c=document.getElementById('expenseList');c.innerHTML='<div class="loading">Loading...</div>';
try{const d=await jget('/api/expenses');
const total=d.expenses.reduce((s,x)=>s+parseFloat(x.amount||0),0);
let h='<div class="card" style="background:linear-gradient(135deg,#ef4444,#f87171);color:white"><h3 style="color:white">Total Expenses</h3><p style="font-size:26px;color:white;font-weight:800">R'+total.toFixed(2)+'</p></div>';
if(d.expenses.length){h+=d.expenses.map(e=>'<div class="card"><h3>'+esc(e.category)+' <span class="badge new">R'+parseFloat(e.amount).toFixed(2)+'</span></h3>'+(e.note?'<p>'+esc(e.note)+'</p>':'')+'<p style="font-size:11px;color:var(--text2)">'+esc(e.date)+'</p><button class="btn-sm red" onclick="delExpense(\''+e.id+'\')">Delete</button></div>').join('');}
else{h+='<div class="card"><p>No expenses</p></div>';}
c.innerHTML=h;
}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>';}
}
async function addExpense(){
const a=parseFloat(document.getElementById('exAmount').value)||0;
if(!a){alert('Amount required');return;}
await jpost('/api/expenses',{category:document.getElementById('exCat').value,amount:a,date:document.getElementById('exDate').value||new Date().toISOString().slice(0,10),note:document.getElementById('exNote').value});
['exAmount','exDate','exNote'].forEach(id=>document.getElementById(id).value='');
hideForm('expForm');loadExpenses();
}
async function delExpense(id){if(!confirm('Delete?'))return;await fetch('/api/expenses/'+id,{method:'DELETE'});loadExpenses();}

// SETTINGS
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

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    v = vin.strip().upper()
    if len(v) != 17:
        raise HTTPException(400, "VIN must be exactly 17 characters")
    wmi = v[:3]
    year_code = v[9]
    plant_code = v[10]
    mfr, country = WMI_DB.get(wmi, ("Unknown", "Unknown"))
    year = YEAR_CODES.get(year_code, "Unknown")
    plants = {"A":"Ingolstadt","B":"Brussels","C":"Changchun","D":"Dingolfing","E":"Eisenach",
              "F":"Flint","G":"Graz","H":"Hiroshima","J":"Jakarta","K":"Kuala Lumpur",
              "L":"Leipzig","M":"Madrid","N":"Nanjing","P":"Paris","R":"Regensburg",
              "S":"Stuttgart","T":"Toyota City","U":"Ulsan","V":"Valencia","W":"Wolfsburg",
              "Y":"Yokohama","Z":"Zwickau"}
    return {"vin":v,"manufacturer":mfr,"country":country,"year":year,
            "plant":plants.get(plant_code,"Unknown"),"serial":v[11:]}

@app.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message","")
    if not msg: raise HTTPException(400,"Message required")
    if not OPENAI_KEY: return {"reply":"AI not configured — set OPENAI_API_KEY"}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You are RamsTech AI, an expert mechanic assistant."},
                      {"role":"user","content":msg}], max_tokens=800, temperature=0.3)
        return {"reply": resp.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

@app.post("/api/diagnose/photo")
async def diagnose_photo(r: Request):
    d = await r.json()
    img = d.get("image_base64","")
    vehicle = d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured — set OPENAI_API_KEY"}
    if img.startswith("data:"): img = img.split(",",1)[1]
    if len(img) > 7_000_000: return {"success":False,"error":"Image too large (max 5MB)"}
    prompt = f"""You are an expert mechanic analyzing a vehicle photo.
Vehicle: {vehicle or 'Not specified'}

Identify visible mechanical problems (wear, damage, leaks, corrosion, broken parts, warning lights).
Respond ONLY with valid JSON in this exact format:
{{
  "problem": "Short description of the main issue",
  "description": "What you see in detail",
  "confidence": "High|Medium|Low",
  "possible_causes": ["Cause 1", "Cause 2", "Cause 3"],
  "diagnostic_steps": ["Step 1", "Step 2", "Step 3"],
  "safety_warnings": ["Warning 1", "Warning 2"]
}}"""
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[
                {"type":"text","text":prompt},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000, temperature=0.2, response_format={"type":"json_object"})
        parsed = json.loads(resp.choices[0].message.content)
        parsed["success"] = True
        return parsed
    except Exception as e:
        return {"success":False,"error":str(e)}

@app.post("/api/paint/match")
async def match_paint(r: Request):
    d = await r.json()
    img = d.get("image_base64","")
    vehicle = d.get("vehicle_info","")
    if not img: raise HTTPException(400,"Image required")
    if not OPENAI_KEY: return {"success":False,"error":"AI not configured"}
    if img.startswith("data:"): img = img.split(",",1)[1]
    if len(img) > 7_000_000: return {"success":False,"error":"Image too large (max 5MB)"}
    prompt = f"""You are an expert automotive paint technician analyzing a vehicle panel.
Vehicle: {vehicle or 'Not specified'}

Respond ONLY with valid JSON:
{{
  "detected_colour": {{
    "name": "Common colour name",
    "hex_code": "#RRGGBB",
    "finish": "Solid|Metallic|Pearl|Matte|Satin",
    "colour_family": "White|Black|Red|Blue|Silver|Grey|Green|Yellow|Orange|Brown"
  }},
  "confidence": "High|Medium|Low",
  "brand_codes": [
    {{"brand":"DuPont","code":"example","name":"formula"}},
    {{"brand":"PPG","code":"example","name":"formula"}},
    {{"brand":"Sikkens","code":"example","name":"formula"}}
  ],
  "mixing_formula": {{
    "base_colour": "Description",
    "toners": [{{"name":"Toner","parts":"X"}}],
    "reducer": "2:1"
  }},
  "safety_warnings": ["Warning 1", "Warning 2"]
}}"""
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[
                {"type":"text","text":prompt},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}","detail":"high"}}]}],
            max_tokens=2000, temperature=0.2, response_format={"type":"json_object"})
        parsed = json.loads(resp.choices[0].message.content)
        parsed["success"] = True
        return parsed
    except Exception as e:
        return {"success":False,"error":str(e)}

@app.get("/api/stats")
def stats():
    jobs = db_list("jobs"); invs = db_list("invoices"); custs = db_list("customers")
    appts = db_list("appointments"); exps = db_list("expenses")
    total = len(jobs)
    done = sum(1 for j in jobs if j.get("status")=="Completed")
    open_j = sum(1 for j in jobs if j.get("status")!="Completed")
    new_j = sum(1 for j in jobs if j.get("status")=="New")
    prog = sum(1 for j in jobs if j.get("status")=="In Progress")
    rev = sum(float(i.get("total",0)) for i in invs)
    exp = sum(float(e.get("amount",0)) for e in exps)
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
            "expenses":round(exp,2),
            "revenue_labels":labels,"revenue_data":data}

@app.get("/api/analytics")
def analytics():
    jobs = db_list("jobs"); invs = db_list("invoices"); custs = db_list("customers")
    total_rev = sum(float(i.get("total",0)) for i in invs)
    avg_inv = total_rev/len(invs) if invs else 0
    svc = {}
    for j in jobs:
        c = (j.get("complaint") or "").strip()[:30]
        if c: svc[c] = svc.get(c,0)+1
    top_services = [{"name":k,"count":v} for k,v in sorted(svc.items(), key=lambda x:-x[1])[:5]]
    cr = {}
    for i in invs:
        n = i.get("customer","")
        if n: cr[n] = cr.get(n,0)+float(i.get("total",0))
    top_customers = [{"name":k,"total":v} for k,v in sorted(cr.items(), key=lambda x:-x[1])[:5]]
    month_prefix = datetime.now().strftime("%Y-%m")
    month_rev = sum(float(i.get("total",0)) for i in invs if (i.get("created") or "").startswith(month_prefix))
    month_jobs = sum(1 for j in jobs if (j.get("created") or "").startswith(month_prefix))
    return {"total_revenue":total_rev,"avg_invoice":avg_inv,
            "invoices_count":len(invs),"jobs_count":len(jobs),
            "top_services":top_services,"top_customers":top_customers,
            "month_revenue":month_rev,"month_jobs":month_jobs}

@app.get("/api/warranty")
def warranty_list():
    items = []
    for j in db_list("jobs"):
        if j.get("status") == "Completed" and int(j.get("warranty_months",0) or 0) > 0:
            try:
                done = datetime.strptime((j.get("created") or "")[:10], "%Y-%m-%d")
                months = int(j["warranty_months"])
                year = done.year + (done.month + months - 1) // 12
                month = ((done.month + months - 1) % 12) + 1
                expiry = done.replace(year=year, month=month)
                days_left = (expiry - datetime.now()).days
                items.append({"id":j["id"],"customer":j.get("customer",""),
                              "vehicle":j.get("vehicle",""),"phone":j.get("phone",""),
                              "job_date":(j.get("created") or "")[:10],
                              "months":months,"expiry":expiry.strftime("%Y-%m-%d"),
                              "days_left":days_left,
                              "status":"active" if days_left > 0 else "expired"})
            except Exception: pass
    items.sort(key=lambda x: x["days_left"])
    return {"warranties": items}

@app.get("/api/export/tax")
def export_tax(from_date: str = None, to_date: str = None):
    o = io.StringIO(); w = csv.writer(o)
    w.writerow(["Date","Type","Description","Customer/Note","Amount (R)","VAT (R)"])
    for i in db_list("invoices"):
        d = (i.get("created") or "")[:10]
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"INCOME",i.get("description",""),i.get("customer",""),
                    f"{float(i.get('total',0)):.2f}", f"{float(i.get('vat',0)):.2f}"])
    for e in db_list("expenses"):
        d = e.get("date","")
        if from_date and d < from_date: continue
        if to_date and d > to_date: continue
        w.writerow([d,"EXPENSE",e.get("category",""),e.get("note",""),
                    f"-{float(e.get('amount',0)):.2f}","0.00"])
    invs = [i for i in db_list("invoices") if (not from_date or (i.get("created") or "")[:10] >= from_date) and (not to_date or (i.get("created") or "")[:10] <= to_date)]
    exps = [e for e in db_list("expenses") if (not from_date or e.get("date","") >= from_date) and (not to_date or e.get("date","") <= to_date)]
    total_income = sum(float(i.get("total",0)) for i in invs)
    total_exp = sum(float(e.get("amount",0)) for e in exps)
    w.writerow([])
    w.writerow(["","","TOTAL INCOME","",f"{total_income:.2f}",""])
    w.writerow(["","","TOTAL EXPENSES","",f"-{total_exp:.2f}",""])
    w.writerow(["","","NET PROFIT","",f"{total_income-total_exp:.2f}",""])
    o.seek(0)
    return StreamingResponse(iter([o.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=tax_report.csv"})

# JOBS
@app.get("/api/jobs")
def list_jobs(): return {"jobs": db_list("jobs")}

@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json()
    jid = str(uuid.uuid4())[:6]
    row = {"id":jid,"customer":d.get("customer",""),"phone":d.get("phone",""),
           "vehicle":d.get("vehicle",""),"registration":d.get("registration",""),
           "complaint":d.get("complaint",""),"assigned_to":d.get("assigned_to",""),
           "warranty_months":int(d.get("warranty_months",6)),
           "status":"New","created":now()}
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

# QUOTES
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

# APPOINTMENTS
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

# CUSTOMERS
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

# INVOICES
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

# INVENTORY
@app.get("/api/inventory")
def list_inv_items(): return {"items": db_list("inventory")}

@app.get("/api/inventory/low-stock")
def low_stock():
    items = db_list("inventory")
    return {"items":[{"id":i["id"],"name":i["name"],"qty":int(i.get("qty",0)),"min":int(i.get("min_qty",5))}
                     for i in items if int(i.get("qty",0)) <= int(i.get("min_qty",5))]}

@app.post("/api/inventory")
async def add_inv_item(r: Request):
    d = await r.json()
    iid = str(uuid.uuid4())[:6]
    row = {"id":iid,"part_number":d.get("part_number",""),"name":d.get("name",""),
           "category":d.get("category",""),"qty":int(d.get("qty",0)),
           "min_qty":int(d.get("min_qty",5)),"cost_price":float(d.get("cost_price",0)),
           "sell_price":float(d.get("sell_price",0)),"supplier":d.get("supplier",""),
           "created":today()}
    db_save("inventory", iid, row)
    return {"success":True,"item":row}

@app.post("/api/inventory/{iid}/adjust")
async def adjust_inv(iid: str, r: Request):
    d = await r.json()
    item = db_get("inventory", iid)
    if not item: raise HTTPException(404,"Item not found")
    item["qty"] = max(0, int(item.get("qty",0)) + int(d.get("delta",0)))
    db_save("inventory", iid, item)
    return {"success":True,"item":item}

@app.delete("/api/inventory/{iid}")
def delete_inv_item(iid: str):
    db_del("inventory", iid); return {"success":True}

# STAFF
@app.get("/api/staff")
def list_staff(): return {"staff": db_list("staff")}

@app.post("/api/staff")
async def add_staff(r: Request):
    d = await r.json()
    sid = str(uuid.uuid4())[:6]
    row = {"id":sid,"name":d.get("name",""),"role":d.get("role",""),
           "phone":d.get("phone",""),"email":d.get("email",""),
           "hourly_rate":float(d.get("hourly_rate",150)),"created":today()}
    db_save("staff", sid, row)
    return {"success":True,"staff":row}

@app.delete("/api/staff/{sid}")
def delete_staff(sid: str):
    db_del("staff", sid); return {"success":True}

# EXPENSES
@app.get("/api/expenses")
def list_exp(): return {"expenses": db_list("expenses")}

@app.post("/api/expenses")
async def add_exp(r: Request):
    d = await r.json()
    eid = str(uuid.uuid4())[:6]
    row = {"id":eid,"category":d.get("category","Other"),
           "amount":float(d.get("amount",0)),
           "date":d.get("date",today()),"note":d.get("note",""),"created":now()}
    db_save("expenses", eid, row)
    return {"success":True,"expense":row}

@app.delete("/api/expenses/{eid}")
def delete_exp(eid: str):
    db_del("expenses", eid); return {"success":True}

# WORKSHOP
@app.get("/api/workshop")
def get_ws(): return ws_get()

@app.post("/api/workshop")
async def save_ws(r: Request):
    d = await r.json(); ws_save(d); return {"success":True,"workshop":ws_get()}
