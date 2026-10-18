# pages.py — RamsTech v10.0
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

/* HEADER */
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

/* HOME / CATEGORY VIEW */
.home-container{padding:16px;max-width:900px;margin:0 auto}
.hero-card{background:var(--card);border-radius:20px;padding:16px;margin-bottom:16px;border:1px solid var(--border);}
.cat-title{font-size:13px;font-weight:700;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;margin:20px 4px 12px;}
.cat-grid{display:grid;grid-template-columns:1fr;gap:12px}
.cat-card{border-radius:20px;padding:20px 18px;color:white;cursor:pointer;display:flex;align-items:center;gap:16px;}
.cat-icon{font-size:38px;min-width:50px;text-align:center;}
.cat-info{flex:1;}
.cat-name{font-size:17px;font-weight:800;margin-bottom:3px}
.cat-count{font-size:12px;opacity:.85;}

/* TILE GRID */
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:16px;padding:16px 12px;cursor:pointer;text-align:center;border:1px solid var(--border);}
.tile-icon{font-size:32px;margin-bottom:8px;display:block}
.tile-label{font-size:12px;font-weight:700;}
.tile-accent{position:absolute;top:0;left:0;right:0;height:4px}

/* BOTTOM NAV */
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:8px 4px;z-index:100;}
.bnav-item{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px;}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase;}
.bnav-item.active .bnav-label{color:var(--primary)}
.bnav-item.active{background:rgba(230,81,0,.08)}

/* PANELS */
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;}
.panel-title{font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px;display:flex;align-items:center;gap:8px;}

/* CARDS & FORMS */
.card{background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;border:1px solid var(--border);}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;}
.form-input{width:100%;padding:14px;border:1.5px solid var(--border);border-radius:12px;font-size:15px;margin-bottom:10px;background:var(--input-bg);color:var(--text);}
.btn{width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:var(--grad1);color:white;}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-success{background:var(--grad4)}
.btn-sm{padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;margin-right:5px;background:var(--primary);color:white;}

/* BADGES */
.badge{padding:3px 9px;border-radius:6px;font-size:11px;font-weight:700;color:white;}
.badge.high,.badge.critical,.badge.outstanding{background:#ef4444}
.badge.medium{background:#f59e0b}
.badge.low,.badge.ok,.badge.completed,.badge.paid{background:#10b981}

/* BACK BUTTON */
.back-btn{background:var(--grad6);color:white;border:none;padding:10px 16px;border-radius:12px;font-size:13px;font-weight:700;cursor:pointer;margin-bottom:16px;}

/* PRINT */
@media print{
.header,.bottom-nav,.no-print,button,.btn{display:none!important}
.panel{display:block!important;padding:0}
.panel:not(.active){display:none!important}
body{background:white;color:black}
}
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
<div id="dashStats">Loading...</div>
</div>

<!-- AI CHAT -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! Ask me anything.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()">
<button onclick="sendMsg()">➤</button>
</div>
</div>

<!-- FAULT CODES -->
<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code..." oninput="searchCodes()">
<div id="codeResults">Loading...</div>
</div>

<!-- PROBLEMS -->
<div id="problems" class="panel">
<div class="panel-title">📖 Common Problems</div>
<input type="text" class="form-input" id="problemSearch" placeholder="🔍 Search problems..." oninput="filterProblems()">
<div id="problemList">Loading...</div>
</div>

<!-- VIN -->
<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<input type="text" class="form-input" id="vinInput" placeholder="Enter VIN" maxlength="17">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<!-- PAINT -->
<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info">
<input type="file" id="paintImage" accept="image/*" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint</button>
<div id="paintResult"></div>
</div>

<!-- PHOTO DIAG -->
<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<input type="file" id="photoImage" accept="image/*" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze</button>
<div id="photoResult"></div>
</div>

<!-- JOBS -->
<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<div id="jobList">Loading...</div>
</div>

<!-- SETTINGS (More) -->
<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
<div class="card"><button class="btn btn-success" onclick="saveSettings()">Save Settings</button></div>
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
// ═══════════════════════════════════
// CATEGORIES
// ═══════════════════════════════════
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
      {icon:'📋',label:'Jobs',tab:'jobs',color:'#f59e0b'}
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
  </div>`
).join('');

function openCategory(key) {
  const cat = CATEGORIES[key];
  document.getElementById('categoryView').style.display = 'none';
  document.getElementById('subView').style.display = 'block';
  document.getElementById('subTitle').textContent = cat.icon + ' ' + cat.name;
  document.getElementById('subGrid').innerHTML = cat.items.map(item =>
    `<div class="tile" onclick="showTab('${item.tab}')">
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

// ═══════════════════════════════════
// TAB NAVIGATION (Flawless AI Robot Toggle)
// ═══════════════════════════════════
const DIAG_TABS = ['chat','codes','problems','vin','paint','photo','wiring','obd','bulbs','batteries','tyres','fuses','service','inspect','boltcalc','torque'];

function showTab(name, el) {
  // 1. Hide all panels
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  
  // 2. Reset Home internal views
  var subV = document.getElementById('subView');
  var catV = document.getElementById('categoryView');
  if (subV) subV.style.display = 'none';
  if (catV) catV.style.display = 'block';

  // 3. Show target panel
  var panel = document.getElementById(name);
  if (panel) panel.classList.add('active');
  
  // 4. Update bottom nav
  if (el) {
    document.querySelectorAll('.bnav-item').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
  }
  window.scrollTo(0, 0);

  // 5. TOGGLE AI ROBOT (No intervals, no flashing)
  var fab = document.getElementById('aiFab');
  if (fab) {
    if (DIAG_TABS.includes(name)) {
      fab.classList.add('show');
    } else {
      fab.classList.remove('show');
    }
  }
}

// THEME & HELPERS
function toggleTheme() {
  document.body.classList.toggle('dark');
  const d = document.body.classList.contains('dark');
  localStorage.setItem('theme', d ? 'dark' : 'light');
  document.getElementById('themeBtn').textContent = d ? '☀️' : '🌙';
}
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
  document.getElementById('themeBtn').textContent = '☀️';
}

async function checkStatus() {
  try { await fetch('/health'); document.getElementById('status').innerHTML = '<span class="badge ok">✓ Backend Online</span>'; }
  catch (e) { document.getElementById('status').innerHTML = '<span class="badge high">✗ Backend Offline</span>'; }
}
checkStatus();

// DUMMY LOADERS (To prevent errors in this stripped version)
function sendMsg(){}
function searchCodes(){}
function filterProblems(){}
function decodeVin(){}
function previewPaint(){}
function matchPaint(){}
function previewDiag(){}
function diagnosePhoto(){}
function saveSettings(){}
</script>
</body>
</html>"""
