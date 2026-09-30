P1 = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f0f2f5;--card:#fff;--text:#1a1a2e;--text2:#6b7280;--border:#e5e7eb;--primary:#E65100;--input-bg:#f9fafb;--grad1:linear-gradient(135deg,#667eea,#764ba2);--grad2:linear-gradient(135deg,#f093fb,#f5576c);--grad4:linear-gradient(135deg,#43e97b,#38f9d7);--grad6:linear-gradient(135deg,#30cfd0,#330867)}
body.dark{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--text2:#94a3b8;--border:#334155;--input-bg:#0f172a}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);padding-bottom:80px;transition:background .3s,color .3s;background-image:radial-gradient(circle at 20% 20%,rgba(230,81,0,.08),transparent 40%),radial-gradient(circle at 80% 60%,rgba(102,126,234,.08),transparent 40%);background-attachment:fixed}
.header{background:var(--grad1);color:white;padding:16px 14px 18px;position:relative;overflow:hidden;border-bottom-left-radius:24px;border-bottom-right-radius:24px;box-shadow:0 6px 24px rgba(102,126,234,.35)}
.header::before{content:'';position:absolute;top:-50%;right:-20%;width:300px;height:300px;background:radial-gradient(circle,rgba(255,255,255,.15),transparent 70%);border-radius:50%}
.header h1{font-size:20px;display:flex;align-items:center;justify-content:center;gap:8px;position:relative;z-index:1;font-weight:800}
.header h1 .logo{font-size:26px}
.header p{font-size:11px;opacity:.9;margin-top:3px;text-align:center;position:relative;z-index:1}
.top-btns{position:absolute;right:10px;top:10px;display:flex;gap:6px;z-index:2}
.top-btns button{background:rgba(255,255,255,.25);border:none;color:white;padding:8px;border-radius:10px;font-size:15px;cursor:pointer}
.lang-sel{background:rgba(255,255,255,.25);border:none;color:white;padding:8px 6px;border-radius:10px;font-size:12px;outline:none;font-weight:600}
.lang-sel option{color:#333}
.home-container{padding:16px;max-width:900px;margin:0 auto}
.hero-card{background:var(--card);border-radius:20px;padding:16px;margin-bottom:16px;box-shadow:0 4px 20px rgba(0,0,0,.06);border:1px solid var(--border)}
.cat-title{font-size:13px;font-weight:700;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;margin:20px 4px 12px}
.cat-grid{display:grid;grid-template-columns:1fr;gap:12px}
.cat-card{border-radius:20px;padding:20px 18px;color:white;cursor:pointer;position:relative;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.15);display:flex;align-items:center;gap:16px}
.cat-card:active{transform:scale(.97)}
.cat-icon{font-size:38px;min-width:50px;text-align:center}
.cat-info{flex:1}
.cat-name{font-size:17px;font-weight:800;margin-bottom:3px}
.cat-count{font-size:12px;opacity:.85}
.cat-arrow{font-size:20px;opacity:.7}
.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border-radius:16px;padding:16px 12px;cursor:pointer;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);position:relative;overflow:hidden}
.tile:active{transform:scale(.95)}
.tile-icon{font-size:32px;margin-bottom:8px;display:block}
.tile-label{font-size:12px;font-weight:700;color:var(--text)}
.tile-accent{position:absolute;top:0;left:0;right:0;height:4px}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:8px 4px;z-index:100}
.bnav-item{flex:1;text-align:center;padding:6px 4px;cursor:pointer;border-radius:12px}
.bnav-item.active{background:rgba(230,81,0,.08)}
.bnav-icon{font-size:20px;display:block;margin-bottom:2px}
.bnav-label{font-size:9px;font-weight:700;color:var(--text2);text-transform:uppercase}
.bnav-item.active .bnav-label{color:var(--primary)}
.panel{display:none;padding:16px;max-width:800px;margin:0 auto;padding-bottom:100px}
.panel.active{display:block;animation:fadeIn .3s}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.panel-title{font-size:20px;font-weight:800;color:var(--primary);margin-bottom:16px}
.card{background:var(--card);padding:16px;border-radius:16px;margin-bottom:12px;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px;font-weight:700}
.card p{margin:4px 0;font-size:13px;line-height:1.5}
.form-input{width:100%;padding:14px;border:1.5px solid var(--border);border-radius:12px;font-size:15px;margin-bottom:10px;background:var(--input-bg);color:var(--text);font-family:inherit}
.form-input:focus{outline:none;border-color:var(--primary)}
textarea.form-input{resize:vertical}
.btn{width:100%;padding:15px;border:none;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:10px;background:var(--grad1);color:white;box-shadow:0 4px 12px rgba(102,126,234,.3)}
.btn:active{transform:scale(.97)}
.btn-warn{background:var(--grad2);box-shadow:0 4px 12px rgba(245,87,108,.3)}
.btn-success{background:var(--grad4);box-shadow:0 4px 12px rgba(67,233,123,.3)}
.btn-dark{background:linear-gradient(135deg,#4b5563,#1f2937)}
.btn-sm{padding:8px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;margin-right:5px;margin-bottom:4px;background:var(--primary);color:white}
.btn-sm.gray{background:#6b7280}.btn-sm.green{background:#10b981}.btn-sm.red{background:#ef4444}.btn-sm.blue{background:#3b82f6}.btn-sm.whatsapp{background:#25D366}.btn-sm.purple{background:#8b5cf6}
.badge{display:inline-block;padding:3px 9px;border-radius:6px;font-size:11px;font-weight:700;color:white;margin-left:6px}
.badge.high,.badge.critical,.badge.warn{background:#ef4444}
.badge.medium{background:#f59e0b}
.badge.low,.badge.ok,.badge.completed,.badge.paid{background:#10b981}
.badge.new{background:#6b7280}.badge.inprogress{background:#f59e0b}
.badge.unpaid,.badge.outstanding{background:#ef4444}.badge.partial{background:#f59e0b}
.list-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.list-item:last-child{border-bottom:none}
.chat-box{background:var(--card);border-radius:16px;padding:14px;height:calc(100vh - 280px);overflow-y:auto;margin-bottom:12px;border:1px solid var(--border)}
.msg{padding:12px 16px;margin:8px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.45}
.msg.user{background:var(--grad1);color:white;margin-left:auto;border-bottom-right-radius:4px}
.msg.ai{background:var(--input-bg);border-bottom-left-radius:4px;border:1px solid var(--border)}
.input-row{display:flex;gap:8px;align-items:center}
.input-row input{flex:1;padding:14px 18px;border:1.5px solid var(--border);border-radius:25px;font-size:15px;outline:none;background:var(--input-bg);color:var(--text)}
.input-row button{padding:14px 16px;background:var(--grad1);color:white;border:none;border-radius:50%;font-weight:bold;cursor:pointer;font-size:16px}
.mic-btn{background:var(--grad4)!important}
.mic-btn.recording{background:var(--grad2)!important;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.img-preview{width:100%;border-radius:14px;margin-bottom:12px}
.thumb-row{display:flex;gap:8px;overflow-x:auto;margin-top:8px}
.thumb{width:80px;height:80px;object-fit:cover;border-radius:10px;border:2px solid var(--border)}
.thumb-wrap{position:relative}
.thumb-del{position:absolute;top:-6px;right:-6px;background:#ef4444;color:white;border:none;border-radius:50%;width:22px;height:22px;font-size:12px;cursor:pointer;font-weight:bold}
.swatch{height:90px;border-radius:14px;border:2px solid var(--border);margin-bottom:12px}
.status-online{background:linear-gradient(135deg,#10b981,#34d399);color:white;padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.status-offline{background:linear-gradient(135deg,#ef4444,#f87171);color:white;padding:10px 14px;border-radius:12px;display:inline-block;font-size:13px;font-weight:700}
.loading{text-align:center;padding:20px;color:var(--text2);font-size:13px}
.torque-table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:var(--grad1);color:white;padding:10px 8px;text-align:left;font-weight:700;font-size:11px}
.torque-table td{padding:10px 8px;border-bottom:1px solid var(--border)}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-card{background:var(--card);padding:16px 12px;border-radius:16px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,.06);border:1px solid var(--border);position:relative;overflow:hidden}
.stat-card .num{font-size:22px;font-weight:800;color:var(--primary)}
.stat-card .lbl{font-size:10px;color:var(--text2);margin-top:4px;font-weight:600;text-transform:uppercase}
.stat-card.green .num{color:#10b981}.stat-card.red .num{color:#ef4444}.stat-card.blue .num{color:#3b82f6}.stat-card.purple .num{color:#8b5cf6}
canvas{max-height:220px}
.checklist-item{padding:10px 0;border-bottom:1px solid var(--border);font-size:13px;display:flex;align-items:center;gap:10px}
.checklist-item input{width:20px;height:20px;accent-color:var(--primary)}
.back-btn{background:var(--grad6);color:white;border:none;padding:10px 16px;border-radius:12px;font-size:13px;font-weight:700;cursor:pointer;margin-bottom:16px}
@media print{.header,.bottom-nav,.no-print,button{display:none!important}.panel{display:block!important}.panel:not(.active){display:none!important}body{background:white;color:black}}
</style>
</head>
<body>
<div class="header">
<h1><span class="logo" id="logoDisplay">🔧</span> <span id="wsNameDisplay">RAMSTECH</span></h1>
<p id="wsSubtitle">AI Workshop Assistant v10.1</p>
<div class="top-btns">
<select class="lang-sel" id="langSel" onchange="setLang()"><option value="en">EN</option><option value="af">AF</option><option value="zu">ZU</option></select>
<button onclick="toggleTheme()" id="themeBtn">🌙</button>
</div>
</div>
"""
