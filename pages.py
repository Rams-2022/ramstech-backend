# pages.py — RamsTech v10.0 (Expanded Inspection Checklist)
HTML_PAGE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>RamsTech — AI Workshop Assistant</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<style>
:root{
--bg:#eef2f6;--card:rgba(255, 255, 255, 0.9);--text:#0f172a;--text2:#475569;--border:rgba(203, 213, 225, 0.8);
--primary:#0ea5e9;--primary-glow:rgba(14, 165, 233, 0.4);--input-bg:rgba(248, 250, 252, 0.9);
--grad1:linear-gradient(135deg,#0ea5e9 0%,#2563eb 100%);
--grad2:linear-gradient(135deg,#f43f5e 0%,#be123c 100%);
--grad4:linear-gradient(135deg,#10b981 0%,#059669 100%);
--grad6:linear-gradient(135deg,#8b5cf6 0%,#6d28d9 100%);
}
body.dark{
--bg:#050a14;--card:rgba(15, 23, 42, 0.85);--text:#f8fafc;--text2:#94a3b8;--border:rgba(51, 65, 85, 0.8);
--primary:#00f2fe;--primary-glow:rgba(0, 242, 254, 0.5);--input-bg:rgba(2, 6, 23, 0.8);
--grad1:linear-gradient(135deg,#00f2fe 0%,#4facfe 100%);
--grad2:linear-gradient(135deg,#ff0844 0%,#ffb199 100%);
--grad4:linear-gradient(135deg,#43e97b 0%,#38f9d7 100%);
--grad6:linear-gradient(135deg,#b224ef 0%,#7579ff 100%);
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background-color:var(--bg);color:var(--text);padding-bottom:20px;transition:background .3s,color .3s;background-image:linear-gradient(rgba(14, 165, 233, 0.05) 1px, transparent 1px),linear-gradient(90deg, rgba(14, 165, 233, 0.05) 1px, transparent 1px);background-size:30px 30px;background-attachment:fixed;}
body.dark::before{content:'';position:fixed;inset:0;pointer-events:none;background:radial-gradient(circle at 50% 0%,rgba(0, 242, 254, 0.1) 0%,transparent 60%);z-index:-1;}

.header{background:var(--grad1);color:#fff;padding:20px 16px;position:relative;overflow:hidden;border-bottom:2px solid var(--primary);box-shadow:0 8px 32px var(--primary-glow);clip-path:polygon(0 0, 100% 0, 100% 90%, 95% 100%, 5% 100%, 0 90%);}
.header h1{font-size:22px;display:flex;align-items:center;justify-content:center;gap:10px;position:relative;z-index:1;font-weight:800;letter-spacing:1px;text-transform:uppercase;}
.header p{font-size:11px;opacity:.9;margin-top:4px;text-align:center;position:relative;z-index:1;letter-spacing:2px;}
.top-btns{position:absolute;right:14px;top:14px;display:flex;gap:8px;z-index:2}
.top-btns button,.lang-sel{background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.3);color:#fff;padding:8px;border-radius:8px;font-size:14px;cursor:pointer;backdrop-filter:blur(4px);transition:all .2s;}
.top-btns button:active{transform:scale(0.9);background:rgba(0,0,0,0.4);}
.lang-sel option{color:#333}

.home-container{padding:16px;max-width:900px;margin:0 auto}
.hero-card{background:var(--card);border-radius:8px;padding:16px;margin-bottom:16px;border:1px solid var(--border);backdrop-filter:blur(10px);box-shadow:0 4px 20px rgba(0,0,0,0.1);}
.cat-title{font-size:12px;font-weight:800;color:var(--primary);text-transform:uppercase;letter-spacing:2px;margin:24px 4px 12px;display:flex;align-items:center;gap:8px;}
.cat-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--primary),transparent);}
.cat-grid{display:grid;grid-template-columns:1fr;gap:16px}
.cat-card{border-radius:4px;padding:22px 18px;color:white;cursor:pointer;position:relative;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.3);transition:all .2s ease;display:flex;align-items:center;gap:16px;border:1px solid rgba(255,255,255,0.1);clip-path:polygon(0 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%);}
.cat-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--primary);box-shadow:0 0 15px var(--primary);}
.cat-card:active{transform:scale(.97);box-shadow:0 4px 12px rgba(0,0,0,.4)}
.cat-icon{font-size:38px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.5));min-width:50px;text-align:center;display:flex;justify-content:center;}
.cat-icon svg{width:38px;height:38px;stroke-width:1.5;}
.cat-info{flex:1;}
.cat-name{font-size:18px;font-weight:900;margin-bottom:4px;letter-spacing:0.5px;text-shadow:0 2px 4px rgba(0,0,0,0.5);}
.cat-count{font-size:12px;opacity:.9;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--primary);}
.cat-arrow{font-size:24px;opacity:.8;}

.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tile{background:var(--card);border-radius:4px;padding:24px 16px;cursor:pointer;text-align:center;border:1px solid var(--border);position:relative;transition:all .2s;box-shadow:0 4px 15px rgba(0,0,0,0.1),inset 0 0 20px rgba(0,0,0,0.02);backdrop-filter:blur(10px);clip-path:polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);overflow:hidden;display:flex;flex-direction:column;align-items:center;}
body.dark .tile{border-color:rgba(0, 242, 254, 0.2);box-shadow:0 4px 15px rgba(0,0,0,0.5),inset 0 0 20px rgba(0, 242, 254, 0.05);}
.tile::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--primary);opacity:0.8;transition:opacity 0.2s,box-shadow 0.2s;}
.tile:active{transform:scale(.95);background:rgba(14, 165, 233, 0.1);border-color:var(--primary);box-shadow:0 0 25px var(--primary-glow),inset 0 0 20px var(--primary-glow);}
.tile:active::before{opacity:1;box-shadow:0 0 15px var(--primary);}
.tile-icon{font-size:38px;margin-bottom:12px;display:flex;justify-content:center;align-items:center;filter:drop-shadow(0 4px 6px rgba(0,0,0,0.3));transition:transform 0.2s;height:40px;}
.tile-icon svg{width:32px;height:32px;stroke-width:1.8;}
.tile:active .tile-icon{transform:scale(1.1);}
.tile-label{font-size:13px;font-weight:900;letter-spacing:1px;text-transform:uppercase;color:var(--text);}

.bottom-nav{position:fixed;bottom:16px;left:16px;right:16px;background:rgba(5, 10, 20, 0.85);backdrop-filter:blur(20px);border:1px solid rgba(0, 242, 254, 0.3);border-radius:20px;display:flex;justify-content:space-around;padding:12px 8px;z-index:100;box-shadow:0 10px 40px rgba(0,0,0,0.6),inset 0 1px 0 rgba(255,255,255,0.1);padding-bottom:env(safe-area-inset-bottom, 12px);}
body:not(.dark) .bottom-nav{background:rgba(255, 255, 255, 0.9);border:1px solid var(--border);box-shadow:0 10px 30px rgba(0,0,0,0.1);}
.bnav-item{flex:1;text-align:center;padding:8px 4px;cursor:pointer;position:relative;display:flex;flex-direction:column;align-items:center;color:var(--text2);transition:all .3s cubic-bezier(0.34, 1.56, 0.64, 1);}
.bnav-icon{font-size:22px;display:flex;justify-content:center;align-items:center;margin-bottom:4px;transition:all .3s cubic-bezier(0.34, 1.56, 0.64, 1);height:24px;}
.bnav-icon svg{width:22px;height:22px;stroke-width:2;}
.bnav-label{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:1px;transition:all .3s;}
.bnav-item.active{color:var(--primary);}
body.dark .bnav-item.active .bnav-icon{transform:translateY(-6px) scale(1.2);filter:drop-shadow(0 0 12px var(--primary));}
body:not(.dark) .bnav-item.active .bnav-icon{transform:translateY(-6px) scale(1.2);filter:drop-shadow(0 4px 6px rgba(0,0,0,0.2));}
.bnav-item.active .bnav-label{transform:translateY(2px);}
.bnav-item.active::after{content:'';position:absolute;bottom:-12px;width:6px;height:6px;background:var(--primary);border-radius:50%;box-shadow:0 0 10px var(--primary),0 0 20px var(--primary);}

.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:120px}
.panel.active{display:block;animation:techSlide .35s cubic-bezier(.16,1,.3,1)}
@keyframes techSlide{from{opacity:0;transform:translateY(15px) scale(0.98)}to{opacity:1;transform:translateY(0) scale(1)}}
.panel-title{font-size:20px;font-weight:900;color:var(--primary);margin-bottom:20px;display:flex;align-items:center;gap:8px;text-transform:uppercase;letter-spacing:1px;}

.card{background:var(--card);padding:18px;border-radius:8px;margin-bottom:14px;border:1px solid var(--border);transition:all .2s;backdrop-filter:blur(10px);box-shadow:0 4px 15px rgba(0,0,0,0.03);}
body.dark .card{border-left:3px solid var(--primary);box-shadow:0 4px 20px rgba(0,0,0,0.3);}
.card h3{color:var(--primary);margin-bottom:10px;font-size:16px;font-weight:800;letter-spacing:0.5px;}

input:not([type="checkbox"]),textarea,select{width:100%;padding:16px;border:1.5px solid var(--border);border-radius:8px;font-size:16px;background:var(--input-bg);color:var(--text);font-family:inherit;transition:all 0.2s ease;-webkit-appearance:none;appearance:none;box-shadow:inset 0 3px 6px rgba(0,0,0,0.05);}
input:not([type="checkbox"]):focus,textarea:focus,select:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-glow),inset 0 3px 6px rgba(0,0,0,0.05);background:var(--bg);}
select{background-image:url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23666%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");background-repeat:no-repeat;background-position:right 16px top 50%;background-size:12px auto;padding-right:40px;}
body.dark select{background-image:url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%2300f2fe%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");}

/* THE FIX: Checkboxes are fully restored */
input[type="checkbox"] { 
  -webkit-appearance: checkbox !important; 
  appearance: checkbox !important; 
  width: 24px !important; 
  height: 24px !important; 
  padding: 0 !important; 
  margin: 0 !important; 
  accent-color: var(--primary); 
  cursor: pointer; 
  flex-shrink: 0;
}
.checklist-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: var(--input-bg); border-radius: 8px; border: 1px solid var(--border); margin-bottom: 10px; cursor: pointer; font-weight: 600; font-size: 15px; transition: all 0.2s; }
.checklist-item:active { background: var(--bg); }

.btn{width:100%;padding:16px;border:none;border-radius:8px;font-size:16px;font-weight:800;cursor:pointer;margin-bottom:12px;background:var(--grad1);color:#fff;text-transform:uppercase;letter-spacing:1px;transition:all 0.15s cubic-bezier(0.4, 0, 0.2, 1);box-shadow:0 4px 15px var(--primary-glow);border-bottom:3px solid rgba(0,0,0,0.3);}
.btn:active{transform:translateY(2px);box-shadow:0 2px 5px var(--primary-glow);border-bottom:1px solid rgba(0,0,0,0.3);}
.btn-dark{background:linear-gradient(135deg,#334155,#1e293b);box-shadow:0 4px 15px rgba(51,65,85,0.4);border-bottom-color:rgba(0,0,0,0.5);}
.btn-success{background:var(--grad4);box-shadow:0 4px 15px rgba(67,233,123,0.3);border-bottom-color:rgba(0,0,0,0.2);}

.btn-sm{padding:10px 16px;border:none;border-radius:6px;font-size:13px;font-weight:800;margin-right:6px;margin-bottom:6px;background:var(--primary);color:#fff;cursor:pointer;transition:all 0.15s;box-shadow:0 2px 8px var(--primary-glow);border-bottom:2px solid rgba(0,0,0,0.2);text-transform:uppercase;letter-spacing:0.5px;}
.btn-sm:active{transform:translateY(1px);border-bottom:1px solid rgba(0,0,0,0.2);box-shadow:0 1px 3px var(--primary-glow);}
.btn-sm.whatsapp{background:#25D366;box-shadow:0 2px 8px rgba(37,211,102,0.3);border-bottom-color:rgba(0,0,0,0.2);}

.badge{padding:4px 10px;border-radius:4px;font-size:11px;font-weight:800;color:white;letter-spacing:.5px;text-transform:uppercase;border-bottom:2px solid rgba(0,0,0,0.2);}
.badge.high,.badge.critical,.badge.outstanding{background:#ef4444;box-shadow:0 2px 8px rgba(239,68,68,0.3);}
.badge.medium{background:#f59e0b;box-shadow:0 2px 8px rgba(245,158,11,0.3);}
.badge.low,.badge.ok,.badge.completed,.badge.paid{background:#10b981;box-shadow:0 2px 8px rgba(16,185,129,0.3);}

.back-btn{background:var(--grad6);color:white;border:none;padding:12px 18px;border-radius:8px;font-size:14px;font-weight:800;cursor:pointer;margin-bottom:16px;box-shadow:0 4px 15px rgba(139,92,246,.4);border-bottom:2px solid rgba(0,0,0,0.3);text-transform:uppercase;letter-spacing:1px;display:flex;align-items:center;gap:6px;}

.chat-box{height:calc(100vh - 280px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border);border-radius:12px;padding:14px;display:flex;flex-direction:column;background:var(--input-bg);box-shadow:inset 0 4px 10px rgba(0,0,0,0.05);}
.msg{padding:12px 16px;border-radius:12px;margin-bottom:10px;max-width:85%;line-height:1.45;font-size:14px;animation:msgIn .2s ease;box-shadow:0 2px 10px rgba(0,0,0,0.05);}
@keyframes msgIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.msg.user{background:var(--grad1);color:#fff;margin-left:auto;border-bottom-right-radius:2px;}
.msg.ai{background:var(--card);border:1px solid var(--border);margin-right:auto;border-bottom-left-radius:2px;}

#toastWrap{position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:99999;display:flex;flex-direction:column;gap:8px;pointer-events:none;}
.toast{background:#0f172a;color:#fff;padding:14px 24px;border-radius:8px;font-size:14px;font-weight:700;box-shadow:0 10px 30px rgba(0,0,0,.5);animation:toastIn .3s cubic-bezier(.16,1,.3,1);display:flex;align-items:center;gap:10px;border-left:4px solid var(--primary);}
.toast.success{border-left-color:#10b981;}
.toast.error{border-left-color:#ef4444;}
@keyframes toastIn{from{opacity:0;transform:translateY(-20px) scale(.9)}to{opacity:1;transform:translateY(0) scale(1)}}
.toast.out{animation:toastOut .2s ease forwards;}
@keyframes toastOut{to{opacity:0;transform:translateY(-20px) scale(.9)}}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
</style>
</head>
<body>

<div id="toastWrap"></div>

<div class="header">
<h1><span class="logo" id="logoDisplay"><i data-lucide="cpu"></i></span> <span id="wsNameDisplay">RAMSTECH</span></h1>
<p id="wsSubtitle">AI WORKSHOP ASSISTANT v10.0</p>
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
<div class="hero-card"><div id="status">SYSTEM CHECK...</div></div>
<div id="categoryView">
<div class="cat-title">Select Protocol</div>
<div class="cat-grid" id="categoryGrid"></div>
</div>
<div id="subView" style="display:none">
<button class="back-btn" onclick="backToCategories()"><i data-lucide="arrow-left"></i> RETURN TO MAIN</button>
<div class="cat-title" id="subTitle"></div>
<div class="tile-grid" id="subGrid"></div>
</div>
</div>
</div>

<!-- DASHBOARD -->
<div id="dashboard" class="panel">
<div class="panel-title">📊 Advanced Analytics</div>
<div id="kpiCards" style="margin-bottom:16px;"></div>
<div class="card"><h3>📈 Revenue Stream (7 Days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Diagnostics</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>🔧 Top Mechanics</h3><canvas id="mechChart"></canvas></div>
<div class="card"><h3>🔥 Top Services</h3><div id="topServicesList"></div></div>
</div>

<!-- AI CHAT -->
<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox">
  <div class="msg ai">RAMSTECH AI ONLINE. I specialize in mechanics, hydraulics, pneumatics, transmission, electrical, suspension, and tool procedures. How can I help you today?</div>
</div>
<div class="input-row" style="display:flex;gap:8px;align-items:center;">
<input type="text" id="chatInput" placeholder="Ask about hydraulics, wiring, or procedures..." onkeypress="if(event.key==='Enter')sendMsg()" style="flex:1;border-radius:25px;">
<button class="mic-btn" id="micBtn" onclick="toggleMic()" style="padding:14px;border-radius:50%;background:var(--grad4);color:white;border:none;box-shadow:0 4px 12px rgba(67,233,123,.3);display:flex;align-items:center;justify-content:center;"><i data-lucide="mic"></i></button>
<button onclick="sendMsg()" style="padding:14px;border-radius:50%;background:var(--grad1);color:white;border:none;box-shadow:0 4px 12px var(--primary-glow);display:flex;align-items:center;justify-content:center;"><i data-lucide="send"></i></button>
</div>
</div>

<!-- INSPECTIONS -->
<div id="inspections" class="panel">
<div class="panel-title">📋 Vehicle Inspections</div>
<button class="btn" onclick="showInspectForm()">+ New Inspection</button>
<div id="inspectForm" style="display:none">
<div class="card">
<h3>Vehicle Details</h3>
<input type="text" class="form-input" id="inspCustomer" placeholder="Customer Name">
<input type="text" class="form-input" id="inspVehicle" placeholder="Vehicle (e.g. 2018 Toyota Hilux)">
<hr style="border:none;border-top:1px solid var(--border);margin:15px 0;">
<h3>Multi-Point Checklist</h3>
<div id="checklistContainer" style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"></div>
<hr style="border:none;border-top:1px solid var(--border);margin:15px 0;">
<h3>Photo & Notes</h3>
<input type="file" id="inspPhoto" accept="image/*" capture="environment" class="form-input" onchange="previewInspectPhoto(event)">
<div id="inspPhotoPreview"></div>
<textarea class="form-input" id="inspNotes" placeholder="Additional notes..." rows="2"></textarea>
<button class="btn btn-success" onclick="createInspection()">Save Inspection Report</button>
<button class="btn btn-dark" onclick="hideInspectForm()">Cancel</button>
</div>
</div>
<div id="inspectList"><div class="loading">Loading...</div></div>
</div>

<!-- FAULT CODES -->
<div id="codes" class="panel">
<div class="panel-title">📟 Fault Codes</div>
<input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code or description..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Type to search...</div></div>
</div>

<!-- PROBLEMS -->
<div id="problems" class="panel">
<div class="panel-title">📖 Common Problems</div>
<div style="display:flex; gap:8px; margin-bottom:14px;">
    <input type="text" class="form-input" style="margin-bottom:0;" id="problemSearch" placeholder="🔍 Search problems..." oninput="filterProblems()">
    <button class="btn" style="margin-bottom:0; width:auto; padding:0 20px;" onclick="filterProblems()"><i data-lucide="search"></i></button>
</div>
<div id="problemList"><div class="loading">Loading...</div></div>
</div>

<!-- VIN -->
<div id="vin" class="panel">
<div class="panel-title">🔍 VIN Decoder</div>
<button class="btn" onclick="openScanner()" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);display:flex;align-items:center;justify-content:center;gap:8px;"><i data-lucide="camera"></i> Scan VIN / Barcode</button>
<input type="text" class="form-input" id="vinInput" placeholder="Enter 17-character VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<!-- PAINT -->
<div id="paint" class="panel">
<div class="panel-title">🎨 Paint Match</div>
<div class="card"><p style="font-size:13px;color:var(--text2);">📸 Take a photo of a vehicle panel in good light. AI identifies colour and provides paint codes.</p></div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button>
<div id="paintResult"></div>
</div>

<!-- PHOTO DIAG -->
<div id="photo" class="panel">
<div class="panel-title">📸 Photo Diagnosis</div>
<div class="card"><p style="font-size:13px;color:var(--text2);">📸 Take a photo of a mechanical issue. AI diagnoses the problem.</p></div>
<input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button>
<div id="photoResult"></div>
</div>

<!-- JOBS -->
<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<button class="btn" onclick="openKanban()" style="background:linear-gradient(135deg,#7c3aed,#5b21b6);display:flex;align-items:center;justify-content:center;gap:8px;"><i data-lucide="layout-dashboard"></i> Open Kanban Board</button>
<button class="btn" onclick="openPhotoIntake()" style="background:linear-gradient(135deg,#8b5cf6,#6d28d9);display:flex;align-items:center;justify-content:center;gap:8px;"><i data-lucide="camera"></i> New Job from Photo</button>
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

<!-- INVENTORY -->
<div id="inventory" class="panel">
<div class="panel-title">📦 Inventory</div>
<button class="btn" onclick="showInvForm()">+ Add Stock Item</button>
<div id="invForm" style="display:none">
<div class="card">
<input type="text" class="form-input" id="invPartNum" placeholder="Part number">
<input type="text" class="form-input" id="invPartName" placeholder="Part name">
<input type="text" class="form-input" id="invCategory" placeholder="Category">
<input type="number" class="form-input" id="invQty" placeholder="Quantity">
<input type="number" class="form-input" id="invMinQty" placeholder="Minimum qty" value="5">
<input type="number" class="form-input" id="invCostPrice" placeholder="Cost price (R)">
<input type="number" class="form-input" id="invSellPrice" placeholder="Sell price (R)">
<input type="text" class="form-input" id="invSupplier" placeholder="Supplier">
<button class="btn btn-success" onclick="addInventory()">Save Item</button>
<button class="btn btn-dark" onclick="hideInvForm()">Cancel</button>
</div>
</div>
<div id="inventoryList"><div class="loading">Loading...</div></div>
</div>

<!-- APPOINTMENTS -->
<div id="appointments" class="panel">
<div class="panel-title">📅 Appointments</div>
<button class="btn" onclick="showApptForm()">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input type="text" class="form-input" id="apptCustomer" placeholder="Customer">
<input type="text" class="form-input" id="apptPhone" placeholder="Phone">
<input type="text" class="form-input" id="apptVehicle" placeholder="Vehicle">
<input type="text" class="form-input" id="apptService" placeholder="Service">
<input type="date" class="form-input" id="apptDate">
<input type="time" class="form-input" id="apptTime">
<button class="btn btn-success" onclick="createAppt()">Book Appointment</button>
<button class="btn btn-dark" onclick="hideApptForm()">Cancel</button>
</div>
</div>
<div id="apptList"><div class="loading">Loading...</div></div>
</div>

<!-- CLOCK IN/OUT -->
<div id="clockin" class="panel">
<div class="panel-title">🕐 Clock In/Out</div>
<div id="clockinList"><div class="loading">Loading...</div></div>
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
<div class="panel-title">⚙️ System Settings</div>
<button class="btn" onclick="openStaffManager()" style="background:linear-gradient(135deg,#10b981,#059669);display:flex;align-items:center;justify-content:center;gap:8px;"><i data-lucide="users"></i> Manage Staff & PINs</button>
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
  <div class="bnav-item active" onclick="showTab('home',this)"><div class="bnav-icon"><i data-lucide="home"></i></div><div class="bnav-label">Home</div></div>
  <div class="bnav-item" onclick="showTab('dashboard',this)"><div class="bnav-icon"><i data-lucide="bar-chart-3"></i></div><div class="bnav-label">Dash</div></div>
  <div class="bnav-item" onclick="showTab('chat',this)"><div class="bnav-icon"><i data-lucide="bot"></i></div><div class="bnav-label">AI</div></div>
  <div class="bnav-item" onclick="showTab('jobs',this)"><div class="bnav-icon"><i data-lucide="clipboard-list"></i></div><div class="bnav-label">Jobs</div></div>
  <div class="bnav-item" onclick="showTab('settings',this)"><div class="bnav-icon"><i data-lucide="settings"></i></div><div class="bnav-label">More</div></div>
</div>

<script>
function toast(msg, type='success') {
  const wrap = document.getElementById('toastWrap');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${type === 'success' ? '✓' : '⚠'}</span> ${msg}`;
  wrap.appendChild(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, 3000);
}

const CATEGORIES = {
  diagnostics: { name: 'Diagnostics', icon: 'wrench', gradient: 'linear-gradient(135deg,#0ea5e9,#1e3a8a)', items: [
      {icon:'bot',label:'AI Chat',tab:'chat',color:'#0ea5e9'},{icon:'activity',label:'Fault Codes',tab:'codes',color:'#ef4444'},
      {icon:'book-open',label:'Problems',tab:'problems',color:'#f59e0b'},{icon:'search',label:'VIN Decoder',tab:'vin',color:'#8b5cf6'},
      {icon:'palette',label:'Paint Match',tab:'paint',color:'#ec4899'},{icon:'camera',label:'Photo Diag',tab:'photo',color:'#06b6d4'}
  ]},
  workshop: { name: 'Workshop', icon: 'clipboard-list', gradient: 'linear-gradient(135deg,#f59e0b,#b91c1c)', items: [
      {icon:'clipboard-list',label:'Jobs',tab:'jobs',color:'#f59e0b'},{icon:'users',label:'Customers',tab:'customers',color:'#10b981'},
      {icon:'dollar-sign',label:'Invoices',tab:'invoices',color:'#10b981'},{icon:'clipboard-check',label:'Inspections',tab:'inspections',color:'#ec4899'}
  ]},
  operations: { name: 'Operations', icon: 'settings', gradient: 'linear-gradient(135deg,#10b981,#065f46)', items: [
      {icon:'package',label:'Inventory',tab:'inventory',color:'#f59e0b'},{icon:'calendar',label:'Appointments',tab:'appointments',color:'#3b82f6'},
      {icon:'clock',label:'Clock In/Out',tab:'clockin',color:'#8b5cf6'},{icon:'shopping-cart',label:'Purchase',tab:'purchase',color:'#3b82f6'}
  ]},
  reference: { name: 'Reference', icon: 'book', gradient: 'linear-gradient(135deg,#8b5cf6,#4c1d95)', items: [
      {icon:'package',label:'Parts Search',tab:'parts',color:'#6b7280'}
  ]},
  business: { name: 'Business', icon: 'briefcase', gradient: 'linear-gradient(135deg,#334155,#0f172a)', items: [
      {icon:'bar-chart-3',label:'Dashboard',tab:'dashboard',color:'#3b82f6'},{icon:'settings',label:'Settings',tab:'settings',color:'#6b7280'}
  ]}
};

document.getElementById('categoryGrid').innerHTML = Object.entries(CATEGORIES).map(([key, cat]) =>
  `<div class="cat-card" style="background:${cat.gradient}" onclick="openCategory('${key}')"><div class="cat-icon"><i data-lucide="${cat.icon}"></i></div><div class="cat-info"><div class="cat-name">${cat.name}</div><div class="cat-count">${cat.items.length} modules</div></div><div class="cat-arrow">›</div></div>`
).join('');

function openCategory(key) {
  const cat = CATEGORIES[key];
  document.getElementById('categoryView').style.display = 'none'; document.getElementById('subView').style.display = 'block';
  document.getElementById('subTitle').innerHTML = `<i data-lucide="${cat.icon}" style="width:18px;height:18px;display:inline-block;vertical-align:middle;margin-right:6px;color:var(--primary);"></i> ${cat.name}`;
  document.getElementById('subGrid').innerHTML = cat.items.map(item =>
    `<div class="tile" onclick="showTab('${item.tab}')"><div class="tile-icon" style="color:${item.color}"><i data-lucide="${item.icon}"></i></div><div class="tile-label">${item.label}</div></div>`
  ).join('');
  lucide.createIcons(); window.scrollTo(0, 0);
}
function backToCategories() { document.getElementById('subView').style.display = 'none'; document.getElementById('categoryView').style.display = 'block'; window.scrollTo(0, 0); }

function showTab(name, el) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  var subV = document.getElementById('subView'), catV = document.getElementById('categoryView');
  if (subV) subV.style.display = 'none'; if (catV) catV.style.display = 'block';
  var panel = document.getElementById(name); if (panel) panel.classList.add('active');
  if (el) { document.querySelectorAll('.bnav-item').forEach(t => t.classList.remove('active')); el.classList.add('active'); }
  window.scrollTo(0, 0);
  var fab = document.getElementById('aiFab'), diagTabs = ['chat','codes','problems','vin','paint','photo'];
  if (fab) {
    if (diagTabs.includes(name)) { fab.style.setProperty('display', 'flex', 'important'); fab.style.setProperty('opacity', '1', 'important'); fab.style.setProperty('visibility', 'visible', 'important'); }
    else { fab.style.setProperty('display', 'none', 'important'); fab.style.setProperty('opacity', '0', 'important'); fab.style.setProperty('visibility', 'hidden', 'important'); }
  }
  const loaders = {
    codes: () => !document.getElementById('codeResults').dataset.loaded && searchCodes(), problems: () => !document.getElementById('problemList').dataset.loaded && loadProblems(),
    jobs: () => { loadJobs(); loadStaffDropdown(); }, customers: loadCustomers, invoices: loadInvoices, settings: loadSettings, dashboard: loadDashboard,
    parts: searchParts, purchase: loadPOs, inventory: loadInventory, appointments: loadAppts, clockin: loadClockin, inspections: loadInspections
  };
  if (loaders[name]) try { loaders[name](); } catch (e) { console.error(e); }
}

function toggleTheme() { document.body.classList.toggle('dark'); document.getElementById('themeBtn').textContent = document.body.classList.contains('dark') ? '☀️' : '🌙'; }
async function checkStatus() { try { await fetch('/health'); document.getElementById('status').innerHTML = '<span style="color:var(--primary);font-weight:800;letter-spacing:1px;">● SYSTEM ONLINE</span>'; } catch (e) { document.getElementById('status').innerHTML = '<span style="color:#ef4444;font-weight:800;letter-spacing:1px;">● SYSTEM OFFLINE</span>'; } }
checkStatus();
function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
async function jget(u) { const r = await fetch(u); return r.json(); }
async function jpost(u, b) { const r = await fetch(u, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); return r.json(); }
async function jput(u, b) { const r = await fetch(u, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}); return r.json(); }
async function jdel(u) { const r = await fetch(u, {method:'DELETE'}); return r.json(); }

// DASHBOARD ADVANCED ANALYTICS
let rC = null, jC = null, mC = null;
async function loadDashboard() { 
  try { 
    const d = await jget('/api/analytics'); 
    document.getElementById('kpiCards').innerHTML = `
      <div class="stats-row" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;">
        <div class="stat-card" style="background:var(--card);padding:14px;border-radius:8px;border:1px solid var(--border);text-align:center;"><div style="font-size:22px;font-weight:900;color:#10b981;">R ${d.revenue.toFixed(0)}</div><div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Total Revenue</div></div>
        <div class="stat-card" style="background:var(--card);padding:14px;border-radius:8px;border:1px solid var(--border);text-align:center;"><div style="font-size:22px;font-weight:900;color:#ef4444;">R ${d.expenses.toFixed(0)}</div><div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Total Expenses</div></div>
        <div class="stat-card" style="background:var(--card);padding:14px;border-radius:8px;border:1px solid var(--border);text-align:center;"><div style="font-size:22px;font-weight:900;color:var(--primary);">R ${d.net_profit.toFixed(0)}</div><div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Net Profit</div></div>
        <div class="stat-card" style="background:var(--card);padding:14px;border-radius:8px;border:1px solid var(--border);text-align:center;"><div style="font-size:22px;font-weight:900;color:#8b5cf6;">R ${d.avg_job.toFixed(0)}</div><div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Avg Job Value</div></div>
      </div>`;
    if (rC) rC.destroy(); 
    rC = new Chart(document.getElementById('revenueChart'), { type:'line', data:{labels:d.rev_labels,datasets:[{data:d.rev_data,borderColor:'#0ea5e9',backgroundColor:'rgba(14,165,233,.15)',fill:true,tension:.4,pointBackgroundColor:'#0ea5e9'}]}, options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{grid:{color:'rgba(255,255,255,0.05)'},ticks:{color:'#64748b'}},x:{grid:{display:false},ticks:{color:'#64748b'}}}} });
    if (jC) jC.destroy(); 
    jC = new Chart(document.getElementById('jobChart'), { type:'doughnut', data:{labels:d.status_labels,datasets:[{data:d.status_data,backgroundColor:['#64748b','#3b82f6','#f59e0b','#ef4444','#06b6d4','#8b5cf6','#10b981','#16a34a','#475569'],borderWidth:0}]}, options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:'#64748b',boxWidth:12}}},cutout:'75%'} });
    if (mC) mC.destroy();
    mC = new Chart(document.getElementById('mechChart'), { type:'bar', data:{labels:d.mech_labels,datasets:[{data:d.mech_data,backgroundColor:'#8b5cf6',borderRadius:4}]}, options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:'rgba(255,255,255,0.05)'},ticks:{color:'#64748b',stepSize:1}},x:{grid:{display:false},ticks:{color:'#64748b'}}}} });
    document.getElementById('topServicesList').innerHTML = d.svc_labels.length ? d.svc_labels.map((label, i) => `<div class="list-item" style="display:flex;justify-content:space-between;"><span>${esc(label)}</span><span class="badge new">${d.svc_data[i]} jobs</span></div>`).join('') : '<p style="color:var(--text2);font-size:13px;">No service data yet.</p>';
  } catch(e){ console.error(e); }
}

// INSPECTIONS
const INSPECT_ITEMS = [
  "Body & Paint Condition", "Windscreen & Glass", "Mirrors & Wipers", "Headlights & Taillights",
  "Indicators & Hazards", "Brake Lights", "Tyre Tread & Condition", "Tyre Pressures & Spare",
  "Brakes (Pads/Discs)", "Suspension & Shocks", "Steering & Alignment", "Exhaust System",
  "Engine Oil & Filter", "Coolant Level", "Brake Fluid", "Power Steering Fluid",
  "Belts & Hoses", "Battery & Terminals", "Interior Upholstery", "Seatbelts & Buckles",
  "Dashboard Warning Lights", "Horn & Aircon", "Infotainment System", "Leaks (Oil/Coolant/Fuel)"
];
let inspectB64 = "";

function showInspectForm() {
  document.getElementById('inspectForm').style.display = 'block';
  document.getElementById('checklistContainer').innerHTML = INSPECT_ITEMS.map((item, i) => `
    <label class="checklist-item" style="padding:8px; margin-bottom:0;">
      <input type="checkbox" id="chk_insp_${i}" value="${item}">
      <span style="font-size:12px;">${item}</span>
    </label>
  `).join('');
}
function hideInspectForm() { document.getElementById('inspectForm').style.display = 'none'; inspectB64 = ""; document.getElementById('inspPhotoPreview').innerHTML = ""; }

async function previewInspectPhoto(e) {
  const file = e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = function(ev) {
    const img = new Image();
    img.onload = function() {
      const canvas = document.createElement('canvas'); let w = img.width, h = img.height;
      if (w > 1000) { h = (h * 1000) / w; w = 1000; } canvas.width = w; canvas.height = h; canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      inspectB64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
      document.getElementById('inspPhotoPreview').innerHTML = `<img src="${canvas.toDataURL('image/jpeg', 0.8)}" style="width:100%;border-radius:12px;margin-top:10px;border:1px solid var(--border);">`;
    }; img.src = ev.target.result;
  }; reader.readAsDataURL(file);
}

async function createInspection() {
  const customer = document.getElementById('inspCustomer').value.trim();
  const vehicle = document.getElementById('inspVehicle').value.trim();
  if (!customer || !vehicle) { toast('Customer and vehicle required', 'error'); return; }
  
  const checkedItems = [];
  INSPECT_ITEMS.forEach((item, i) => {
    if (document.getElementById(`chk_insp_${i}`).checked) checkedItems.push(item);
  });

  const payload = {
    customer: customer, vehicle: vehicle, checklist: checkedItems,
    notes: document.getElementById('inspNotes').value, photos: inspectB64 ? [inspectB64] : []
  };

  try {
    const res = await jpost('/api/inspections', payload);
    if (res.success) { toast('Inspection saved!'); hideInspectForm(); loadInspections(); }
  } catch(e) { toast('Error saving', 'error'); }
}

async function loadInspections() {
  try {
    const d = await jget('/api/inspections');
    document.getElementById('inspectList').innerHTML = d.inspections.length ? d.inspections.reverse().map(i => `
      <div class="card">
        <h3>Inspection #${i.id}</h3>
        <p><strong>${esc(i.customer)}</strong></p>
        <p>🚗 ${esc(i.vehicle)}</p>
        <div style="margin:10px 0;">
          ${i.checklist.map(x => `<span class="badge ok" style="margin-bottom:4px;display:inline-block;">${esc(x)} ✓</span>`).join('')}
        </div>
        ${i.notes ? `<p style="color:var(--text2);font-size:13px;">${esc(i.notes)}</p>` : ''}
        ${i.photos.length ? `<img src="data:image/jpeg;base64,${i.photos[0]}" style="width:100%;border-radius:8px;margin-top:10px;border:1px solid var(--border);">` : ''}
        <p style="font-size:11px;color:var(--text2);margin-top:10px;">${esc(i.created)}</p>
      </div>
    `).join('') : '<div class="card"><p>No inspections yet</p></div>';
  } catch(e) {}
}

// CHAT & VOICE
let rec = null, isRec = false;
function toggleMic() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) { toast('Voice not supported', 'error'); return; }
  if (!rec) { const SR = window.SpeechRecognition || window.webkitSpeechRecognition; rec = new SR(); rec.lang = 'en-ZA'; rec.onresult = e => { document.getElementById('chatInput').value = e.results[0][0].transcript; resetMic(); sendMsg(); }; rec.onerror = resetMic; rec.onend = resetMic; }
  function resetMic() { isRec = false; document.getElementById('micBtn').style.background = 'var(--grad4)'; document.getElementById('micBtn').innerHTML = '<i data-lucide="mic"></i>'; lucide.createIcons(); }
  if (isRec) { rec.stop(); resetMic(); } else { try { rec.start(); isRec = true; document.getElementById('micBtn').style.background = 'var(--grad2)'; document.getElementById('micBtn').innerHTML = '<i data-lucide="square"></i>'; lucide.createIcons(); } catch (e) { toast(e.message, 'error'); } }
}
async function sendMsg() {
  const i = document.getElementById('chatInput'); const m = i.value.trim(); if (!m) return;
  const b = document.getElementById('chatBox'); b.innerHTML += '<div class="msg user">' + esc(m) + '</div>'; i.value = ''; b.scrollTop = b.scrollHeight;
  const typId = 'typ_' + Date.now(); b.innerHTML += `<div class="msg ai" id="${typId}">Processing...</div>`; b.scrollTop = b.scrollHeight;
  try { const d = await jpost('/api/chat', {message:m}); document.getElementById(typId).outerHTML = '<div class="msg ai">' + esc(d.reply) + '</div>'; } catch (e) { document.getElementById(typId).outerHTML = '<div class="msg ai">Error connecting to AI.</div>'; }
  b.scrollTop = b.scrollHeight;
}

// JOBS
async function loadJobs() {
  const c = document.getElementById('jobList'); c.innerHTML = '<div class="loading">Loading...</div>';
  try { const d = await jget('/api/jobs'); if (!d.jobs.length) { c.innerHTML = '<div class="card"><p>No jobs yet.</p></div>'; return; }
    c.innerHTML = d.jobs.reverse().map(j => {
      let badgeClass = 'new'; if (j.status === 'Completed' || j.status === 'Invoiced') badgeClass = 'completed'; if (j.status === 'In Progress' || j.status === 'Diagnosing') badgeClass = 'medium'; if (j.status === 'Awaiting Parts' || j.status === 'Awaiting Approval') badgeClass = 'high';
      let cost = j.total ? `<div style="margin-top:10px;padding:10px;background:var(--input-bg);border-radius:8px;font-size:13px;border:1px solid var(--border);"><strong>💰 Total: R${j.total.toFixed(2)}</strong></div>` : '';
      let as = j.assigned_to ? `<p style="color:var(--text2);font-size:12px;">👷 ${esc(j.assigned_to)}</p>` : '';
      const statuses = ["New", "Diagnosing", "Awaiting Approval", "Awaiting Parts", "In Progress", "QC", "Ready for Pickup", "Completed", "Invoiced"];
      let statusOpts = statuses.map(s => `<option value="${s}" ${j.status === s ? 'selected' : ''}>${s}</option>`).join('');
      let invBtn = j.total ? `<button class="btn-sm green" onclick="generateInvoice('${j.id}')">Invoice</button>` : '';
      let waBtn = `<button class="btn-sm whatsapp" onclick="shareJobWhatsApp('${j.id}')">📱</button>`;
      return `<div class="card" id="job-${j.id}"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div><h3>Job #${j.id} <span class="badge ${badgeClass}">${esc(j.status)}</span></h3><p><strong>${esc(j.customer)}</strong></p><p>🚗 ${esc(j.vehicle)} ${j.registration ? '(' + esc(j.registration) + ')' : ''}</p>${as}</div><div style="text-align:right;"><p style="font-size:11px;color:var(--text2);">${esc(j.created)}</p></div></div><p style="color:var(--text2);font-size:13px;margin-top:8px;">${esc(j.complaint)}</p>${cost}<div class="no-print" style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;"><select class="form-input" style="margin:0;flex:1;padding:8px;font-size:12px;width:auto;" onchange="updateJobStatus('${j.id}', this.value)">${statusOpts}</select><button class="btn-sm purple" onclick="setCost('${j.id}')">💰 Cost</button>${invBtn}${waBtn}</div></div>`;
    }).join('');
  } catch (e) { c.innerHTML = '<div class="card"><p>Error loading jobs</p></div>'; }
}
async function updateJobStatus(jid, newStatus) { try { await jput('/api/jobs/' + jid, { status: newStatus }); toast('Status updated'); loadJobs(); if (document.getElementById('kanbanModal') && document.getElementById('kanbanModal').style.display === 'block') openKanban(); } catch (e) { toast('Failed', 'error'); } }
async function setCost(id) { const h = prompt('Labour hours:', '1'); if (h === null) return; const p = prompt('Parts cost (R):', '0'); if (p === null) return; try { await jpost('/api/jobs/' + id + '/cost', { labour_hours: parseFloat(h), labour_rate: 450, parts_cost: parseFloat(p) }); toast('Cost updated'); loadJobs(); } catch(e) { toast('Error', 'error'); } }
async function generateInvoice(jid) { try { const d = await jget('/api/jobs'); const job = d.jobs.find(x => x.id == jid); if (!job) return; const res = await jpost('/api/invoices', { customer: job.customer, vehicle: job.vehicle, description: job.complaint, labour: job.labour_cost || 0, parts: job.parts_cost || 0 }); if (res.success) { toast('Invoice generated!'); showTab('invoices'); loadInvoices(); } } catch(e) { toast('Error', 'error'); } }
async function shareJobWhatsApp(id) { const d = await jget('/api/jobs'); const j = d.jobs.find(x => x.id == id); if (!j) return; const txt = `🔧 *Job #${j.id} Update*\n\nHi ${j.customer},\nYour vehicle (${j.vehicle}) is currently: *${j.status}*.\n\nIssue: ${j.complaint}`; window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank'); }

// CUSTOMERS & INVOICES
function showCustomerForm(){document.getElementById('customerForm').style.display='block'} function hideCustomerForm(){document.getElementById('customerForm').style.display='none'}
async function createCustomer() { const name = document.getElementById('custName').value.trim(); const phone = document.getElementById('custPhone').value.trim(); if (!name || !phone) { toast('Name and phone required', 'error'); return; } await jpost('/api/customers', { name: name, phone: phone, email: document.getElementById('custEmail').value, address: document.getElementById('custAddress').value }); document.getElementById('custName').value = ''; document.getElementById('custPhone').value = ''; hideCustomerForm(); loadCustomers(); toast('Customer added'); }
async function loadCustomers() { try { const d = await jget('/api/customers'); document.getElementById('customerList').innerHTML = d.customers.map(c=>`<div class="card"><div style="display:flex;justify-content:space-between;"><div><h3>👤 ${esc(c.name)}</h3><p>📞 ${esc(c.phone)}</p>${c.email ? `<p>📧 ${esc(c.email)}</p>` : ''}</div><button class="btn-sm whatsapp" onclick="window.open('https://wa.me/${c.phone.replace(/\D/g,'')}', '_blank')">📱 Chat</button></div></div>`).join('') || '<div class="card"><p>No customers yet</p></div>'; } catch(e){} }
async function loadInvoices() { try { const d = await jget('/api/invoices'); document.getElementById('invoiceList').innerHTML = d.invoices.map(i=>{ const isPaid = i.paid; const badge = isPaid ? 'paid' : 'outstanding'; const payBtn = !isPaid ? `<button class="btn-sm blue" onclick="window.location.href='/pay/${i.id}'">💳 Pay Now</button>` : ''; return `<div class="card"><h3>Invoice #${i.id} <span class="badge ${badge}">${badge.toUpperCase()}</span></h3><p><strong>${esc(i.customer)}</strong></p><p style="font-size:20px; font-weight:800; color:var(--primary); margin: 8px 0;">R ${i.total.toFixed(2)}</p><div style="display:flex; gap:5px; flex-wrap:wrap;"><button class="btn-sm green" onclick="window.open('/api/workflow/invoice-html/${i.id}', '_blank')">🖨 PDF</button><button class="btn-sm whatsapp" onclick="shareInvoiceWhatsApp('${i.id}', '${esc(i.customer)}', '${i.total}')">📱 Share</button>${payBtn}</div></div>`; }).join('') || '<div class="card"><p>No invoices yet</p></div>'; } catch(e){} }
function shareInvoiceWhatsApp(id, customer, total) { const txt = `Hi ${customer}, your invoice #${id} is ready. Total due: R${total}. You can view and pay it here: https://ramstech.onrender.com/pay/${id}`; window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank'); }

// INVENTORY
function showInvForm(){document.getElementById('invForm').style.display='block'} function hideInvForm(){document.getElementById('invForm').style.display='none'}
async function addInventory() {
  const name = document.getElementById('invPartName').value.trim();
  if (!name) { toast('Part name required', 'error'); return; }
  await jpost('/api/inventory', { part_number: document.getElementById('invPartNum').value, name: name, category: document.getElementById('invCategory').value, qty: parseInt(document.getElementById('invQty').value) || 0, min_qty: parseInt(document.getElementById('invMinQty').value) || 5, cost_price: parseFloat(document.getElementById('invCostPrice').value) || 0, sell_price: parseFloat(document.getElementById('invSellPrice').value) || 0, supplier: document.getElementById('invSupplier').value });
  ['invPartNum','invPartName','invCategory','invQty','invMinQty','invCostPrice','invSellPrice','invSupplier'].forEach(id => document.getElementById(id).value = '');
  hideInvForm(); loadInventory(); toast('Item added to stock');
}
async function loadInventory() { 
  try { const d = await jget('/api/inventory'); 
    document.getElementById('inventoryList').innerHTML = d.items.map(i => {
      const cls = i.qty <= i.min_qty ? 'warn' : 'ok';
      return `<div class="card"><h3>${esc(i.name)} <span class="badge ${cls}">${i.qty} in stock</span></h3><p style="font-family:monospace;font-size:12px;">${esc(i.part_number || '-')}</p><p>Cost: R${i.cost_price.toFixed(2)} | Sell: R${i.sell_price.toFixed(2)}</p>${i.qty <= i.min_qty ? '<p style="color:#ef4444;font-size:12px;font-weight:700;">⚠ Low stock (min ' + i.min_qty + ')</p>' : ''}<div style="margin-top:10px;"><button class="btn-sm green" onclick="adjInv('${i.id}',1)">+1</button><button class="btn-sm red" onclick="adjInv('${i.id}',-1)">-1</button></div></div>`;
    }).join('') || '<div class="card"><p>No stock items</p></div>'; 
  } catch(e){} 
}
async function adjInv(id, d) { await jpost('/api/inventory/' + id + '/adjust', {delta:d}); loadInventory(); }

// APPOINTMENTS
function showApptForm(){document.getElementById('apptForm').style.display='block'} function hideApptForm(){document.getElementById('apptForm').style.display='none'}
async function createAppt() {
  const c = document.getElementById('apptCustomer').value.trim(); const d = document.getElementById('apptDate').value; const t = document.getElementById('apptTime').value;
  if (!c || !d || !t) { toast('Customer, date, time required', 'error'); return; }
  await jpost('/api/appointments', {customer:c, phone:document.getElementById('apptPhone').value, vehicle:document.getElementById('apptVehicle').value, service:document.getElementById('apptService').value, date:d, time:t});
  ['apptCustomer','apptPhone','apptVehicle','apptService','apptDate','apptTime'].forEach(id => document.getElementById(id).value = '');
  hideApptForm(); loadAppts(); toast('Appointment booked');
}
async function loadAppts() { 
  try { const d = await jget('/api/appointments'); const s = d.appointments.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
    document.getElementById('apptList').innerHTML = s.length ? s.map(a => `<div class="card"><h3>📅 ${esc(a.date)} at ${esc(a.time)}</h3><p><strong>${esc(a.customer)}</strong></p>${a.phone ? `<p>📞 ${esc(a.phone)}</p>` : ''}${a.vehicle ? `<p>🚗 ${esc(a.vehicle)}</p>` : ''}${a.service ? `<p style="color:var(--text2);">${esc(a.service)}</p>` : ''}<button class="btn-sm red" onclick="delAppt('${a.id}')">Delete</button></div>`).join('') : '<div class="card"><p>No appointments</p></div>'; 
  } catch(e){} 
}
async function delAppt(id) { if (!confirm('Delete?')) return; await jdel('/api/appointments/' + id); loadAppts(); }

// CLOCK INS
async function loadClockin() {
  try { const sd = await jget('/api/staff'); const cd = await jget('/api/clockins');
    document.getElementById('clockinList').innerHTML = sd.staff.length ? sd.staff.map(s => {
      const active = cd.clockins.find(x => x.staff_id === s.id && !x.clock_out);
      return `<div class="card"><h3>👷 ${esc(s.name)}</h3>${active ? `<p style="color:#10b981;font-weight:700;">🕐 Clocked in at ${esc(active.clock_in)}</p><button class="btn-sm red" onclick="clockOut('${s.id}')">Clock Out</button>` : `<button class="btn-sm green" onclick="clockIn('${s.id}')">Clock In</button>`}</div>`;
    }).join('') : '<div class="card"><p>Add staff first in Settings</p></div>';
  } catch(e){}
}
async function clockIn(id) { await jpost('/api/clockins', {staff_id:id}); loadClockin(); }
async function clockOut(id) { await jpost('/api/clockins/' + id + '/out', {}); loadClockin(); }

// SETTINGS & PARTS
async function loadSettings() { try { const d = await jget('/api/workshop'); document.getElementById('wsName').value = d.name||''; } catch(e){} }
async function saveSettings() { const p = { name: document.getElementById('wsName').value, logo: document.getElementById('wsLogo').value, phone: document.getElementById('wsPhone').value, address: document.getElementById('wsAddress').value, email: document.getElementById('wsEmail').value, labour_rate: parseFloat(document.getElementById('wsRate').value) || 450 }; await jpost('/api/workshop', p); toast('Settings saved!'); }

async function searchParts() { const q = document.getElementById('partsSearch').value; if (!q) return; const c = document.getElementById('partsResults'); c.innerHTML = '<div class="loading">Searching...</div>'; try { const d = await jget('/api/parts-search?q=' + encodeURIComponent(q)); c.innerHTML = d.results.length ? d.results.map(p=>`<div class="card"><h3>${esc(p.name)}</h3><p style="font-size:12px;font-family:monospace;">${esc(p.part_number)}</p><p>Price: R${p.sell_price.toFixed(2)}</p></div>`).join('') : '<div class="card"><p>No parts found</p></div>'; } catch(e) { c.innerHTML = 'Error'; } }
function showPOForm(){document.getElementById('poForm').style.display='block'} function hidePOForm(){document.getElementById('poForm').style.display='none'}
async function createPO() { const sup = document.getElementById('poSupplier').value; const items = document.getElementById('poItems').value; if (!sup || !items) { toast('Supplier and items required', 'error'); return; } try { await jpost('/api/po/create', { supplier: sup, items: items }); hidePOForm(); loadPOs(); toast('PO Created'); } catch(e) { toast('Error', 'error'); } }
async function loadPOs() { try { const d = await jget('/api/po/list'); document.getElementById('poList').innerHTML = d.purchase_orders.length ? d.purchase_orders.map(p=>`<div class="card"><h3>PO #${p.po_number}</h3><p>${esc(p.supplier)}</p><p>Status: <b>${p.status}</b></p></div>`).join('') : '<div class="card"><p>No purchase orders</p></div>'; } catch(e){} }

// MODALS (Kanban, Photo, Staff, Scanner)
async function openKanban() {
  let modal = document.getElementById('kanbanModal');
  if (!modal) { modal = document.createElement('div'); modal.id = 'kanbanModal'; modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);z-index:9999;padding:16px;overflow:auto;'; modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:800px;margin:0 auto;color:var(--text);border:1px solid var(--primary);"><div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:800;">📊 Kanban Board</h2><button onclick="document.getElementById('kanbanModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button></div><div id="kanbanContent" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;">Loading...</div></div>`; document.body.appendChild(modal); } else { modal.style.display = 'block'; }
  const d = await jget('/api/jobs/kanban'); let html = '';
  d.statuses.forEach(s => { const items = d.columns[s] || []; html += `<div style="background:var(--input-bg);border-radius:10px;padding:10px;border:1px solid var(--border);"><h4 style="font-size:12px;color:var(--primary);text-transform:uppercase;margin-bottom:8px;letter-spacing:1px;">${s} (${items.length})</h4>`; items.forEach(j => { html += `<div style="background:var(--card);padding:10px;border-radius:8px;margin-bottom:8px;border-left:4px solid var(--primary);box-shadow:0 2px 8px rgba(0,0,0,0.1);"><h5 style="font-size:13px;margin-bottom:2px;">#${j.id} ${esc(j.customer)}</h5><p style="font-size:11px;color:var(--text2);">${esc(j.vehicle)}</p></div>`; }); html += `</div>`; });
  document.getElementById('kanbanContent').innerHTML = html;
}

async function openPhotoIntake() {
  let modal = document.getElementById('photoIntakeModal');
  if (!modal) { modal = document.createElement('div'); modal.id = 'photoIntakeModal'; modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);z-index:9999;padding:16px;overflow:auto;'; modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:0 auto;color:var(--text);border:1px solid var(--primary);"><div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:800;">📸 Photo Intake</h2><button onclick="document.getElementById('photoIntakeModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button></div><div id="piStep1" class="card" style="background:var(--input-bg);"><p style="font-size:13px;color:var(--text2);margin-bottom:10px;">Take a photo of the VIN sticker, license plate, or dashboard.</p><input type="file" id="piImage" accept="image/*" capture="environment" class="form-input" onchange="processPhotoIntake(event)"></div><div id="piStep2" style="display:none;"><div id="piPreview" style="margin-bottom:10px;"></div><div id="piResult" class="card" style="background:var(--input-bg);"><h3 style="margin-bottom:10px;font-size:14px;">Vehicle Details</h3><input type="text" id="piMake" class="form-input" placeholder="Make"><input type="text" id="piModel" class="form-input" placeholder="Model"><input type="text" id="piReg" class="form-input" placeholder="Registration"><input type="text" id="piVin" class="form-input" placeholder="VIN"><input type="number" id="piKm" class="form-input" placeholder="Odometer"><button class="btn btn-success" onclick="createJobFromPhoto()">✓ Create Job Card</button></div></div><div id="piLoading" style="display:none;text-align:center;padding:20px;color:var(--primary);"><div class="spinner" style="border:3px solid rgba(0,0,0,0.1);border-top-color:var(--primary);border-radius:50%;width:30px;height:30px;animation:spin 1s linear infinite;margin:0 auto 10px;"></div>Analyzing photo...</div></div>`; document.body.appendChild(modal); } else { modal.style.display = 'block'; document.getElementById('piStep1').style.display = 'block'; document.getElementById('piStep2').style.display = 'none'; document.getElementById('piImage').value = ''; }
}
async function processPhotoIntake(e) { const file = e.target.files[0]; if (!file) return; document.getElementById('piStep1').style.display = 'none'; document.getElementById('piLoading').style.display = 'block'; const reader = new FileReader(); reader.onload = async function(ev) { const img = new Image(); img.onload = async function() { const canvas = document.createElement('canvas'); let w = img.width, h = img.height; if (w > 1200) { h = (h * 1200) / w; w = 1200; } canvas.width = w; canvas.height = h; canvas.getContext('2d').drawImage(img, 0, 0, w, h); const b64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1]; document.getElementById('piPreview').innerHTML = '<img src="' + canvas.toDataURL('image/jpeg', 0.8) + '" style="width:100%;border-radius:12px;border:1px solid var(--border);">'; try { const res = await jpost('/api/photo/intake', { image_base64: b64 }); document.getElementById('piLoading').style.display = 'none'; document.getElementById('piStep2').style.display = 'block'; if (res.success) { document.getElementById('piMake').value = res.make || ''; document.getElementById('piModel').value = res.model || ''; document.getElementById('piReg').value = res.registration || ''; document.getElementById('piVin').value = res.vin || ''; document.getElementById('piKm').value = res.km || ''; } else { toast('AI could not read: ' + (res.error || 'Try clearer'), 'error'); } } catch (err) { document.getElementById('piLoading').style.display = 'none'; document.getElementById('piStep2').style.display = 'block'; toast('Network error', 'error'); } }; img.src = ev.target.result; }; reader.readAsDataURL(file); }
async function createJobFromPhoto() { const make = document.getElementById('piMake').value.trim(); const model = document.getElementById('piModel').value.trim(); const reg = document.getElementById('piReg').value.trim(); const vin = document.getElementById('piVin').value.trim(); const km = document.getElementById('piKm').value.trim(); const payload = { customer: 'New Customer (Photo)', phone: '', vehicle: (make + ' ' + model).trim(), registration: reg || vin, km: parseInt(km) || 0, complaint: 'Photo Intake', assigned_to: '', photos: [], signature: '', warranty_months: 6 }; try { const res = await jpost('/api/jobs', payload); if (res.success) { toast('Job created!'); document.getElementById('photoIntakeModal').style.display = 'none'; showTab('jobs'); loadJobs(); } } catch (e) { toast('Error', 'error'); } }

async function openStaffManager() {
  let modal = document.getElementById('staffModal');
  if (!modal) { modal = document.createElement('div'); modal.id = 'staffModal'; modal.style.cssText = 'display:block;position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);z-index:9999;padding:16px;overflow:auto;'; modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:0 auto;color:var(--text);border:1px solid var(--primary);"><div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:800;">👥 Manage Staff</h2><button onclick="document.getElementById('staffModal').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button></div><div class="card" style="background:var(--input-bg);"><h3 style="margin-bottom:10px;font-size:14px;">Add New Staff</h3><input type="text" id="newStaffName" class="form-input" placeholder="Full Name"><select id="newStaffRole" class="form-input"><option value="technician">Technician</option><option value="manager">Manager</option></select><input type="number" id="newStaffPin" class="form-input" placeholder="4-digit PIN" maxlength="4"><button class="btn btn-success" onclick="addNewStaff()">+ Add Staff</button></div><div id="staffList" style="margin-top:16px;"><div style="text-align:center;padding:20px;color:var(--text2);font-size:13px;">Loading...</div></div></div>`; document.body.appendChild(modal); } else { modal.style.display = 'block'; }
  loadStaffList();
}
async function loadStaffList() { const list = document.getElementById('staffList'); list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text2);">Loading...</div>'; try { const d = await jget('/api/staff'); if (!d.staff || d.staff.length === 0) { list.innerHTML = '<p style="text-align:center;color:var(--text2);font-size:13px;">No staff added yet.</p>'; return; } list.innerHTML = d.staff.map(s => `<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:12px;"><div><strong style="font-size:14px;">${esc(s.name)}</strong><br><span style="font-size:11px;color:var(--text2);">${esc(s.role)} • PIN: ${s.pin || 'None'}</span></div><button class="btn-sm red" onclick="deleteStaff('${s.id}')">Delete</button></div>`).join(''); } catch (e) { list.innerHTML = '<p style="color:red;text-align:center;">Error loading staff</p>'; } }
async function addNewStaff() { const name = document.getElementById('newStaffName').value.trim(); const role = document.getElementById('newStaffRole').value; const pin = document.getElementById('newStaffPin').value.trim(); if (!name || pin.length !== 4) { toast('Enter name and 4-digit PIN', 'error'); return; } try { const res = await jpost('/api/staff', { name: name, role: role, pin: pin }); if (res.success) { await jpost('/api/staff/' + res.staff.id + '/pin', { pin: pin }); document.getElementById('newStaffName').value = ''; document.getElementById('newStaffPin').value = ''; loadStaffList(); loadStaffDropdown(); toast('Staff added'); } } catch (e) { toast('Error', 'error'); } }
async function deleteStaff(id) { if (!confirm('Delete?')) return; try { await jdel('/api/staff/' + id); loadStaffList(); loadStaffDropdown(); toast('Staff removed'); } catch (e) {} }
async function loadStaffDropdown() { try { const d = await jget('/api/staff'); const sel = document.getElementById('jobAssigned'); sel.innerHTML = '<option value="">— Assign to staff —</option>' + (d.staff||[]).map(s => '<option value="' + esc(s.name) + '">' + esc(s.name) + '</option>').join(''); } catch (e) {} }

let html5QrCode = null;
async function openScanner() { let modal = document.getElementById('scannerModal'); if (!modal) { modal = document.createElement('div'); modal.id = 'scannerModal'; modal.style.cssText = 'display:block;position:fixed;inset:0;background:#000;z-index:9999;padding:16px;'; modal.innerHTML = `<div style="color:white;display:flex;justify-content:space-between;margin-bottom:10px;"><h2 style="font-size:18px;">📷 Scan Barcode</h2><button onclick="closeScanner()" style="background:none;border:none;color:white;font-size:24px;">✕</button></div><div id="reader" style="width:100%;border-radius:12px;overflow:hidden;"></div>`; document.body.appendChild(modal); } else { modal.style.display = 'block'; } if (!html5QrCode) { const script = document.createElement('script'); script.src = "https://unpkg.com/html5-qrcode"; script.onload = () => { html5QrCode = new Html5Qrcode("reader"); html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: {width: 250, height: 150} }, (text) => { closeScanner(); document.getElementById('vinInput').value = text; decodeVin(); }); }; document.body.appendChild(script); } else { html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: {width: 250, height: 150} }, (text) => { closeScanner(); document.getElementById('vinInput').value = text; decodeVin(); }); } }
function closeScanner() { document.getElementById('scannerModal').style.display = 'none'; if (html5QrCode) html5QrCode.stop().catch(e=>{}); }

// VIN & AI VISION & FAULT CODES
async function decodeVin() { try { const d = await jget('/api/vin/'+document.getElementById('vinInput').value); document.getElementById('vinResult').innerHTML = '<div class="card"><h3>'+d.manufacturer+'</h3><p>Year: '+d.year+'</p></div>'; } catch(e){} }

async function searchCodes() { 
    const q = document.getElementById('codeSearch').value.trim();
    const c = document.getElementById('codeResults');
    
    if (!q) {
        c.innerHTML = '<div class="loading">Type to search...</div>';
        return;
    }
    
    c.innerHTML = '<div class="loading">Searching...</div>';
    
    try { 
        const d = await jget('/api/fault-codes?search=' + encodeURIComponent(q)); 
        document.getElementById('codeResults').dataset.loaded = '1'; 
        
        if (!d.codes || d.codes.length === 0) {
            c.innerHTML = `<div class="card">
                <h3>Code not found</h3>
                <p style="color:var(--text2);font-size:13px;">Code <b>${esc(q)}</b> is not in the local database.</p>
                <button class="btn" style="margin-top:10px;font-size:12px;padding:10px;" onclick="document.getElementById('aiCode').value='${esc(q)}'; aiMode('code'); aiToggle();">Ask AI about this code</button>
            </div>`;
            return;
        }
        
        c.innerHTML = d.codes.map(x => `
            <div class="card">
                <h3>${x.code} <span class="badge ${x.severity === 'High' ? 'high' : (x.severity === 'Medium' ? 'medium' : 'low')}">${x.severity}</span></h3>
                <p style="font-weight:700;margin-bottom:8px;">${esc(x.description)}</p>
                <p style="font-size:12px;color:var(--text2);margin-bottom:4px;"><b>System:</b> ${esc(x.system)}</p>
                ${x.causes ? `<p style="font-size:13px;margin-top:8px;"><b>Causes:</b></p><ul style="padding-left:20px;font-size:13px;color:var(--text2);">${x.causes.map(c => `<li>${esc(c)}</li>`).join('')}</ul>` : ''}
                ${x.steps ? `<p style="font-size:13px;margin-top:8px;"><b>Steps:</b></p><ol style="padding-left:20px;font-size:13px;color:var(--text2);">${x.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>` : ''}
            </div>
        `).join(''); 
    } catch(e) {
        c.innerHTML = '<div class="card"><p style="color:red;">Network error loading codes.</p></div>';
    } 
}

// PROBLEMS SEARCH & MODAL
window.ALL_PROBLEMS = [];

async function loadProblems() { 
    try { 
        const d = await jget('/api/problems'); 
        window.ALL_PROBLEMS = d.problems;
        renderProblems(window.ALL_PROBLEMS);
    } catch(e){} 
}

function renderProblems(problems) {
    document.getElementById('problemList').innerHTML = problems.map((x, i) => `
        <div class="card" style="cursor:pointer;" onclick="showProblemDetails('${esc(x.title)}')">
            <h3>${esc(x.title)}</h3>
            <p style="font-size:13px;color:var(--text2);">${esc(x.system)} - ${esc(x.severity)}</p>
        </div>
    `).join('') || '<div class="card"><p>No problems found.</p></div>';
}

function filterProblems() {
    const q = document.getElementById('problemSearch').value.toLowerCase().trim();
    if (!q) {
        renderProblems(window.ALL_PROBLEMS);
        return;
    }
    
    // 1. Try exact substring match
    let filtered = window.ALL_PROBLEMS.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.system.toLowerCase().includes(q)
    );
    
    // 2. If nothing found, try keyword match (any word in title/system/causes)
    if (filtered.length === 0) {
        const words = q.split(/\s+/);
        filtered = window.ALL_PROBLEMS.filter(p => {
            const text = (p.title + " " + p.system + " " + (p.causes||[]).join(" ")).toLowerCase();
            return words.some(w => w.length > 2 && text.includes(w));
        });
    }

    if (filtered.length > 0) {
        renderProblems(filtered);
    } else {
        // 3. AI Fallback if nothing local is found
        document.getElementById('problemList').innerHTML = `
            <div class="card">
                <h3>No local match found</h3>
                <p style="color:var(--text2);font-size:13px;margin-bottom:12px;">We couldn't find a local match for "<b>${esc(q)}</b>".</p>
                <button class="btn" onclick="getAIProcedureForSearch('${esc(q)}')" style="background:var(--grad6);font-size:14px;">🤖 Ask AI for Diagnosis & Procedure</button>
            </div>
            <div id="aiSearchResult" style="display:none; background:var(--input-bg); padding:14px; border-radius:8px; border:1px solid var(--border); margin-top:14px; font-size:14px; line-height:1.6;"></div>
        `;
    }
}

async function getAIProcedureForSearch(query) {
    const resBox = document.getElementById('aiSearchResult');
    resBox.style.display = 'block';
    resBox.innerHTML = '<span style="color:var(--primary);">Analyzing your query and generating procedures... please wait.</span>';
    
    try {
        const res = await jpost('/api/problems/ai-procedure', { problem: query });
        if (res.reply) {
            let html = esc(res.reply)
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
            resBox.innerHTML = html;
        } else {
            resBox.innerHTML = 'Error getting response.';
        }
    } catch(e) {
        resBox.innerHTML = 'Network error.';
    }
}

async function showProblemDetails(problemTitle) {
    const p = window.ALL_PROBLEMS.find(x => x.title === problemTitle);
    if (!p) return;
    
    let modal = document.getElementById('probModal');
    if (!modal) { 
        modal = document.createElement('div'); 
        modal.id = 'probModal'; 
        modal.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);z-index:9999;padding:16px;overflow:auto;'; 
        modal.innerHTML = `<div style="background:var(--card);padding:20px;border-radius:16px;max-width:600px;margin:20px auto;color:var(--text);border:1px solid var(--primary);position:relative;">
            <button onclick="document.getElementById('probModal').style.display='none'" style="position:absolute;top:15px;right:15px;background:none;border:none;font-size:20px;cursor:pointer;color:var(--text);">✕</button>
            <h2 id="pmTitle" style="font-size:18px;font-weight:800;color:var(--primary);margin-bottom:4px;"></h2>
            <p id="pmSub" style="font-size:12px;color:var(--text2);margin-bottom:16px;"></p>
            
            <div id="pmCauses" style="margin-bottom:16px;"></div>
            <div id="pmChecks" style="margin-bottom:16px;"></div>
            
            <hr style="border:none;border-top:1px solid var(--border);margin:15px 0;">
            <h3 style="font-size:14px;margin-bottom:10px;">🤖 AI Deep Dive</h3>
            <p style="font-size:12px;color:var(--text2);margin-bottom:10px;">Need exact testing procedures? Let the AI generate a step-by-step diagnostic guide.</p>
            <button class="btn" onclick="getAIProcedure('${esc(p.title)}')" style="background:var(--grad6);font-size:14px;">Get Step-by-Step Procedure</button>
            <div id="pmAIResult" style="margin-top:15px;font-size:14px;line-height:1.6;display:none;background:var(--input-bg);padding:12px;border-radius:8px;border:1px solid var(--border);"></div>
        </div>`;
        document.body.appendChild(modal); 
    }
    
    document.getElementById('pmTitle').textContent = p.title;
    document.getElementById('pmSub').textContent = `${p.system} • ${p.severity} Severity`;
    
    document.getElementById('pmCauses').innerHTML = `<p style="font-size:13px;font-weight:700;margin-bottom:4px;">Possible Causes:</p><ul style="padding-left:20px;font-size:13px;color:var(--text2);">${p.causes.map(c => `<li>${esc(c)}</li>`).join('')}</ul>`;
    document.getElementById('pmChecks').innerHTML = `<p style="font-size:13px;font-weight:700;margin-bottom:4px;">Basic Checks:</p><ul style="padding-left:20px;font-size:13px;color:var(--text2);">${p.checks.map(c => `<li>${esc(c)}</li>`).join('')}</ul>`;
    
    document.getElementById('pmAIResult').style.display = 'none';
    document.getElementById('pmAIResult').innerHTML = '';
    
    modal.style.display = 'block';
}

async function getAIProcedure(problemTitle) {
    const resBox = document.getElementById('pmAIResult');
    resBox.style.display = 'block';
    resBox.innerHTML = '<span style="color:var(--primary);">Generating procedures... please wait.</span>';
    
    try {
        const res = await jpost('/api/problems/ai-procedure', { problem: problemTitle });
        if (res.reply) {
            let html = esc(res.reply)
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
            resBox.innerHTML = html;
        } else {
            resBox.innerHTML = 'Error getting response.';
        }
    } catch(e) {
        resBox.innerHTML = 'Network error.';
    }
}

let paintB64 = '';
async function previewPaint(e) { const file = e.target.files[0]; if (!file) return; const reader = new FileReader(); reader.onload = function(ev) { const img = new Image(); img.onload = function() { const canvas = document.createElement('canvas'); let w = img.width, h = img.height; if (w > 1000) { h = (h * 1000) / w; w = 1000; } canvas.width = w; canvas.height = h; canvas.getContext('2d').drawImage(img, 0, 0, w, h); paintB64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1]; document.getElementById('paintPreview').innerHTML = `<img src="${canvas.toDataURL('image/jpeg', 0.8)}" style="width:100%;border-radius:12px;margin-bottom:10px;border:1px solid var(--border);">`; }; img.src = ev.target.result; }; reader.readAsDataURL(file); }
async function matchPaint() { const btn = document.getElementById('paintBtn'); const c = document.getElementById('paintResult'); if (!paintB64) { toast('Please select an image', 'error'); return; } btn.disabled = true; btn.textContent = '🎨 Analyzing...'; c.innerHTML = '<div class="loading">Scanning paint colour...</div>'; try { const res = await jpost('/api/paint/match', { image_base64: paintB64 }); if (!res.success) throw new Error(res.error); const col = res.detected_colour || {}; let h = `<div class="card" style="border-left:4px solid ${col.hex_code || '#ccc'};"><div style="height:60px;border-radius:8px;background:${col.hex_code || '#000'};margin-bottom:12px;"></div><h3>${esc(col.name || 'Unknown')}</h3><p style="font-family:monospace;font-size:18px;">${col.hex_code || ''}</p></div>`; c.innerHTML = h; } catch(e) { c.innerHTML = `<div class="card" style="border-left:4px solid #ef4444;"><p style="color:#ef4444;">Error: ${e.message}</p></div>`; } btn.disabled = false; btn.textContent = '🎨 Match Paint Colour'; }

let diagB64 = '';
async function previewDiag(e) { const file = e.target.files[0]; if (!file) return; const reader = new FileReader(); reader.onload = function(ev) { const img = new Image(); img.onload = function() { const canvas = document.createElement('canvas'); let w = img.width, h = img.height; if (w > 1000) { h = (h * 1000) / w; w = 1000; } canvas.width = w; canvas.height = h; canvas.getContext('2d').drawImage(img, 0, 0, w, h); diagB64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1]; document.getElementById('photoPreview').innerHTML = `<img src="${canvas.toDataURL('image/jpeg', 0.8)}" style="width:100%;border-radius:12px;margin-bottom:10px;border:1px solid var(--border);">`; }; img.src = ev.target.result; }; reader.readAsDataURL(file); }
async function diagnosePhoto() { const btn = document.getElementById('photoBtn'); const c = document.getElementById('photoResult'); if (!diagB64) { toast('Please select an image', 'error'); return; } btn.disabled = true; btn.textContent = '📸 Analyzing...'; c.innerHTML = '<div class="loading">Scanning photo...</div>'; try { const res = await jpost('/api/diagnose/photo', { image_base64: diagB64, vehicle_info: document.getElementById('photoVehicle').value }); if (!res.success) throw new Error(res.error); let h = `<div class="card" style="border-left:4px solid var(--primary);"><h3>🔍 ${esc(res.problem || 'Detected')}</h3><p><strong>Confidence:</strong> ${esc(res.confidence || '')}</p><p style="margin-top:8px;">${esc(res.description || '')}</p></div>`; if (res.possible_causes) res.possible_causes.forEach(x => h += `<div class="list-item">• ${esc(x)}</div>`); c.innerHTML = h; } catch(e) { c.innerHTML = `<div class="card" style="border-left:4px solid #ef4444;"><p style="color:#ef4444;">Error: ${e.message}</p></div>`; } btn.disabled = false; btn.textContent = '📸 Analyze Photo'; }

lucide.createIcons();
</script>
</body>
</html>"""
