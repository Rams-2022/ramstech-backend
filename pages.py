# pages.py — RamsTech v10.0 (Complete Final UI)
HTML_PAGE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>RamsTech — AI Workshop Assistant</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
--bg:#f0f2f5;--card:#ffffff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;
--primary:#E65100;--input-bg:#f9fafb;
--grad1:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
--grad2:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);
--grad3:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);
--grad4:linear-gradient(135deg,#43e97b 0%,#38f9d7 100%);
--grad5:linear-gradient(135deg,#fa709a 0%,#fee140 100%);
--grad6:linear-gradient(135deg,#30cfd0 0%,#330867 100%);
}
body.dark{
--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--text2:#94a3b8;--border:#334155;
--input-bg:#0f172a;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:var(--bg);color:var(--text);padding-bottom:20px;
transition:background .3s,color .3s;
background-image:
radial-gradient(circle at 20% 20%,rgba(230,81,0,.08) 0%,transparent 40%),
radial-gradient(circle at 80% 60%,rgba(102,126,234,.08) 0%,transparent 40%),
radial-gradient(circle at 50% 90%,rgba(240,147,251,.06) 0%,transparent 40%);
background-attachment:fixed;
}
.header{
background:var(--grad1);color:white;padding:16px 14px 18px;
position:relative;overflow:hidden;
border-bottom-left-radius:24px;border-bottom-right-radius:24px;
box-shadow:0 6px 24px rgba(102,126,234,.35);
}
.header h1{
font-size:20px;display:flex;align-items:center;justify-content:center;gap:8px;
position:relative;z-index:1;font-weight:800;letter-spacing:.5px;
}
.header p{font-size:11px;opacity:.9;margin-top:3px;text-align:center;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:10px;display:flex;gap:6px;z-index:2}
.top-btns button, .lang-sel{
background:rgba(255,255,255,.25);border:none;color:white;padding:8px;
border-radius:10px;font-size:13px;cursor:pointer;backdrop-filter:blur(8px);
}
.lang-sel option{color:#333}
.home-container{padding:16px;max-width:900px;margin:0 auto}
.hero-card{background:var(--card);border-radius:20px;padding:16px;margin-bottom:16px;border:1px solid var(--border);}
.cat-title{font-size:13px;font-weight:700;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;margin:20px 4px 12px;}
.cat-grid{display:grid;grid-template-columns:1fr;gap:12px}
.cat-card{
border-radius:20px;padding:20px 18px;color:white;cursor:pointer;
position:relative;overflow:hidden;
box-shadow:0 8px 24px rgba(0,0,0,.15);transition:all .25s ease;
display:flex;align-items:center;gap:16px;
}
.cat-icon{font-size:38px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.2));min-width:50px;text-align:center;}
.cat-info{flex:1;}
.cat-name{font-size:17px;font-weight:800;margin-bottom:3px}
.cat-count{font-size:12px;opacity:.85;}
.cat-arrow{font-size:20px;opacity:.7;}
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:16px;padding:16px 12px;cursor:pointer;text-align:center;border:1px solid var(--border);position:relative;}
.tile-icon{font-size:32px;margin-bottom:8px;display:block}
.tile-label{font-size:12px;font-weight:700;}
.tile-accent{position:absolute;top:0;left:0;right:0;height:4px}
.bottom-nav{
position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);
display:flex;justify-content:space-around;padding:8px 4px;z-index:100;
}
.bnav-item{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px;}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase;}
.bnav-item.active .bnav-label{color:var(--primary)}
.bnav-item.active{background:rgba(230,81,0,.08)}
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;}
.panel-title{font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px;display:flex;align-items:center;gap:8px;}
.card{background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;border:1px solid var(--border);}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;}
.form-input{width:100%;padding:14px;border:1.5px solid var(--border);border-radius:12px;font-size:15px;margin-bottom:10px;background:var(--input-bg);color:var(--text);}
.btn{width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:var(--grad1);color:white;}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-success{background:var(--grad4)}
.btn-sm{padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;margin-right:5px;background:var(--primary);color:white;}
.badge{padding:3px 9px;border-radius:6px;font-size:11px;font-weight:700;color:white;}
.badge.high,.badge.critical{background:#ef4444}
.badge.medium{background:#f59e0b}
.badge.low,.badge.ok,.badge.completed{background:#10b981}
.back-btn{background:var(--grad6);color:white;border:none;padding:10px 16px;border-radius:12px;font-size:13px;font-weight:700;cursor:pointer;margin-bottom:16px;}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
</head>
<body>

<div class="header">
<h1><span class="logo" id="logoDisplay">🔧</span> <span id="wsNameDisplay">RAMSTECH</span></h1>
<p id="wsSubtitle">AI Workshop Assistant v10.0</p>
<div class="top-btns">
<select class="lang-sel" id="langSel" onchange="setLang()">
<option value="en">EN</option><option value="af">AF</option><option value="zu">ZU</option>
</select>
<button onclick="toggleTheme()" id="themeBtn">🌙</button>
</div>
</div>

<!-- HOME -->
<div id="home" class="panel active">
<div class="home-container">
<div class="hero-card"><div id="status">Checking backend...</div></div>
<div id="categoryView">
<div class="cat-title">Choose a Category</div>
<div class="cat-grid" id="categoryGrid"></div>
</div>
<div id="subView" style="display:none">
<button class="back-btn" onclick="backToCategories()">← Back to Categories</button>
<div class="cat-title" id="subTitle"></div>
<div class="tile-grid" id="subGrid"></div>
</div>
</div>
</div>

<!-- DASHBOARD -->
<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock Alerts</h3><div id="dashLowStock"></div></div>
<div class="card"><h3>🎁 Warranty Expiring</h3><div id="dashWarranty"></div></div>
</div>

<!-- AI CHAT -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox" style="height:calc(100vh - 280px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border);border-radius:16px;padding:14px;"><div class="msg ai">Hi! I'm RamsTech AI. Ask about repairs, diagnostics, or tools.</div></div>
<div class="input-row" style="display:flex;gap:8px;align-items:center;">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()" style="flex:1;padding:14px;border-radius:25px;border:1px solid var(--border);background:var(--input-bg);color:var(--text);">
<button class="mic-btn" id="micBtn" onclick="toggleMic()" style="padding:14px;border-radius:50%;background:var(--grad4);color:white;border:none;">🎤</button>
<button onclick="sendMsg()" style="padding:14px;border-radius:50%;background:var(--grad1);color:white;border:none;">➤</button>
</div>
</div>

<!-- FAULT CODES -->
<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code or description..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<!-- PROBLEMS -->
<div id="problems" class="panel">
<div class="panel-title">📖 Common Problems</div>
<input type="text" class="form-input" id="problemSearch" placeholder="🔍 Search problems..." oninput="filterProblems()">
<div id="problemList"><div class="loading">Loading...</div></div>
</div>

<!-- VIN -->
<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<button class="btn" onclick="openScanner()" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);">📷 Scan VIN / Barcode</button>
<input type="text" class="form-input" id="vinInput" placeholder="Enter 17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<!-- PAINT -->
<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card"><p style="font-size:13px">📸 Take a photo of a vehicle panel in good light. AI identifies colour and provides paint codes.</p></div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
</div>

<!-- PHOTO DIAG -->
<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card"><p style="font-size:13px">📸 Take a photo of a mechanical issue. AI diagnoses the problem.</p></div>
<input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>

<!-- JOBS -->
<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>

<button class="btn" onclick="openKanban()" style="background:linear-gradient(135deg,#7c3aed,#5b21b6);">📊 Open Kanban Board</button>
<button class="btn" onclick="openPhotoIntake()" style="background:linear-gradient(135deg,#8b5cf6,#6d28d9);">📸 New Job from Photo</button>

<button class="btn no-print" onclick="showJobForm()">+ New Job Card (Manual)</button>
<button class="btn btn-dark no-print" onclick="exportJobsCSV()">📥 Export CSV</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jobCustomer" placeholder="Customer name">
<input class="form-input" id="jobPhone" placeholder="Phone">
<input class="form-input" id="jobVehicle" placeholder="Vehicle (e.g. 2018 Toyota Hilux)">
<input class="form-input" id="jobVehicleReg" placeholder="Registration">
<input class="form-input" id="jobKm" type="number" placeholder="Odometer (km)">
<textarea class="form-input" id="jobComplaint" placeholder="Complaint / issue" rows="2"></textarea>
<select class="form-input" id="jobAssigned"><option value="">— Assign to staff —</option></select>
<input class="form-input" id="jobWarranty" type="number" placeholder="Warranty (months)" value="6">
<label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">📸 Photos</label>
<input type="file" id="jobPhotos" accept="image/*" multiple capture="environment" class="form-input" onchange="addJobPhotos(event)">
<div class="thumb-row" id="jobPhotoThumbs"></div>
<label style="font-size:13px;font-weight:700;margin-top:10px;display:block;margin-bottom:6px">✍️ Customer Signature</label>
<button class="btn btn-success" onclick="openSignature()">✍️ Capture Signature</button>
<div id="sigPreview" style="margin-bottom:10px"></div>
<button class="btn btn-success" onclick="createJob()" style="margin-top:10px">✓ Create Job</button>
<button class="btn btn-dark" onclick="hideJobForm()">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<!-- CUSTOMERS -->
<div id="customers" class="panel">
<div class="panel-title">👥 Customers</div>
<button class="btn no-print" onclick="showCustomerForm()">+ New Customer</button>
<button class="btn btn-dark no-print" onclick="exportCustomersCSV()">📥 Export CSV</button>
<div id="customerForm" style="display:none">
<div class="card">
<input class="form-input" id="custName" placeholder="Full name">
<input class="form-input" id="custPhone" placeholder="Phone number">
<input class="form-input" id="custEmail" placeholder="Email (optional)">
<input class="form-input" id="custAddress" placeholder="Address (optional)">
<button class="btn btn-success" onclick="createCustomer()">Save Customer</button>
<button class="btn btn-dark" onclick="hideCustomerForm()">Cancel</button>
</div>
</div>
<div id="customerList"><div class="loading">Loading...</div></div>
</div>

<!-- INVOICES -->
<div id="invoices" class="panel">
<div class="panel-title">💰 Invoices</div>
<button class="btn no-print" onclick="showInvoiceForm()">+ New Invoice</button>
<div id="invoiceForm" style="display:none">
<div class="card">
<input class="form-input" id="invCustomer" placeholder="Customer">
<input class="form-input" id="invVehicle" placeholder="Vehicle">
<input class="form-input" id="invDesc" placeholder="Description">
<input class="form-input" id="invLabour" type="number" placeholder="Labour (R)">
<input class="form-input" id="invParts" type="number" placeholder="Parts (R)">
<button class="btn btn-success" onclick="createInvoice()">Generate Invoice</button>
<button class="btn btn-dark" onclick="hideInvoiceForm()">Cancel</button>
</div>
</div>
<div id="invoiceList"><div class="loading">Loading...</div></div>
</div>

<!-- SETTINGS -->
<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>

<button class="btn" onclick="openStaffManager()" style="background:linear-gradient(135deg,#10b981,#059669);">👥 Manage Staff & PINs</button>

<div class="card">
<h3>🏢 Workshop Branding</h3>
<input class="form-input" id="wsLogo" placeholder="🔧" maxlength="4">
<input class="form-input" id="wsName" placeholder="Workshop name">
<input class="form-input" id="wsPhone" placeholder="Phone">
<input class="form-input" id="wsAddress" placeholder="Address">
<input class="form-input" id="wsEmail" placeholder="Email">
<input class="form-input" id="wsRate" type="number" placeholder="Labour rate R/hr">
<button class="btn btn-success" onclick="saveSettings()">Save Settings</button>
</div>
</div>

<!-- BOTTOM NAVIGATION -->
<div class="bottom-nav no-print">
  <div class="bnav-item active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
  <div class="bnav-item" onclick="showTab('dashboard',this)"><div class="bnav-icon">📊</div><div class="bnav-label">Dash</div></div>
  <div class="bnav-item" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
  <div class="bnav-item" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
  <div class="bnav-item" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>

<script>
// CATEGORIES
const CATEGORIES = {
  diagnostics: { name: 'Diagnostics', icon: '🔧', gradient: 'linear-gradient(135deg,#2196F3,#0d47a1)', items: [
      {icon:'🤖',label:'AI Chat',tab:'chat',color:'#3b82f6'},
      {icon:'📟',label:'Fault Codes',tab:'codes',color:'#ef4444'},
      {icon:'📖',label:'Problems',tab:'problems',color:'#f59e0b'},
      {icon:'🔍',label:'VIN Decoder',tab:'vin',color:'#8b5cf6'},
      {icon:'🎨',label:'Paint Match',tab:'paint',color:'#ec4899'},
      {icon:'📸',label:'Photo Diag',tab:'photo',color:'#06b6d4'}
  ]},
  workshop: { name: 'Workshop', icon: '📋', gradient: 'linear-gradient(135deg,#f59e0b,#dc2626)', items: [
      {icon:'📋',label:'Jobs',tab:'jobs',color:'#f59e0b'},
      {icon:'👥',label:'Customers',tab:'customers',color:'#10b981'},
      {icon:'💰',label:'Invoices',tab:'invoices',color:'#10b981'}
  ]},
  operations: { name: 'Operations', icon: '⚙️', gradient: 'linear-gradient(135deg,#10b981,#047857)', items: []},
  reference: { name: 'Reference', icon: '📚', gradient: 'linear-gradient(135deg,#8b5cf6,#4c1d95)', items: []},
  business: { name: 'Business', icon: '💼', gradient: 'linear-gradient(135deg,#1f2937,#4b5563)', items: [
      {icon:'📊',label:'Dashboard',tab:'dashboard',color:'#3b82f6'},
      {icon:'⚙️',label:'Settings',tab:'settings',color:'#6b7280'}
  ]}
};

document.getElementById('categoryGrid').innerHTML = Object.entries(CATEGORIES).map(([key, cat]) =>
  `<div class="cat-card" style="background:${cat.gradient}" onclick="openCategory('${key}')">
    <div class="cat-icon">${cat.icon}</div>
    <div class="cat-info"><div class="cat-name">${cat.name}</div><div class="cat-count">${cat.items.length} features</div></div>
    <div class="cat-arrow">›</div>
  </div>`
).join('');

function openCategory(key) {
  const cat = CATEGORIES[key];
  document.getElementById('categoryView').style.display = 'none';
  document.getElementById('subView').style.display = 'block';
  document.getElementById('subTitle').textContent = cat.icon + ' ' + cat.name;
  document.getElementById('subGrid').innerHTML = cat.items.map(item =>
    `<div class="tile" onclick="showTab('${item.tab}')">
      <div class="tile-accent" style="background:${item.color}"></div>
      <div class="tile-icon" style="color:${item.color}">${item.icon}</div>
      <div class="tile-label">${item.label}</div>
    </div>`
  ).join('');
  window.scrollTo(0, 0);
}

function backToCategories() {
  document.getElementById('subView').style.display = 'none';
  document.getElementById('categoryView').style.display = 'block';
  window.scrollTo(0, 0);
}

function showTab(name, el) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  
  var subV = document.getElementById('subView');
  var catV = document.getElementById('categoryView');
  if (subV) subV.style.display = 'none';
  if (catV) catV.style.display = 'block';

  var panel = document.getElementById(name);
  if (panel) panel.classList.add('active');
  
  if (el) {
    document.querySelectorAll('.bnav-item').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
  }
  window.scrollTo(0, 0);

  // AI ROBOT TOGGLE
  var fab = document.getElementById('aiFab');
  var diagTabs = ['chat','codes','problems','vin','paint','photo'];
  if (fab) {
    if (diagTabs.includes(name)) {
      fab.style.setProperty('display', 'flex', 'important');
      fab.style.setProperty('opacity', '1', 'important');
      fab.style.setProperty('visibility', 'visible', 'important');
    } else {
      fab.style.setProperty('display', 'none', 'important');
      fab.style.setProperty('opacity', '0', 'important');
      fab.style.setProperty('visibility', 'hidden', 'important');
    }
  }

  // Loaders
  const loaders = {
    codes: () => !document.getElementById('codeResults').dataset.loaded && searchCodes(),
    problems: () => !document.getElementById('problemList').dataset.loaded && loadProblems(),
    jobs: () => { loadJobs(); loadStaffDropdown(); },
    customers: loadCustomers, invoices: loadInvoices, settings: loadSettings, dashboard: loadDashboard
  };
  if (loaders[name]) try { loaders[name](); } catch (e) { console.error(e); }
}

// HELPERS
function toggleTheme() { document.body.classList.toggle('dark'); document.getElementById('themeBtn').textContent = document.body.classList.contains('dark') ? '☀️' : '🌙'; }
async function checkStatus() { try { await fetch('/health'); document.getElementById('status').innerHTML = '<span style="color:green;font-weight:bold;">✓ Backend Online</span>'; } catch (e) { document.getElementById('status').innerHTML = '<span style="color:red;font-weight:bold;">✗ Backend Offline</span>'; } }
checkStatus();
function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
async function jget(u) { const r = await fetch(u); return r.json(); }
async function jpost(u, b) { const r = await fetch(u, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); return r.json(); }
async function jput(u, b) { const r = await fetch(u, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); return r.json(); }
async function jdel(u) { const r = await fetch(u, {method:'DELETE'}); return r.json(); }

// API FETCHES
async function loadDashboard() { try { const d = await jget('/api/stats'); document.getElementById('dashStats').innerHTML = '<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Jobs</div></div><div class="stat-card purple"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open</div></div></div>'; } catch(e){} }
async function searchCodes() { try { const d = await jget('/api/fault-codes?search='+document.getElementById('codeSearch').value); document.getElementById('codeResults').dataset.loaded='1'; document.getElementById('codeResults').innerHTML = d.codes.map(x=>'<div class="card"><h3>'+x.code+'</h3><p>'+esc(x.description)+'</p></div>').join(''); } catch(e){} }
async function loadProblems() { try { const d = await jget('/api/problems'); document.getElementById('problemList').innerHTML = d.problems.map(x=>'<div class="card"><h3>'+esc(x.title)+'</h3></div>').join(''); } catch(e){} }
async function decodeVin() { try { const d = await jget('/api/vin/'+document.getElementById('vinInput').value); document.getElementById('vinResult').innerHTML = '<div class="card"><h3>'+d.manufacturer+'</h3><p>Year: '+d.year+'</p></div>'; } catch(e){} }
async function matchPaint() { alert('Paint API placeholder'); }
async function diagnosePhoto() { alert('Photo API placeholder'); }
async function loadJobs() { try { const d = await jget('/api/jobs'); document.getElementById('jobList').innerHTML = d.jobs.map(j=>'<div class="card"><h3>'+esc(j.customer)+'</h3><p>'+esc(j.status)+'</p></div>').join(''); } catch(e){} }
async function loadCustomers() { try { const d = await jget('/api/customers'); document.getElementById('customerList').innerHTML = d.customers.map(c=>'<div class="card"><h3>'+esc(c.name)+'</h3></div>').join(''); } catch(e){} }
async function loadInvoices() { try { const d = await jget('/api/invoices'); document.getElementById('invoiceList').innerHTML = d.invoices.map(i=>'<div class="card"><h3>Invoice #'+i.id+'</h3></div>').join(''); } catch(e){} }
async function loadSettings() { try { const d = await jget('/api/workshop'); document.getElementById('wsName').value = d.name||''; } catch(e){} }
function showJobForm(){document.getElementById('jobForm').style.display='block'} function hideJobForm(){document.getElementById('jobForm').style.display='none'}
function showCustomerForm(){document.getElementById('customerForm').style.display='block'} function hideCustomerForm(){document.getElementById('customerForm').style.display='none'}
function showInvoiceForm(){document.getElementById('invoiceForm').style.display='block'} function hideInvoiceForm(){document.getElementById('invoiceForm').style.display='none'}
function sendMsg(){}

// MODALS & FEATURES
async function openKanban() {
  let modal = document.getElementById('kanbanModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'kanbanModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:9999;padding:16px;overflow:auto;';
    modal.innerHTML = `
      <div style="background:var(--card);padding:20px;border-radius:16px;max-width:800px;margin:0 auto;color:var(--text);">
        <div style="display:flex;justify-content:space-between;margin-bottom:16px;">
          <h2 style="font-size:18px;font-weight:800;">📊 Kanban Board</h2>
          <button onclick="document.getElementById('kanbanModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button>
        </div>
        <div id="kanbanContent" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;">Loading...</div>
      </div>
    `;
    document.body.appendChild(modal);
  } else {
    modal.style.display = 'block';
  }
  
  const d = await jget('/api/jobs/kanban');
  let html = '';
  d.statuses.forEach(s => {
    const items = d.columns[s] || [];
    html += `<div style="background:var(--input-bg);border-radius:10px;padding:10px;border:1px solid var(--border);"><h4 style="font-size:12px;color:var(--text2);text-transform:uppercase;margin-bottom:8px;">${s} (${items.length})</h4>`;
    items.forEach(j => {
      html += `<div style="background:var(--card);padding:10px;border-radius:8px;margin-bottom:8px;border-left:4px solid var(--primary);"><h5 style="font-size:13px;margin-bottom:2px;">#${j.id} ${esc(j.customer)}</h5><p style="font-size:11px;color:var(--text2);">${esc(j.vehicle)}</p></div>`;
    });
    html += `</div>`;
  });
  document.getElementById('kanbanContent').innerHTML = html;
}

// PHOTO INTAKE
async function openPhotoIntake() {
  let modal = document.getElementById('photoIntakeModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'photoIntakeModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:9999;padding:16px;overflow:auto;';
    modal.innerHTML = `
      <div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:0 auto;color:var(--text);">
        <div style="display:flex;justify-content:space-between;margin-bottom:16px;">
          <h2 style="font-size:18px;font-weight:800;">📸 Photo Intake</h2>
          <button onclick="document.getElementById('photoIntakeModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button>
        </div>
        <div id="piStep1" class="card" style="background:var(--input-bg);">
          <p style="font-size:13px;color:var(--text2);margin-bottom:10px;">Take a photo of the VIN sticker, license plate, or dashboard. The AI will read the details and pre-fill the job card.</p>
          <input type="file" id="piImage" accept="image/*" capture="environment" class="form-input" onchange="processPhotoIntake(event)">
        </div>
        <div id="piStep2" style="display:none;">
          <div id="piPreview" style="margin-bottom:10px;"></div>
          <div id="piResult" class="card" style="background:var(--input-bg);">
            <h3 style="margin-bottom:10px;font-size:14px;">Vehicle Details</h3>
            <input type="text" id="piMake" class="form-input" placeholder="Make (e.g. Toyota)">
            <input type="text" id="piModel" class="form-input" placeholder="Model (e.g. Hilux)">
            <input type="text" id="piReg" class="form-input" placeholder="Registration">
            <input type="text" id="piVin" class="form-input" placeholder="VIN">
            <input type="number" id="piKm" class="form-input" placeholder="Odometer (km)">
            <button class="btn btn-success" onclick="createJobFromPhoto()">✓ Create Job Card</button>
          </div>
        </div>
        <div id="piLoading" style="display:none;text-align:center;padding:20px;color:var(--primary);">
          <div class="spinner" style="border:3px solid rgba(0,0,0,0.1);border-top-color:var(--primary);border-radius:50%;width:30px;height:30px;animation:spin 1s linear infinite;margin:0 auto 10px;"></div>
          Analyzing photo...
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  } else {
    modal.style.display = 'block';
    document.getElementById('piStep1').style.display = 'block';
    document.getElementById('piStep2').style.display = 'none';
    document.getElementById('piImage').value = '';
  }
}

async function processPhotoIntake(e) {
  const file = e.target.files[0];
  if (!file) return;

  document.getElementById('piStep1').style.display = 'none';
  document.getElementById('piLoading').style.display = 'block';

  const reader = new FileReader();
  reader.onload = async function(ev) {
    const img = new Image();
    img.onload = async function() {
      const canvas = document.createElement('canvas');
      let w = img.width, h = img.height;
      if (w > 1200) { h = (h * 1200) / w; w = 1200; }
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      const b64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

      document.getElementById('piPreview').innerHTML = '<img src="' + canvas.toDataURL('image/jpeg', 0.8) + '" style="width:100%;border-radius:12px;border:1px solid var(--border);">';

      try {
        const res = await jpost('/api/photo/intake', { image_base64: b64 });
        document.getElementById('piLoading').style.display = 'none';
        document.getElementById('piStep2').style.display = 'block';

        if (res.success) {
          document.getElementById('piMake').value = res.make || '';
          document.getElementById('piModel').value = res.model || '';
          document.getElementById('piReg').value = res.registration || '';
          document.getElementById('piVin').value = res.vin || '';
          document.getElementById('piKm').value = res.km || '';
        } else {
          alert('AI could not read the photo: ' + (res.error || 'Try a clearer photo'));
        }
      } catch (err) {
        document.getElementById('piLoading').style.display = 'none';
        document.getElementById('piStep2').style.display = 'block';
        alert('Network error: ' + err.message);
      }
    };
    img.src = ev.target.result;
  };
  reader.readAsDataURL(file);
}

async function createJobFromPhoto() {
  const make = document.getElementById('piMake').value.trim();
  const model = document.getElementById('piModel').value.trim();
  const reg = document.getElementById('piReg').value.trim();
  const vin = document.getElementById('piVin').value.trim();
  const km = document.getElementById('piKm').value.trim();

  const vehicle = (make + ' ' + model).trim();

  const payload = {
    customer: 'New Customer (Photo Intake)',
    phone: '',
    vehicle: vehicle || 'Unknown Vehicle',
    registration: reg || vin,
    km: parseInt(km) || 0,
    complaint: 'Vehicle checked in via Photo Intake',
    assigned_to: '',
    photos: [],
    signature: '',
    warranty_months: 6
  };

  try {
    const res = await jpost('/api/jobs', payload);
    if (res.success) {
      alert('✓ Job #' + res.job.id + ' created successfully!');
      document.getElementById('photoIntakeModal').style.display = 'none';
      showTab('jobs');
      loadJobs();
    }
  } catch (e) {
    alert('Error creating job: ' + e.message);
  }
}

// STAFF MANAGER
async function openStaffManager() {
  let modal = document.getElementById('staffModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'staffModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:9999;padding:16px;overflow:auto;';
    modal.innerHTML = `
      <div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:0 auto;color:var(--text);">
        <div style="display:flex;justify-content:space-between;margin-bottom:16px;">
          <h2 style="font-size:18px;font-weight:800;">👥 Manage Staff</h2>
          <button onclick="document.getElementById('staffModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button>
        </div>
        <div class="card" style="background:var(--input-bg);">
          <h3 style="margin-bottom:10px;font-size:14px;">Add New Staff</h3>
          <input type="text" id="newStaffName" class="form-input" placeholder="Full Name">
          <select id="newStaffRole" class="form-input">
            <option value="technician">Technician</option>
            <option value="manager">Manager</option>
            <option value="receptionist">Receptionist</option>
          </select>
          <input type="number" id="newStaffPin" class="form-input" placeholder="4-digit PIN" maxlength="4">
          <button class="btn btn-success" onclick="addNewStaff()">+ Add Staff Member</button>
        </div>
        <div id="staffList" style="margin-top:16px;">
          <div style="text-align:center;padding:20px;color:var(--text2);font-size:13px;">Loading...</div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  } else {
    modal.style.display = 'block';
  }
  loadStaffList();
}

async function loadStaffList() {
  const list = document.getElementById('staffList');
  list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text2);font-size:13px;">Loading...</div>';
  try {
    const d = await jget('/api/staff');
    if (!d.staff || d.staff.length === 0) {
      list.innerHTML = '<p style="text-align:center;color:var(--text2);font-size:13px;">No staff added yet.</p>';
      return;
    }
    let html = '';
    d.staff.forEach(s => {
      html += `
        <div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:12px;">
          <div>
            <strong style="font-size:14px;">${esc(s.name)}</strong><br>
            <span style="font-size:11px;color:var(--text2);">${esc(s.role || 'Staff')} • PIN: ${s.pin || 'None'}</span>
          </div>
          <button class="btn-sm red" onclick="deleteStaff('${s.id}')">Delete</button>
        </div>
      `;
    });
    list.innerHTML = html;
  } catch (e) {
    list.innerHTML = '<p style="color:red;text-align:center;">Error loading staff</p>';
  }
}

async function addNewStaff() {
  const name = document.getElementById('newStaffName').value.trim();
  const role = document.getElementById('newStaffRole').value;
  const pin = document.getElementById('newStaffPin').value.trim();
  
  if (!name || pin.length !== 4) {
    alert('Please enter a name and a 4-digit PIN');
    return;
  }

  try {
    const res = await jpost('/api/staff', { name: name, role: role, pin: pin });
    if (res.success) {
      await jpost('/api/staff/' + res.staff.id + '/pin', { pin: pin });
      document.getElementById('newStaffName').value = '';
      document.getElementById('newStaffPin').value = '';
      loadStaffList();
      loadStaffDropdown();
    }
  } catch (e) {
    alert('Error adding staff: ' + e.message);
  }
}

async function deleteStaff(id) {
  if (!confirm('Delete this staff member?')) return;
  try {
    await jdel('/api/staff/' + id);
    loadStaffList();
    loadStaffDropdown();
  } catch (e) {
    alert('Error deleting staff');
  }
}

// BARCODE SCANNER
let html5QrCode = null;
async function openScanner() {
  let modal = document.getElementById('scannerModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'scannerModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:#000;z-index:9999;padding:16px;';
    modal.innerHTML = `
      <div style="color:white;display:flex;justify-content:space-between;margin-bottom:10px;">
        <h2 style="font-size:18px;">📷 Scan Barcode</h2>
        <button onclick="closeScanner()" style="background:none;border:none;color:white;font-size:24px;">✕</button>
      </div>
      <div id="reader" style="width:100%;border-radius:12px;overflow:hidden;"></div>
    `;
    document.body.appendChild(modal);
  } else {
    modal.style.display = 'block';
  }

  if (!html5QrCode) {
    const script = document.createElement('script');
    script.src = "https://unpkg.com/html5-qrcode";
    script.onload = () => {
      html5QrCode = new Html5Qrcode("reader");
      html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: {width: 250, height: 150} }, (text) => {
        closeScanner();
        document.getElementById('vinInput').value = text;
        decodeVin();
      });
    };
    document.body.appendChild(script);
  } else {
    html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: {width: 250, height: 150} }, (text) => {
      closeScanner();
      document.getElementById('vinInput').value = text;
      decodeVin();
    });
  }
}

function closeScanner() {
  document.getElementById('scannerModal').style.display = 'none';
  if (html5QrCode) html5QrCode.stop().catch(e=>{});
}
</script>
</body>
</html>"""
