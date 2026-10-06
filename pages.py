# pages.py — RamsTech v10.0 — Beautiful categorized UI
# Includes: Category navigation, gradient colors, animations, all features
# TEST-MARKER-XYZ-987
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

/* ═══════════════════════════════ */
/* HEADER */
/* ═══════════════════════════════ */
.header{
background:var(--grad1);color:white;padding:16px 14px 18px;
position:relative;overflow:hidden;
border-bottom-left-radius:24px;border-bottom-right-radius:24px;
box-shadow:0 6px 24px rgba(102,126,234,.35);
}
.header::before{
content:'';position:absolute;top:-50%;right:-20%;width:300px;height:300px;
background:radial-gradient(circle,rgba(255,255,255,.15) 0%,transparent 70%);
border-radius:50%;
}
.header::after{
content:'';position:absolute;bottom:-60%;left:-10%;width:200px;height:200px;
background:radial-gradient(circle,rgba(255,255,255,.1) 0%,transparent 70%);
border-radius:50%;
}
.header h1{
font-size:20px;display:flex;align-items:center;justify-content:center;gap:8px;
position:relative;z-index:1;font-weight:800;letter-spacing:.5px;
}
.header h1 .logo{font-size:26px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.2))}
.header p{font-size:11px;opacity:.9;margin-top:3px;text-align:center;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:10px;display:flex;gap:6px;z-index:2}
.top-btns button{
background:rgba(255,255,255,.25);border:none;color:white;padding:8px;
border-radius:10px;font-size:15px;cursor:pointer;backdrop-filter:blur(8px);
transition:all .2s;
}
.top-btns button:active{transform:scale(.9);background:rgba(255,255,255,.4)}
.lang-sel{
background:rgba(255,255,255,.25);border:none;color:white;padding:8px 6px;
border-radius:10px;font-size:12px;outline:none;backdrop-filter:blur(8px);
font-weight:600;
}
.lang-sel option{color:#333}

/* ═══════════════════════════════ */
/* HOME / CATEGORY VIEW */
/* ═══════════════════════════════ */
.home-container{padding:16px;max-width:900px;margin:0 auto}
.hero-card{
background:var(--card);border-radius:20px;padding:16px;margin-bottom:16px;
box-shadow:0 4px 20px rgba(0,0,0,.06);
border:1px solid var(--border);
}
.cat-title{
font-size:13px;font-weight:700;color:var(--text2);text-transform:uppercase;
letter-spacing:1.5px;margin:20px 4px 12px;
}
.cat-grid{display:grid;grid-template-columns:1fr;gap:12px}
.cat-card{
border-radius:20px;padding:20px 18px;color:white;cursor:pointer;
position:relative;overflow:hidden;
box-shadow:0 8px 24px rgba(0,0,0,.15);
transition:all .25s ease;
display:flex;align-items:center;gap:16px;
}
.cat-card:active{transform:scale(.97);box-shadow:0 4px 12px rgba(0,0,0,.2)}
.cat-card::before{
content:'';position:absolute;top:-30%;right:-10%;width:180px;height:180px;
background:radial-gradient(circle,rgba(255,255,255,.2) 0%,transparent 70%);
border-radius:50%;
}
.cat-icon{
font-size:38px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.2));
position:relative;z-index:1;min-width:50px;text-align:center;
}
.cat-info{flex:1;position:relative;z-index:1}
.cat-name{font-size:17px;font-weight:800;letter-spacing:.3px;margin-bottom:3px}
.cat-count{font-size:12px;opacity:.85;font-weight:500}
.cat-arrow{font-size:20px;opacity:.7;position:relative;z-index:1}

/* ═══════════════════════════════ */
/* TILE GRID (subview) */
/* ═══════════════════════════════ */
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{
background:var(--card);border-radius:16px;padding:16px 12px;cursor:pointer;
text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);
border:1px solid var(--border);transition:all .2s ease;
position:relative;overflow:hidden;
}
.tile:active{transform:scale(.95);box-shadow:0 2px 6px rgba(0,0,0,.1)}
.tile-icon{font-size:32px;margin-bottom:8px;display:block}
.tile-label{font-size:12px;font-weight:700;color:var(--text);letter-spacing:.2px}
.tile-sub{font-size:10px;color:var(--text2);margin-top:3px}
.tile-accent{position:absolute;top:0;left:0;right:0;height:4px}

/* ═══════════════════════════════ */
/* BOTTOM NAV */
/* ═══════════════════════════════ */
.bottom-nav{
position:fixed;bottom:0;left:0;right:0;
background:var(--card);border-top:1px solid var(--border);
display:flex;justify-content:space-around;padding:8px 4px;z-index:100;
box-shadow:0 -4px 20px rgba(0,0,0,.06);
}
.bnav-item{
flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px;
transition:all .2s;
}
.bnav-item:active{background:var(--input-bg)}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase;letter-spacing:.5px}
.bnav-item.active .bnav-label{color:var(--primary)}
.bnav-item.active{background:rgba(230,81,0,.08)}

/* ═══════════════════════════════ */
/* PANELS */
/* ═══════════════════════════════ */
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.panel-title{
font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px;
display:flex;align-items:center;gap:8px;
}

/* ═══════════════════════════════ */
/* CARDS */
/* ═══════════════════════════════ */
.card{
background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;
box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);
}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;font-weight:700}
.card p{margin:4px 0;font-size:13px;line-height:1.5;color:var(--text)}

/* ═══════════════════════════════ */
/* FORMS */
/* ═══════════════════════════════ */
.form-input{
width:100%;padding:14px;border:1.5px solid var(--border);border-radius:12px;
font-size:15px;margin-bottom:10px;background:var(--input-bg);color:var(--text);
transition:border-color .2s;font-family:inherit;
}
.form-input:focus{outline:none;border-color:var(--primary)}
textarea.form-input{resize:vertical;font-family:inherit}

.btn{
width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;
font-weight:800;cursor:pointer;margin-bottom:10px;
background:var(--grad1);color:white;letter-spacing:.3px;
box-shadow:0 4px 12px rgba(102,126,234,.3);
transition:all .2s;
}
.btn:active{transform:scale(.97);box-shadow:0 2px 6px rgba(102,126,234,.4)}
.btn.btn-warn{background:var(--grad2);box-shadow:0 4px 12px rgba(245,87,108,.3)}
.btn.btn-success{background:var(--grad4);box-shadow:0 4px 12px rgba(67,233,123,.3)}
.btn.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}

.btn-sm{
padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;
cursor:pointer;margin-right:5px;margin-bottom:4px;
background:var(--primary);color:white;transition:all .2s;
}
.btn-sm:active{transform:scale(.95)}
.btn-sm.gray{background:#6b7280}
.btn-sm.green{background:#10b981}
.btn-sm.red{background:#ef4444}
.btn-sm.blue{background:#3b82f6}
.btn-sm.whatsapp{background:#25D366}
.btn-sm.purple{background:#8b5cf6}

/* ═══════════════════════════════ */
/* BADGES */
/* ═══════════════════════════════ */
.badge{
display:inline-block;padding:3px 9px;border-radius:6px;font-size:11px;
font-weight:700;color:white;margin-left:6px;letter-spacing:.3px;
}
.badge.high,.badge.critical,.badge.warn{background:#ef4444}
.badge.medium{background:#f59e0b}
.badge.low,.badge.ok,.badge.completed,.badge.paid{background:#10b981}
.badge.new{background:#6b7280}
.badge.inprogress{background:#f59e0b}
.badge.unpaid,.badge.outstanding{background:#ef4444}
.badge.partial{background:#f59e0b}

/* ═══════════════════════════════ */
/* LISTS */
/* ═══════════════════════════════ */
.list-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.list-item:last-child{border-bottom:none}

/* ═══════════════════════════════ */
/* CHAT */
/* ═══════════════════════════════ */
.chat-box{
background:var(--card);border-radius:16px;padding:14px;height:calc(100vh - 280px);
overflow-y:auto;margin-bottom:12px;border:1px solid var(--border);
box-shadow:0 4px 12px rgba(0,0,0,.06);
}
.msg{
padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;
word-wrap:break-word;font-size:14px;line-height:1.45;animation:msgIn .25s ease;
}
@keyframes msgIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.msg.user{background:var(--grad1);color:white;margin-left:auto;border-bottom-right-radius:4px}
.msg.ai{background:var(--input-bg);border-bottom-left-radius:4px;border:1px solid var(--border)}
.input-row{display:flex;gap:8px;align-items:center}
.input-row input{
flex:1;padding:14px 18px;border:1.5px solid var(--border);border-radius:25px;
font-size:15px;outline:none;background:var(--input-bg);color:var(--text);
}
.input-row input:focus{border-color:var(--primary)}
.input-row button{
padding:14px 16px;background:var(--grad1);color:white;border:none;
border-radius:50%;font-weight:bold;cursor:pointer;font-size:16px;
box-shadow:0 4px 12px rgba(102,126,234,.3);transition:all .2s;
}
.input-row button:active{transform:scale(.9)}
.mic-btn{background:var(--grad4)!important;box-shadow:0 4px 12px rgba(67,233,123,.3)!important}
.mic-btn.recording{background:var(--grad2)!important;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

/* ═══════════════════════════════ */
/* IMAGES */
/* ═══════════════════════════════ */
.img-preview{width:100%;border-radius:14px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.1)}
.thumb-row{display:flex;gap:8px;overflow-x:auto;margin-top:8px;padding-bottom:4px}
.thumb{width:80px;height:80px;object-fit:cover;border-radius:10px;border:2px solid var(--border)}
.thumb-wrap{position:relative}
.thumb-del{
position:absolute;top:-6px;right:-6px;background:#ef4444;color:white;
border:none;border-radius:50%;width:22px;height:22px;font-size:12px;
cursor:pointer;line-height:1;font-weight:bold;
}
.swatch{height:90px;border-radius:14px;border:2px solid var(--border);margin-bottom:12px}

/* ═══════════════════════════════ */
/* STATUS */
/* ═══════════════════════════════ */
.status-online{
background:linear-gradient(135deg,#10b981,#34d399);color:white;
padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;
font-weight:700;box-shadow:0 4px 12px rgba(16,185,129,.3);
}
.status-offline{
background:linear-gradient(135deg,#ef4444,#f87171);color:white;
padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;
font-weight:700;box-shadow:0 4px 12px rgba(239,68,68,.3);
}
.loading{text-align:center;padding:20px;color:var(--text2);font-size:13px}

/* ═══════════════════════════════ */
/* TABLES */
/* ═══════════════════════════════ */
.torque-table{
width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;
overflow:hidden;font-size:12px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.06);
}
.torque-table th{
background:var(--grad1);color:white;padding:10px 8px;text-align:left;
font-weight:700;font-size:11px;letter-spacing:.5px;
}
.torque-table td{padding:10px 8px;border-bottom:1px solid var(--border);color:var(--text)}

/* ═══════════════════════════════ */
/* STATS */
/* ═══════════════════════════════ */
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{
background:var(--card);padding:16px 12px;border-radius:16px;text-align:center;
box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);
position:relative;overflow:hidden;
}
.stat-card .num{font-size:22px;font-weight:800;color:var(--primary);letter-spacing:-.5px}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:4px;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
.stat-card.green .num{color:#10b981}
.stat-card.red .num{color:#ef4444}
.stat-card.blue .num{color:#3b82f6}
.stat-card.purple .num{color:#8b5cf6}
.stat-card.green::before,.stat-card.red::before,.stat-card.blue::before,.stat-card.purple::before{
content:'';position:absolute;top:0;left:0;right:0;height:3px;
}
.stat-card.green::before{background:linear-gradient(90deg,#10b981,#34d399)}
.stat-card.red::before{background:linear-gradient(90deg,#ef4444,#f87171)}
.stat-card.blue::before{background:linear-gradient(90deg,#3b82f6,#60a5fa)}
.stat-card.purple::before{background:linear-gradient(90deg,#8b5cf6,#a78bfa)}

canvas{max-height:220px}

/* ═══════════════════════════════ */
/* CHECKLIST */
/* ═══════════════════════════════ */
.checklist-item{
padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;
display:flex;align-items:center;gap:10px;
}
.checklist-item input{width:20px;height:20px;accent-color:var(--primary)}
.checklist-item:last-child{border-bottom:none}

/* ═══════════════════════════════ */
/* BACK BUTTON */
/* ═══════════════════════════════ */
.back-btn{
background:var(--grad6);color:white;border:none;padding:10px 16px;
border-radius:12px;font-size:13px;font-weight:700;cursor:pointer;
margin-bottom:16px;box-shadow:0 4px 12px rgba(48,207,208,.3);
display:flex;align-items:center;gap:6px;
}

/* ═══════════════════════════════ */
/* PRINT */
/* ═══════════════════════════════ */
@media print{
.header,.bottom-nav,.no-print,button,.btn,.btn-sm{display:none!important}
.panel{display:block!important;padding:0}
.panel:not(.active){display:none!important}
body{background:white;color:black}
.card{box-shadow:none;border:1px solid #ccc;page-break-inside:avoid}
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

<!-- ═══════════════════════════════ -->
<!-- HOME (CATEGORY VIEW) -->
<!-- ═══════════════════════════════ -->
<div id="home" class="panel active">
<div class="home-container">
<div class="hero-card">
<div id="status">Checking backend...</div>
</div>

<!-- Categories -->
<div id="categoryView">
<div class="cat-title">Choose a Category</div>
<div class="cat-grid" id="categoryGrid"></div>
</div>

<!-- Sub-category -->
<div id="subView" style="display:none">
<button class="back-btn" onclick="backToCategories()">← Back to Categories</button>
<div class="cat-title" id="subTitle"></div>
<div class="tile-grid" id="subGrid"></div>
</div>
</div>
</div>

<!-- ═══════════════════════════════ -->
<!-- DASHBOARD -->
<!-- ═══════════════════════════════ -->
<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock Alerts</h3><div id="dashLowStock"></div></div>
<div class="card"><h3>🎁 Warranty Expiring</h3><div id="dashWarranty"></div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- AI CHAT -->
<!-- ═══════════════════════════════ -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! I'm RamsTech AI. Ask about repairs, diagnostics, or tools.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()">
<button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
<button onclick="sendMsg()">➤</button>
</div>
</div>

<!-- ═══════════════════════════════ -->
<!-- FAULT CODES -->
<!-- ═══════════════════════════════ -->
<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code or description..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- PROBLEMS -->
<!-- ═══════════════════════════════ -->
<div id="problems" class="panel">
<div class="panel-title">📖 Common Problems</div>
<input type="text" class="form-input" id="problemSearch" placeholder="🔍 Search problems..." oninput="filterProblems()">
<div id="problemList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- VIN -->
<!-- ═══════════════════════════════ -->
<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<input type="text" class="form-input" id="vinInput" placeholder="Enter 17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- PAINT -->
<!-- ═══════════════════════════════ -->
<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card"><p style="font-size:13px">📸 Take a photo of a vehicle panel in good light. AI identifies colour and provides paint codes.</p></div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- PHOTO DIAG -->
<!-- ═══════════════════════════════ -->
<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card"><p style="font-size:13px">📸 Take a photo of a mechanical issue. AI diagnoses the problem.</p></div>
<input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- JOBS -->
<!-- ═══════════════════════════════ -->
<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<button class="btn no-print" onclick="showJobForm()">+ New Job Card</button>
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

<!-- ═══════════════════════════════ -->
<!-- CUSTOMERS -->
<!-- ═══════════════════════════════ -->
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

<!-- ═══════════════════════════════ -->
<!-- APPOINTMENTS -->
<!-- ═══════════════════════════════ -->
<div id="appointments" class="panel">
<div class="panel-title">📅 Appointments</div>
<button class="btn no-print" onclick="showApptForm()">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="apptCustomer" placeholder="Customer">
<input class="form-input" id="apptPhone" placeholder="Phone">
<input class="form-input" id="apptVehicle" placeholder="Vehicle">
<input class="form-input" id="apptService" placeholder="Service">
<input class="form-input" id="apptDate" type="date">
<input class="form-input" id="apptTime" type="time">
<button class="btn btn-success" onclick="createAppt()">Book Appointment</button>
<button class="btn btn-dark" onclick="hideApptForm()">Cancel</button>
</div>
</div>
<div id="apptList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- QUOTES -->
<!-- ═══════════════════════════════ -->
<div id="quotes" class="panel">
<div class="panel-title">💬 Quotes</div>
<button class="btn no-print" onclick="showQuoteForm()">+ New Quote</button>
<div id="quoteForm" style="display:none">
<div class="card">
<input class="form-input" id="qCustomer" placeholder="Customer">
<input class="form-input" id="qVehicle" placeholder="Vehicle">
<textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea>
<input class="form-input" id="qLabour" type="number" placeholder="Labour (R)" value="0">
<input class="form-input" id="qParts" type="number" placeholder="Parts (R)" value="0">
<button class="btn btn-success" onclick="createQuote()">Save Quote</button>
<button class="btn btn-dark" onclick="hideQuoteForm()">Cancel</button>
</div>
</div>
<div id="quoteList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- INVOICES -->
<!-- ═══════════════════════════════ -->
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

<!-- ═══════════════════════════════ -->
<!-- PARTS -->
<!-- ═══════════════════════════════ -->
<div id="parts" class="panel">
<div class="panel-title">🔩 Parts Catalog</div>
<input type="text" class="form-input" id="partsSearch" placeholder="🔍 Search parts..." oninput="filterParts()">
<div id="partsList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- INVENTORY -->
<!-- ═══════════════════════════════ -->
<div id="inventory" class="panel">
<div class="panel-title">📦 Inventory</div>
<button class="btn no-print" onclick="showInvForm()">+ Add Stock Item</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="invPartNum" placeholder="Part number">
<input class="form-input" id="invPartName" placeholder="Part name">
<input class="form-input" id="invCategory" placeholder="Category">
<input class="form-input" id="invQty" type="number" placeholder="Quantity">
<input class="form-input" id="invMinQty" type="number" placeholder="Minimum qty">
<input class="form-input" id="invCostPrice" type="number" placeholder="Cost price (R)">
<input class="form-input" id="invSellPrice" type="number" placeholder="Sell price (R)">
<input class="form-input" id="invSupplier" placeholder="Supplier">
<button class="btn btn-success" onclick="addInventory()">Save Item</button>
<button class="btn btn-dark" onclick="hideInvForm()">Cancel</button>
</div>
</div>
<div id="inventoryList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- PURCHASE ORDERS -->
<!-- ═══════════════════════════════ -->
<div id="purchase" class="panel">
<div class="panel-title">🛒 Purchase Orders</div>
<button class="btn no-print" onclick="showPOForm()">+ New Purchase Order</button>
<div id="poForm" style="display:none">
<div class="card">
<input class="form-input" id="poSupplier" placeholder="Supplier">
<textarea class="form-input" id="poItems" placeholder="Items (one per line)" rows="3"></textarea>
<input class="form-input" id="poTotal" type="number" placeholder="Total (R)">
<button class="btn btn-success" onclick="createPO()">Save PO</button>
<button class="btn btn-dark" onclick="hidePOForm()">Cancel</button>
</div>
</div>
<div id="poList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- STAFF -->
<!-- ═══════════════════════════════ -->
<div id="staff" class="panel">
<div class="panel-title">👷 Staff</div>
<button class="btn no-print" onclick="showStaffForm()">+ Add Staff</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="staffName" placeholder="Full name">
<input class="form-input" id="staffRole" placeholder="Role (e.g. Mechanic)">
<input class="form-input" id="staffPhone" placeholder="Phone">
<input class="form-input" id="staffEmail" placeholder="Email">
<input class="form-input" id="staffRate" type="number" placeholder="Hourly rate (R)" value="150">
<button class="btn btn-success" onclick="addStaff()">Save Staff</button>
<button class="btn btn-dark" onclick="hideStaffForm()">Cancel</button>
</div>
</div>
<div id="staffList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- CLOCK IN/OUT -->
<!-- ═══════════════════════════════ -->
<div id="clockin" class="panel">
<div class="panel-title">🕐 Clock In/Out</div>
<div id="clockinList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- EXPENSES -->
<!-- ═══════════════════════════════ -->
<div id="expenses" class="panel">
<div class="panel-title">💸 Expenses</div>
<button class="btn no-print" onclick="showExpenseForm()">+ Add Expense</button>
<div id="expenseForm" style="display:none">
<div class="card">
<select class="form-input" id="expCat">
<option>Rent</option><option>Utilities</option><option>Tools</option>
<option>Parts</option><option>Salaries</option><option>Fuel</option><option>Other</option>
</select>
<input class="form-input" id="expAmount" type="number" placeholder="Amount (R)">
<input class="form-input" id="expDate" type="date">
<textarea class="form-input" id="expNote" placeholder="Note" rows="2"></textarea>
<button class="btn btn-success" onclick="addExpense()">Save Expense</button>
<button class="btn btn-dark" onclick="hideExpenseForm()">Cancel</button>
</div>
</div>
<div id="expenseList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- FUEL LOG -->
<!-- ═══════════════════════════════ -->
<div id="fuel" class="panel">
<div class="panel-title">⛽ Fuel Log</div>
<button class="btn no-print" onclick="showFuelForm()">+ Add Fill-Up</button>
<div id="fuelForm" style="display:none">
<div class="card">
<input class="form-input" id="fuelVehicle" placeholder="Vehicle">
<input class="form-input" id="fuelKm" type="number" placeholder="Odometer (km)">
<input class="form-input" id="fuelLitres" type="number" step="0.01" placeholder="Litres">
<input class="form-input" id="fuelCost" type="number" step="0.01" placeholder="Total cost (R)">
<input class="form-input" id="fuelStation" placeholder="Station (optional)">
<input class="form-input" id="fuelDate" type="date">
<button class="btn btn-success" onclick="addFuel()">Save Fill-Up</button>
<button class="btn btn-dark" onclick="hideFuelForm()">Cancel</button>
</div>
</div>
<div id="fuelList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- WARRANTY -->
<!-- ═══════════════════════════════ -->
<div id="warranty" class="panel">
<div class="panel-title">🎁 Warranty Tracker</div>
<p style="font-size:12px;color:var(--text2);margin-bottom:12px">Active warranties on completed jobs</p>
<div id="warrantyList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- REMINDERS -->
<!-- ═══════════════════════════════ -->
<div id="reminders" class="panel">
<div class="panel-title">🗓️ Service Reminders</div>
<div id="remindersList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- WIRING -->
<!-- ═══════════════════════════════ -->
<div id="wiring" class="panel">
<div class="panel-title">🔌 Wiring Library</div>
<input type="text" class="form-input" id="wiringSearch" placeholder="🔍 Search circuits..." oninput="filterWiring()">
<div id="wiringList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- OBD-II -->
<!-- ═══════════════════════════════ -->
<div id="obd" class="panel">
<div class="panel-title">⚡ OBD-II PID Reference</div>
<input type="text" class="form-input" id="obdSearch" placeholder="🔍 Search PIDs..." oninput="filterOBD()">
<div id="obdList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- BULBS -->
<!-- ═══════════════════════════════ -->
<div id="bulbs" class="panel">
<div class="panel-title">💡 Bulb Chart</div>
<input type="text" class="form-input" id="bulbSearch" placeholder="🔍 Search vehicle..." oninput="filterBulbs()">
<div id="bulbList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- BATTERIES -->
<!-- ═══════════════════════════════ -->
<div id="batteries" class="panel">
<div class="panel-title">🔋 Battery Sizes</div>
<input type="text" class="form-input" id="battSearch" placeholder="🔍 Search vehicle..." oninput="filterBatt()">
<div id="battList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- TYRES -->
<!-- ═══════════════════════════════ -->
<div id="tyres" class="panel">
<div class="panel-title">🛞 Tyre Sizes</div>
<input type="text" class="form-input" id="tyreSearch" placeholder="🔍 Search vehicle..." oninput="filterTyre()">
<div id="tyreList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- FUSES -->
<!-- ═══════════════════════════════ -->
<div id="fuses" class="panel">
<div class="panel-title">🔌 Fuse Box Diagrams</div>
<div id="fuseList"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- SERVICE CALC -->
<!-- ═══════════════════════════════ -->
<div id="service" class="panel">
<div class="panel-title">⏰ Service Calculator</div>
<div class="card">
<input class="form-input" id="svcKm" type="number" placeholder="Current odometer (km)">
<select class="form-input" id="svcType">
<option value="petrol">Petrol Vehicle</option>
<option value="diesel">Diesel Vehicle</option>
<option value="truck_diesel">Truck / Heavy Diesel</option>
<option value="motorcycle">Motorcycle</option>
</select>
<button class="btn" onclick="calcService()">Calculate Next Service</button>
<div id="svcResult"></div>
</div>
</div>

<!-- ═══════════════════════════════ -->
<!-- INSPECT -->
<!-- ═══════════════════════════════ -->
<div id="inspect" class="panel">
<div class="panel-title">✅ Inspection Checklists</div>
<select class="form-input" id="inspectType" onchange="loadChecklist()">
<option value="pre_purchase">Pre-Purchase Inspection</option>
<option value="roadworthy">Roadworthy Checklist</option>
</select>
<div id="inspectList"><div class="loading">Select a checklist</div></div>
<button class="btn btn-dark" onclick="printChecklist()">🖨 Print Checklist</button>
</div>

<!-- ═══════════════════════════════ -->
<!-- BOLT CALC -->
<!-- ═══════════════════════════════ -->
<div id="boltcalc" class="panel">
<div class="panel-title">🔧 Bolt Torque Calculator</div>
<div class="card">
<label style="font-size:13px;font-weight:700">Bolt Size</label>
<select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M18</option><option>M20</option></select>
<label style="font-size:13px;font-weight:700">Grade</label>
<select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select>
<label style="font-size:13px;font-weight:700">Condition</label>
<select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly lubricated</option></select>
<button class="btn" onclick="calcTorque()">Calculate</button>
<div id="boltResult"></div>
</div>
</div>

<!-- ═══════════════════════════════ -->
<!-- TORQUE -->
<!-- ═══════════════════════════════ -->
<div id="torque" class="panel">
<div class="panel-title">⚙️ Torque Specs</div>
<input type="text" class="form-input" id="torqueSearch" placeholder="🔍 Search..." oninput="filterTorque()">
<h3 style="margin-bottom:8px;font-size:14px;color:var(--text2)">Bolt Torque</h3>
<div id="torqueTable"></div>
<h3 style="margin:16px 0 8px;font-size:14px;color:var(--text2)">Sequences</h3>
<div id="torqueSeq"></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- HISTORY -->
<!-- ═══════════════════════════════ -->
<div id="history" class="panel">
<div class="panel-title">🚗 Vehicle History</div>
<input type="text" class="form-input" id="vehicleSearch" placeholder="🔍 Search reg or vehicle..." oninput="searchVehicleHistory()">
<div id="vehicleHistory"><div class="loading">Enter search term above</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- ANALYTICS -->
<!-- ═══════════════════════════════ -->
<div id="analytics" class="panel">
<div class="panel-title">📈 Analytics</div>
<div id="analyticsContent"><div class="loading">Loading...</div></div>
</div>

<!-- ═══════════════════════════════ -->
<!-- TAX -->
<!-- ═══════════════════════════════ -->
<div id="tax" class="panel">
<div class="panel-title">🧾 Tax & Reports</div>
<div class="card">
<h3>Tax Report</h3>
<input class="form-input" id="taxFrom" type="date">
<input class="form-input" id="taxTo" type="date">
<button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV</button>
</div>
<div class="card">
<h3>Business Card</h3>
<div id="bizCard" style="padding:20px;background:white;color:black;border-radius:12px;border:2px solid #E65100;text-align:center">
<div id="bcLogo" style="font-size:48px">🔧</div>
<h2 id="bcName" style="color:#E65100;margin:8px 0">My Workshop</h2>
<p id="bcPhone" style="font-size:14px">Phone</p>
<p id="bcAddress" style="font-size:12px;color:#666">Address</p>
<p style="font-size:11px;color:#999;margin-top:8px">Powered by RamsTech</p>
</div>
<button class="btn" style="margin-top:12px" onclick="printBizCard()">🖨 Print Card</button>
</div>
</div>

<!-- ═══════════════════════════════ -->
<!-- SETTINGS -->
<!-- ═══════════════════════════════ -->
<div id="settings" class="panel">
<div class="panel-title">⚙️ Settings</div>
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

<!-- ═══════════════════════════════ -->
<!-- BOTTOM NAVIGATION -->
<!-- ═══════════════════════════════ -->
<div class="bottom-nav no-print">
<div class="bnav-item active" onclick="showTab('home',document.querySelectorAll('.bnav-item')[0])">
<div class="bnav-icon">🏠</div>
<div class="bnav-label">Home</div>
</div>
<div class="bnav-item" onclick="showTab('dashboard',document.querySelectorAll('.bnav-item')[1])">
<div class="bnav-icon">📊</div>
<div class="bnav-label">Dash</div>
</div>
<div class="bnav-item" onclick="showTab('chat',document.querySelectorAll('.bnav-item')[2])">
<div class="bnav-icon">🤖</div>
<div class="bnav-label">AI</div>
</div>
<div class="bnav-item" onclick="showTab('jobs',document.querySelectorAll('.bnav-item')[3])">
<div class="bnav-icon">📋</div>
<div class="bnav-label">Jobs</div>
</div>
<div class="bnav-item" onclick="showTab('settings',document.querySelectorAll('.bnav-item')[4])">
<div class="bnav-icon">⚙️</div>
<div class="bnav-label">More</div>
</div>
</div>

<script>
// ═══════════════════════════════════
// CATEGORY DEFINITIONS
// ═══════════════════════════════════
const CATEGORIES = {
  diagnostics: {
    name: 'Diagnostics',
    icon: '🔧',
    gradient: 'linear-gradient(135deg,#2196F3 0%,#0d47a1 100%)',
    items: [
      {icon:'🤖',label:'AI Chat',tab:'chat',color:'#3b82f6'},
      {icon:'📟',label:'Fault Codes',tab:'codes',color:'#ef4444'},
      {icon:'📖',label:'Problems',tab:'problems',color:'#f59e0b'},
      {icon:'🔍',label:'VIN Decoder',tab:'vin',color:'#8b5cf6'},
      {icon:'🎨',label:'Paint Match',tab:'paint',color:'#ec4899'},
      {icon:'📸',label:'Photo Diag',tab:'photo',color:'#06b6d4'}
    ]
  },
  workshop: {
    name: 'Workshop',
    icon: '📋',
    gradient: 'linear-gradient(135deg,#f59e0b 0%,#dc2626 100%)',
    items: [
      {icon:'📋',label:'Jobs',tab:'jobs',color:'#f59e0b'},
      {icon:'👥',label:'Customers',tab:'customers',color:'#10b981'},
      {icon:'📅',label:'Appointments',tab:'appointments',color:'#3b82f6'},
      {icon:'💬',label:'Quotes',tab:'quotes',color:'#8b5cf6'},
      {icon:'💰',label:'Invoices',tab:'invoices',color:'#10b981'}
    ]
  },
  operations: {
    name: 'Operations',
    icon: '⚙️',
    gradient: 'linear-gradient(135deg,#10b981 0%,#047857 100%)',
    items: [
      {icon:'📦',label:'Inventory',tab:'inventory',color:'#f59e0b'},
      {icon:'🛒',label:'Purchase',tab:'purchase',color:'#3b82f6'},
      {icon:'👷',label:'Staff',tab:'staff',color:'#10b981'},
      {icon:'🕐',label:'Clock In/Out',tab:'clockin',color:'#8b5cf6'},
      {icon:'💸',label:'Expenses',tab:'expenses',color:'#ef4444'},
      {icon:'⛽',label:'Fuel Log',tab:'fuel',color:'#f59e0b'},
      {icon:'🎁',label:'Warranty',tab:'warranty',color:'#ec4899'},
      {icon:'🗓️',label:'Reminders',tab:'reminders',color:'#06b6d4'}
    ]
  },
  reference: {
    name: 'Reference',
    icon: '📚',
    gradient: 'linear-gradient(135deg,#8b5cf6 0%,#4c1d95 100%)',
    items: [
      {icon:'🔩',label:'Parts',tab:'parts',color:'#6b7280'},
      {icon:'🔌',label:'Wiring',tab:'wiring',color:'#f59e0b'},
      {icon:'⚡',label:'OBD-II PIDs',tab:'obd',color:'#eab308'},
      {icon:'💡',label:'Bulbs',tab:'bulbs',color:'#f59e0b'},
      {icon:'🔋',label:'Batteries',tab:'batteries',color:'#10b981'},
      {icon:'🛞',label:'Tyres',tab:'tyres',color:'#1f2937'},
      {icon:'🔌',label:'Fuses',tab:'fuses',color:'#ef4444'},
      {icon:'⏰',label:'Service Calc',tab:'service',color:'#3b82f6'},
      {icon:'✅',label:'Inspect',tab:'inspect',color:'#10b981'},
      {icon:'🔧',label:'Bolt Calc',tab:'boltcalc',color:'#8b5cf6'},
      {icon:'⚙️',label:'Torque',tab:'torque',color:'#ec4899'}
    ]
  },
  business: {
    name: 'Business',
    icon: '💼',
    gradient: 'linear-gradient(135deg,#1f2937 0%,#4b5563 100%)',
    items: [
      {icon:'📊',label:'Dashboard',tab:'dashboard',color:'#3b82f6'},
      {icon:'🚗',label:'History',tab:'history',color:'#10b981'},
      {icon:'📈',label:'Analytics',tab:'analytics',color:'#8b5cf6'},
      {icon:'🧾',label:'Tax & Reports',tab:'tax',color:'#f59e0b'},
      {icon:'⚙️',label:'Settings',tab:'settings',color:'#6b7280'}
    ]
  }
};

// ═══════════════════════════════════
// RENDER CATEGORY GRID
// ═══════════════════════════════════
document.getElementById('categoryGrid').innerHTML = Object.entries(CATEGORIES).map(([key, cat]) =>
  `<div class="cat-card" style="background:${cat.gradient}" onclick="openCategory('${key}')">
    <div class="cat-icon">${cat.icon}</div>
    <div class="cat-info">
      <div class="cat-name">${cat.name}</div>
      <div class="cat-count">${cat.items.length} features</div>
    </div>
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

// ═══════════════════════════════════
// TAB NAVIGATION
// ═══════════════════════════════════
const TABS = ['home','dashboard','chat','codes','problems','vin','paint','photo','jobs','customers','appointments','quotes','invoices','parts','inventory','purchase','staff','clockin','expenses','fuel','warranty','reminders','wiring','obd','bulbs','batteries','tyres','fuses','service','inspect','boltcalc','torque','history','analytics','tax','settings'];

function showTab(name, el) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.bnav-item').forEach(t => t.classList.remove('active'));
  const panel = document.getElementById(name);
  if (panel) panel.classList.add('active');
  if (el) el.classList.add('active');
  window.scrollTo(0, 0);

  const loaders = {
    codes: () => !document.getElementById('codeResults').dataset.loaded && searchCodes(),
    problems: () => !document.getElementById('problemList').dataset.loaded && loadProblems(),
    jobs: () => { loadJobs(); loadStaffDropdown(); },
    customers: loadCustomers,
    appointments: loadAppts,
    quotes: loadQuotes,
    invoices: loadInvoices,
    parts: () => !document.getElementById('partsList').dataset.loaded && loadParts(),
    inventory: loadInventory,
    purchase: loadPOs,
    staff: loadStaff,
    clockin: loadClockin,
    expenses: loadExpenses,
    fuel: loadFuel,
    warranty: loadWarranty,
    reminders: loadReminders,
    wiring: loadWiring,
    obd: loadOBD,
    bulbs: loadBulbs,
    batteries: loadBatt,
    tyres: loadTyre,
    fuses: loadFuses,
    inspect: () => document.getElementById('inspectType').value === 'pre_purchase' && loadChecklist(),
    torque: loadTorque,
    analytics: loadAnalytics,
    tax: loadBizCard,
    settings: loadSettings,
    dashboard: loadDashboard
  };
  if (loaders[name]) try { loaders[name](); } catch (e) { console.error(e); }
}

// THEME
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

// LANGUAGE
let LANG = localStorage.getItem('lang') || 'en';
let STRINGS = {};
async function loadLang() {
  try {
    const r = await fetch('/api/translations/' + LANG);
    const d = await r.json();
    STRINGS = d.strings;
    document.getElementById('langSel').value = LANG;
  } catch (e) {}
}
function setLang() {
  LANG = document.getElementById('langSel').value;
  localStorage.setItem('lang', LANG);
  loadLang();
}
loadLang();

// HELPERS
async function checkStatus() {
  try { await fetch('/health'); document.getElementById('status').innerHTML = '<span class="status-online">✓ Backend Online</span>'; }
  catch (e) { document.getElementById('status').innerHTML = '<span class="status-offline">✗ Backend Offline</span>'; }
}
checkStatus();
function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
async function jget(u) { const r = await fetch(u); return r.json(); }
async function jpost(u, b) { const r = await fetch(u, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); return r.json(); }
async function jput(u, b) { const r = await fetch(u, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); return r.json(); }
async function jdel(u) { const r = await fetch(u, {method:'DELETE'}); return r.json(); }

// ═══════════════════════════════════
// PHOTO COMPRESSION
// ═══════════════════════════════════
function compressImage(file, maxWidth, quality) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let { width, height } = img;
        if (width > maxWidth) { height = (height * maxWidth) / width; width = maxWidth; }
        canvas.width = width; canvas.height = height;
        canvas.getContext('2d').drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', quality));
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ═══════════════════════════════════
// SIGNATURE
// ═══════════════════════════════════
let sigPad = null, sigCtx = null, sigDrawing = false, sigData = '';
function openSignature() {
  const modal = document.createElement('div');
  modal.id = 'sigModal';
  modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px)';
  modal.innerHTML = '<div style="background:white;border-radius:20px;padding:20px;width:100%;max-width:500px;box-shadow:0 20px 60px rgba(0,0,0,.4)"><h3 style="color:#E65100;margin-bottom:12px;font-weight:800">✍️ Customer Signature</h3><canvas id="sigPad" width="440" height="200" style="border:2px dashed #ddd;border-radius:12px;width:100%;touch-action:none;background:white"></canvas><div style="margin-top:14px;display:flex;gap:8px"><button class="btn-sm gray" onclick="clearSig()" style="flex:1;padding:12px">Clear</button><button class="btn-sm green" onclick="saveSig()" style="flex:1;padding:12px">Confirm</button><button class="btn-sm red" onclick="closeSig()" style="flex:1;padding:12px">Cancel</button></div></div>';
  document.body.appendChild(modal);
  sigPad = document.getElementById('sigPad');
  sigCtx = sigPad.getContext('2d');
  sigCtx.strokeStyle = '#000';
  sigCtx.lineWidth = 2.5;
  sigCtx.lineCap = 'round';
  const start = (e) => { sigDrawing = true; sigCtx.beginPath(); const p = getPos(e); sigCtx.moveTo(p.x, p.y); e.preventDefault(); };
  const draw = (e) => { if (!sigDrawing) return; const p = getPos(e); sigCtx.lineTo(p.x, p.y); sigCtx.stroke(); e.preventDefault(); };
  const stop = () => { sigDrawing = false; };
  const getPos = (e) => {
    const rect = sigPad.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    return { x: x * (sigPad.width / rect.width), y: y * (sigPad.height / rect.height) };
  };
  sigPad.addEventListener('mousedown', start);
  sigPad.addEventListener('mousemove', draw);
  sigPad.addEventListener('mouseup', stop);
  sigPad.addEventListener('touchstart', start, { passive: false });
  sigPad.addEventListener('touchmove', draw, { passive: false });
  sigPad.addEventListener('touchend', stop);
}
function clearSig() { sigCtx.clearRect(0, 0, sigPad.width, sigPad.height); }
function saveSig() {
  sigData = sigPad.toDataURL('image/png');
  document.getElementById('sigPreview').innerHTML = '<img src="' + sigData + '" style="width:100%;border:1px solid #ddd;border-radius:12px;background:white">';
  closeSig();
}
function closeSig() { const m = document.getElementById('sigModal'); if (m) m.remove(); }

// VOICE
let rec = null, isRec = false;
function toggleMic() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) { alert('Voice not supported'); return; }
  if (!rec) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    rec = new SR();
    rec.lang = 'en-ZA';
    rec.onresult = e => { document.getElementById('chatInput').value = e.results[0][0].transcript; resetMic(); sendMsg(); };
    rec.onerror = resetMic;
    rec.onend = resetMic;
  }
  function resetMic() { isRec = false; document.getElementById('micBtn').classList.remove('recording'); document.getElementById('micBtn').textContent = '🎤'; }
  if (isRec) { rec.stop(); resetMic(); }
  else { try { rec.start(); isRec = true; document.getElementById('micBtn').classList.add('recording'); document.getElementById('micBtn').textContent = '⏹'; } catch (e) { alert(e.message); } }
}

// CHAT
async function sendMsg() {
  const i = document.getElementById('chatInput');
  const m = i.value.trim();
  if (!m) return;
  const b = document.getElementById('chatBox');
  b.innerHTML += '<div class="msg user">' + esc(m) + '</div>';
  i.value = '';
  b.scrollTop = b.scrollHeight;
  b.innerHTML += '<div class="msg ai" id="typ">Thinking...</div>';
  b.scrollTop = b.scrollHeight;
  try {
    const d = await jpost('/api/chat', {message:m});
    document.getElementById('typ').outerHTML = '<div class="msg ai">' + esc(d.reply) + '</div>';
  } catch (e) {
    document.getElementById('typ').outerHTML = '<div class="msg ai">Error</div>';
  }
  b.scrollTop = b.scrollHeight;
}

// DASHBOARD
let rC = null, jC = null;
async function loadDashboard() {
  try {
    const d = await jget('/api/stats');
    document.getElementById('dashStats').innerHTML = '<div class="stats-row"><div class="stat-card blue"><div class="num">' + d.jobs_total + '</div><div class="lbl">Jobs</div></div><div class="stat-card purple"><div class="num">' + d.jobs_open + '</div><div class="lbl">Open</div></div><div class="stat-card green"><div class="num">' + d.jobs_completed + '</div><div class="lbl">Done</div></div><div class="stat-card"><div class="num">' + d.customers + '</div><div class="lbl">Customers</div></div><div class="stat-card green"><div class="num">R' + d.revenue + '</div><div class="lbl">Revenue</div></div><div class="stat-card red"><div class="num">R' + d.expenses + '</div><div class="lbl">Expenses</div></div></div>';
    if (rC) rC.destroy();
    const c1 = document.getElementById('revenueChart');
    if (c1) rC = new Chart(c1, {type:'line', data:{labels:d.revenue_labels, datasets:[{data:d.revenue_data, borderColor:'#667eea', backgroundColor:'rgba(102,126,234,.15)', tension:.4, fill:true, borderWidth:3, pointBackgroundColor:'#667eea', pointRadius:4}]}, options:{responsive:true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}});
    if (jC) jC.destroy();
    const c2 = document.getElementById('jobChart');
    if (c2) jC = new Chart(c2, {type:'doughnut', data:{labels:['New','Progress','Done'], datasets:[{data:[d.jobs_new, d.jobs_progress, d.jobs_completed], backgroundColor:['#6b7280','#f59e0b','#10b981'], borderWidth:0}]}, options:{responsive:true, plugins:{legend:{position:'bottom'}}}});
    const ls = await jget('/api/inventory/low-stock');
    document.getElementById('dashLowStock').innerHTML = ls.items.length ? ls.items.map(i => '<div class="list-item">⚠️ <strong>' + esc(i.name) + '</strong> — only ' + i.qty + ' left</div>').join('') : '<p style="color:var(--text2)">✓ All stock OK</p>';
    const w = await jget('/api/warranty');
    const soon = w.warranties.filter(x => x.status === 'active').slice(0, 5);
    document.getElementById('dashWarranty').innerHTML = soon.length ? soon.map(x => '<div class="list-item">⏰ ' + esc(x.vehicle) + ' — ' + x.days_left + ' days</div>').join('') : '<p style="color:var(--text2)">No active warranties</p>';
  } catch (e) {}
}

// CODES
async function searchCodes() {
  const q = document.getElementById('codeSearch').value;
  const c = document.getElementById('codeResults');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/fault-codes?search=' + encodeURIComponent(q));
    c.dataset.loaded = '1';
    c.innerHTML = d.codes.length ? d.codes.map(x => '<div class="card"><h3>' + x.code + '<span class="badge ' + x.severity.toLowerCase() + '">' + x.severity + '</span></h3><p><strong>' + esc(x.description) + '</strong></p><p style="color:var(--text2);font-size:12px">' + esc(x.system) + '</p><p style="margin-top:8px"><strong>Causes:</strong></p>' + x.causes.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '<p style="margin-top:8px"><strong>Diagnostic Steps:</strong></p>' + x.steps.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '</div>').join('') : '<div class="card"><p>No matches found</p></div>';
  } catch (e) { c.innerHTML = '<div class="card"><p>Error loading</p></div>'; }
}

// PROBLEMS
let probData = [];
async function loadProblems() {
  const d = await jget('/api/problems');
  probData = d.problems;
  document.getElementById('problemList').dataset.loaded = '1';
  filterProblems();
}
function filterProblems() {
  const q = (document.getElementById('problemSearch').value || '').toLowerCase();
  const f = probData.filter(x => !q || x.title.toLowerCase().includes(q) || x.system.toLowerCase().includes(q));
  document.getElementById('problemList').innerHTML = f.length ? f.map(x => '<div class="card"><h3>' + esc(x.title) + '<span class="badge ' + x.severity.toLowerCase() + '">' + x.severity + '</span></h3><p style="color:var(--text2);font-size:12px">' + esc(x.system) + '</p><p><strong>Causes:</strong></p>' + x.causes.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '<p><strong>Checks:</strong></p>' + x.checks.map(y => '<div class="list-item">• ' + esc(y) + '</div>').join('') + '</div>').join('') : '<div class="card"><p>No matches</p></div>';
}

// VIN
async function decodeVin() {
  const vin = document.getElementById('vinInput').value.trim().toUpperCase();
  const c = document.getElementById('vinResult');
  if (vin.length !== 17) { c.innerHTML = '<div class="card"><p style="color:#ef4444">VIN must be 17 characters</p></div>'; return; }
  c.innerHTML = '<div class="loading">Decoding...</div>';
  try {
    const d = await jget('/api/vin/' + vin);
    if (d.detail) { c.innerHTML = '<div class="card"><p style="color:#ef4444">' + d.detail + '</p></div>'; return; }
    c.innerHTML = '<div class="card"><h3>🔍 Vehicle Information</h3><p><strong>VIN:</strong> <span style="font-family:monospace">' + d.vin + '</span></p><p><strong>Manufacturer:</strong> ' + d.manufacturer + '</p><p><strong>Country:</strong> ' + d.country + '</p><p><strong>Year:</strong> ' + d.year + '</p></div>';
  } catch (e) { c.innerHTML = '<div class="card"><p>Error</p></div>'; }
}

// PAINT
let paintB64 = '';
async function previewPaint(e) {
  const f = e.target.files[0];
  if (!f) return;
  paintB64 = await compressImage(f, 1200, 0.75);
  document.getElementById('paintPreview').innerHTML = '<img class="img-preview" src="' + paintB64 + '">';
}
async function matchPaint() {
  const btn = document.getElementById('paintBtn');
  const c = document.getElementById('paintResult');
  if (!paintB64) { c.innerHTML = '<div class="card"><p style="color:#ef4444">Select an image first</p></div>'; return; }
  btn.disabled = true; btn.textContent = '🎨 Analyzing...';
  c.innerHTML = '<div class="loading">Analyzing paint colour...</div>';
  try {
    const d = await jpost('/api/paint/match', {image_base64:paintB64, vehicle_info:document.getElementById('paintVehicle').value});
    if (!d.success) { c.innerHTML = '<div class="card"><p style="color:#ef4444">' + (d.error || 'Failed') + '</p></div>'; }
    else {
      const col = d.detected_colour;
      let h = '<div class="card"><div class="swatch" style="background:' + col.hex_code + '"></div><h3>' + esc(col.name) + '</h3><p><strong>' + esc(col.finish) + '</strong> • ' + esc(col.colour_family) + '</p><p style="font-family:monospace">' + col.hex_code + '</p><p>Confidence: <strong>' + d.confidence + '</strong></p></div>';
      if (d.brand_codes) { h += '<div class="card"><h3>Brand Codes</h3>'; d.brand_codes.forEach(b => { h += '<div class="list-item"><strong>' + esc(b.brand) + ':</strong> ' + esc(b.code) + '</div>'; }); h += '</div>'; }
      if (d.mixing_formula) { const m = d.mixing_formula; h += '<div class="card"><h3>Mixing Formula</h3><p><strong>Base:</strong> ' + esc(m.base_colour) + '</p>'; if (m.toners) m.toners.forEach(t => { h += '<div class="list-item">• ' + esc(t.name) + ': ' + esc(t.parts) + ' parts</div>'; }); h += '<p><strong>Reducer:</strong> ' + esc(m.reducer) + '</p></div>'; }
      c.innerHTML = h;
    }
  } catch (e) { c.innerHTML = '<div class="card"><p>Error</p></div>'; }
  btn.disabled = false; btn.textContent = '🎨 Match Paint Colour';
}

// PHOTO DIAG
let diagB64 = '';
async function previewDiag(e) {
  const f = e.target.files[0];
  if (!f) return;
  diagB64 = await compressImage(f, 1200, 0.75);
  document.getElementById('photoPreview').innerHTML = '<img class="img-preview" src="' + diagB64 + '">';
}
async function diagnosePhoto() {
  const btn = document.getElementById('photoBtn');
  const c = document.getElementById('photoResult');
  if (!diagB64) { c.innerHTML = '<div class="card"><p style="color:#ef4444">Select an image</p></div>'; return; }
  btn.disabled = true; btn.textContent = '📸 Analyzing...';
  c.innerHTML = '<div class="loading">Analyzing photo...</div>';
  try {
    const d = await jpost('/api/diagnose/photo', {image_base64:diagB64, vehicle_info:document.getElementById('photoVehicle').value});
    if (!d.success) { c.innerHTML = '<div class="card"><p style="color:#ef4444">' + (d.error || 'Failed') + '</p></div>'; }
    else {
      let h = '<div class="card"><h3>🔍 ' + esc(d.problem || 'Detected') + '</h3><p><strong>Confidence:</strong> ' + d.confidence + '</p><p>' + esc(d.description || '') + '</p></div>';
      if (d.possible_causes) { h += '<div class="card"><h3>Possible Causes</h3>' + d.possible_causes.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>'; }
      if (d.diagnostic_steps) { h += '<div class="card"><h3>Diagnostic Steps</h3>' + d.diagnostic_steps.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>'; }
      if (d.safety_warnings) { h += '<div class="card" style="background:#fef2f2;border-color:#fecaca"><h3 style="color:#dc2626">⚠️ Safety</h3>' + d.safety_warnings.map(x => '<div class="list-item">⚠ ' + esc(x) + '</div>').join('') + '</div>'; }
      c.innerHTML = h;
    }
  } catch (e) { c.innerHTML = '<div class="card"><p>Error</p></div>'; }
  btn.disabled = false; btn.textContent = '📸 Analyze Photo';
}

// JOBS
let jobPhotos = [];
async function addJobPhotos(e) {
  for (const f of Array.from(e.target.files)) {
    jobPhotos.push(await compressImage(f, 1000, 0.7));
  }
  renderJobThumbs();
}
function renderJobThumbs() {
  document.getElementById('jobPhotoThumbs').innerHTML = jobPhotos.map((p, i) => '<div class="thumb-wrap"><img class="thumb" src="' + p + '"><button class="thumb-del" onclick="removeJobPhoto(' + i + ')">×</button></div>').join('');
}
function removeJobPhoto(i) { jobPhotos.splice(i, 1); renderJobThumbs(); }
function showJobForm() { document.getElementById('jobForm').style.display = 'block'; }
function hideJobForm() {
  document.getElementById('jobForm').style.display = 'none';
  jobPhotos = []; renderJobThumbs();
  sigData = ''; document.getElementById('sigPreview').innerHTML = '';
}
async function loadStaffDropdown() {
  try {
    const d = await jget('/api/staff');
    const sel = document.getElementById('jobAssigned');
    sel.innerHTML = '<option value="">— Assign to staff —</option>' + d.staff.map(s => '<option value="' + esc(s.name) + '">' + esc(s.name) + '</option>').join('');
  } catch (e) {}
}
async function createJob() {
  const c = document.getElementById('jobCustomer').value.trim();
  const v = document.getElementById('jobVehicle').value.trim();
  const comp = document.getElementById('jobComplaint').value.trim();
  if (!c || !v || !comp) { alert('Please fill customer, vehicle, and complaint'); return; }
  try {
    await jpost('/api/jobs', {customer:c, phone:document.getElementById('jobPhone').value, vehicle:v, registration:document.getElementById('jobVehicleReg').value, km:parseInt(document.getElementById('jobKm').value) || 0, complaint:comp, assigned_to:document.getElementById('jobAssigned').value, warranty_months:parseInt(document.getElementById('jobWarranty').value) || 6, photos:jobPhotos, signature:sigData});
    ['jobCustomer','jobPhone','jobVehicle','jobComplaint','jobVehicleReg','jobKm'].forEach(id => document.getElementById(id).value = '');
    sigData = ''; document.getElementById('sigPreview').innerHTML = '';
    hideJobForm();
    loadJobs();
  } catch (e) { alert(e.message); }
}
async function loadJobs() {
  const c = document.getElementById('jobList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/jobs');
    if (!d.jobs.length) { c.innerHTML = '<div class="card"><p>No jobs yet. Tap + New Job Card to create one.</p></div>'; return; }
    c.innerHTML = d.jobs.reverse().map(j => {
      const s = j.status.toLowerCase().replace(' ', '');
      let ph = j.photos && j.photos.length ? '<div class="thumb-row">' + j.photos.map(p => '<img class="thumb" src="' + p + '">').join('') + '</div>' : '';
      let cost = j.total ? '<div style="margin-top:10px;padding:10px;background:linear-gradient(135deg,#dcfce7,#bbf7d0);border-radius:10px;font-size:13px"><strong>💰 Total: R' + j.total.toFixed(2) + '</strong></div>' : '';
      let as = j.assigned_to ? '<p style="color:var(--text2);font-size:12px">👷 ' + esc(j.assigned_to) + '</p>' : '';
      let sig = j.signature ? '<div style="margin-top:10px"><strong style="font-size:12px">Customer signature:</strong><br><img src="' + j.signature + '" style="width:200px;border:1px solid #ddd;background:white;border-radius:8px;margin-top:6px"></div>' : '';
      return '<div class="card" id="job-' + j.id + '"><h3>Job #' + j.id + ' <span class="badge ' + s + '">' + esc(j.status) + '</span></h3><p><strong>' + esc(j.customer) + '</strong></p><p>🚗 ' + esc(j.vehicle) + (j.registration ? ' (' + esc(j.registration) + ')' : '') + '</p>' + as + '<p style="color:var(--text2)">' + esc(j.complaint) + '</p>' + ph + cost + sig + '<p style="font-size:11px;color:var(--text2);margin-top:6px">' + esc(j.created) + '</p><div class="no-print" style="margin-top:10px"><button class="btn-sm blue" onclick="upJob(\'' + j.id + '\',\'In Progress\')">In Progress</button><button class="btn-sm green" onclick="upJob(\'' + j.id + '\',\'Completed\')">Complete</button><button class="btn-sm purple" onclick="setCost(\'' + j.id + '\')">💰 Cost</button><button class="btn-sm whatsapp" onclick="waJob(\'' + j.id + '\')">📱</button><button class="btn-sm gray" onclick="printJob(\'' + j.id + '\')">🖨</button></div></div>';
    }).join('');
  } catch (e) { c.innerHTML = '<div class="card"><p>Error loading jobs</p></div>'; }
}
async function upJob(id, s) { await jput('/api/jobs/' + id, {status:s, note:'Status → ' + s}); loadJobs(); }
async function setCost(id) {
  const h = prompt('Labour hours:', '1');
  if (h === null) return;
  const p = prompt('Parts cost (R):', '0');
  if (p === null) return;
  const rate = await getRate();
  await jpost('/api/jobs/' + id + '/cost', {labour_hours:parseFloat(h), labour_rate:rate, parts_cost:parseFloat(p)});
  loadJobs();
}
async function getRate() { try { const r = await jget('/api/workshop'); return r.labour_rate || 450; } catch (e) { return 450; } }
function waJob(id) {
  jget('/api/jobs').then(d => {
    const j = d.jobs.find(x => x.id == id);
    if (!j) return;
    const txt = '🔧 *Job #' + j.id + '*\n' + j.customer + '\n' + j.vehicle + '\n' + (j.registration ? 'Reg: ' + j.registration + '\n' : '') + 'Issue: ' + j.complaint + '\nStatus: ' + j.status + (j.total ? '\nTotal: R' + j.total.toFixed(2) : '');
    window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
  });
}
function printJob(id) {
  const el = document.getElementById('job-' + id);
  const w = window.open('', '', 'width=800,height=600');
  w.document.write('<html><head><title>Job #' + id + '</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}img{max-width:200px;margin:4px}</style></head><body><h1>' + document.getElementById('logoDisplay').textContent + ' ' + document.getElementById('wsNameDisplay').textContent + ' — Job #' + id + '</h1>');
  w.document.write(el.innerHTML.replace(/<div class="no-print".*?<\/div>/gs, ''));
  w.document.write('</body></html>');
  w.document.close();
  setTimeout(() => w.print(), 500);
}

// CUSTOMERS
function showCustomerForm() { document.getElementById('customerForm').style.display = 'block'; }
function hideCustomerForm() { document.getElementById('customerForm').style.display = 'none'; }
async function createCustomer() {
  const n = document.getElementById('custName').value.trim();
  const p = document.getElementById('custPhone').value.trim();
  if (!n || !p) { alert('Name and phone required'); return; }
  await jpost('/api/customers', {name:n, phone:p, email:document.getElementById('custEmail').value, address:document.getElementById('custAddress').value});
  ['custName','custPhone','custEmail','custAddress'].forEach(id => document.getElementById(id).value = '');
  hideCustomerForm();
  loadCustomers();
}
async function loadCustomers() {
  const c = document.getElementById('customerList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/customers');
    c.innerHTML = d.customers.length ? d.customers.reverse().map(x => '<div class="card"><h3>👤 ' + esc(x.name) + '</h3><p>📞 ' + esc(x.phone) + '</p>' + (x.email ? '<p>📧 ' + esc(x.email) + '</p>' : '') + (x.address ? '<p>📍 ' + esc(x.address) + '</p>' : '') + '<button class="btn-sm whatsapp" onclick="waCust(\'' + esc(x.phone) + '\')">📱 WhatsApp</button></div>').join('') : '<div class="card"><p>No customers yet</p></div>';
  } catch (e) {}
}
function waCust(p) { window.open('https://wa.me/' + p.replace(/\D/g, ''), '_blank'); }

// APPOINTMENTS
function showApptForm() { document.getElementById('apptForm').style.display = 'block'; }
function hideApptForm() { document.getElementById('apptForm').style.display = 'none'; }
async function createAppt() {
  const c = document.getElementById('apptCustomer').value.trim();
  const d = document.getElementById('apptDate').value;
  const t = document.getElementById('apptTime').value;
  if (!c || !d || !t) { alert('Customer, date, time required'); return; }
  await jpost('/api/appointments', {customer:c, phone:document.getElementById('apptPhone').value, vehicle:document.getElementById('apptVehicle').value, service:document.getElementById('apptService').value, date:d, time:t});
  ['apptCustomer','apptPhone','apptVehicle','apptService','apptDate','apptTime'].forEach(id => document.getElementById(id).value = '');
  hideApptForm();
  loadAppts();
}
async function loadAppts() {
  const c = document.getElementById('apptList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/appointments');
    const s = d.appointments.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
    c.innerHTML = s.length ? s.map(a => '<div class="card"><h3>📅 ' + esc(a.date) + ' at ' + esc(a.time) + '</h3><p><strong>' + esc(a.customer) + '</strong></p>' + (a.phone ? '<p>📞 ' + esc(a.phone) + '</p>' : '') + (a.vehicle ? '<p>🚗 ' + esc(a.vehicle) + '</p>' : '') + (a.service ? '<p style="color:var(--text2)">' + esc(a.service) + '</p>' : '') + '<button class="btn-sm red" onclick="delAppt(\'' + a.id + '\')">Delete</button></div>').join('') : '<div class="card"><p>No appointments</p></div>';
  } catch (e) {}
}
async function delAppt(id) { if (!confirm('Delete this appointment?')) return; await jdel('/api/appointments/' + id); loadAppts(); }

// QUOTES
function showQuoteForm() { document.getElementById('quoteForm').style.display = 'block'; }
function hideQuoteForm() { document.getElementById('quoteForm').style.display = 'none'; }
async function createQuote() {
  const c = document.getElementById('qCustomer').value.trim();
  const d = document.getElementById('qDesc').value.trim();
  if (!c || !d) { alert('Customer and description required'); return; }
  await jpost('/api/quotes', {customer:c, vehicle:document.getElementById('qVehicle').value, description:d, labour:parseFloat(document.getElementById('qLabour').value) || 0, parts:parseFloat(document.getElementById('qParts').value) || 0});
  ['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id => document.getElementById(id).value = '');
  hideQuoteForm();
  loadQuotes();
}
async function loadQuotes() {
  const c = document.getElementById('quoteList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/quotes');
    c.innerHTML = d.quotes.length ? d.quotes.reverse().map(q => '<div class="card"><h3>💬 Quote #' + q.id + '</h3><p><strong>' + esc(q.customer) + '</strong></p><p>' + esc(q.description) + '</p><div class="list-item">Labour: R' + q.labour.toFixed(2) + '</div><div class="list-item">Parts: R' + q.parts.toFixed(2) + '</div><div class="list-item"><strong>Total: R' + q.total.toFixed(2) + '</strong></div><div style="margin-top:10px"><button class="btn-sm green" onclick="acceptQuote(\'' + q.id + '\')">Accept → Invoice</button><button class="btn-sm red" onclick="delQuote(\'' + q.id + '\')">Delete</button></div></div>').join('') : '<div class="card"><p>No quotes yet</p></div>';
  } catch (e) {}
}
async function acceptQuote(id) { const r = await jpost('/api/quotes/' + id + '/accept', {}); if (r.success) { alert('Converted to invoice'); loadQuotes(); } }
async function delQuote(id) { if (!confirm('Delete?')) return; await jdel('/api/quotes/' + id); loadQuotes(); }

// INVOICES
function showInvoiceForm() { document.getElementById('invoiceForm').style.display = 'block'; }
function hideInvoiceForm() { document.getElementById('invoiceForm').style.display = 'none'; }
async function createInvoice() {
  const c = document.getElementById('invCustomer').value.trim();
  const d = document.getElementById('invDesc').value.trim();
  if (!c || !d) { alert('Customer and description required'); return; }
  await jpost('/api/invoices', {customer:c, vehicle:document.getElementById('invVehicle').value, description:d, labour:parseFloat(document.getElementById('invLabour').value) || 0, parts:parseFloat(document.getElementById('invParts').value) || 0});
  ['invCustomer','invVehicle','invDesc','invLabour','invParts'].forEach(id => document.getElementById(id).value = '');
  hideInvoiceForm();
  loadInvoices();
}
async function loadInvoices() {
  const c = document.getElementById('invoiceList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/invoices');
    c.innerHTML = d.invoices.length ? d.invoices.reverse().map(i => {
      const s = i.paid ? 'paid' : (i.amount_paid > 0 ? 'partial' : 'outstanding');
      return '<div class="card" id="inv-' + i.id + '"><h3>Invoice #' + i.id + ' <span class="badge ' + s + '">' + s.toUpperCase() + '</span></h3><p><strong>' + esc(i.customer) + '</strong></p><p>' + esc(i.description) + '</p><div class="list-item">Labour: R' + i.labour.toFixed(2) + '</div><div class="list-item">Parts: R' + i.parts.toFixed(2) + '</div><div class="list-item"><strong>Total: R' + i.total.toFixed(2) + '</strong></div><div class="list-item">Paid: R' + (i.amount_paid || 0).toFixed(2) + ' | Balance: R' + (i.total - (i.amount_paid || 0)).toFixed(2) + '</div><div class="no-print" style="margin-top:10px"><button class="btn-sm green" onclick="recordPay(\'' + i.id + '\')">💰 Payment</button><button class="btn-sm whatsapp" onclick="waInv(\'' + i.id + '\')">📱</button><button class="btn-sm blue" onclick="printInv(\'' + i.id + '\')">🖨</button></div></div>';
    }).join('') : '<div class="card"><p>No invoices yet</p></div>';
  } catch (e) {}
}
async function recordPay(id) { const a = prompt('Amount received (R):'); if (!a) return; await jpost('/api/invoices/' + id + '/pay', {amount:parseFloat(a)}); loadInvoices(); }
function waInv(id) {
  jget('/api/invoices').then(d => {
    const i = d.invoices.find(x => x.id == id);
    const txt = '🔧 *' + document.getElementById('wsNameDisplay').textContent + '*\nInvoice #' + i.id + '\n' + i.customer + '\n' + i.description + '\nTotal: R' + i.total.toFixed(2);
    window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
  });
}
function printInv(id) {
  const el = document.getElementById('inv-' + id);
  const w = window.open('', '', 'width=800,height=600');
  w.document.write('<html><head><title>Invoice #' + id + '</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}</style></head><body><h1>' + document.getElementById('logoDisplay').textContent + ' ' + document.getElementById('wsNameDisplay').textContent + ' — Invoice #' + id + '</h1>');
  w.document.write(el.innerHTML.replace(/<div class="no-print".*?<\/div>/gs, ''));
  w.document.write('</body></html>');
  w.document.close();
  setTimeout(() => w.print(), 500);
}

// PARTS
let partsData = [];
async function loadParts() { const d = await jget('/api/parts'); partsData = d.parts; document.getElementById('partsList').dataset.loaded = '1'; filterParts(); }
function filterParts() {
  const q = (document.getElementById('partsSearch').value || '').toLowerCase();
  const f = partsData.filter(x => !q || x.name.toLowerCase().includes(q) || x.number.toLowerCase().includes(q) || x.brand.toLowerCase().includes(q));
  document.getElementById('partsList').innerHTML = f.map(p => '<div class="card"><h3>' + esc(p.name) + '</h3><p style="font-family:monospace;font-size:12px">' + esc(p.number) + '</p><p>Brand: <strong>' + esc(p.brand) + '</strong> | ' + esc(p.category) + '</p><p style="font-size:16px;color:var(--primary);font-weight:700">R' + p.price + '</p></div>').join('') || '<div class="card"><p>No matches</p></div>';
}

// INVENTORY
function showInvForm() { document.getElementById('invForm').style.display = 'block'; }
function hideInvForm() { document.getElementById('invForm').style.display = 'none'; }
async function addInventory() {
  const n = document.getElementById('invPartName').value.trim();
  if (!n) { alert('Part name required'); return; }
  await jpost('/api/inventory', {part_number:document.getElementById('invPartNum').value, name:n, category:document.getElementById('invCategory').value, qty:parseInt(document.getElementById('invQty').value) || 0, min_qty:parseInt(document.getElementById('invMinQty').value) || 5, cost_price:parseFloat(document.getElementById('invCostPrice').value) || 0, sell_price:parseFloat(document.getElementById('invSellPrice').value) || 0, supplier:document.getElementById('invSupplier').value});
  ['invPartNum','invPartName','invCategory','invQty','invMinQty','invCostPrice','invSellPrice','invSupplier'].forEach(id => document.getElementById(id).value = '');
  hideInvForm();
  loadInventory();
}
async function loadInventory() {
  const c = document.getElementById('inventoryList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/inventory');
    c.innerHTML = d.items.length ? d.items.map(i => {
      const cls = i.qty <= i.min_qty ? 'warn' : 'ok';
      return '<div class="card"><h3>' + esc(i.name) + ' <span class="badge ' + cls + '">' + i.qty + ' in stock</span></h3><p style="font-family:monospace;font-size:12px">' + esc(i.part_number || '-') + '</p><p>Cost: R' + i.cost_price.toFixed(2) + ' | Sell: R' + i.sell_price.toFixed(2) + '</p>' + (i.qty <= i.min_qty ? '<p style="color:#ef4444;font-size:12px;font-weight:700">⚠ Low stock (min ' + i.min_qty + ')</p>' : '') + '<div style="margin-top:10px"><button class="btn-sm green" onclick="adjInv(\'' + i.id + '\',1)">+1</button><button class="btn-sm red" onclick="adjInv(\'' + i.id + '\',-1)">-1</button><button class="btn-sm gray" onclick="delInv(\'' + i.id + '\')">Delete</button></div></div>';
    }).join('') : '<div class="card"><p>No stock items</p></div>';
  } catch (e) {}
}
async function adjInv(id, d) { await jpost('/api/inventory/' + id + '/adjust', {delta:d}); loadInventory(); }
async function delInv(id) { if (!confirm('Delete?')) return; await jdel('/api/inventory/' + id); loadInventory(); }

// PURCHASE ORDERS
function showPOForm() { document.getElementById('poForm').style.display = 'block'; }
function hidePOForm() { document.getElementById('poForm').style.display = 'none'; }
async function createPO() {
  const s = document.getElementById('poSupplier').value.trim();
  const i = document.getElementById('poItems').value.trim();
  if (!s || !i) { alert('Supplier and items required'); return; }
  await jpost('/api/purchase-orders', {supplier:s, items:i, total:parseFloat(document.getElementById('poTotal').value) || 0});
  ['poSupplier','poItems','poTotal'].forEach(id => document.getElementById(id).value = '');
  hidePOForm();
  loadPOs();
}
async function loadPOs() {
  const c = document.getElementById('poList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/purchase-orders');
    c.innerHTML = d.pos.length ? d.pos.reverse().map(p => '<div class="card"><h3>PO #' + p.id + ' <span class="badge ' + (p.status === 'received' ? 'ok' : 'new') + '">' + p.status + '</span></h3><p><strong>' + esc(p.supplier) + '</strong></p><p>' + esc(p.items) + '</p><p>Total: R' + p.total.toFixed(2) + '</p><div style="margin-top:10px"><button class="btn-sm green" onclick="markPO(\'' + p.id + '\',\'received\')">Mark Received</button><button class="btn-sm red" onclick="delPO(\'' + p.id + '\')">Delete</button></div></div>').join('') : '<div class="card"><p>No purchase orders</p></div>';
  } catch (e) {}
}
async function markPO(id, s) { await jput('/api/purchase-orders/' + id, {status:s}); loadPOs(); }
async function delPO(id) { if (!confirm('Delete?')) return; await jdel('/api/purchase-orders/' + id); loadPOs(); }

// STAFF
function showStaffForm() { document.getElementById('staffForm').style.display = 'block'; }
function hideStaffForm() { document.getElementById('staffForm').style.display = 'none'; }
async function addStaff() {
  const n = document.getElementById('staffName').value.trim();
  if (!n) { alert('Name required'); return; }
  await jpost('/api/staff', {name:n, role:document.getElementById('staffRole').value, phone:document.getElementById('staffPhone').value, email:document.getElementById('staffEmail').value, hourly_rate:parseFloat(document.getElementById('staffRate').value) || 150});
  ['staffName','staffRole','staffPhone','staffEmail'].forEach(id => document.getElementById(id).value = '');
  hideStaffForm();
  loadStaff();
}
async function loadStaff() {
  const c = document.getElementById('staffList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/staff');
    c.innerHTML = d.staff.length ? d.staff.map(s => '<div class="card"><h3>👷 ' + esc(s.name) + '</h3><p>' + esc(s.role || '-') + '</p>' + (s.phone ? '<p>📞 ' + esc(s.phone) + '</p>' : '') + '<p>Rate: R' + s.hourly_rate.toFixed(2) + '/hr</p><button class="btn-sm red" onclick="delStaff(\'' + s.id + '\')">Delete</button></div>').join('') : '<div class="card"><p>No staff yet</p></div>';
  } catch (e) {}
}
async function delStaff(id) { if (!confirm('Delete?')) return; await jdel('/api/staff/' + id); loadStaff(); }

// CLOCKIN
async function loadClockin() {
  const c = document.getElementById('clockinList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const sd = await jget('/api/staff');
    const cd = await jget('/api/clockins');
    c.innerHTML = sd.staff.length ? sd.staff.map(s => {
      const active = cd.clockins.find(x => x.staff_id === s.id && !x.clock_out);
      return '<div class="card"><h3>👷 ' + esc(s.name) + '</h3>' + (active ? '<p style="color:#10b981;font-weight:700">🕐 Clocked in at ' + esc(active.clock_in) + '</p><button class="btn-sm red" onclick="clockOut(\'' + s.id + '\')">Clock Out</button>' : '<button class="btn-sm green" onclick="clockIn(\'' + s.id + '\')">Clock In</button>') + '</div>';
    }).join('') : '<div class="card"><p>Add staff first</p></div>';
  } catch (e) {}
}
async function clockIn(id) { await jpost('/api/clockins', {staff_id:id}); loadClockin(); }
async function clockOut(id) { await jpost('/api/clockins/' + id + '/out', {}); loadClockin(); }

// EXPENSES
function showExpenseForm() { document.getElementById('expenseForm').style.display = 'block'; }
function hideExpenseForm() { document.getElementById('expenseForm').style.display = 'none'; }
async function addExpense() {
  const a = parseFloat(document.getElementById('expAmount').value) || 0;
  if (!a) { alert('Amount required'); return; }
  await jpost('/api/expenses', {category:document.getElementById('expCat').value, amount:a, date:document.getElementById('expDate').value || new Date().toISOString().slice(0, 10), note:document.getElementById('expNote').value});
  ['expAmount','expDate','expNote'].forEach(id => document.getElementById(id).value = '');
  hideExpenseForm();
  loadExpenses();
}
async function loadExpenses() {
  const c = document.getElementById('expenseList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/expenses');
    const total = d.expenses.reduce((s, x) => s + x.amount, 0);
    c.innerHTML = '<div class="card" style="background:linear-gradient(135deg,#ef4444,#f87171);color:white"><h3 style="color:white">Total Expenses</h3><p style="font-size:26px;color:white;font-weight:800">R' + total.toFixed(2) + '</p></div>' + (d.expenses.length ? d.expenses.reverse().map(e => '<div class="card"><h3>' + esc(e.category) + ' <span class="badge new">R' + e.amount.toFixed(2) + '</span></h3><p>' + esc(e.note || '-') + '</p><p style="font-size:11px;color:var(--text2)">' + esc(e.date) + '</p><button class="btn-sm red" onclick="delExp(\'' + e.id + '\')">Delete</button></div>').join('') : '<div class="card"><p>No expenses</p></div>');
  } catch (e) {}
}
async function delExp(id) { if (!confirm('Delete?')) return; await jdel('/api/expenses/' + id); loadExpenses(); }

// FUEL
function showFuelForm() { document.getElementById('fuelForm').style.display = 'block'; }
function hideFuelForm() { document.getElementById('fuelForm').style.display = 'none'; }
async function addFuel() {
  const v = document.getElementById('fuelVehicle').value.trim();
  const km = parseInt(document.getElementById('fuelKm').value) || 0;
  const l = parseFloat(document.getElementById('fuelLitres').value) || 0;
  if (!v || !km || !l) { alert('Vehicle, km and litres required'); return; }
  await jpost('/api/fuel', {vehicle:v, km:km, litres:l, cost:parseFloat(document.getElementById('fuelCost').value) || 0, station:document.getElementById('fuelStation').value, date:document.getElementById('fuelDate').value || new Date().toISOString().slice(0, 10)});
  ['fuelVehicle','fuelKm','fuelLitres','fuelCost','fuelStation','fuelDate'].forEach(id => document.getElementById(id).value = '');
  hideFuelForm();
  loadFuel();
}
async function loadFuel() {
  const c = document.getElementById('fuelList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/fuel');
    c.innerHTML = d.logs.length ? d.logs.reverse().map(f => '<div class="card"><h3>⛽ ' + esc(f.vehicle) + '</h3><div class="list-item">Odometer: <strong>' + f.km + ' km</strong></div><div class="list-item">Litres: <strong>' + f.litres + ' L</strong></div><div class="list-item">Cost: <strong>R' + f.cost.toFixed(2) + '</strong></div>' + (f.consumption > 0 ? '<div class="list-item">Consumption: <strong style="color:#10b981">' + f.consumption + ' L/100km</strong></div>' : '') + (f.station ? '<div class="list-item">Station: ' + esc(f.station) + '</div>' : '') + '<p style="font-size:11px;color:var(--text2)">' + esc(f.date) + '</p><button class="btn-sm red" onclick="delFuel(\'' + f.id + '\')">Delete</button></div>').join('') : '<div class="card"><p>No fuel logs</p></div>';
  } catch (e) {}
}
async function delFuel(id) { if (!confirm('Delete?')) return; await jdel('/api/fuel/' + id); loadFuel(); }

// WARRANTY
async function loadWarranty() {
  const c = document.getElementById('warrantyList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/warranty');
    c.innerHTML = d.warranties.length ? d.warranties.map(w => {
      const cls = w.status === 'active' ? 'ok' : 'warn';
      return '<div class="card"><h3>🎁 ' + esc(w.vehicle) + ' <span class="badge ' + cls + '">' + w.status.toUpperCase() + '</span></h3><p><strong>' + esc(w.customer) + '</strong></p>' + (w.phone ? '<p>📞 ' + esc(w.phone) + '</p>' : '') + '<div class="list-item">Job #' + w.id + ' on ' + esc(w.job_date) + '</div><div class="list-item">Warranty: ' + w.months + ' months</div><div class="list-item">Expires: <strong>' + esc(w.expiry) + '</strong></div><div class="list-item">' + (w.days_left > 0 ? '<span style="color:#10b981;font-weight:700">Expires in ' + w.days_left + ' days</span>' : '<span style="color:#ef4444;font-weight:700">Expired ' + Math.abs(w.days_left) + ' days ago</span>') + '</div></div>';
    }).join('') : '<div class="card"><p>No warranties yet</p></div>';
  } catch (e) {}
}

// REMINDERS
async function loadReminders() {
  const c = document.getElementById('remindersList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/reminders');
    c.innerHTML = d.reminders.length ? d.reminders.map(r => '<div class="card"><h3>🗓️ ' + esc(r.vehicle) + '</h3><p>' + esc(r.customer) + '</p><p>Due: <strong>' + esc(r.due) + '</strong></p><p style="color:var(--text2);font-size:12px">Last: ' + esc(r.last_service) + ' (' + r.last_km + ' km)</p><button class="btn-sm whatsapp" onclick="remindWA(\'' + esc(r.phone || '') + '\',\'' + esc(r.customer) + '\',\'' + esc(r.vehicle) + '\')">📱 Remind</button></div>').join('') : '<div class="card"><p>No reminders due</p></div>';
  } catch (e) {}
}
function remindWA(phone, name, vehicle) {
  const txt = 'Hi ' + name + ', your ' + vehicle + ' is due for service. Please book an appointment.';
  window.open(phone ? 'https://wa.me/' + phone.replace(/\D/g, '') + '?text=' + encodeURIComponent(txt) : 'https://wa.me/?text=' + encodeURIComponent(txt), '_blank');
}

// WIRING
let wiringData = [];
async function loadWiring() { const d = await jget('/api/wiring'); wiringData = d.circuits; filterWiring(); }
function filterWiring() {
  const q = (document.getElementById('wiringSearch').value || '').toLowerCase();
  const f = wiringData.filter(x => !q || x.name.toLowerCase().includes(q) || x.system.toLowerCase().includes(q));
  document.getElementById('wiringList').innerHTML = f.map(w => '<div class="card"><h3>🔌 ' + esc(w.name) + '</h3><p style="font-size:12px;color:var(--text2)">' + esc(w.system) + ' — ' + esc(w.description) + '</p><p><strong>Components:</strong></p>' + w.components.map(c => '<div class="list-item">• ' + esc(c) + '</div>').join('') + '<p><strong>Connections:</strong></p>' + w.connections.map(c => '<div class="list-item" style="font-family:monospace;font-size:11px">' + esc(c) + '</div>').join('') + '</div>').join('') || '<div class="card"><p>None</p></div>';
}

// OBD
let obdData = [];
async function loadOBD() { const d = await jget('/api/obd-pids'); obdData = d.pids; filterOBD(); }
function filterOBD() {
  const q = (document.getElementById('obdSearch').value || '').toLowerCase();
  const f = obdData.filter(x => !q || x.name.toLowerCase().includes(q) || x.pid.includes(q));
  document.getElementById('obdList').innerHTML = '<table class="torque-table"><tr><th>PID</th><th>Name</th><th>Desc</th></tr>' + f.map(x => '<tr><td><strong>' + x.pid + '</strong></td><td>' + esc(x.name) + '</td><td style="font-size:11px">' + esc(x.desc) + '</td></tr>').join('') + '</table>';
}

// BULBS
let bulbsData = [];
async function loadBulbs() { const d = await jget('/api/bulbs'); bulbsData = d.bulbs; filterBulbs(); }
function filterBulbs() {
  const q = (document.getElementById('bulbSearch').value || '').toLowerCase();
  const f = bulbsData.filter(x => !q || x.vehicle.toLowerCase().includes(q));
  document.getElementById('bulbList').innerHTML = f.map(b => '<div class="card"><h3>💡 ' + esc(b.vehicle) + '</h3><div class="list-item">Low: <strong>' + esc(b.headlight_low) + '</strong></div><div class="list-item">High: <strong>' + esc(b.headlight_high) + '</strong></div><div class="list-item">Fog: <strong>' + esc(b.fog) + '</strong></div></div>').join('') || '<div class="card"><p>None</p></div>';
}

// BATTERIES
let battData = [];
async function loadBatt() { const d = await jget('/api/batteries'); battData = d.batteries; filterBatt(); }
function filterBatt() {
  const q = (document.getElementById('battSearch').value || '').toLowerCase();
  const f = battData.filter(x => !q || x.vehicle.toLowerCase().includes(q));
  document.getElementById('battList').innerHTML = f.map(b => '<div class="card"><h3>🔋 ' + esc(b.vehicle) + '</h3><div class="list-item">Group: <strong>' + esc(b.group) + '</strong></div><div class="list-item">CCA: <strong>' + b.cca + '</strong></div><div class="list-item">Ah: <strong>' + b.ah + '</strong></div></div>').join('') || '<div class="card"><p>None</p></div>';
}

// TYRES
let tyreData = [];
async function loadTyre() { const d = await jget('/api/tyres'); tyreData = d.tyres; filterTyre(); }
function filterTyre() {
  const q = (document.getElementById('tyreSearch').value || '').toLowerCase();
  const f = tyreData.filter(x => !q || x.vehicle.toLowerCase().includes(q));
  document.getElementById('tyreList').innerHTML = f.map(t => '<div class="card"><h3>🛞 ' + esc(t.vehicle) + '</h3><div class="list-item">Size: <strong>' + esc(t.size) + '</strong></div><div class="list-item">Front: <strong>' + esc(t.pressure_f) + '</strong></div><div class="list-item">Rear: <strong>' + esc(t.pressure_r) + '</strong></div></div>').join('') || '<div class="card"><p>None</p></div>';
}

// FUSES
async function loadFuses() {
  const c = document.getElementById('fuseList');
  c.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const d = await jget('/api/fuses');
    c.innerHTML = d.fuses.map(f => '<div class="card"><h3>🔌 ' + esc(f.vehicle) + '</h3><p style="font-size:12px;color:var(--text2)">' + esc(f.location) + '</p>' + f.common.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '</div>').join('');
  } catch (e) {}
}

// SERVICE CALC
async function calcService() {
  const km = parseInt(document.getElementById('svcKm').value) || 0;
  const t = document.getElementById('svcType').value;
  if (!km) { alert('Enter current km'); return; }
  const d = await jpost('/api/service-calc', {current_km:km, vehicle_type:t});
  document.getElementById('svcResult').innerHTML = '<div class="card" style="background:linear-gradient(135deg,#4facfe,#00f2fe);color:white"><h3 style="color:white">Next Service Due</h3><p style="font-size:28px;font-weight:800;color:white">at ' + d.next_service_km + ' km</p><p style="color:white">or in ' + d.months_interval + ' months</p></div><div class="card"><h3>Items to check</h3>' + d.items.map(i => '<div class="list-item">• ' + esc(i) + '</div>').join('') + '</div>';
}

// INSPECT
async function loadChecklist() {
  const t = document.getElementById('inspectType').value;
  const d = await jget('/api/checklists/' + t);
  document.getElementById('inspectList').innerHTML = '<div class="card"><h3>' + esc(d.name) + '</h3>' + d.items.map((x, i) => '<div class="checklist-item"><input type="checkbox" id="chk' + i + '"><label for="chk' + i + '">' + esc(x) + '</label></div>').join('') + '</div>';
}
function printChecklist() {
  const w = window.open('', '', 'width=800,height=600');
  w.document.write('<html><head><title>Checklist</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}div{padding:4px 0}</style></head><body><h1>' + document.getElementById('wsNameDisplay').textContent + '</h1>');
  w.document.write(document.getElementById('inspectList').innerHTML);
  w.document.write('</body></html>');
  w.document.close();
  setTimeout(() => w.print(), 500);
}

// BOLT CALC
async function calcTorque() {
  const d = await jpost('/api/bolt-calc', {size:document.getElementById('boltSize').value, grade:document.getElementById('boltGrade').value, condition:document.getElementById('boltCondition').value});
  document.getElementById('boltResult').innerHTML = '<div class="card" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white"><h3 style="color:white">Recommended Torque</h3><p style="font-size:32px;font-weight:800;color:white;margin:8px 0">' + d.nm.toFixed(1) + ' Nm</p><p style="color:white">' + d.ftlb.toFixed(1) + ' ft·lb</p></div><div class="card"><p><strong>Clamp force:</strong> ' + d.clamp_kn.toFixed(1) + ' kN</p></div>';
}

// TORQUE
let torqueData = [], seqData = [];
async function loadTorque() {
  if (!torqueData.length) { const d = await jget('/api/torque'); torqueData = d.bolts; seqData = d.sequences; }
  filterTorque();
}
function filterTorque() {
  const q = (document.getElementById('torqueSearch').value || '').toLowerCase();
  const f = torqueData.filter(x => !q || x.size.toLowerCase().includes(q) || x.grade.toLowerCase().includes(q));
  document.getElementById('torqueTable').innerHTML = '<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>' + f.map(x => '<tr><td><strong>' + esc(x.size) + '</strong></td><td>' + esc(x.grade) + '</td><td>' + x.nm + '</td><td>' + x.ftlb + '</td><td>' + esc(x.use) + '</td></tr>').join('') + '</table>';
  document.getElementById('torqueSeq').innerHTML = seqData.map(s => '<div class="card"><h3>' + esc(s.component) + '</h3><p style="font-size:11px;color:var(--text2)">' + esc(s.pattern) + '</p>' + s.steps.map(x => '<div class="list-item">• ' + esc(x) + '</div>').join('') + '<p style="font-size:12px;font-style:italic;margin-top:6px">' + esc(s.note) + '</p></div>').join('');
}

// HISTORY
async function searchVehicleHistory() {
  const q = document.getElementById('vehicleSearch').value.trim().toLowerCase();
  const c = document.getElementById('vehicleHistory');
  if (!q) { c.innerHTML = '<div class="loading">Enter search term above</div>'; return; }
  const d = await jget('/api/jobs');
  const m = d.jobs.filter(j => j.vehicle.toLowerCase().includes(q) || (j.registration || '').toLowerCase().includes(q));
  c.innerHTML = m.length ? '<p style="margin-bottom:12px;color:var(--text2)">' + m.length + ' record(s) found</p>' + m.reverse().map(j => '<div class="card"><h3>Job #' + j.id + '</h3><p><strong>' + esc(j.customer) + '</strong></p><p>🚗 ' + esc(j.vehicle) + '</p><p>' + esc(j.complaint) + '</p><p><span class="badge ' + j.status.toLowerCase().replace(' ', '') + '">' + esc(j.status) + '</span></p></div>').join('') : '<div class="card"><p>No history found</p></div>';
}

// ANALYTICS
async function loadAnalytics() {
  const d = await jget('/api/analytics');
  let h = '<div class="stats-row"><div class="stat-card blue"><div class="num">R' + d.avg_invoice.toFixed(0) + '</div><div class="lbl">Avg Invoice</div></div><div class="stat-card green"><div class="num">R' + d.total_revenue.toFixed(0) + '</div><div class="lbl">Revenue</div></div><div class="stat-card red"><div class="num">R' + d.total_expenses.toFixed(0) + '</div><div class="lbl">Expenses</div></div><div class="stat-card purple"><div class="num">R' + d.net_profit.toFixed(0) + '</div><div class="lbl">Net Profit</div></div></div>';
  if (d.top_services.length) h += '<div class="card"><h3>🔥 Top Services</h3>' + d.top_services.map(s => '<div class="list-item"><strong>' + esc(s.name) + '</strong> — ' + s.count + '×</div>').join('') + '</div>';
  if (d.top_customers.length) h += '<div class="card"><h3>⭐ Top Customers</h3>' + d.top_customers.map(x => '<div class="list-item"><strong>' + esc(x.name) + '</strong> — R' + x.total.toFixed(0) + '</div>').join('') + '</div>';
  document.getElementById('analyticsContent').innerHTML = h;
}

// TAX
async function loadBizCard() {
  const d = await jget('/api/workshop');
  document.getElementById('bcLogo').textContent = d.logo || '🔧';
  document.getElementById('bcName').textContent = d.name || 'My Workshop';
  document.getElementById('bcPhone').textContent = d.phone || '';
  document.getElementById('bcAddress').textContent = d.address || '';
}
function downloadTax() {
  const f = document.getElementById('taxFrom').value;
  const t = document.getElementById('taxTo').value;
  window.location.href = '/api/export/tax?from_date=' + f + '&to_date=' + t;
}
function printBizCard() {
  const w = window.open('', '', 'width=600,height=400');
  w.document.write('<html><head><title>Business Card</title></head><body style="padding:20px">' + document.getElementById('bizCard').outerHTML + '</body></html>');
  w.document.close();
  setTimeout(() => w.print(), 500);
}

// SETTINGS
async function loadSettings() {
  const d = await jget('/api/workshop');
  document.getElementById('wsLogo').value = d.logo || '🔧';
  document.getElementById('wsName').value = d.name || '';
  document.getElementById('wsPhone').value = d.phone || '';
  document.getElementById('wsAddress').value = d.address || '';
  document.getElementById('wsEmail').value = d.email || '';
  document.getElementById('wsRate').value = d.labour_rate || 450;
  applyBranding(d);
}
function applyBranding(d) {
  document.getElementById('logoDisplay').textContent = d.logo || '🔧';
  document.getElementById('wsNameDisplay').textContent = (d.name || 'RAMSTECH').toUpperCase();
  const sub = [d.phone, d.address].filter(Boolean).join(' • ');
  document.getElementById('wsSubtitle').textContent = sub || 'AI Workshop Assistant v10.0';
}
async function saveSettings() {
  const p = {logo:document.getElementById('wsLogo').value || '🔧', name:document.getElementById('wsName').value, phone:document.getElementById('wsPhone').value, address:document.getElementById('wsAddress').value, email:document.getElementById('wsEmail').value, labour_rate:parseFloat(document.getElementById('wsRate').value) || 450};
  await jpost('/api/workshop', p);
  applyBranding(p);
  alert('Settings saved ✓');
}
loadSettings();

function exportJobsCSV() { window.location.href = '/api/export/jobs'; }
function exportCustomersCSV() { window.location.href = '/api/export/customers'; }
</script>
<!-- ═══════════════════════════════════════════ -->
<!-- FLOATING AI ASSISTANT — available on every tab -->
<!-- ═══════════════════════════════════════════ -->
<style>
  #aiFab {
    position: fixed;
    bottom: 24px;
    right: 18px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #00a8e8, #0066a8);
    color: #fff;
    border: none;
    font-size: 26px;
    cursor: pointer;
    z-index: 9997;
    box-shadow: 0 6px 18px rgba(0,168,232,.45);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform .15s ease;
  }
  #aiFab:active { transform: scale(.92); }
  #aiFabLabel {
    position: fixed;
    bottom: 32px;
    right: 86px;
    background: #0f1520;
    color: #00a8e8;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    z-index: 9997;
    border: 1px solid #1e2938;
    pointer-events: none;
  }
  #aiPanel {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.7);
    z-index: 9999;
    padding: 12px;
    overflow: auto;
  }
  #aiPanelInner {
    max-width: 680px;
    margin: 20px auto;
    background: #0f1520;
    color: #e6edf5;
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #1e2938;
  }
  #aiPanelTabs {
    display: flex;
    gap: 4px;
    margin-bottom: 14px;
    background: #0a1018;
    padding: 4px;
    border-radius: 10px;
    border: 1px solid #1e2938;
  }
  .aiPanelTab {
    flex: 1;
    padding: 10px 6px;
    background: transparent;
    color: #7b8da3;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all .15s;
  }
  .aiPanelTab.active {
    background: #00a8e8;
    color: #03121c;
  }
  .aiPanelInput {
    width: 100%;
    padding: 12px 14px;
    background: #0a1018;
    border: 1px solid #1e2938;
    border-radius: 10px;
    color: #e6edf5;
    font-size: 15px;
    box-sizing: border-box;
    font-family: inherit;
    margin-bottom: 10px;
  }
  #aiPanelSubmit {
    background: #00a8e8;
    color: #03121c;
    border: none;
    border-radius: 10px;
    padding: 14px 18px;
    font-weight: 700;
    font-size: 15px;
    cursor: pointer;
    width: 100%;
  }
  #aiPanelSubmit:disabled { opacity: .55; }
  #aiPanelReply {
    display: none;
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    background: #0a1018;
    border: 1px solid #1e2938;
    border-radius: 12px;
    padding: 14px;
    margin-top: 14px;
  }
  #aiPanelChips {
    display: none;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
  }
  .aiChip {
    background: #0a1018;
    color: #00a8e8;
    border: 1px solid #00a8e8;
    border-radius: 16px;
    padding: 6px 12px;
    font-size: 13px;
    cursor: pointer;
    font-weight: 600;
  }
</style>

<button id="aiFab" onclick="toggleAiPanel()" title="AI Assistant">🤖</button>
<div id="aiFabLabel">AI Assistant</div>

<div id="aiPanel">
  <div id="aiPanelInner">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div>
        <div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">RAMSTECH AI</div>
        <div style="font-size:17px;font-weight:700;color:#00a8e8;">Diagnostic Assistant</div>
      </div>
      <button onclick="toggleAiPanel()" style="background:#1e2938;color:#e6edf5;border:none;border-radius:8px;padding:8px 14px;font-size:16px;cursor:pointer;">✕</button>
    </div>

    <div id="aiPanelTabs">
      <button class="aiPanelTab active" data-mode="code" onclick="setAiMode('code')">🔤 Code</button>
      <button class="aiPanelTab" data-mode="symptom" onclick="setAiMode('symptom')">🩺 Symptom</button>
      <button class="aiPanelTab" data-mode="ask" onclick="setAiMode('ask')">💬 Ask</button>
    </div>

    <input id="aiPanelVehicle" class="aiPanelInput" placeholder="Vehicle (optional) — e.g. Toyota Hilux 2015" autocomplete="off">

    <input id="aiPanelCode" class="aiPanelInput" placeholder="e.g. P0301, B1318, U0100"
      autocomplete="off" autocapitalize="characters"
      style="font-family:monospace;font-size:16px;letter-spacing:1px;">

    <textarea id="aiPanelSymptom" class="aiPanelInput" rows="3"
      placeholder="Describe the symptom — e.g. rough idle when cold, black smoke, battery warning light"
      style="display:none;resize:vertical;"></textarea>

    <textarea id="aiPanelAsk" class="aiPanelInput" rows="3"
      placeholder="Ask anything — e.g. how do I test a camshaft sensor?"
      style="display:none;resize:vertical;"></textarea>

    <button id="aiPanelSubmit" onclick="submitAiPanel()">🤖 Get Answer</button>

    <div id="aiPanelChips"></div>
    <div id="aiPanelReply"></div>
  </div>
</div>

<script>
  // ─── Panel open/close ───
      if (e.key === 'Enter' && !e.shiftKey) {
      const active = document.activeElement;
      if (active && (active.id === 'aiPanelCode' || active.id === 'aiPanelVehicle')) {
        e.preventDefault();
        submitAiPanel();
      }
    }
  });

  // ─── Backdrop close ───
  document.getElementById('aiPanel').addEventListener('click', function(e) {
    if (e.target === this) toggleAiPanel();
  });

  // ─── Auto-open with pre-filled data (optional) ───
  window.aiOpenWithCode = function(code, vehicle) {
    document.getElementById('aiPanel').style.display = 'block';
    setAiMode('code');
    document.getElementById('aiPanelCode').value = code || '';
    document.getElementById('aiPanelVehicle').value = vehicle || '';
    if (code) setTimeout(submitAiPanel, 200);
  };

  window.aiOpenWithSymptom = function(symptom, vehicle) {
    document.getElementById('aiPanel').style.display = 'block';
    setAiMode('symptom');
    document.getElementById('aiPanelSymptom').value = symptom || '';
    document.getElementById('aiPanelVehicle').value = vehicle || '';
    if (symptom) setTimeout(submitAiPanel, 200);
  };
</script>
</body>
</html>"""
