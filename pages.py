# pages.py — RamsTech v10.0 (Phase A - Modern UI)
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
--primary:#E65100;--input-bg:#f8fafc;
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

/* HEADER & NAV */
.header{
background:var(--grad1);color:white;padding:16px 14px 18px;
position:relative;overflow:hidden;
border-bottom-left-radius:24px;border-bottom-right-radius:24px;
box-shadow:0 6px 24px rgba(102,126,234,.35);
}
.header h1{font-size:20px;display:flex;align-items:center;justify-content:center;gap:8px;position:relative;z-index:1;font-weight:800;letter-spacing:.5px;}
.header p{font-size:11px;opacity:.9;margin-top:3px;text-align:center;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:10px;display:flex;gap:6px;z-index:2}
.top-btns button, .lang-sel{background:rgba(255,255,255,.25);border:none;color:white;padding:8px;border-radius:10px;font-size:13px;cursor:pointer;backdrop-filter:blur(8px);}
.lang-sel option{color:#333}

/* HOME */
.home-container{padding:16px;max-width:900px;margin:0 auto}
.hero-card{background:var(--card);border-radius:20px;padding:16px;margin-bottom:16px;border:1px solid var(--border);box-shadow:0 2px 10px rgba(0,0,0,0.02);}
.cat-title{font-size:13px;font-weight:700;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;margin:20px 4px 12px;}
.cat-grid{display:grid;grid-template-columns:1fr;gap:12px}
.cat-card{
border-radius:20px;padding:20px 18px;color:white;cursor:pointer;
position:relative;overflow:hidden;
box-shadow:0 8px 24px rgba(0,0,0,.15);transition:all .25s ease;
display:flex;align-items:center;gap:16px;
}
.cat-card:active{transform:scale(.97);box-shadow:0 4px 12px rgba(0,0,0,.2)}
.cat-icon{font-size:38px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.2));min-width:50px;text-align:center;}
.cat-info{flex:1;}
.cat-name{font-size:17px;font-weight:800;margin-bottom:3px}
.cat-count{font-size:12px;opacity:.85;}
.cat-arrow{font-size:20px;opacity:.7;}

/* TILES */
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:16px;padding:16px 12px;cursor:pointer;text-align:center;border:1px solid var(--border);position:relative;transition:transform .1s;box-shadow:0 2px 8px rgba(0,0,0,0.02);}
.tile:active{transform:scale(.95);}
.tile-icon{font-size:32px;margin-bottom:8px;display:block}
.tile-label{font-size:12px;font-weight:700;}
.tile-accent{position:absolute;top:0;left:0;right:0;height:4px}

/* BOTTOM NAV */
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:8px 4px;z-index:100;box-shadow:0 -4px 20px rgba(0,0,0,0.04);}
.bnav-item{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px;transition:all .2s;}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase;}
.bnav-item.active .bnav-label{color:var(--primary)}
.bnav-item.active{background:rgba(230,81,0,.08)}

/* PANELS & ANIMATIONS */
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;animation:slideUp .3s cubic-bezier(.16,1,.3,1)}
@keyframes slideUp {from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.panel-title{font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px;display:flex;align-items:center;gap:8px;}

/* CARDS */
.card{background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;border:1px solid var(--border);transition:box-shadow .2s;box-shadow:0 2px 10px rgba(0,0,0,0.03);}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;}

/* ═══════════════════════════════════════════════════════ */
/* MODERN INPUTS & FORMS                                  */
/* ═══════════════════════════════════════════════════════ */
input, textarea, select {
  width: 100%;
  padding: 16px;
  border: 1.5px solid var(--border);
  border-radius: 14px; /* Smoother radius */
  font-size: 16px; /* Prevents iOS auto-zoom */
  background: var(--input-bg);
  color: var(--text);
  font-family: inherit;
  transition: all 0.2s ease;
  -webkit-appearance: none; /* Removes default iOS styling */
  appearance: none;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

/* The Focus Ring (Glows when tapped) */
input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(230, 81, 0, 0.15), inset 0 2px 4px rgba(0,0,0,0.02);
  background: var(--card);
}

/* Custom Arrow for Select Dropdowns */
select {
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23666%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 16px top 50%;
  background-size: 12px auto;
  padding-right: 40px; /* Make room for arrow */
}
body.dark select {
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%2394a3b8%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
}

/* ═══════════════════════════════════════════════════════ */
/* MODERN BUTTONS                                         */
/* ═══════════════════════════════════════════════════════ */
.btn{
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  margin-bottom: 12px;
  background: var(--grad1);
  color: white;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  letter-spacing: 0.3px;
}
.btn:active{
  transform: scale(0.96); /* Presses in */
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937);box-shadow: 0 4px 12px rgba(75,85,99,0.3);}
.btn-dark:active{box-shadow: 0 2px 6px rgba(75,85,99,0.2);}
.btn-success{background:var(--grad4);box-shadow: 0 4px 12px rgba(67,233,123,0.3);}
.btn-success:active{box-shadow: 0 2px 6px rgba(67,233,123,0.2);}

.btn-sm{
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  margin-right: 6px;
  margin-bottom: 6px;
  background: var(--primary);
  color: white;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 2px 8px rgba(230, 81, 0, 0.25);
}
.btn-sm:active{transform: scale(0.92); box-shadow: 0 1px 4px rgba(230, 81, 0, 0.2);}
.btn-sm.whatsapp{background:#25D366;box-shadow: 0 2px 8px rgba(37,211,102,0.3);}

.badge{padding:4px 10px;border-radius:8px;font-size:11px;font-weight:700;color:white;letter-spacing:.5px;}
.badge.high,.badge.critical,.badge.outstanding{background:#ef4444}
.badge.medium{background:#f59e0b}
.badge.low,.badge.ok,.badge.completed,.badge.paid{background:#10b981}

.back-btn{background:var(--grad6);color:white;border:none;padding:12px 18px;border-radius:12px;font-size:14px;font-weight:700;cursor:pointer;margin-bottom:16px;box-shadow:0 4px 12px rgba(48,207,208,.3);}

/* CHAT BUBBLES */
.chat-box{height:calc(100vh - 280px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border);border-radius:16px;padding:14px;display:flex;flex-direction:column;background:var(--input-bg);}
.msg{padding:12px 16px;border-radius:18px;margin-bottom:10px;max-width:85%;line-height:1.45;font-size:14px;animation:msgIn .2s ease;}
@keyframes msgIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.msg.user{background:var(--grad1);color:white;margin-left:auto;border-bottom-right-radius:4px;box-shadow:0 4px 12px rgba(102,126,234,.2);}
.msg.ai{background:var(--card);border:1px solid var(--border);margin-right:auto;border-bottom-left-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,.05);}

/* TOAST NOTIFICATIONS */
#toastWrap{position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:99999;display:flex;flex-direction:column;gap:8px;pointer-events:none;}
.toast{background:#111;color:#fff;padding:12px 20px;border-radius:30px;font-size:14px;font-weight:600;box-shadow:0 8px 24px rgba(0,0,0,.3);animation:toastIn .3s cubic-bezier(.16,1,.3,1);display:flex;align-items:center;gap:8px;}
.toast.success{background:#10b981;}
.toast.error{background:#ef4444;}
@keyframes toastIn{from{opacity:0;transform:translateY(-20px) scale(.9)}to{opacity:1;transform:translateY(0) scale(1)}}
.toast.out{animation:toastOut .2s ease forwards;}
@keyframes toastOut{to{opacity:0;transform:translateY(-20px) scale(.9)}}

@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
</style>
</head>
<body>

<!-- TOAST CONTAINER -->
<div id="toastWrap"></div>

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
<div id="dashStats" style="margin-bottom:16px;"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
</div>

<!-- AI CHAT -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox">
  <div class="msg ai">Hi! I'm RamsTech AI. Ask about repairs, diagnostics, or tools.</div>
</div>
<div class="input-row" style="display:flex;gap:8px;align-items:center;">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()" style="flex:1;border-radius:25px;">
<button class="mic-btn" id="micBtn" onclick="toggleMic()" style="padding:14px;border-radius:50%;background:var(--grad4);color:white;border:none;box-shadow:0 4px 12px rgba(67,233,123,.3);">🎤</button>
<button onclick="sendMsg()" style="padding:14px;border-radius:50%;background:var(--grad1);color:white;border:none;box-shadow:0 4px 12px rgba(102,126,234,.3);">➤</button>
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

<!-- JOBS -->
<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<button class="btn" onclick="openKanban()" style="background:linear-gradient(135deg,#7c3aed,#5b21b6);">📊 Open Kanban Board</button>
<button class="btn" onclick="openPhotoIntake()" style="background:linear-gradient(135deg,#8b5cf6,#6d28d9);">📸 New Job from Photo</button>
<button class="btn no-print" onclick="showJobForm()">+ New Job Card (Manual)</button>
<div id="jobForm" style="display:none">
<div class="card">
<input type="text" class="form-input" id="jobCustomer" placeholder="Customer name">
<input type="text" class="form-input" id="jobPhone" placeholder="Phone">
<input type="text" class="form-input" id="jobVehicle" placeholder="Vehicle (e.g. 2018 Toyota Hilux)">
<input type="text" class="form-input" id="jobVehicleReg" placeholder="Registration">
<input type="number" class="form-input" id="jobKm" placeholder="Odometer (km)">
<textarea class="form-input" id="jobComplaint" placeholder="Complaint / issue" rows="2"></textarea>
<select class="form-input" id="jobAssigned"><option value="">— Assign to staff —</option></select>
<button class="btn btn-success" onclick="createJob()">✓ Create Job</button>
<button class="btn btn-dark" onclick="hideJobForm()">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<!-- CUSTOMERS -->
<div id="customers" class="panel">
<div class="panel-title">👥 Customers</div>
<button class="btn no-print" onclick="showCustomerForm()">+ New Customer</button>
<div id="customerForm" style="display:none">
<div class="card">
<input type="text" class="form-input" id="custName" placeholder="Full name">
<input type="text" class="form-input" id="custPhone" placeholder="Phone number">
<input type="text" class="form-input" id="custEmail" placeholder="Email (optional)">
<input type="text" class="form-input" id="custAddress" placeholder="Address (optional)">
<button class="btn btn-success" onclick="createCustomer()">Save Customer</button>
<button class="btn btn-dark" onclick="hideCustomerForm()">Cancel</button>
</div>
</div>
<div id="customerList"><div class="loading">Loading...</div></div>
</div>

<!-- INVOICES -->
<div id="invoices" class="panel">
<div class="panel-title">💰 Invoices</div>
<div id="invoiceList"><div class="loading">Loading...</div></div>
</div>

<!-- PARTS SEARCH -->
<div id="parts" class="panel">
<div class="panel-title">🔩 Parts Search</div>
<input type="text" class="form-input" id="partsSearch" placeholder="🔍 Search part number or name..." oninput="searchParts()">
<div id="partsResults"><div class="loading">Type to search...</div></div>
</div>

<!-- PURCHASE ORDERS -->
<div id="purchase" class="panel">
<div class="panel-title">🛒 Purchase Orders</div>
<button class="btn" onclick="showPOForm()">+ New Purchase Order</button>
<div id="poForm" style="display:none">
<div class="card">
<input type="text" class="form-input" id="poSupplier" placeholder="Supplier Name">
<textarea class="form-input" id="poItems" placeholder="Items (one per line)" rows="3"></textarea>
<button class="btn btn-success" onclick="createPO()">Save PO</button>
<button class="btn btn-dark" onclick="hidePOForm()">Cancel</button>
</div>
</div>
<div id="poList"><div class="loading">Loading...</div></div>
</div>

<!-- SETTINGS -->
<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
<button class="btn" onclick="openStaffManager()" style="background:linear-gradient(135deg,#10b981,#059669);">👥 Manage Staff & PINs</button>
<div class="card">
<h3>🏢 Workshop Branding</h3>
<input type="text" class="form-input" id="wsLogo" placeholder="🔧" maxlength="4">
<input type="text" class="form-input" id="wsName" placeholder="Workshop name">
<input type="text" class="form-input" id="wsPhone" placeholder="Phone">
<input type="text" class="form-input" id="wsAddress" placeholder="Address">
<input type="text" class="form-input" id="wsEmail" placeholder="Email">
<input type="number" class="form-input" id="wsRate" placeholder="Labour rate R/hr">
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
// TOAST NOTIFICATIONS (Replaces alert)
function toast(msg, type='success') {
  const wrap = document.getElementById('toastWrap');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${type === 'success' ? '✓' : '⚠'}</span> ${msg}`;
  wrap.appendChild(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, 3000);
}

// CATEGORIES
const CATEGORIES = {
  diagnostics: { name: 'Diagnostics', icon: '🔧', gradient: 'linear-gradient(135deg,#2196F3,#0d47a1)', items: [
      {icon:'🤖',label:'AI Chat',tab:'chat',color:'#3b82f6'},
      {icon:'📟',label:'Fault Codes',tab:'codes',color:'#ef4444'},
      {icon:'📖',label:'Problems',tab:'problems',color:'#f59e0b'},
      {icon:'🔍',label:'VIN Decoder',tab:'vin',color:'#8b5cf6'}
  ]},
  workshop: { name: 'Workshop', icon: '📋', gradient: 'linear-gradient(135deg,#f59e0b,#dc2626)', items: [
      {icon:'📋',label:'Jobs',tab:'jobs',color:'#f59e0b'},
      {icon:'👥',label:'Customers',tab:'customers',color:'#10b981'},
      {icon:'💰',label:'Invoices',tab:'invoices',color:'#10b981'}
  ]},
  operations: { name: 'Operations', icon: '⚙️', gradient: 'linear-gradient(135deg,#10b981,#047857)', items: [
      {icon:'🛒',label:'Purchase',tab:'purchase',color:'#3b82f6'}
  ]},
  reference: { name: 'Reference', icon: '📚', gradient: 'linear-gradient(135deg,#8b5cf6,#4c1d95)', items: [
      {icon:'🔩',label:'Parts Search',tab:'parts',color:'#6b7280'}
  ]},
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
  var diagTabs = ['chat','codes','problems','vin'];
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
    customers: loadCustomers, invoices: loadInvoices, settings: loadSettings, dashboard: loadDashboard,
    parts: searchParts, purchase: loadPOs
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

// DASHBOARD CHARTS
let rC = null, jC = null;
async function loadDashboard() { 
  try { 
    const d = await jget('/api/stats'); 
    document.getElementById('dashStats').innerHTML = `
      <div class="stats-row">
        <div class="stat-card blue"><div class="num">${d.jobs_total}</div><div class="lbl">Jobs</div></div>
        <div class="stat-card purple"><div class="num">${d.jobs_open}</div><div class="lbl">Open</div></div>
        <div class="stat-card green"><div class="num">R${d.revenue}</div><div class="lbl">Revenue</div></div>
      </div>`;
    if (rC) rC.destroy();
    rC = new Chart(document.getElementById('revenueChart'), {
      type: 'line', data: { labels: d.revenue_labels, datasets: [{ data: d.revenue_data, borderColor: '#667eea', backgroundColor: 'rgba(102,126,234,.15)', fill: true, tension: .4 }] }, options: { responsive: true, plugins: { legend: { display: false } } }
    });
    if (jC) jC.destroy();
    jC = new Chart(document.getElementById('jobChart'), {
      type: 'doughnut', data: { labels: ['New', 'Progress', 'Done'], datasets: [{ data: [d.jobs_new, d.jobs_progress, d.jobs_completed], backgroundColor: ['#6b7280', '#f59e0b', '#10b981'] }] }, options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
  } catch(e){ console.error(e); }
}

// AI CHAT & VOICE
let rec = null, isRec = false;
function toggleMic() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) { toast('Voice not supported', 'error'); return; }
  if (!rec) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    rec = new SR(); rec.lang = 'en-ZA';
    rec.onresult = e => { document.getElementById('chatInput').value = e.results[0][0].transcript; resetMic(); sendMsg(); };
    rec.onerror = resetMic; rec.onend = resetMic;
  }
  function resetMic() { isRec = false; document.getElementById('micBtn').style.background = 'var(--grad4)'; document.getElementById('micBtn').textContent = '🎤'; }
  if (isRec) { rec.stop(); resetMic(); }
  else { try { rec.start(); isRec = true; document.getElementById('micBtn').style.background = 'var(--grad2)'; document.getElementById('micBtn').textContent = '⏹'; } catch (e) { toast(e.message, 'error'); } }
}

async function sendMsg() {
  const i = document.getElementById('chatInput');
  const m = i.value.trim();
  if (!m) return;
  const b = document.getElementById('chatBox');
  
  b.innerHTML += '<div class="msg user">' + esc(m) + '</div>';
  i.value = '';
  b.scrollTop = b.scrollHeight;
  
  const typId = 'typ_' + Date.now();
  b.innerHTML += `<div class="msg ai" id="${typId}">Thinking...</div>`;
  b.scrollTop = b.scrollHeight;
  
  try {
    const d = await jpost('/api/chat', {message:m});
    document.getElementById(typId).outerHTML = '<div class="msg ai">' + esc(d.reply) + '</div>';
  } catch (e) {
    document.getElementById(typId).outerHTML = '<div class="msg ai">Error connecting to AI.</div>';
  }
  b.scrollTop = b.scrollHeight;
}

// JOBS
async function loadJobs() {
  const c = document.getElementById('jobList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/jobs');
    if (!d.jobs.length) { c.innerHTML = '<div class="card"><p>No jobs yet. Tap + New Job Card to create one.</p></div>'; return; }
    
    const jobs = d.jobs.reverse();
    c.innerHTML = jobs.map(j => {
      let badgeClass = 'new';
      if (j.status === 'Completed' || j.status === 'Invoiced') badgeClass = 'completed';
      if (j.status === 'In Progress' || j.status === 'Diagnosing') badgeClass = 'medium';
      if (j.status === 'Awaiting Parts' || j.status === 'Awaiting Approval') badgeClass = 'high';
      
      let cost = j.total ? `<div style="margin-top:10px;padding:10px;background:var(--input-bg);border-radius:10px;font-size:13px;"><strong>💰 Total: R${j.total.toFixed(2)}</strong></div>` : '';
      let as = j.assigned_to ? `<p style="color:var(--text2);font-size:12px;">👷 ${esc(j.assigned_to)}</p>` : '';
      
      const statuses = ["New", "Diagnosing", "Awaiting Approval", "Awaiting Parts", "In Progress", "QC", "Ready for Pickup", "Completed", "Invoiced"];
      let statusOpts = statuses.map(s => `<option value="${s}" ${j.status === s ? 'selected' : ''}>${s}</option>`).join('');
      
      let invBtn = j.total ? `<button class="btn-sm green" onclick="generateInvoice('${j.id}')">Invoice</button>` : '';
      let waBtn = `<button class="btn-sm whatsapp" onclick="shareJobWhatsApp('${j.id}')">📱</button>`;
      
      return `
        <div class="card" id="job-${j.id}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <h3>Job #${j.id} <span class="badge ${badgeClass}">${esc(j.status)}</span></h3>
              <p><strong>${esc(j.customer)}</strong></p>
              <p>🚗 ${esc(j.vehicle)} ${j.registration ? '(' + esc(j.registration) + ')' : ''}</p>
              ${as}
            </div>
            <div style="text-align:right;">
              <p style="font-size:11px;color:var(--text2);">${esc(j.created)}</p>
            </div>
          </div>
          
          <p style="color:var(--text2);font-size:13px;margin-top:8px;">${esc(j.complaint)}</p>
          ${cost}
          
          <div class="no-print" style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            <select class="form-input" style="margin:0;flex:1;padding:8px;font-size:12px;width:auto;" onchange="updateJobStatus('${j.id}', this.value)">
              ${statusOpts}
            </select>
            <button class="btn-sm purple" onclick="setCost('${j.id}')">💰 Cost</button>
            ${invBtn}
            ${waBtn}
          </div>
        </div>
      `;
    }).join('');
  } catch (e) { c.innerHTML = '<div class="card"><p>Error loading jobs</p></div>'; }
}

async function shareJobWhatsApp(id) {
  const d = await jget('/api/jobs');
  const j = d.jobs.find(x => x.id == id);
  if (!j) return;
  const txt = `🔧 *Job #${j.id} Update*\n\nHi ${j.customer},\nYour vehicle (${j.vehicle}) is currently: *${j.status}*.\n\nIssue: ${j.complaint}`;
  window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
}

async function updateJobStatus(jid, newStatus) {
  try {
    await jput('/api/jobs/' + jid, { status: newStatus });
    toast('Status updated to ' + newStatus);
    loadJobs(); 
    if (document.getElementById('kanbanModal') && document.getElementById('kanbanModal').style.display === 'block') openKanban();
  } catch (e) { toast('Failed to update status', 'error'); }
}

async function setCost(id) {
  const h = prompt('Labour hours:', '1');
  if (h === null) return;
  const p = prompt('Parts cost (R):', '0');
  if (p === null) return;
  const rate = 450; 
  try {
    await jpost('/api/jobs/' + id + '/cost', { labour_hours: parseFloat(h), labour_rate: rate, parts_cost: parseFloat(p) });
    toast('Cost updated successfully');
    loadJobs();
  } catch(e) { toast('Error setting cost', 'error'); }
}

async function generateInvoice(jid) {
  try {
    const d = await jget('/api/jobs');
    const job = d.jobs.find(x => x.id == jid);
    if (!job) return;
    const payload = { customer: job.customer, vehicle: job.vehicle, description: job.complaint, labour: job.labour_cost || 0, parts: job.parts_cost || 0 };
    const res = await jpost('/api/invoices', payload);
    if (res.success) {
      toast('Invoice #' + res.invoice.id + ' generated!');
      showTab('invoices'); loadInvoices();
    }
  } catch(e) { toast('Error generating invoice', 'error'); }
}

// CUSTOMERS
function showCustomerForm(){document.getElementById('customerForm').style.display='block'} 
function hideCustomerForm(){document.getElementById('customerForm').style.display='none'}
async function createCustomer() {
  const name = document.getElementById('custName').value.trim();
  const phone = document.getElementById('custPhone').value.trim();
  if (!name || !phone) { toast('Name and phone required', 'error'); return; }
  await jpost('/api/customers', { name: name, phone: phone, email: document.getElementById('custEmail').value, address: document.getElementById('custAddress').value });
  document.getElementById('custName').value = ''; document.getElementById('custPhone').value = '';
  hideCustomerForm(); loadCustomers();
  toast('Customer added');
}
async function loadCustomers() { 
  try { 
    const d = await jget('/api/customers'); 
    document.getElementById('customerList').innerHTML = d.customers.map(c=>`
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div><h3>👤 ${esc(c.name)}</h3><p>📞 ${esc(c.phone)}</p>${c.email ? `<p>📧 ${esc(c.email)}</p>` : ''}</div>
          <button class="btn-sm whatsapp" onclick="window.open('https://wa.me/${c.phone.replace(/\D/g,'')}', '_blank')">📱 Chat</button>
        </div>
      </div>`).join('') || '<div class="card"><p>No customers yet</p></div>'; 
  } catch(e){} 
}

// INVOICES
async function loadInvoices() { 
  try { 
    const d = await jget('/api/invoices'); 
    document.getElementById('invoiceList').innerHTML = d.invoices.map(i=>{
      const isPaid = i.paid;
      const badge = isPaid ? 'paid' : 'outstanding';
      const payBtn = !isPaid ? `<button class="btn-sm blue" onclick="window.location.href='/pay/${i.id}'">💳 Pay Now</button>` : '';
      return `
        <div class="card">
          <h3>Invoice #${i.id} <span class="badge ${badge}">${badge.toUpperCase()}</span></h3>
          <p><strong>${esc(i.customer)}</strong></p>
          <p style="font-size:20px; font-weight:800; color:var(--primary); margin: 8px 0;">R ${i.total.toFixed(2)}</p>
          <div style="display:flex; gap:5px; flex-wrap:wrap;">
            <button class="btn-sm green" onclick="window.open('/api/workflow/invoice-html/${i.id}', '_blank')">🖨 PDF</button>
            <button class="btn-sm whatsapp" onclick="shareInvoiceWhatsApp('${i.id}', '${esc(i.customer)}', '${i.total}')">📱 Share</button>
            ${payBtn}
          </div>
        </div>`;
    }).join('') || '<div class="card"><p>No invoices yet</p></div>'; 
  } catch(e){} 
}

function shareInvoiceWhatsApp(id, customer, total) {
  const txt = `Hi ${customer}, your invoice #${id} is ready. Total due: R${total}. You can view and pay it here: https://ramstech.onrender.com/pay/${id}`;
  window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
}

// SETTINGS
async function loadSettings() { try { const d = await jget('/api/workshop'); document.getElementById('wsName').value = d.name||''; } catch(e){} }
async function saveSettings() {
  const p = { name: document.getElementById('wsName').value, logo: document.getElementById('wsLogo').value, phone: document.getElementById('wsPhone').value, address: document.getElementById('wsAddress').value, email: document.getElementById('wsEmail').value, labour_rate: parseFloat(document.getElementById('wsRate').value) || 450 };
  await jpost('/api/workshop', p); toast('Settings saved!');
}

// FAULT CODES & PROBLEMS
async function searchCodes() { try { const d = await jget('/api/fault-codes?search='+document.getElementById('codeSearch').value); document.getElementById('codeResults').dataset.loaded='1'; document.getElementById('codeResults').innerHTML = d.codes.map(x=>'<div class="card"><h3>'+x.code+'</h3><p>'+esc(x.description)+'</p></div>').join(''); } catch(e){} }
async function loadProblems() { try { const d = await jget('/api/problems'); document.getElementById('problemList').innerHTML = d.problems.map(x=>'<div class="card"><h3>'+esc(x.title)+'</h3></div>').join(''); } catch(e){} }

// VIN
async function decodeVin() { try { const d = await jget('/api/vin/'+document.getElementById('vinInput').value); document.getElementById('vinResult').innerHTML = '<div class="card"><h3>'+d.manufacturer+'</h3><p>Year: '+d.year+'</p></div>'; } catch(e){} }

// PARTS SEARCH & PO
async function searchParts() {
  const q = document.getElementById('partsSearch').value;
  if (!q) return;
  const c = document.getElementById('partsResults');
  c.innerHTML = '<div class="loading">Searching...</div>';
  try {
    const d = await jget('/api/parts-search?q=' + encodeURIComponent(q));
    c.innerHTML = d.results.length ? d.results.map(p=>`<div class="card"><h3>${esc(p.name)}</h3><p style="font-size:12px;font-family:monospace;">${esc(p.part_number)}</p><p>Price: R${p.sell_price.toFixed(2)}</p></div>`).join('') : '<div class="card"><p>No parts found</p></div>';
  } catch(e) { c.innerHTML = 'Error searching'; }
}
function showPOForm(){document.getElementById('poForm').style.display='block'} 
function hidePOForm(){document.getElementById('poForm').style.display='none'}
async function createPO() {
  const sup = document.getElementById('poSupplier').value; const items = document.getElementById('poItems').value;
  if (!sup || !items) { toast('Supplier and items required', 'error'); return; }
  try { await jpost('/api/po/create', { supplier: sup, items: items }); hidePOForm(); loadPOs(); toast('PO Created'); } catch(e) { toast('Error creating PO', 'error'); }
}
async function loadPOs() { try { const d = await jget('/api/po/list'); document.getElementById('poList').innerHTML = d.purchase_orders.length ? d.purchase_orders.map(p=>`<div class="card"><h3>PO #${p.po_number}</h3><p>${esc(p.supplier)}</p><p>Status: <b>${p.status}</b></p></div>`).join('') : '<div class="card"><p>No purchase orders</p></div>'; } catch(e){} }

// MODALS (Kanban, Photo, Staff, Scanner)
async function openKanban() {
  let modal = document.getElementById('kanbanModal');
  if (!modal) {
    modal = document.createElement('div'); modal.id = 'kanbanModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:9999;padding:16px;overflow:auto;';
    modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:800px;margin:0 auto;color:var(--text);"><div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:800;">📊 Kanban Board</h2><button onclick="document.getElementById('kanbanModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button></div><div id="kanbanContent" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;">Loading...</div></div>`;
    document.body.appendChild(modal);
  } else { modal.style.display = 'block'; }
  const d = await jget('/api/jobs/kanban'); let html = '';
  d.statuses.forEach(s => {
    const items = d.columns[s] || [];
    html += `<div style="background:var(--input-bg);border-radius:10px;padding:10px;border:1px solid var(--border);"><h4 style="font-size:12px;color:var(--text2);text-transform:uppercase;margin-bottom:8px;">${s} (${items.length})</h4>`;
    items.forEach(j => { html += `<div style="background:var(--card);padding:10px;border-radius:8px;margin-bottom:8px;border-left:4px solid var(--primary);"><h5 style="font-size:13px;margin-bottom:2px;">#${j.id} ${esc(j.customer)}</h5><p style="font-size:11px;color:var(--text2);">${esc(j.vehicle)}</p></div>`; });
    html += `</div>`;
  });
  document.getElementById('kanbanContent').innerHTML = html;
}

async function openPhotoIntake() {
  let modal = document.getElementById('photoIntakeModal');
  if (!modal) {
    modal = document.createElement('div'); modal.id = 'photoIntakeModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:9999;padding:16px;overflow:auto;';
    modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:0 auto;color:var(--text);"><div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:800;">📸 Photo Intake</h2><button onclick="document.getElementById('photoIntakeModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button></div><div id="piStep1" class="card" style="background:var(--input-bg);"><p style="font-size:13px;color:var(--text2);margin-bottom:10px;">Take a photo of the VIN sticker, license plate, or dashboard.</p><input type="file" id="piImage" accept="image/*" capture="environment" class="form-input" onchange="processPhotoIntake(event)"></div><div id="piStep2" style="display:none;"><div id="piPreview" style="margin-bottom:10px;"></div><div id="piResult" class="card" style="background:var(--input-bg);"><h3 style="margin-bottom:10px;font-size:14px;">Vehicle Details</h3><input type="text" id="piMake" class="form-input" placeholder="Make"><input type="text" id="piModel" class="form-input" placeholder="Model"><input type="text" id="piReg" class="form-input" placeholder="Registration"><input type="text" id="piVin" class="form-input" placeholder="VIN"><input type="number" id="piKm" class="form-input" placeholder="Odometer"><button class="btn btn-success" onclick="createJobFromPhoto()">✓ Create Job Card</button></div></div><div id="piLoading" style="display:none;text-align:center;padding:20px;color:var(--primary);"><div class="spinner" style="border:3px solid rgba(0,0,0,0.1);border-top-color:var(--primary);border-radius:50%;width:30px;height:30px;animation:spin 1s linear infinite;margin:0 auto 10px;"></div>Analyzing photo...</div></div>`;
    document.body.appendChild(modal);
  } else { modal.style.display = 'block'; document.getElementById('piStep1').style.display = 'block'; document.getElementById('piStep2').style.display = 'none'; document.getElementById('piImage').value = ''; }
}

async function processPhotoIntake(e) {
  const file = e.target.files[0]; if (!file) return;
  document.getElementById('piStep1').style.display = 'none'; document.getElementById('piLoading').style.display = 'block';
  const reader = new FileReader();
  reader.onload = async function(ev) {
    const img = new Image();
    img.onload = async function() {
      const canvas = document.createElement('canvas'); let w = img.width, h = img.height;
      if (w > 1200) { h = (h * 1200) / w; w = 1200; } canvas.width = w; canvas.height = h; canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      const b64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
      document.getElementById('piPreview').innerHTML = '<img src="' + canvas.toDataURL('image/jpeg', 0.8) + '" style="width:100%;border-radius:12px;border:1px solid var(--border);">';
      try {
        const res = await jpost('/api/photo/intake', { image_base64: b64 });
        document.getElementById('piLoading').style.display = 'none'; document.getElementById('piStep2').style.display = 'block';
        if (res.success) {
          document.getElementById('piMake').value = res.make || ''; document.getElementById('piModel').value = res.model || '';
          document.getElementById('piReg').value = res.registration || ''; document.getElementById('piVin').value = res.vin || ''; document.getElementById('piKm').value = res.km || '';
        } else { toast('AI could not read: ' + (res.error || 'Try clearer'), 'error'); }
      } catch (err) { document.getElementById('piLoading').style.display = 'none'; document.getElementById('piStep2').style.display = 'block'; toast('Network error', 'error'); }
    }; img.src = ev.target.result;
  }; reader.readAsDataURL(file);
}
async function createJobFromPhoto() {
  const make = document.getElementById('piMake').value.trim(); const model = document.getElementById('piModel').value.trim();
  const reg = document.getElementById('piReg').value.trim(); const vin = document.getElementById('piVin').value.trim(); const km = document.getElementById('piKm').value.trim();
  const payload = { customer: 'New Customer (Photo)', phone: '', vehicle: (make + ' ' + model).trim(), registration: reg || vin, km: parseInt(km) || 0, complaint: 'Photo Intake', assigned_to: '', photos: [], signature: '', warranty_months: 6 };
  try { const res = await jpost('/api/jobs', payload); if (res.success) { toast('Job created!'); document.getElementById('photoIntakeModal').style.display = 'none'; showTab('jobs'); loadJobs(); } } catch (e) { toast('Error', 'error'); }
}

// STAFF MANAGER
async function openStaffManager() {
  let modal = document.getElementById('staffModal');
  if (!modal) {
    modal = document.createElement('div'); modal.id = 'staffModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:9999;padding:16px;overflow:auto;';
    modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:0 auto;color:var(--text);"><div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:800;">👥 Manage Staff</h2><button onclick="document.getElementById('staffModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button></div><div class="card" style="background:var(--input-bg);"><h3 style="margin-bottom:10px;font-size:14px;">Add New Staff</h3><input type="text" id="newStaffName" class="form-input" placeholder="Full Name"><select id="newStaffRole" class="form-input"><option value="technician">Technician</option><option value="manager">Manager</option></select><input type="number" id="newStaffPin" class="form-input" placeholder="4-digit PIN" maxlength="4"><button class="btn btn-success" onclick="addNewStaff()">+ Add Staff</button></div><div id="staffList" style="margin-top:16px;"><div style="text-align:center;padding:20px;color:var(--text2);font-size:13px;">Loading...</div></div></div>`;
    document.body.appendChild(modal);
  } else { modal.style.display = 'block'; }
  loadStaffList();
}
async function loadStaffList() {
  const list = document.getElementById('staffList'); list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text2);">Loading...</div>';
  try {
    const d = await jget('/api/staff');
    if (!d.staff || d.staff.length === 0) { list.innerHTML = '<p style="text-align:center;color:var(--text2);font-size:13px;">No staff added yet.</p>'; return; }
    list.innerHTML = d.staff.map(s => `<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:12px;"><div><strong style="font-size:14px;">${esc(s.name)}</strong><br><span style="font-size:11px;color:var(--text2);">${esc(s.role)} • PIN: ${s.pin || 'None'}</span></div><button class="btn-sm red" onclick="deleteStaff('${s.id}')">Delete</button></div>`).join('');
  } catch (e) { list.innerHTML = '<p style="color:red;text-align:center;">Error loading staff</p>'; }
}
async function addNewStaff() {
  const name = document.getElementById('newStaffName').value.trim(); const role = document.getElementById('newStaffRole').value; const pin = document.getElementById('newStaffPin').value.trim();
  if (!name || pin.length !== 4) { toast('Enter name and 4-digit PIN', 'error'); return; }
  try {
    const res = await jpost('/api/staff', { name: name, role: role, pin: pin });
    if (res.success) { await jpost('/api/staff/' + res.staff.id + '/pin', { pin: pin }); document.getElementById('newStaffName').value = ''; document.getElementById('newStaffPin').value = ''; loadStaffList(); loadStaffDropdown(); toast('Staff added'); }
  } catch (e) { toast('Error', 'error'); }
}
async function deleteStaff(id) { if (!confirm('Delete?')) return; try { await jdel('/api/staff/' + id); loadStaffList(); loadStaffDropdown(); toast('Staff removed'); } catch (e) {} }
async function loadStaffDropdown() { try { const d = await jget('/api/staff'); const sel = document.getElementById('jobAssigned'); sel.innerHTML = '<option value="">— Assign to staff —</option>' + (d.staff||[]).map(s => '<option value="' + esc(s.name) + '">' + esc(s.name) + '</option>').join(''); } catch (e) {} }

// BARCODE SCANNER
let html5QrCode = null;
async function openScanner() {
  let modal = document.getElementById('scannerModal');
  if (!modal) {
    modal = document.createElement('div'); modal.id = 'scannerModal';
    modal.style.cssText = 'display:block;position:fixed;inset:0;background:#000;z-index:9999;padding:16px;';
    modal.innerHTML = `<div style="color:white;display:flex;justify-content:space-between;margin-bottom:10px;"><h2 style="font-size:18px;">📷 Scan Barcode</h2><button onclick="closeScanner()" style="background:none;border:none;color:white;font-size:24px;">✕</button></div><div id="reader" style="width:100%;border-radius:12px;overflow:hidden;"></div>`;
    document.body.appendChild(modal);
  } else { modal.style.display = 'block'; }
  if (!html5QrCode) {
    const script = document.createElement('script'); script.src = "https://unpkg.com/html5-qrcode";
    script.onload = () => {
      html5QrCode = new Html5Qrcode("reader");
      html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: {width: 250, height: 150} }, (text) => { closeScanner(); document.getElementById('vinInput').value = text; decodeVin(); });
    }; document.body.appendChild(script);
  } else { html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: {width: 250, height: 150} }, (text) => { closeScanner(); document.getElementById('vinInput').value = text; decodeVin(); }); }
}
function closeScanner() { document.getElementById('scannerModal').style.display = 'none'; if (html5QrCode) html5QrCode.stop().catch(e=>{}); }
</script>
</body>
</html>"""
