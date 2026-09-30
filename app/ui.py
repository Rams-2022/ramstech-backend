# app/ui.py — Polished HTML/CSS/JS interface

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#E65100">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#f0f2f5; --card:#fff; --text:#1a1a2e; --text2:#6b7280; --border:#e5e7eb;
  --primary:#E65100; --primary-light:#FFF3E0;
  --success:#10b981; --danger:#ef4444; --warning:#f59e0b; --info:#3b82f6; --purple:#8b5cf6;
  --grad1:linear-gradient(135deg,#667eea,#764ba2);
  --grad-success:linear-gradient(135deg,#43e97b,#38f9d7);
  --grad-danger:linear-gradient(135deg,#ef4444,#f87171);
  --grad-primary:linear-gradient(135deg,#E65100,#FF9800);
  --shadow-sm:0 2px 6px rgba(0,0,0,.04);
  --shadow:0 4px 12px rgba(0,0,0,.06);
  --shadow-lg:0 8px 24px rgba(0,0,0,.12);
}
body.dark{
  --bg:#0f172a; --card:#1e293b; --text:#f1f5f9; --text2:#94a3b8; --border:#334155;
  --primary-light:#78350f;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
html,body{overflow-x:hidden}
body{
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:var(--bg);color:var(--text);
  padding-bottom:90px;
  transition:background .3s,color .3s;
  background-image:
    radial-gradient(circle at 20% 20%,rgba(230,81,0,.06) 0%,transparent 45%),
    radial-gradient(circle at 80% 60%,rgba(102,126,234,.06) 0%,transparent 45%),
    radial-gradient(circle at 50% 90%,rgba(240,147,251,.04) 0%,transparent 40%);
  background-attachment:fixed;
}

/* ═══ HEADER ═══ */
.header{
  background:var(--grad1);color:white;
  padding:18px 16px 22px;text-align:center;position:relative;overflow:hidden;
  border-bottom-left-radius:26px;border-bottom-right-radius:26px;
  box-shadow:0 6px 24px rgba(102,126,234,.35);
}
.header::before{content:'';position:absolute;top:-60%;right:-25%;width:320px;height:320px;
  background:radial-gradient(circle,rgba(255,255,255,.15),transparent 70%);border-radius:50%}
.header::after{content:'';position:absolute;bottom:-70%;left:-15%;width:220px;height:220px;
  background:radial-gradient(circle,rgba(255,255,255,.1),transparent 70%);border-radius:50%}
.header h1{font-size:21px;font-weight:800;letter-spacing:.5px;
  display:flex;align-items:center;justify-content:center;gap:10px;position:relative;z-index:1}
.header h1 .logo{font-size:28px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.2))}
.header p{font-size:11px;opacity:.9;margin-top:4px;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:12px;display:flex;gap:6px;z-index:2}
.top-btns button{
  background:rgba(255,255,255,.25);border:none;color:white;padding:8px 10px;
  border-radius:11px;font-size:15px;cursor:pointer;backdrop-filter:blur(8px);
  transition:all .2s;
}
.top-btns button:active{transform:scale(.9);background:rgba(255,255,255,.4)}

/* ═══ PANELS ═══ */
.panel{display:none;padding:16px;max-width:820px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;animation:fadeSlide .35s ease}
@keyframes fadeSlide{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.panel-title{
  font-size:21px;font-weight:800;color:var(--primary);margin-bottom:18px;
  display:flex;align-items:center;gap:8px;
}

/* ═══ TILES ═══ */
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{
  background:var(--card);border-radius:18px;padding:22px 12px;cursor:pointer;
  text-align:center;box-shadow:var(--shadow);border:1px solid var(--border);
  transition:transform .15s ease,box-shadow .15s ease;
  position:relative;overflow:hidden;
}
.tile::before{content:'';position:absolute;inset:0;opacity:0;
  background:linear-gradient(135deg,rgba(230,81,0,.06),transparent);
  transition:opacity .2s}
.tile:active{transform:scale(.96);box-shadow:var(--shadow-lg)}
.tile:active::before{opacity:1}
.tile-icon{font-size:38px;margin-bottom:8px;display:block;filter:drop-shadow(0 2px 4px rgba(0,0,0,.08))}
.tile-label{font-size:12.5px;font-weight:700;color:var(--text)}

/* ═══ CARDS ═══ */
.card{
  background:var(--card);padding:16px;border-radius:18px;margin-bottom:12px;
  box-shadow:var(--shadow);border:1px solid var(--border);
  animation:fadeSlide .25s ease;
}
.card h3{color:var(--primary);margin-bottom:10px;font-size:15px;font-weight:800;
  display:flex;align-items:center;gap:6px}
.card p{margin:5px 0;font-size:13px;line-height:1.55;color:var(--text)}

/* ═══ INPUTS ═══ */
.form-input{
  width:100%;padding:14px 16px;border:1.5px solid var(--border);
  border-radius:13px;font-size:15px;margin-bottom:10px;
  background:var(--card);color:var(--text);font-family:inherit;
  transition:border-color .2s,box-shadow .2s;
}
.form-input:focus{outline:none;border-color:var(--primary);
  box-shadow:0 0 0 3px rgba(230,81,0,.1)}
textarea.form-input{resize:vertical;min-height:60px}
select.form-input{appearance:none;background-image:url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%236b7280' d='M6 8L0 0h12z'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 16px center;padding-right:36px}

/* ═══ BUTTONS ═══ */
.btn{
  width:100%;padding:15px;border:none;border-radius:13px;font-size:15px;
  font-weight:800;cursor:pointer;margin-bottom:10px;letter-spacing:.3px;
  background:var(--grad1);color:white;
  box-shadow:0 4px 14px rgba(102,126,234,.28);
  transition:transform .15s,box-shadow .15s;
  display:flex;align-items:center;justify-content:center;gap:8px;
}
.btn:active{transform:scale(.97);box-shadow:0 2px 6px rgba(102,126,234,.35)}
.btn-green{background:var(--grad-success);box-shadow:0 4px 14px rgba(67,233,123,.28)}
.btn-green:active{box-shadow:0 2px 6px rgba(67,233,123,.35)}
.btn-red{background:var(--grad-danger);box-shadow:0 4px 14px rgba(239,68,68,.28)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937);box-shadow:0 4px 14px rgba(75,85,99,.28)}
.btn-primary{background:var(--grad-primary);box-shadow:0 4px 14px rgba(230,81,0,.28)}

.btn-sm{
  padding:8px 13px;border:none;border-radius:9px;font-size:12px;
  font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;
  background:var(--primary);color:white;transition:transform .12s;
}
.btn-sm:active{transform:scale(.92)}
.btn-sm.green{background:var(--success)}
.btn-sm.red{background:var(--danger)}
.btn-sm.blue{background:var(--info)}
.btn-sm.gray{background:#6b7280}
.btn-sm.wa{background:#25D366}
.btn-sm.purple{background:var(--purple)}

/* ═══ BADGES ═══ */
.badge{
  display:inline-block;padding:3px 10px;border-radius:7px;font-size:11px;
  font-weight:800;color:white;margin-left:6px;letter-spacing:.3px;
}
.badge.high,.badge.critical,.badge.warn,.badge.outstanding,.badge.unpaid{background:var(--danger)}
.badge.medium,.badge.inprogress,.badge.partial{background:var(--warning)}
.badge.low,.badge.ok,.badge.completed,.badge.paid,.badge.active{background:var(--success)}
.badge.new{background:#6b7280}
.badge.expired{background:#6b7280}

/* ═══ LISTS ═══ */
.list-item{
  padding:9px 0;border-bottom:1px solid var(--border);
  font-size:13px;line-height:1.5;
}
.list-item:last-child{border-bottom:none}

/* ═══ CHAT ═══ */
.chat-box{
  background:var(--card);border-radius:18px;padding:14px;
  height:calc(100vh - 300px);overflow-y:auto;margin-bottom:12px;
  border:1px solid var(--border);box-shadow:var(--shadow);
}
.chat-box::-webkit-scrollbar{width:6px}
.chat-box::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.msg{
  padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;
  word-wrap:break-word;font-size:14px;line-height:1.5;
  animation:msgPop .25s ease;
}
@keyframes msgPop{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.msg.user{
  background:var(--grad1);color:white;margin-left:auto;
  border-bottom-right-radius:4px;
}
.msg.ai{
  background:var(--primary-light);border-bottom-left-radius:4px;
  border:1px solid var(--border);
}
body.dark .msg.ai{background:#334155}

.input-row{display:flex;gap:8px;align-items:center}
.input-row input{
  flex:1;padding:14px 18px;border:1.5px solid var(--border);
  border-radius:26px;font-size:15px;outline:none;
  background:var(--card);color:var(--text);
  transition:border-color .2s;
}
.input-row input:focus{border-color:var(--primary)}
.input-row button{
  padding:14px 15px;background:var(--grad1);color:white;border:none;
  border-radius:50%;font-weight:bold;cursor:pointer;font-size:16px;
  box-shadow:0 4px 12px rgba(102,126,234,.3);transition:transform .15s;
}
.input-row button:active{transform:scale(.9)}
.mic-btn{background:var(--grad-success)!important;
  box-shadow:0 4px 12px rgba(67,233,123,.3)!important}
.mic-btn.recording{background:var(--grad-danger)!important;
  animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

/* ═══ BOTTOM NAV ═══ */
.bottom-nav{
  position:fixed;bottom:0;left:0;right:0;background:var(--card);
  border-top:1px solid var(--border);display:flex;padding:8px 4px 10px;
  z-index:100;box-shadow:0 -4px 20px rgba(0,0,0,.06);
}
.bnav{
  flex:1;text-align:center;padding:6px 4px;cursor:pointer;
  border-radius:12px;transition:background .2s;
}
.bnav:active{background:var(--primary-light)}
.bnav.active{background:var(--primary-light)}
.bnav-icon{font-size:20px;display:block;margin-bottom:3px;
  transition:transform .2s}
.bnav.active .bnav-icon{transform:scale(1.15)}
.bnav-label{
  font-size:9px;font-weight:800;color:var(--text2);
  text-transform:uppercase;letter-spacing:.5px;
}
.bnav.active .bnav-label{color:var(--primary)}

/* ═══ STATUS ═══ */
.status-online{
  background:var(--grad-success);color:white;padding:11px 16px;
  border-radius:12px;display:inline-block;font-size:13px;font-weight:700;
  box-shadow:0 4px 12px rgba(16,185,129,.25);
}
.status-offline{
  background:var(--grad-danger);color:white;padding:11px 16px;
  border-radius:12px;display:inline-block;font-size:13px;font-weight:700;
  box-shadow:0 4px 12px rgba(239,68,68,.25);
}
.status-checking{
  background:#6b7280;color:white;padding:11px 16px;
  border-radius:12px;display:inline-block;font-size:13px;font-weight:700;
}

/* ═══ EMPTY STATE ═══ */
.empty{
  text-align:center;padding:40px 20px;color:var(--text2);
}
.empty-icon{
  font-size:64px;margin-bottom:12px;display:block;
  opacity:.5;filter:grayscale(.3);
}
.empty-title{
  font-size:15px;font-weight:700;color:var(--text);margin-bottom:6px;
}
.empty-text{font-size:13px;line-height:1.5}

/* ═══ SKELETON LOADER ═══ */
.skeleton{
  background:linear-gradient(90deg,
    var(--border) 25%,
    rgba(255,255,255,.4) 50%,
    var(--border) 75%);
  background-size:200% 100%;
  animation:shimmer 1.5s infinite;
  border-radius:8px;
}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.skeleton-card{
  background:var(--card);padding:16px;border-radius:18px;margin-bottom:12px;
  border:1px solid var(--border);box-shadow:var(--shadow);
}
.skeleton-line{
  height:12px;margin-bottom:10px;border-radius:6px;
}
.skeleton-line.title{width:60%;height:16px}
.skeleton-line.short{width:40%}

/* ═══ TOAST ═══ */
#toast-container{
  position:fixed;top:16px;left:16px;right:16px;z-index:9999;
  display:flex;flex-direction:column;gap:8px;pointer-events:none;
}
.toast{
  padding:14px 18px;border-radius:14px;color:white;
  font-size:14px;font-weight:600;
  box-shadow:0 8px 24px rgba(0,0,0,.25);
  animation:toastIn .3s ease;
  pointer-events:auto;max-width:500px;margin:0 auto;width:100%;
  display:flex;align-items:center;gap:10px;
}
@keyframes toastIn{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
.toast.out{animation:toastOut .3s ease forwards}
@keyframes toastOut{from{opacity:1;transform:translateY(0)}to{opacity:0;transform:translateY(-20px)}}
.toast.success{background:var(--grad-success)}
.toast.error{background:var(--grad-danger)}
.toast.info{background:var(--grad1)}
.toast.warning{background:linear-gradient(135deg,#f59e0b,#fbbf24)}
.toast-icon{font-size:20px}

/* ═══ IMAGES ═══ */
.img-preview{width:100%;border-radius:16px;margin-bottom:12px;
  box-shadow:var(--shadow);animation:fadeSlide .3s ease}
.swatch{height:100px;border-radius:16px;border:2px solid var(--border);
  margin-bottom:12px;box-shadow:var(--shadow)}
.photo-row{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;
  margin-bottom:10px;scrollbar-width:none}
.photo-row::-webkit-scrollbar{display:none}
.photo-thumb{
  width:88px;height:88px;object-fit:cover;border-radius:12px;
  border:2px solid var(--border);flex-shrink:0;
  transition:transform .15s;
}
.photo-thumb:active{transform:scale(.95)}

/* ═══ TABLES ═══ */
.torque-table{
  width:100%;border-collapse:collapse;background:var(--card);
  border-radius:14px;overflow:hidden;font-size:12px;margin-bottom:12px;
  box-shadow:var(--shadow);
}
.torque-table th{
  background:var(--grad1);color:white;padding:11px 9px;text-align:left;
  font-weight:700;font-size:11px;letter-spacing:.4px;
}
.torque-table td{
  padding:11px 9px;border-bottom:1px solid var(--border);color:var(--text);
}

/* ═══ STATS ═══ */
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{
  background:var(--card);padding:16px 12px;border-radius:18px;text-align:center;
  box-shadow:var(--shadow);border:1px solid var(--border);
  position:relative;overflow:hidden;
}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:var(--grad-primary)}
.stat-card.blue::before{background:linear-gradient(90deg,#3b82f6,#60a5fa)}
.stat-card.green::before{background:var(--grad-success)}
.stat-card.red::before{background:var(--grad-danger)}
.stat-card.purple::before{background:linear-gradient(90deg,#8b5cf6,#a78bfa)}
.stat-card .num{font-size:23px;font-weight:800;color:var(--primary);
  letter-spacing:-.5px;line-height:1.2}
.stat-card.blue .num{color:var(--info)}
.stat-card.green .num{color:var(--success)}
.stat-card.red .num{color:var(--danger)}
.stat-card.purple .num{color:var(--purple)}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:5px;
  font-weight:700;text-transform:uppercase;letter-spacing:.5px}

canvas{max-height:220px}

/* ═══ CHECKLIST ═══ */
.checklist-item{
  padding:11px 0;border-bottom:1px solid var(--border);
  font-size:13px;display:flex;align-items:center;gap:10px;
  cursor:pointer;
}
.checklist-item input{width:20px;height:20px;accent-color:var(--primary);cursor:pointer}
.checklist-item:last-child{border-bottom:none}

/* ═══ PRINT ═══ */
@media print{
  .header,.bottom-nav,.no-print,button,.btn,.btn-sm,
  #toast-container{display:none!important}
  .panel{display:block!important;padding:0}
  .panel:not(.active){display:none!important}
  body{background:white;color:black;padding:0}
  .card{box-shadow:none;border:1px solid #ccc;page-break-inside:avoid}
}
</style>
</head>
<body>

<div id="toast-container"></div>

<div class="header">
<h1><span class="logo" id="logoDisplay">🔧</span> <span id="wsName">RAMSTECH</span></h1>
<p id="wsSub">AI Workshop Assistant</p>
<div class="top-btns">
<button onclick="toggleTheme()" id="themeBtn">🌙</button>
</div>
</div>

<!-- HOME -->
<div id="home" class="panel active">
<div class="card"><div id="status"><span class="status-checking">Checking backend...</span></div></div>
<div class="tile-grid" id="homeGrid"></div>
</div>

<!-- DASHBOARD -->
<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock Alerts</h3><div id="dashLowStock"></div></div>
</div>

<!-- ANALYTICS -->
<div id="analytics" class="panel">
<div class="panel-title">📈 Analytics</div>
<div id="analyticsContent"></div>
</div>

<!-- WARRANTY -->
<div id="warranty" class="panel">
<div class="panel-title">🎁 Warranty Tracker</div>
<div id="warrantyList"></div>
</div>

<!-- TAX -->
<div id="tax" class="panel">
<div class="panel-title">🧾 Tax & Reports</div>
<div class="card">
<h3>📅 Tax Report Period</h3>
<input class="form-input" id="taxFrom" type="date">
<input class="form-input" id="taxTo" type="date">
<button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV</button>
</div>
</div>

<!-- VIN -->
<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<div class="card">
<p style="color:var(--text2);font-size:13px;margin-bottom:12px">Enter the 17-character VIN.</p>
<input class="form-input" id="vinInput" placeholder="17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn btn-green" onclick="decodeVin()">🔍 Decode</button>
<div id="vinResult"></div>
</div>
</div>

<!-- PHOTO -->
<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card">
<p style="color:var(--text2);font-size:13px;margin-bottom:12px">Take a photo of the mechanical issue.</p>
<input class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn btn-green" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>
</div>

<!-- PAINT -->
<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card">
<p style="color:var(--text2);font-size:13px;margin-bottom:12px">Photo in natural light. AI matches colour.</p>
<input class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn btn-green" id="paintBtn" onclick="matchPaint()">🎨 Match Colour</button>
<div id="paintResult"></div>
</div>
</div>

<!-- SPECS -->
<div id="specs" class="panel">
<div class="panel-title">🔧 Vehicle Specs</div>
<input type="text" class="form-input" id="specsSearch" placeholder="🔍 Search vehicle..." oninput="filterSpecs()">
<div id="specsList"></div>
</div>

<!-- INTERVALS -->
<div id="intervals" class="panel">
<div class="panel-title">⏰ Service Intervals</div>
<input type="text" class="form-input" id="intervalSearch" placeholder="🔍 Search..." oninput="filterIntervals()">
<div id="intervalList"></div>
</div>

<!-- BOOK TIME -->
<div id="booktime" class="panel">
<div class="panel-title">⏱️ Book Time</div>
<input type="text" class="form-input" id="bookSearch" placeholder="🔍 Search job..." oninput="filterBook()">
<div id="bookList"></div>
</div>

<!-- SUPPLIERS -->
<div id="suppliers" class="panel">
<div class="panel-title">📞 Suppliers</div>
<button class="btn btn-green" onclick="showForm('supplierForm')">+ Add Supplier</button>
<div id="supplierForm" style="display:none">
<div class="card">
<input class="form-input" id="supName" placeholder="Supplier name">
<input class="form-input" id="supPhone" placeholder="Phone">
<input class="form-input" id="supEmail" placeholder="Email">
<input class="form-input" id="supWhatsapp" placeholder="WhatsApp number">
<input class="form-input" id="supCategory" placeholder="Category">
<input class="form-input" id="supAccount" placeholder="Account number">
<textarea class="form-input" id="supNotes" placeholder="Notes" rows="2"></textarea>
<button class="btn btn-green" onclick="addSupplier()">Save Supplier</button>
<button class="btn btn-dark" onclick="hideForm('supplierForm')">Cancel</button>
</div>
</div>
<div id="supplierList"></div>
</div>

<!-- CHAT -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox">
<div class="msg ai">Hi! Ask me about vehicle repairs, diagnostics, or tools.</div>
</div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendMsg()">
<button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
<button onclick="sendMsg()">➤</button>
</div>
</div>

<!-- CODES -->
<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code..." oninput="searchCodes()">
<div id="codeResults"></div>
</div>

<!-- JOBS -->
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
<label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">📸 Before Photos</label>
<input type="file" id="jBefore" accept="image/*" multiple capture="environment" class="form-input" onchange="addPhoto(event)">
<div class="photo-row" id="beforeRow"></div>
<button class="btn btn-green" onclick="createJob()">Save Job</button>
<button class="btn btn-dark" onclick="hideForm('jobForm')">Cancel</button>
</div>
</div>
<div id="jobList"></div>
</div>

<!-- QUOTES -->
<div id="quotes" class="panel">
<div class="panel-title">💬 Quotes</div>
<button class="btn btn-green" onclick="showForm('quoteForm')">+ New Quote</button>
<div id="quoteForm" style="display:none">
<div class="card">
<input class="form-input" id="qCustomer" placeholder="Customer name">
<input class="form-input" id="qVehicle" placeholder="Vehicle">
<textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea>
<select class="form-input" id="qBookTime" onchange="applyBookTime('q')">
<option value="">— Auto labour from book time —</option>
</select>
<input class="form-input" id="qLabour" type="number" placeholder="Labour (R)" value="0">
<input class="form-input" id="qParts" type="number" placeholder="Parts (R)" value="0">
<button class="btn btn-green" onclick="createQuote()">Save Quote</button>
<button class="btn btn-dark" onclick="hideForm('quoteForm')">Cancel</button>
</div>
</div>
<div id="quoteList"></div>
</div>

<!-- APPOINTMENTS -->
<div id="appointments" class="panel">
<div class="panel-title">📅 Appointments</div>
<button class="btn btn-green" onclick="showForm('apptForm')">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="aCustomer" placeholder="Customer">
<input class="form-input" id="aPhone" placeholder="Phone">
<input class="form-input" id="aVehicle" placeholder="Vehicle">
<input class="form-input" id="aService" placeholder="Service">
<input class="form-input" id="aDate" type="date">
<input class="form-input" id="aTime" type="time">
<button class="btn btn-green" onclick="createAppt()">Book</button>
<button class="btn btn-dark" onclick="hideForm('apptForm')">Cancel</button>
</div>
</div>
<div id="apptList"></div>
</div>

<!-- CUSTOMERS -->
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
<div id="custList"></div>
</div>

<!-- INVOICES -->
<div id="invoices" class="panel">
<div class="panel-title">💰 Invoices</div>
<button class="btn btn-green" onclick="showForm('invForm')">+ New Invoice</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="iCustomer" placeholder="Customer">
<input class="form-input" id="iVehicle" placeholder="Vehicle">
<input class="form-input" id="iDesc" placeholder="Description">
<select class="form-input" id="iBookTime" onchange="applyBookTime('i')">
<option value="">— Auto labour from book time —</option>
</select>
<input class="form-input" id="iLabour" type="number" placeholder="Labour (R)">
<input class="form-input" id="iParts" type="number" placeholder="Parts (R)">
<button class="btn btn-green" onclick="createInvoice()">Save</button>
<button class="btn btn-dark" onclick="hideForm('invForm')">Cancel</button>
</div>
</div>
<div id="invList"></div>
</div>

<!-- INVENTORY -->
<div id="inventory" class="panel">
<div class="panel-title">📦 Inventory</div>
<button class="btn btn-green" onclick="showForm('invItemForm')">+ Add Item</button>
<div id="invItemForm" style="display:none">
<div class="card">
<input class="form-input" id="pNumber" placeholder="Part number">
<input class="form-input" id="pName" placeholder="Name">
<input class="form-input" id="pCategory" placeholder="Category">
<input class="form-input" id="pQty" type="number" placeholder="Qty">
<input class="form-input" id="pMinQty" type="number" placeholder="Min qty" value="5">
<input class="form-input" id="pCost" type="number" placeholder="Cost R">
<input class="form-input" id="pSell" type="number" placeholder="Sell R">
<input class="form-input" id="pSupplier" placeholder="Supplier">
<button class="btn btn-green" onclick="addInventory()">Save</button>
<button class="btn btn-dark" onclick="hideForm('invItemForm')">Cancel</button>
</div>
</div>
<div id="inventoryList"></div>
</div>

<!-- STAFF -->
<div id="staff" class="panel">
<div class="panel-title">👷 Staff</div>
<button class="btn btn-green" onclick="showForm('staffForm')">+ Add Staff</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="stName" placeholder="Name">
<input class="form-input" id="stRole" placeholder="Role">
<input class="form-input" id="stPhone" placeholder="Phone">
<input class="form-input" id="stEmail" placeholder="Email">
<input class="form-input" id="stRate" type="number" placeholder="Hourly rate R" value="150">
<button class="btn btn-green" onclick="addStaff()">Save</button>
<button class="btn btn-dark" onclick="hideForm('staffForm')">Cancel</button>
</div>
</div>
<div id="staffList"></div>
</div>

<!-- EXPENSES -->
<div id="expenses" class="panel">
<div class="panel-title">💸 Expenses</div>
<button class="btn btn-green" onclick="showForm('expForm')">+ Add Expense</button>
<div id="expForm" style="display:none">
<div class="card">
<select class="form-input" id="exCat"><option>Rent</option><option>Utilities</option><option>Tools</option><option>Parts</option><option>Salaries</option><option>Fuel</option><option>Marketing</option><option>Other</option></select>
<input class="form-input" id="exAmount" type="number" placeholder="Amount R">
<input class="form-input" id="exDate" type="date">
<textarea class="form-input" id="exNote" placeholder="Note" rows="2"></textarea>
<button class="btn btn-green" onclick="addExpense()">Save</button>
<button class="btn btn-dark" onclick="hideForm('expForm')">Cancel</button>
</div>
</div>
<div id="expenseList"></div>
</div>

<!-- TORQUE -->
<div id="torque" class="panel">
<div class="panel-title">⚙️ Torque Specs</div>
<input type="text" class="form-input" id="torqueSearch" placeholder="🔍 Search..." oninput="filterTorque()">
<h3 style="margin:8px 0;font-size:14px;color:var(--text2)">Bolt Torque</h3>
<div id="torqueTable"></div>
<h3 style="margin:16px 0 8px;font-size:14px;color:var(--text2)">Sequences</h3>
<div id="torqueSeq"></div>
</div>

<!-- BOLT CALC -->
<div id="boltcalc" class="panel">
<div class="panel-title">🔧 Bolt Calculator</div>
<div class="card">
<select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M20</option></select>
<select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select>
<select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly</option></select>
<button class="btn" onclick="calcTorque()">Calculate</button>
<div id="boltResult"></div>
</div>
</div>

<!-- BULBS -->
<div id="bulbs" class="panel">
<div class="panel-title">💡 Bulb Chart</div>
<input type="text" class="form-input" id="bulbSearch" placeholder="🔍 Search..." oninput="filterBulbs()">
<div id="bulbList"></div>
</div>

<!-- BATTERIES -->
<div id="batteries" class="panel">
<div class="panel-title">🔋 Batteries</div>
<input type="text" class="form-input" id="battSearch" placeholder="🔍 Search..." oninput="filterBatt()">
<div id="battList"></div>
</div>

<!-- TYRES -->
<div id="tyres" class="panel">
<div class="panel-title">🛞 Tyres</div>
<input type="text" class="form-input" id="tyreSearch" placeholder="🔍 Search..." oninput="filterTyre()">
<div id="tyreList"></div>
</div>

<!-- WIRING -->
<div id="wiring" class="panel">
<div class="panel-title">🔌 Wiring Library</div>
<input type="text" class="form-input" id="wiringSearch" placeholder="🔍 Search..." oninput="filterWiring()">
<div id="wiringList"></div>
</div>

<!-- OBD -->
<div id="obd" class="panel">
<div class="panel-title">⚡ OBD-II PIDs</div>
<input type="text" class="form-input" id="obdSearch" placeholder="🔍 Search..." oninput="filterOBD()">
<div id="obdList"></div>
</div>

<!-- SETTINGS -->
<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
<div class="card">
<h3>🏢 Workshop Details</h3>
<input class="form-input" id="sLogo" placeholder="🔧" maxlength="4">
<input class="form-input" id="sName" placeholder="Workshop name">
<input class="form-input" id="sPhone" placeholder="Phone">
<input class="form-input" id="sEmail" placeholder="Email">
<input class="form-input" id="sAddress" placeholder="Address">
<input class="form-input" id="sHours" placeholder="Trading hours">
<input class="form-input" id="sRate" type="number" placeholder="Labour rate R/hr">
<h3 style="margin-top:16px">🧾 Business Registration</h3>
<input class="form-input" id="sVat" placeholder="VAT number">
<input class="form-input" id="sCompany" placeholder="Company reg number">
<input class="form-input" id="sBank" placeholder="Bank details">
<h3 style="margin-top:16px">📜 Terms & Conditions</h3>
<textarea class="form-input" id="sTerms" rows="5"></textarea>
<button class="btn btn-green" onclick="saveSettings()">Save All</button>
</div>
</div>

<!-- BOTTOM NAV -->
<div class="bottom-nav no-print">
<div class="bnav active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
<div class="bnav" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
<div class="bnav" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav" onclick="showTab('specs',this)"><div class="bnav-icon">🔧</div><div class="bnav-label">Specs</div></div>
<div class="bnav" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>

<script>
// ═══ TOAST SYSTEM ═══
function toast(msg, type='info', duration=3000){
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  const icons = {success:'✓', error:'✕', info:'ℹ', warning:'⚠'};
  t.innerHTML = '<span class="toast-icon">' + icons[type] + '</span><span>' + msg + '</span>';
  c.appendChild(t);
  setTimeout(() => {
    t.classList.add('out');
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ═══ HELPERS ═══
function showForm(id){document.getElementById(id).style.display='block';}
function hideForm(id){document.getElementById(id).style.display='none';}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
async function jget(u){const r=await fetch(u);return r.json();}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
async function jput(u,b){const r=await fetch(u,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
function emptyState(icon, title, text){
  return '<div class="empty"><span class="empty-icon">' + icon + '</span><div class="empty-title">' + title + '</div><div class="empty-text">' + text + '</div></div>';
}
function skeleton(){
  return '<div class="skeleton-card"><div class="skeleton skeleton-line title"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div><div class="skeleton-card"><div class="skeleton skeleton-line title"></div><div class="skeleton skeleton-line"></div></div>';
}

// ═══ HOME TILES ═══
const TILES = [
  ['dashboard','📊','Dashboard'],
  ['chat','🤖','AI Chat'],
  ['codes','📟','Fault Codes'],
  ['vin','🔍','VIN'],
  ['photo','📸','Photo Diag'],
  ['paint','🎨','Paint'],
  ['specs','🔧','Vehicle Specs'],
  ['intervals','⏰','Intervals'],
  ['booktime','⏱️','Book Time'],
  ['suppliers','📞','Suppliers'],
  ['jobs','📋','Jobs'],
  ['quotes','💬','Quotes'],
  ['appointments','📅','Appts'],
  ['customers','👥','Customers'],
  ['invoices','💰','Invoices'],
  ['inventory','📦','Inventory'],
  ['staff','👷','Staff'],
  ['expenses','💸','Expenses'],
  ['analytics','📈','Analytics'],
  ['warranty','🎁','Warranty'],
  ['tax','🧾','Tax'],
  ['torque','⚙️','Torque'],
  ['boltcalc','🔧','Bolt Calc'],
  ['bulbs','💡','Bulbs'],
  ['batteries','🔋','Batteries'],
  ['tyres','🛞','Tyres'],
  ['wiring','🔌','Wiring'],
  ['obd','⚡','OBD-II'],
  ['settings','⚙️','Settings']
];
document.getElementById('homeGrid').innerHTML = TILES.map(t =>
  '<div class="tile" onclick="showTab(\'' + t[0] + '\')">' +
  '<span class="tile-icon">' + t[1] + '</span>' +
  '<div class="tile-label">' + t[2] + '</div></div>'
).join('');

// ═══ TAB SWITCHING ═══
function showTab(name, el){
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.bnav').forEach(t => t.classList.remove('active'));
  const panel = document.getElementById(name);
  if (panel) panel.classList.add('active');
  if (el && el.classList) el.classList.add('active');
  window.scrollTo(0,0);
  const loaders = {
    dashboard: loadDash, analytics: loadAnalytics, warranty: loadWarranty,
    tax: loadTax, specs: loadSpecs, intervals: loadIntervals, booktime: loadBookTime,
    suppliers: loadSuppliers, jobs: () => {loadJobs(); loadStaffDropdown(); loadBookTimes();},
    quotes: () => {loadQuotes(); loadBookTimes();},
    appointments: loadAppts, customers: loadCust, invoices: () => {loadInv(); loadBookTimes();},
    inventory: loadInventory, staff: loadStaff, expenses: loadExpenses,
    torque: loadTorque, bulbs: loadBulbs, batteries: loadBatt, tyres: loadTyre,
    wiring: loadWiring, obd: loadOBD, settings: loadSettings,
    codes: () => {if(!document.getElementById('codeResults').dataset.loaded) searchCodes();}
  };
  if (loaders[name]) try { loaders[name](); } catch(e) { console.error(e); }
}

// ═══ THEME ═══
function toggleTheme(){
  document.body.classList.toggle('dark');
  const d = document.body.classList.contains('dark');
  localStorage.setItem('theme', d ? 'dark' : 'light');
  document.getElementById('themeBtn').textContent = d ? '☀️' : '🌙';
}
if (localStorage.getItem('theme') === 'dark'){
  document.body.classList.add('dark');
  document.getElementById('themeBtn').textContent = '☀️';
}

// ═══ IMAGE COMPRESSION ═══
function compressImage(file, maxWidth, quality){
  return new Promise(resolve => {
    const reader = new FileReader();
    reader.onload = e => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let { width, height } = img;
        if (width > maxWidth){ height = (height * maxWidth) / width; width = maxWidth; }
        canvas.width = width; canvas.height = height;
        canvas.getContext('2d').drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', quality));
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ═══ STATUS CHECK ═══
async function checkStatus(){
  try {
    const r = await fetch('/health');
    const d = await r.json();
    const db = d.database === 'supabase' ? ' ✓ DB' : ' ⚠ Memory';
    document.getElementById('status').innerHTML =
      '<span class="status-online">Backend Online' + db + '</span>';
  } catch(e){
    document.getElementById('status').innerHTML =
      '<span class="status-offline">Backend Offline</span>';
  }
}
checkStatus();

// ═══ CHAT ═══
let rec = null, isRec = false;
function toggleMic(){
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){
    toast('Voice not supported in this browser', 'warning'); return;
  }
  if (!rec){
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    rec = new SR(); rec.lang = 'en-ZA';
    rec.onresult = e => {
      document.getElementById('chatInput').value = e.results[0][0].transcript;
      resetMic(); sendMsg();
    };
    rec.onerror = resetMic; rec.onend = resetMic;
  }
  function resetMic(){
    isRec = false;
    document.getElementById('micBtn').classList.remove('recording');
    document.getElementById('micBtn').textContent = '🎤';
  }
  if (isRec){ rec.stop(); resetMic(); }
  else {
    try {
      rec.start(); isRec = true;
      document.getElementById('micBtn').classList.add('recording');
      document.getElementById('micBtn').textContent = '⏹';
    } catch(e){ toast(e.message, 'error'); }
  }
}

async function sendMsg(){
  const i = document.getElementById('chatInput');
  const m = i.value.trim(); if (!m) return;
  const b = document.getElementById('chatBox');
  b.innerHTML += '<div class="msg user">' + esc(m) + '</div>';
  i.value = ''; b.scrollTop = b.scrollHeight;
  b.innerHTML += '<div class="msg ai" id="typ">Thinking...</div>';
  b.scrollTop = b.scrollHeight;
  try {
    const d = await jpost('/api/chat', {message: m});
    document.getElementById('typ').outerHTML = '<div class="msg ai">' + esc(d.reply) + '</div>';
  } catch(e){
    document.getElementById('typ').outerHTML = '<div class="msg ai">Error</div>';
  }
  b.scrollTop = b.scrollHeight;
}

// ═══ DASHBOARD ═══
let rC = null, jC = null;
async function loadDash(){
  try {
    const d = await jget('/api/stats');
    document.getElementById('dashStats').innerHTML =
      '<div class="stats-row">' +
      '<div class="stat-card blue"><div class="num">' + d.jobs_total + '</div><div class="lbl">Jobs</div></div>' +
      '<div class="stat-card purple"><div class="num">' + d.jobs_open + '</div><div class="lbl">Open</div></div>' +
      '<div class="stat-card green"><div class="num">' + d.jobs_completed + '</div><div class="lbl">Done</div></div>' +
      '<div class="stat-card"><div class="num">' + d.customers + '</div><div class="lbl">Customers</div></div>' +
      '<div class="stat-card green"><div class="num">R' + d.revenue + '</div><div class="lbl">Revenue</div></div>' +
      '<div class="stat-card red"><div class="num">R' + d.expenses + '</div><div class="lbl">Expenses</div></div>' +
      '</div>';
    if (rC) rC.destroy();
    const c1 = document.getElementById('revenueChart');
    if (c1) rC = new Chart(c1, {type:'line', data:{labels:d.revenue_labels, datasets:[{data:d.revenue_data, borderColor:'#667eea', backgroundColor:'rgba(102,126,234,.15)', tension:.4, fill:true, borderWidth:3}]}, options:{responsive:true, plugins:{legend:{display:false}}}});
    if (jC) jC.destroy();
    const c2 = document.getElementById('jobChart');
    if (c2) jC = new Chart(c2, {type:'doughnut', data:{labels:['New','Progress','Done'], datasets:[{data:[d.jobs_new, d.jobs_progress, d.jobs_completed], backgroundColor:['#6b7280','#f59e0b','#10b981'], borderWidth:0}]}, options:{responsive:true, plugins:{legend:{position:'bottom'}}}});
    const ls = await jget('/api/inventory/low-stock');
    document.getElementById('dashLowStock').innerHTML = ls.items.length
      ? ls.items.map(i => '<div class="list-item">⚠️ <strong>' + esc(i.name) + '</strong> — ' + i.qty + ' left</div>').join('')
      : '<p style="color:var(--text2)">✓ All stock OK</p>';
  } catch(e){ toast('Failed to load dashboard', 'error'); }
}

// ═══ ANALYTICS ═══
async function loadAnalytics(){
  try {
    const d = await jget('/api/analytics');
    let h = '<div class="stats-row">' +
      '<div class="stat-card blue"><div class="num">R' + d.avg_invoice.toFixed(0) + '</div><div class="lbl">Avg Invoice</div></div>' +
      '<div class="stat-card green"><div class="num">R' + d.total_revenue.toFixed(0) + '</div><div class="lbl">Revenue</div></div>' +
      '<div class="stat-card purple"><div class="num">' + d.invoices_count + '</div><div class="lbl">Invoices</div></div>' +
      '<div class="stat-card"><div class="num">' + d.jobs_count + '</div><div class="lbl">Jobs</div></div>' +
      '</div>';
    if (d.top_services.length){
      h += '<div class="card"><h3>🔥 Top Jobs</h3>';
      d.top_services.forEach(s => { h += '<div class="list-item"><strong>' + esc(s.name) + '</strong> <span style="float:right;color:var(--text2)">' + s.count + '×</span></div>'; });
      h += '</div>';
    }
    if (d.top_customers.length){
      h += '<div class="card"><h3>⭐ Top Customers</h3>';
      d.top_customers.forEach(x => { h += '<div class="list-item"><strong>' + esc(x.name) + '</strong> <span style="float:right;color:var(--success)">R' + x.total.toFixed(0) + '</span></div>'; });
      h += '</div>';
    }
    document.getElementById('analyticsContent').innerHTML = h;
  } catch(e){ toast('Failed to load analytics', 'error'); }
}

// ═══ WARRANTY ═══
async function loadWarranty(){
  const c = document.getElementById('warrantyList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/warranty');
    c.innerHTML = d.warranties.length
      ? d.warranties.map(w => {
          const cls = w.status === 'active' ? 'active' : 'expired';
          return '<div class="card"><h3>🎁 ' + esc(w.vehicle) + ' <span class="badge ' + cls + '">' + w.status.toUpperCase() + '</span></h3>' +
            '<p><strong>' + esc(w.customer) + '</strong></p>' +
            '<div class="list-item">Expires: <strong>' + esc(w.expiry) + '</strong></div>' +
            '<div class="list-item">' + (w.days_left > 0 ? '<span style="color:var(--success);font-weight:700">' + w.days_left + ' days remaining</span>' : '<span style="color:var(--danger)">Expired ' + Math.abs(w.days_left) + ' days ago</span>') + '</div></div>';
        }).join('')
      : emptyState('🎁','No active warranties','Complete a job with warranty to see it here.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load warranties.'); }
}

// ═══ TAX ═══
async function loadTax(){
  try {
    const d = await jget('/api/workshop');
    const n = new Date();
    const f = new Date(n.getFullYear(), n.getMonth(), 1);
    document.getElementById('taxFrom').value = f.toISOString().slice(0,10);
    document.getElementById('taxTo').value = n.toISOString().slice(0,10);
  } catch(e){}
}
function downloadTax(){
  const f = document.getElementById('taxFrom').value;
  const t = document.getElementById('taxTo').value;
  if (!f || !t){ toast('Select both dates', 'warning'); return; }
  window.location.href = '/api/export/tax?from_date=' + f + '&to_date=' + t;
  toast('Download started', 'success');
}

// ═══ VIN ═══
async function decodeVin(){
  const vin = document.getElementById('vinInput').value.trim().toUpperCase();
  const c = document.getElementById('vinResult');
  if (vin.length !== 17){ toast('VIN must be 17 characters', 'warning'); return; }
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/vin/' + vin);
    if (d.detail){ c.innerHTML = ''; toast(d.detail, 'error'); return; }
    c.innerHTML = '<div class="card"><h3>🔍 Vehicle Info</h3>' +
      '<div class="list-item"><strong>VIN:</strong> <span style="font-family:monospace">' + d.vin + '</span></div>' +
      '<div class="list-item"><strong>Manufacturer:</strong> ' + d.manufacturer + '</div>' +
      '<div class="list-item"><strong>Country:</strong> ' + d.country + '</div>' +
      '<div class="list-item"><strong>Year:</strong> ' + d.year + '</div>' +
      '<div class="list-item"><strong>Plant:</strong> ' + d.plant + '</div>' +
      '<div class="list-item"><strong>Serial:</strong> ' + d.serial + '</div></div>';
  } catch(e){ c.innerHTML = ''; toast('Failed', 'error'); }
}

// ═══ PHOTO ═══
let diagB64 = '';
async function previewDiag(e){
  const f = e.target.files[0]; if (!f) return;
  diagB64 = await compressImage(f, 1200, 0.75);
  document.getElementById('photoPreview').innerHTML = '<img class="img-preview" src="' + diagB64 + '">';
}
async function diagnosePhoto(){
  const btn = document.getElementById('photoBtn');
  const c = document.getElementById('photoResult');
  if (!diagB64){ toast('Select a photo first', 'warning'); return; }
  btn.disabled = true; btn.innerHTML = '📸 Analyzing...';
  c.innerHTML = skeleton();
  try {
    const d = await jpost('/api/diagnose/photo', {image_base64:diagB64, vehicle_info:document.getElementById('photoVehicle').value});
    if (!d.success){ c.innerHTML = ''; toast(d.error || 'Failed', 'error'); }
    else {
      let h = '<div class="card"><h3>🔍 ' + esc(d.problem || 'Detected') + '</h3>' +
        '<p><strong>Confidence:</strong> ' + (d.confidence || '?') + '</p>' +
        (d.description ? '<p style="margin-top:8px">' + esc(d.description) + '</p>' : '') + '</div>';
      if (d.possible_causes && d.possible_causes.length) h += '<div class="card"><h3>Possible Causes</h3>' + d.possible_causes.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>';
      if (d.diagnostic_steps && d.diagnostic_steps.length) h += '<div class="card"><h3>Diagnostic Steps</h3>' + d.diagnostic_steps.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>';
      if (d.safety_warnings && d.safety_warnings.length) h += '<div class="card" style="background:linear-gradient(135deg,#fef2f2,#fee2e2);border-color:#fecaca"><h3 style="color:var(--danger)">⚠️ Safety</h3>' + d.safety_warnings.map(x => '<div class="list-item">⚠ ' + esc(x) + '</div>').join('') + '</div>';
      c.innerHTML = h;
      toast('Analysis complete', 'success');
    }
  } catch(e){ c.innerHTML = ''; toast('Error', 'error'); }
  btn.disabled = false; btn.innerHTML = '📸 Analyze Photo';
}

// ═══ PAINT ═══
let paintB64 = '';
async function previewPaint(e){
  const f = e.target.files[0]; if (!f) return;
  paintB64 = await compressImage(f, 1200, 0.75);
  document.getElementById('paintPreview').innerHTML = '<img class="img-preview" src="' + paintB64 + '">';
}
async function matchPaint(){
  const btn = document.getElementById('paintBtn');
  const c = document.getElementById('paintResult');
  if (!paintB64){ toast('Select a photo first', 'warning'); return; }
  btn.disabled = true; btn.innerHTML = '🎨 Analyzing...';
  c.innerHTML = skeleton();
  try {
    const d = await jpost('/api/paint/match', {image_base64:paintB64, vehicle_info:document.getElementById('paintVehicle').value});
    if (!d.success){ c.innerHTML = ''; toast(d.error || 'Failed', 'error'); }
    else {
      const col = d.detected_colour || {};
      let h = '<div class="card"><div class="swatch" style="background:' + (col.hex_code || '#ccc') + '"></div>' +
        '<h3>' + esc(col.name || 'Unknown') + '</h3>' +
        '<p><strong>' + esc(col.finish || '') + '</strong>' + (col.colour_family ? ' • ' + esc(col.colour_family) : '') + '</p>' +
        '<p style="font-family:monospace;margin-top:6px">' + (col.hex_code || '') + '</p>' +
        '<p>Confidence: <strong>' + (d.confidence || '?') + '</strong></p></div>';
      if (d.brand_codes && d.brand_codes.length){
        h += '<div class="card"><h3>🏷️ Brand Codes</h3>';
        d.brand_codes.forEach(b => { h += '<div class="list-item"><strong>' + esc(b.brand) + ':</strong> ' + esc(b.code || '?') + (b.name ? ' — ' + esc(b.name) : '') + '</div>'; });
        h += '</div>';
      }
      c.innerHTML = h;
      toast('Match found', 'success');
    }
  } catch(e){ c.innerHTML = ''; toast('Error', 'error'); }
  btn.disabled = false; btn.innerHTML = '🎨 Match Colour';
}

// ═══ SPECS ═══
let specsData = [];
async function loadSpecs(){
  if (!specsData.length){
    try { const d = await jget('/api/specs'); specsData = d.specs; }
    catch(e){ return; }
  }
  filterSpecs();
}
function filterSpecs(){
  const q = (document.getElementById('specsSearch').value || '').toLowerCase();
  const f = specsData.filter(x => !q || x.v.toLowerCase().includes(q));
  document.getElementById('specsList').innerHTML = f.length ? f.map(s =>
    '<div class="card"><h3>🔧 ' + esc(s.v) + '</h3>' +
    '<div class="list-item"><strong>Engine Code:</strong> ' + esc(s.engine_code) + '</div>' +
    '<div class="list-item"><strong>Oil:</strong> ' + esc(s.oil) + '</div>' +
    '<div class="list-item"><strong>Coolant:</strong> ' + esc(s.coolant) + '</div>' +
    '<div class="list-item"><strong>Brake Fluid:</strong> ' + esc(s.brake) + '</div>' +
    '<div class="list-item"><strong>Transmission:</strong> ' + esc(s.trans) + '</div>' +
    '<div class="list-item"><strong>Firing Order:</strong> ' + esc(s.firing) + '</div>' +
    '<div class="list-item"><strong>Timing:</strong> ' + esc(s.timing) + '</div></div>'
  ).join('') : emptyState('🔧','No match','Try a different search term.');
}

// ═══ INTERVALS ═══
let intData = [];
async function loadIntervals(){
  if (!intData.length){
    try { const d = await jget('/api/intervals'); intData = d.intervals; }
    catch(e){ return; }
  }
  filterIntervals();
}
function filterIntervals(){
  const q = (document.getElementById('intervalSearch').value || '').toLowerCase();
  const f = intData.filter(x => !q || x.t.toLowerCase().includes(q));
  document.getElementById('intervalList').innerHTML = f.map(s =>
    '<div class="card"><h3>⏰ ' + esc(s.t) + '</h3>' +
    '<div class="list-item"><strong>Every:</strong> ' + s.km + ' km / ' + s.months + ' months</div>' +
    '<p style="margin-top:10px"><strong>Replace/Check:</strong></p>' +
    s.items.map(i => '<div class="list-item">• ' + esc(i) + '</div>').join('') + '</div>'
  ).join('');
}

// ═══ BOOK TIME ═══
let bookData = [];
async function loadBookTime(){
  if (!bookData.length){
    try { const d = await jget('/api/book-times'); bookData = d.times; }
    catch(e){ return; }
  }
  filterBook();
}
async function loadBookTimes(){
  if (!bookData.length){
    try { const d = await jget('/api/book-times'); bookData = d.times; } catch(e){ return; }
  }
  const opts = '<option value="">— Auto labour from book time —</option>' +
    bookData.map(b => '<option value="' + b.hrs + '">' + esc(b.job) + ' (' + b.hrs + 'h)</option>').join('');
  const sq = document.getElementById('qBookTime'); if (sq) sq.innerHTML = opts;
  const si = document.getElementById('iBookTime'); if (si) si.innerHTML = opts;
}
function filterBook(){
  const q = (document.getElementById('bookSearch').value || '').toLowerCase();
  const f = bookData.filter(x => !q || x.job.toLowerCase().includes(q));
  document.getElementById('bookList').innerHTML = f.map(b =>
    '<div class="card"><h3>⏱️ ' + esc(b.job) + '</h3>' +
    '<div class="list-item"><strong>Standard time:</strong> ' + b.hrs + ' hours</div></div>'
  ).join('');
}
async function applyBookTime(prefix){
  const h = parseFloat(document.getElementById(prefix + 'BookTime').value) || 0;
  if (!h) return;
  const rate = await getRate();
  document.getElementById(prefix + 'Labour').value = (h * rate).toFixed(2);
  toast('Labour: R' + (h * rate).toFixed(2), 'info');
}
async function getRate(){
  try { const r = await jget('/api/workshop'); return r.labour_rate || 450; }
  catch(e){ return 450; }
}

// ═══ SUPPLIERS ═══
async function loadSuppliers(){
  const c = document.getElementById('supplierList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/suppliers');
    c.innerHTML = d.suppliers.length
      ? d.suppliers.map(s =>
          '<div class="card"><h3>📞 ' + esc(s.name) + '</h3>' +
          (s.category ? '<p style="font-size:12px;color:var(--text2)">' + esc(s.category) + '</p>' : '') +
          (s.phone ? '<p>📞 ' + esc(s.phone) + '</p>' : '') +
          (s.email ? '<p>📧 ' + esc(s.email) + '</p>' : '') +
          (s.account_number ? '<p>Account: ' + esc(s.account_number) + '</p>' : '') +
          (s.notes ? '<p style="font-size:12px;color:var(--text2)">' + esc(s.notes) + '</p>' : '') +
          '<div style="margin-top:10px">' +
          (s.phone ? '<button class="btn-sm blue" onclick="window.location.href=\'tel:' + esc(s.phone) + '\'">📞 Call</button>' : '') +
          (s.whatsapp ? '<button class="btn-sm wa" onclick="window.open(\'https://wa.me/' + esc(s.whatsapp).replace(/[^0-9]/g,\'\') + '\',\'_blank\')">📱 WhatsApp</button>' : '') +
          '<button class="btn-sm red" onclick="delSupplier(\'' + s.id + '\')">Delete</button></div></div>'
        ).join('')
      : emptyState('📞','No suppliers yet','Add suppliers for fast ordering.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load suppliers.'); }
}
async function addSupplier(){
  const n = document.getElementById('supName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/suppliers', {
    name: n,
    phone: document.getElementById('supPhone').value,
    email: document.getElementById('supEmail').value,
    whatsapp: document.getElementById('supWhatsapp').value,
    category: document.getElementById('supCategory').value,
    account_number: document.getElementById('supAccount').value,
    notes: document.getElementById('supNotes').value
  });
  ['supName','supPhone','supEmail','supWhatsapp','supCategory','supAccount','supNotes'].forEach(id => document.getElementById(id).value = '');
  hideForm('supplierForm');
  toast('Supplier added', 'success');
  loadSuppliers();
}
async function delSupplier(id){ if (!confirm('Delete?')) return; await fetch('/api/suppliers/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadSuppliers(); }

// ═══ CODES ═══
async function searchCodes(){
  const q = document.getElementById('codeSearch').value;
  const c = document.getElementById('codeResults');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/fault-codes?search=' + encodeURIComponent(q));
    c.dataset.loaded = '1';
    c.innerHTML = d.codes.length
      ? d.codes.map(x =>
          '<div class="card"><h3>' + x.code + '<span class="badge ' + x.severity.toLowerCase() + '">' + x.severity + '</span></h3>' +
          '<p><strong>' + esc(x.description) + '</strong></p>' +
          '<p style="color:var(--text2);font-size:12px">' + esc(x.system) + '</p>' +
          '<p style="margin-top:8px"><strong>Causes:</strong></p>' + x.causes.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') +
          '<p style="margin-top:8px"><strong>Steps:</strong></p>' + x.steps.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '</div>'
        ).join('')
      : emptyState('📟','No codes match','Try a different code or description.');
  } catch(e){ c.innerHTML = ''; toast('Failed to load', 'error'); }
}

// ═══ JOBS ═══
let jobBeforePhotos = [];
async function addPhoto(e){
  for (const f of Array.from(e.target.files)){
    jobBeforePhotos.push(await compressImage(f, 1000, 0.7));
  }
  renderJobPhotos();
}
function renderJobPhotos(){
  document.getElementById('beforeRow').innerHTML = jobBeforePhotos.map((p, i) =>
    '<div style="position:relative"><img class="photo-thumb" src="' + p + '"><button class="btn-sm red" style="position:absolute;top:-5px;right:-5px;width:24px;height:24px;padding:0;border-radius:50%" onclick="jobBeforePhotos.splice(' + i + ',1);renderJobPhotos()">×</button></div>'
  ).join('');
}
async function loadStaffDropdown(){
  try {
    const d = await jget('/api/staff');
    const sel = document.getElementById('jAssigned');
    if (sel) sel.innerHTML = '<option value="">— Assign staff —</option>' + d.staff.map(s => '<option value="' + esc(s.name) + '">' + esc(s.name) + '</option>').join('');
  } catch(e){}
}
async function loadJobs(){
  const c = document.getElementById('jobList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/jobs');
    c.innerHTML = d.jobs.length
      ? d.jobs.map(j => {
          const ph = j.photos_before && j.photos_before.length
            ? '<div class="photo-row">' + j.photos_before.map(p => '<img class="photo-thumb" src="' + p + '">').join('') + '</div>'
            : '';
          return '<div class="card"><h3>Job #' + j.id + ' <span class="badge ' + j.status.toLowerCase().replace(' ','') + '">' + j.status + '</span></h3>' +
            '<p><strong>' + esc(j.customer) + '</strong></p>' +
            '<p>🚗 ' + esc(j.vehicle) + (j.registration ? ' (' + esc(j.registration) + ')' : '') + '</p>' +
            (j.assigned_to ? '<p style="color:var(--text2);font-size:12px">👷 ' + esc(j.assigned_to) + '</p>' : '') +
            '<p style="color:var(--text2)">' + esc(j.complaint) + '</p>' + ph +
            '<div style="margin-top:10px">' +
            '<button class="btn-sm blue" onclick="upJob(\'' + j.id + '\',\'In Progress\')">Progress</button>' +
            '<button class="btn-sm green" onclick="upJob(\'' + j.id + '\',\'Completed\')">Done</button>' +
            '<button class="btn-sm wa" onclick="waJob(\'' + j.id + '\')">📱</button>' +
            '<button class="btn-sm red" onclick="delJob(\'' + j.id + '\')">Delete</button></div></div>';
        }).join('')
      : emptyState('📋','No jobs yet','Tap + New Job to create your first job card.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load jobs.'); }
}
async function createJob(){
  const c = document.getElementById('jCustomer').value.trim();
  const v = document.getElementById('jVehicle').value.trim();
  const comp = document.getElementById('jComplaint').value.trim();
  if (!c || !v || !comp){ toast('Fill required fields', 'warning'); return; }
  await jpost('/api/jobs', {
    customer: c, phone: document.getElementById('jPhone').value,
    vehicle: v, registration: document.getElementById('jReg').value,
    complaint: comp, assigned_to: document.getElementById('jAssigned').value,
    warranty_months: parseInt(document.getElementById('jWarranty').value) || 6,
    photos_before: jobBeforePhotos
  });
  ['jCustomer','jPhone','jVehicle','jReg','jComplaint'].forEach(id => document.getElementById(id).value = '');
  jobBeforePhotos = []; renderJobPhotos();
  hideForm('jobForm');
  toast('Job created ✓', 'success');
  loadJobs();
}
async function upJob(id, s){ await jput('/api/jobs/' + id, {status:s}); toast('Updated', 'success'); loadJobs(); }
async function delJob(id){ if (!confirm('Delete this job?')) return; await fetch('/api/jobs/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadJobs(); }
function waJob(id){
  jget('/api/jobs').then(d => {
    const j = d.jobs.find(x => x.id == id); if (!j) return;
    const txt = '🔧 Job #' + j.id + '\n' + j.customer + '\n' + j.vehicle + '\nStatus: ' + j.status;
    window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
  });
}

// ═══ QUOTES ═══
async function loadQuotes(){
  const c = document.getElementById('quoteList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/quotes');
    c.innerHTML = d.quotes.length
      ? d.quotes.map(q =>
          '<div class="card"><h3>💬 Quote #' + q.id + '</h3>' +
          '<p><strong>' + esc(q.customer) + '</strong></p>' +
          '<p>' + esc(q.description) + '</p>' +
          '<div class="list-item"><strong>Total: R' + q.total.toFixed(2) + '</strong></div>' +
          '<div style="margin-top:10px">' +
          '<button class="btn-sm green" onclick="acceptQuote(\'' + q.id + '\')">→ Invoice</button>' +
          '<button class="btn-sm wa" onclick="waQuote(\'' + q.id + '\')">📱</button>' +
          '<button class="btn-sm red" onclick="delQuote(\'' + q.id + '\')">Delete</button></div></div>'
        ).join('')
      : emptyState('💬','No quotes yet','Create a quote to send to customers.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load quotes.'); }
}
async function createQuote(){
  const c = document.getElementById('qCustomer').value.trim();
  const d = document.getElementById('qDesc').value.trim();
  if (!c || !d){ toast('Fill required fields', 'warning'); return; }
  await jpost('/api/quotes', {
    customer: c, vehicle: document.getElementById('qVehicle').value,
    description: d,
    labour: parseFloat(document.getElementById('qLabour').value) || 0,
    parts: parseFloat(document.getElementById('qParts').value) || 0
  });
  ['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id => document.getElementById(id).value = '');
  hideForm('quoteForm');
  toast('Quote created ✓', 'success');
  loadQuotes();
}
async function acceptQuote(id){
  if (!confirm('Convert to invoice?')) return;
  const r = await jpost('/api/quotes/' + id + '/accept', {});
  if (r.success){ toast('Converted to invoice ✓', 'success'); loadQuotes(); }
}
async function delQuote(id){ if (!confirm('Delete?')) return; await fetch('/api/quotes/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadQuotes(); }
function waQuote(id){
  jget('/api/quotes').then(d => {
    const q = d.quotes.find(x => x.id == id);
    const txt = '💬 Quote #' + q.id + '\n' + q.customer + '\nTotal: R' + q.total.toFixed(2);
    window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
  });
}

// ═══ APPOINTMENTS ═══
async function loadAppts(){
  const c = document.getElementById('apptList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/appointments');
    const s = d.appointments.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
    c.innerHTML = s.length
      ? s.map(a =>
          '<div class="card"><h3>📅 ' + esc(a.date) + ' at ' + esc(a.time) + '</h3>' +
          '<p><strong>' + esc(a.customer) + '</strong></p>' +
          (a.vehicle ? '<p>🚗 ' + esc(a.vehicle) + '</p>' : '') +
          (a.service ? '<p style="color:var(--text2)">' + esc(a.service) + '</p>' : '') +
          '<button class="btn-sm red" onclick="delAppt(\'' + a.id + '\')">Delete</button></div>'
        ).join('')
      : emptyState('📅','No appointments','Book a customer appointment.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load appointments.'); }
}
async function createAppt(){
  const c = document.getElementById('aCustomer').value.trim();
  const d = document.getElementById('aDate').value;
  const t = document.getElementById('aTime').value;
  if (!c || !d || !t){ toast('Fill required fields', 'warning'); return; }
  await jpost('/api/appointments', {
    customer: c, phone: document.getElementById('aPhone').value,
    vehicle: document.getElementById('aVehicle').value,
    service: document.getElementById('aService').value, date: d, time: t
  });
  ['aCustomer','aPhone','aVehicle','aService','aDate','aTime'].forEach(id => document.getElementById(id).value = '');
  hideForm('apptForm');
  toast('Appointment booked ✓', 'success');
  loadAppts();
}
async function delAppt(id){ if (!confirm('Delete?')) return; await fetch('/api/appointments/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadAppts(); }

// ═══ CUSTOMERS ═══
async function loadCust(){
  const c = document.getElementById('custList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/customers');
    c.innerHTML = d.customers.length
      ? d.customers.map(x =>
          '<div class="card"><h3>👤 ' + esc(x.name) + '</h3>' +
          '<p>📞 ' + esc(x.phone) + '</p>' +
          (x.email ? '<p>📧 ' + esc(x.email) + '</p>' : '') +
          '<div style="margin-top:10px">' +
          '<button class="btn-sm wa" onclick="waCust(\'' + esc(x.phone) + '\')">📱 WhatsApp</button>' +
          '<button class="btn-sm red" onclick="delCust(\'' + x.id + '\')">Delete</button></div></div>'
        ).join('')
      : emptyState('👥','No customers yet','Add customers to build your database.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load customers.'); }
}
async function createCustomer(){
  const n = document.getElementById('cName').value.trim();
  const p = document.getElementById('cPhone').value.trim();
  if (!n || !p){ toast('Name and phone required', 'warning'); return; }
  await jpost('/api/customers', {name:n, phone:p, email:document.getElementById('cEmail').value});
  ['cName','cPhone','cEmail'].forEach(id => document.getElementById(id).value = '');
  hideForm('custForm');
  toast('Customer added ✓', 'success');
  loadCust();
}
async function delCust(id){ if (!confirm('Delete?')) return; await fetch('/api/customers/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadCust(); }
function waCust(p){ window.open('https://wa.me/' + p.replace(/[^0-9]/g,''), '_blank'); }

// ═══ INVOICES ═══
async function loadInv(){
  const c = document.getElementById('invList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/invoices');
    c.innerHTML = d.invoices.length
      ? d.invoices.map(i =>
          '<div class="card" id="inv-' + i.id + '"><h3>Invoice #' + i.id + '</h3>' +
          '<p><strong>' + esc(i.customer) + '</strong></p>' +
          '<p>' + esc(i.description) + '</p>' +
          '<div class="list-item">Labour: R' + i.labour.toFixed(2) + '</div>' +
          '<div class="list-item">Parts: R' + i.parts.toFixed(2) + '</div>' +
          '<div class="list-item"><strong>Total: R' + i.total.toFixed(2) + '</strong></div>' +
          '<div style="margin-top:10px">' +
          '<button class="btn-sm wa" onclick="waInv(\'' + i.id + '\')">📱</button>' +
          '<button class="btn-sm blue" onclick="printInv(\'' + i.id + '\')">🖨</button>' +
          '<button class="btn-sm red" onclick="delInv(\'' + i.id + '\')">Delete</button></div></div>'
        ).join('')
      : emptyState('💰','No invoices yet','Create an invoice to bill customers.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load invoices.'); }
}
async function createInvoice(){
  const c = document.getElementById('iCustomer').value.trim();
  const d = document.getElementById('iDesc').value.trim();
  if (!c || !d){ toast('Fill required fields', 'warning'); return; }
  await jpost('/api/invoices', {
    customer:c, vehicle:document.getElementById('iVehicle').value,
    description:d, labour:parseFloat(document.getElementById('iLabour').value) || 0,
    parts:parseFloat(document.getElementById('iParts').value) || 0
  });
  ['iCustomer','iVehicle','iDesc','iLabour','iParts'].forEach(id => document.getElementById(id).value = '');
  hideForm('invForm');
  toast('Invoice created ✓', 'success');
  loadInv();
}
async function delInv(id){ if (!confirm('Delete?')) return; await fetch('/api/invoices/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadInv(); }
function waInv(id){
  jget('/api/invoices').then(d => {
    const i = d.invoices.find(x => x.id == id);
    const txt = '💰 Invoice #' + i.id + '\n' + i.customer + '\nTotal: R' + i.total.toFixed(2);
    window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
  });
}
function printInv(id){
  jget('/api/invoices').then(async d => {
    const i = d.invoices.find(x => x.id == id);
    const ws = await jget('/api/workshop');
    const w = window.open('', '', 'width=800,height=600');
    w.document.write('<html><head><title>Invoice #' + i.id + '</title><style>body{font-family:Arial;padding:20px;max-width:600px;margin:auto}h1{color:#E65100;border-bottom:2px solid #E65100;padding-bottom:8px}h2{color:#333}.row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #eee}.total{font-size:20px;font-weight:bold;color:#E65100;border-top:2px solid #E65100;padding-top:8px}.terms{margin-top:24px;font-size:11px;color:#666;border-top:1px dashed #ccc;padding-top:12px}</style></head><body>');
    w.document.write('<h1>' + (ws.logo || '🔧') + ' ' + esc(ws.name || 'Workshop') + '</h1>');
    w.document.write('<p>' + esc(ws.phone || '') + ' | ' + esc(ws.email || '') + '<br>' + esc(ws.address || '') + '<br>' + (ws.vat_number ? 'VAT: ' + esc(ws.vat_number) + ' | ' : '') + (ws.company_reg ? 'Reg: ' + esc(ws.company_reg) : '') + '</p>');
    w.document.write('<h2>Invoice #' + i.id + '</h2>');
    w.document.write('<p><strong>Customer:</strong> ' + esc(i.customer) + '<br><strong>Vehicle:</strong> ' + esc(i.vehicle || '-') + '</p>');
    w.document.write('<div class="row"><span>' + esc(i.description) + '</span><span></span></div>');
    w.document.write('<div class="row"><span>Labour</span><span>R' + i.labour.toFixed(2) + '</span></div>');
    w.document.write('<div class="row"><span>Parts</span><span>R' + i.parts.toFixed(2) + '</span></div>');
    w.document.write('<div class="row"><span>Subtotal</span><span>R' + i.subtotal.toFixed(2) + '</span></div>');
    w.document.write('<div class="row"><span>VAT (15%)</span><span>R' + i.vat.toFixed(2) + '</span></div>');
    w.document.write('<div class="row total"><span>TOTAL</span><span>R' + i.total.toFixed(2) + '</span></div>');
    if (ws.bank_details) w.document.write('<p><strong>Bank:</strong> ' + esc(ws.bank_details) + '</p>');
    w.document.write('<div class="terms"><strong>Terms & Conditions:</strong><br>' + esc(ws.terms || 'Payment due within 30 days.') + '</div>');
    w.document.write('</body></html>');
    w.document.close();
    setTimeout(() => w.print(), 500);
  });
}

// ═══ INVENTORY ═══
async function loadInventory(){
  const c = document.getElementById('inventoryList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/inventory');
    c.innerHTML = d.items.length
      ? d.items.map(i => {
          const cls = i.qty <= i.min_qty ? 'warn' : 'ok';
          return '<div class="card"><h3>' + esc(i.name) + ' <span class="badge ' + cls + '">' + i.qty + '</span></h3>' +
            '<div class="list-item">Cost: R' + i.cost_price.toFixed(2) + ' | Sell: R' + i.sell_price.toFixed(2) + '</div>' +
            '<div style="margin-top:10px">' +
            '<button class="btn-sm green" onclick="adjInv(\'' + i.id + '\',1)">+1</button>' +
            '<button class="btn-sm red" onclick="adjInv(\'' + i.id + '\',-1)">-1</button>' +
            '<button class="btn-sm gray" onclick="delInvItem(\'' + i.id + '\')">Delete</button></div></div>';
        }).join('')
      : emptyState('📦','No stock items','Add parts you keep in inventory.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load inventory.'); }
}
async function addInventory(){
  const n = document.getElementById('pName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/inventory', {
    part_number:document.getElementById('pNumber').value, name:n,
    category:document.getElementById('pCategory').value,
    qty:parseInt(document.getElementById('pQty').value) || 0,
    min_qty:parseInt(document.getElementById('pMinQty').value) || 5,
    cost_price:parseFloat(document.getElementById('pCost').value) || 0,
    sell_price:parseFloat(document.getElementById('pSell').value) || 0,
    supplier:document.getElementById('pSupplier').value
  });
  ['pNumber','pName','pCategory','pQty','pMinQty','pCost','pSell','pSupplier'].forEach(id => document.getElementById(id).value = '');
  hideForm('invItemForm');
  toast('Item added ✓', 'success');
  loadInventory();
}
async function adjInv(id, d){ await jpost('/api/inventory/' + id + '/adjust', {delta:d}); loadInventory(); }
async function delInvItem(id){ if (!confirm('Delete?')) return; await fetch('/api/inventory/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadInventory(); }

// ═══ STAFF ═══
async function loadStaff(){
  const c = document.getElementById('staffList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/staff');
    c.innerHTML = d.staff.length
      ? d.staff.map(s =>
          '<div class="card"><h3>👷 ' + esc(s.name) + '</h3>' +
          (s.role ? '<p><strong>' + esc(s.role) + '</strong></p>' : '') +
          (s.phone ? '<p>📞 ' + esc(s.phone) + '</p>' : '') +
          '<p>Rate: R' + s.hourly_rate.toFixed(2) + '/hr</p>' +
          '<button class="btn-sm red" onclick="delStaff(\'' + s.id + '\')">Delete</button></div>'
        ).join('')
      : emptyState('👷','No staff yet','Add your team members.');
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load staff.'); }
}
async function addStaff(){
  const n = document.getElementById('stName').value.trim();
  if (!n){ toast('Name required', 'warning'); return; }
  await jpost('/api/staff', {
    name:n, role:document.getElementById('stRole').value,
    phone:document.getElementById('stPhone').value, email:document.getElementById('stEmail').value,
    hourly_rate:parseFloat(document.getElementById('stRate').value) || 150
  });
  ['stName','stRole','stPhone','stEmail'].forEach(id => document.getElementById(id).value = '');
  hideForm('staffForm');
  toast('Staff added ✓', 'success');
  loadStaff();
}
async function delStaff(id){ if (!confirm('Delete?')) return; await fetch('/api/staff/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadStaff(); }

// ═══ EXPENSES ═══
async function loadExpenses(){
  const c = document.getElementById('expenseList');
  c.innerHTML = skeleton();
  try {
    const d = await jget('/api/expenses');
    const total = d.expenses.reduce((s, x) => s + parseFloat(x.amount || 0), 0);
    let h = '<div class="card" style="background:var(--grad-danger);color:white"><h3 style="color:white">Total Expenses</h3><p style="font-size:28px;color:white;font-weight:800">R' + total.toFixed(2) + '</p></div>';
    h += d.expenses.length
      ? d.expenses.map(e =>
          '<div class="card"><h3>' + esc(e.category) + ' <span class="badge new">R' + parseFloat(e.amount).toFixed(2) + '</span></h3>' +
          (e.note ? '<p>' + esc(e.note) + '</p>' : '') +
          '<p style="font-size:11px;color:var(--text2)">' + esc(e.date) + '</p>' +
          '<button class="btn-sm red" onclick="delExpense(\'' + e.id + '\')">Delete</button></div>'
        ).join('')
      : emptyState('💸','No expenses yet','Track your workshop costs.');
    c.innerHTML = h;
  } catch(e){ c.innerHTML = emptyState('❌','Error','Could not load expenses.'); }
}
async function addExpense(){
  const a = parseFloat(document.getElementById('exAmount').value) || 0;
  if (!a){ toast('Amount required', 'warning'); return; }
  await jpost('/api/expenses', {
    category:document.getElementById('exCat').value, amount:a,
    date:document.getElementById('exDate').value || new Date().toISOString().slice(0,10),
    note:document.getElementById('exNote').value
  });
  ['exAmount','exDate','exNote'].forEach(id => document.getElementById(id).value = '');
  hideForm('expForm');
  toast('Expense added ✓', 'success');
  loadExpenses();
}
async function delExpense(id){ if (!confirm('Delete?')) return; await fetch('/api/expenses/' + id, {method:'DELETE'}); toast('Deleted', 'success'); loadExpenses(); }

// ═══ TORQUE ═══
let torqueData = [], seqData = [];
async function loadTorque(){
  if (!torqueData.length){
    try { const d = await jget('/api/torque'); torqueData = d.bolts; seqData = d.sequences; }
    catch(e){ return; }
  }
  filterTorque();
}
function filterTorque(){
  const q = (document.getElementById('torqueSearch').value || '').toLowerCase();
  const f = torqueData.filter(x => !q || x.s.toLowerCase().includes(q) || x.g.toLowerCase().includes(q));
  document.getElementById('torqueTable').innerHTML = '<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>' +
    f.map(x => '<tr><td><strong>' + esc(x.s) + '</strong></td><td>' + esc(x.g) + '</td><td>' + x.nm + '</td><td>' + x.ft + '</td><td>' + esc(x.u) + '</td></tr>').join('') + '</table>';
  document.getElementById('torqueSeq').innerHTML = seqData.map(s =>
    '<div class="card"><h3>' + esc(s.c) + '</h3>' + s.st.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>'
  ).join('');
}

// ═══ BOLT CALC ═══
async function calcTorque(){
  const d = await jpost('/api/bolt-calc', {
    size:document.getElementById('boltSize').value,
    grade:document.getElementById('boltGrade').value,
    condition:document.getElementById('boltCondition').value
  });
  document.getElementById('boltResult').innerHTML =
    '<div class="card" style="background:var(--grad1);color:white"><h3 style="color:white">Torque</h3>' +
    '<p style="font-size:34px;font-weight:800;color:white;margin:8px 0">' + d.nm.toFixed(1) + ' Nm</p>' +
    '<p style="color:white">' + d.ftlb.toFixed(1) + ' ft·lb</p></div>';
}

// ═══ BULBS/BATT/TYRES/WIRING/OBD ═══
let bulbsData = [], battData = [], tyreData = [], wiringData = [], obdData = [];
async function loadBulbs(){ if (!bulbsData.length){ try { bulbsData = (await jget('/api/bulbs')).bulbs; } catch(e){} } filterBulbs(); }
function filterBulbs(){
  const q = (document.getElementById('bulbSearch').value || '').toLowerCase();
  const f = bulbsData.filter(x => !q || x.v.toLowerCase().includes(q));
  document.getElementById('bulbList').innerHTML = f.map(b =>
    '<div class="card"><h3>💡 ' + esc(b.v) + '</h3>' +
    '<div class="list-item">Low: <strong>' + esc(b.l) + '</strong></div>' +
    '<div class="list-item">High: <strong>' + esc(b.h) + '</strong></div>' +
    '<div class="list-item">Fog: <strong>' + esc(b.f) + '</strong></div>' +
    '<div class="list-item">Reverse: <strong>' + esc(b.r) + '</strong></div></div>'
  ).join('') || emptyState('💡','No match','');
}
async function loadBatt(){ if (!battData.length){ try { battData = (await jget('/api/batteries')).batteries; } catch(e){} } filterBatt(); }
function filterBatt(){
  const q = (document.getElementById('battSearch').value || '').toLowerCase();
  const f = battData.filter(x => !q || x.v.toLowerCase().includes(q));
  document.getElementById('battList').innerHTML = f.map(b =>
    '<div class="card"><h3>🔋 ' + esc(b.v) + '</h3>' +
    '<div class="list-item">Group: <strong>' + esc(b.g) + '</strong></div>' +
    '<div class="list-item">CCA: <strong>' + b.c + '</strong></div>' +
    '<div class="list-item">Ah: <strong>' + b.a + '</strong></div></div>'
  ).join('') || emptyState('🔋','No match','');
}
async function loadTyre(){ if (!tyreData.length){ try { tyreData = (await jget('/api/tyres')).tyres; } catch(e){} } filterTyre(); }
function filterTyre(){
  const q = (document.getElementById('tyreSearch').value || '').toLowerCase();
  const f = tyreData.filter(x => !q || x.v.toLowerCase().includes(q));
  document.getElementById('tyreList').innerHTML = f.map(t =>
    '<div class="card"><h3>🛞 ' + esc(t.v) + '</h3>' +
    '<div class="list-item">Size: <strong>' + esc(t.s) + '</strong></div>' +
    '<div class="list-item">Front: <strong>' + esc(t.f) + '</strong></div>' +
    '<div class="list-item">Rear: <strong>' + esc(t.r) + '</strong></div></div>'
  ).join('') || emptyState('🛞','No match','');
}
async function loadWiring(){ if (!wiringData.length){ try { wiringData = (await jget('/api/wiring')).circuits; } catch(e){} } filterWiring(); }
function filterWiring(){
  const q = (document.getElementById('wiringSearch').value || '').toLowerCase();
  const f = wiringData.filter(x => !q || x.n.toLowerCase().includes(q) || x.sy.toLowerCase().includes(q));
  document.getElementById('wiringList').innerHTML = f.map(w =>
    '<div class="card"><h3>🔌 ' + esc(w.n) + '</h3>' +
    '<p style="font-size:12px;color:var(--text2)">' + esc(w.sy) + '</p>' +
    '<p><strong>Components:</strong></p>' + w.c.map(c => '<div class="list-item">• ' + esc(c) + '</div>').join('') +
    '<p><strong>Connections:</strong></p>' + w.co.map(c => '<div class="list-item" style="font-family:monospace;font-size:11px">' + esc(c) + '</div>').join('') + '</div>'
  ).join('') || emptyState('🔌','No match','');
}
async function loadOBD(){ if (!obdData.length){ try { obdData = (await jget('/api/obd-pids')).pids; } catch(e){} } filterOBD(); }
function filterOBD(){
  const q = (document.getElementById('obdSearch').value || '').toLowerCase();
  const f = obdData.filter(x => !q || x.n.toLowerCase().includes(q) || x.p.includes(q));
  document.getElementById('obdList').innerHTML = '<table class="torque-table"><tr><th>PID</th><th>Name</th><th>Desc</th></tr>' +
    f.map(x => '<tr><td><strong>' + x.p + '</strong></td><td>' + esc(x.n) + '</td><td style="font-size:11px">' + esc(x.d) + '</td></tr>').join('') + '</table>';
}

// ═══ SETTINGS ═══
async function loadSettings(){
  try {
    const d = await jget('/api/workshop');
    document.getElementById('sLogo').value = d.logo || '🔧';
    document.getElementById('sName').value = d.name || '';
    document.getElementById('sPhone').value = d.phone || '';
    document.getElementById('sEmail').value = d.email || '';
    document.getElementById('sAddress').value = d.address || '';
    document.getElementById('sHours').value = d.hours || '';
    document.getElementById('sRate').value = d.labour_rate || 450;
    document.getElementById('sVat').value = d.vat_number || '';
    document.getElementById('sCompany').value = d.company_reg || '';
    document.getElementById('sBank').value = d.bank_details || '';
    document.getElementById('sTerms').value = d.terms || '';
    applyBrand(d);
  } catch(e){}
}
function applyBrand(d){
  const logo = d.logo || '🔧';
  const name = (d.name || 'RAMSTECH').toUpperCase();
  document.querySelector('.header h1').innerHTML = logo + ' <span id="wsName">' + name + '</span>';
  const sub = [d.phone, d.address].filter(Boolean).join(' • ');
  document.getElementById('wsSub').textContent = sub || 'AI Workshop Assistant';
}
async function saveSettings(){
  const p = {
    logo:document.getElementById('sLogo').value || '🔧',
    name:document.getElementById('sName').value,
    phone:document.getElementById('sPhone').value,
    email:document.getElementById('sEmail').value,
    address:document.getElementById('sAddress').value,
    hours:document.getElementById('sHours').value,
    labour_rate:parseFloat(document.getElementById('sRate').value) || 450,
    vat_number:document.getElementById('sVat').value,
    company_reg:document.getElementById('sCompany').value,
    bank_details:document.getElementById('sBank').value,
    terms:document.getElementById('sTerms').value
  };
  await jpost('/api/workshop', p);
  applyBrand(p);
  toast('Settings saved ✓', 'success');
}
loadSettings();
</script>
</body>
</html>"""
