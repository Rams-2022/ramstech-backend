# pages.py — RamsTech HTML frontend v9.0
# Includes: Multi-language, Photo compression, Signature, Fuel log, Warranty

HTML_PAGE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RamsTech</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f5f5f5;--card:#fff;--text:#212121;--text2:#666;--border:#ddd;--primary:#E65100;--input-bg:#fff}
body.dark{--bg:#121212;--card:#1e1e1e;--text:#e0e0e0;--text2:#999;--border:#333;--input-bg:#2a2a2a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text);padding-bottom:20px}
.header{background:var(--primary);color:white;padding:14px;text-align:center;position:relative}
.header h1{font-size:20px;display:flex;align-items:center;justify-content:center;gap:8px}
.header h1 .logo{font-size:26px}
.header p{font-size:11px;opacity:.9;margin-top:2px}
.top-btns{position:absolute;right:8px;top:8px;display:flex;gap:4px}
.top-btns button{background:rgba(255,255,255,.2);border:none;color:white;padding:6px 9px;border-radius:8px;font-size:15px;cursor:pointer}
.lang-sel{background:rgba(255,255,255,.2);border:none;color:white;padding:6px;border-radius:8px;font-size:13px;outline:none}
.lang-sel option{color:#333}
.tabs{display:flex;background:var(--card);border-bottom:1px solid var(--border);overflow-x:auto;position:sticky;top:0;z-index:99;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{padding:12px 11px;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap;font-size:11px;color:var(--text)}
.tab.active{color:var(--primary);border-bottom-color:var(--primary);font-weight:bold}
.panel{display:none;padding:14px;max-width:800px;margin:0 auto}
.panel.active{display:block}
.chat-box{background:var(--card);border-radius:12px;padding:12px;height:400px;overflow-y:auto;margin-bottom:12px}
.msg{padding:10px 14px;margin:6px 0;border-radius:16px;max-width:85%;word-wrap:break-word;font-size:14px;line-height:1.4}
.msg.user{background:var(--primary);color:white;margin-left:auto}
.msg.ai{background:var(--border)}
.input-row{display:flex;gap:6px}
.input-row input{flex:1;padding:12px 16px;border:1px solid var(--border);border-radius:25px;font-size:14px;outline:none;background:var(--input-bg);color:var(--text)}
.input-row button{padding:12px 15px;background:var(--primary);color:white;border:none;border-radius:25px;font-weight:bold;cursor:pointer}
.mic-btn{background:#4CAF50!important}
.mic-btn.recording{background:#F44336!important;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.form-input{width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;margin-bottom:10px;background:var(--input-bg);color:var(--text)}
textarea.form-input{font-family:inherit;resize:vertical}
.btn{width:100%;padding:13px;background:var(--primary);color:white;border:none;border-radius:8px;font-size:15px;font-weight:bold;cursor:pointer;margin-bottom:10px}
.btn-sm{padding:6px 10px;background:var(--primary);color:white;border:none;border-radius:6px;font-size:12px;font-weight:bold;cursor:pointer;margin-right:5px;margin-bottom:4px}
.btn-sm.gray{background:#666}.btn-sm.green{background:#4CAF50}.btn-sm.red{background:#F44336}.btn-sm.blue{background:#2196F3}.btn-sm.whatsapp{background:#25D366}
.card{background:var(--card);padding:14px;border-radius:12px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.card h3{color:var(--primary);margin-bottom:8px;font-size:15px}
.card p{margin:4px 0;font-size:13px;line-height:1.4;color:var(--text)}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;color:white;margin-left:6px}
.badge.high,.badge.critical,.badge.warn{background:#F44336}
.badge.medium{background:#FF9800}
.badge.low,.badge.ok,.badge.completed,.badge.paid{background:#4CAF50}
.badge.new{background:#666}.badge.inprogress{background:#FF9800}
.badge.unpaid,.badge.outstanding{background:#F44336}
.badge.partial{background:#FF9800}
.list-item{padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.list-item:last-child{border-bottom:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.grid-item{background:var(--card);padding:14px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08);cursor:pointer}
.grid-item .icon{font-size:26px;margin-bottom:6px}
.grid-item .label{font-size:11px;font-weight:bold}
.img-preview{width:100%;border-radius:12px;margin-bottom:12px}
.thumb-row{display:flex;gap:8px;overflow-x:auto;margin-top:8px;padding-bottom:4px}
.thumb{width:80px;height:80px;object-fit:cover;border-radius:8px;border:1px solid var(--border)}
.thumb-wrap{position:relative}
.thumb-del{position:absolute;top:-6px;right:-6px;background:#F44336;color:white;border:none;border-radius:50%;width:20px;height:20px;font-size:11px;cursor:pointer;line-height:1}
.swatch{height:80px;border-radius:12px;border:1px solid var(--border);margin-bottom:12px}
.status-online{background:#E8F5E9;color:#2E7D32;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.status-offline{background:#FFEBEE;color:#C62828;padding:8px 12px;border-radius:8px;display:inline-block;font-size:13px}
.loading{text-align:center;padding:20px;color:var(--text2)}
.torque-table{width:100%;border-collapse:collapse;background:var(--card);border-radius:8px;overflow:hidden;font-size:12px;margin-bottom:12px}
.torque-table th{background:var(--primary);color:white;padding:8px 6px;text-align:left}
.torque-table td{padding:8px 6px;border-bottom:1px solid var(--border);color:var(--text)}
.stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.stat-card{background:var(--card);padding:14px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.stat-card .num{font-size:22px;font-weight:bold;color:var(--primary)}
.stat-card .lbl{font-size:11px;color:var(--text2);margin-top:4px}
.stat-card.green .num{color:#4CAF50}.stat-card.red .num{color:#F44336}.stat-card.blue .num{color:#2196F3}
canvas{max-height:220px}
.checklist-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;display:flex;align-items:center;gap:8px}
.checklist-item input{width:18px;height:18px}
@media print{.header,.tabs,.no-print,button,.btn,.btn-sm{display:none!important}.panel{display:block!important;padding:0}.panel:not(.active){display:none!important}body{background:white;color:black}.card{box-shadow:none;border:1px solid #ccc;page-break-inside:avoid}}
</style>
</head>
<body>

<div class="header">
<h1><span class="logo" id="logoDisplay">🔧</span> <span id="wsNameDisplay">RAMSTECH</span></h1>
<p id="wsSubtitle">v9.0 — Complete Workshop Platform</p>
<div class="top-btns">
<select class="lang-sel" id="langSel" onchange="setLang()">
<option value="en">EN</option><option value="af">AF</option><option value="zu">ZU</option>
</select>
<button onclick="toggleTheme()" id="themeBtn">🌙</button>
</div>
</div>

<div class="tabs no-print">
<div class="tab active" onclick="showTab('home',this)">🏠</div>
<div class="tab" onclick="showTab('dashboard',this)">📊</div>
<div class="tab" onclick="showTab('chat',this)">🤖</div>
<div class="tab" onclick="showTab('codes',this)">📟</div>
<div class="tab" onclick="showTab('problems',this)">📖</div>
<div class="tab" onclick="showTab('vin',this)">🔍</div>
<div class="tab" onclick="showTab('paint',this)">🎨</div>
<div class="tab" onclick="showTab('photo',this)">📸</div>
<div class="tab" onclick="showTab('jobs',this)">📋</div>
<div class="tab" onclick="showTab('customers',this)">👥</div>
<div class="tab" onclick="showTab('appointments',this)">📅</div>
<div class="tab" onclick="showTab('quotes',this)">💬</div>
<div class="tab" onclick="showTab('invoices',this)">💰</div>
<div class="tab" onclick="showTab('parts',this)">🔩</div>
<div class="tab" onclick="showTab('inventory',this)">📦</div>
<div class="tab" onclick="showTab('purchase',this)">🛒</div>
<div class="tab" onclick="showTab('staff',this)">👷</div>
<div class="tab" onclick="showTab('clockin',this)">🕐</div>
<div class="tab" onclick="showTab('expenses',this)">💸</div>
<div class="tab" onclick="showTab('fuel',this)">⛽</div>
<div class="tab" onclick="showTab('warranty',this)">🎁</div>
<div class="tab" onclick="showTab('reminders',this)">🗓️</div>
<div class="tab" onclick="showTab('wiring',this)">🔌</div>
<div class="tab" onclick="showTab('obd',this)">⚡</div>
<div class="tab" onclick="showTab('bulbs',this)">💡</div>
<div class="tab" onclick="showTab('batteries',this)">🔋</div>
<div class="tab" onclick="showTab('tyres',this)">🛞</div>
<div class="tab" onclick="showTab('fuses',this)">🔌</div>
<div class="tab" onclick="showTab('service',this)">⏰</div>
<div class="tab" onclick="showTab('inspect',this)">✅</div>
<div class="tab" onclick="showTab('boltcalc',this)">🔧</div>
<div class="tab" onclick="showTab('torque',this)">⚙️</div>
<div class="tab" onclick="showTab('history',this)">🚗</div>
<div class="tab" onclick="showTab('analytics',this)">📈</div>
<div class="tab" onclick="showTab('tax',this)">🧾</div>
<div class="tab" onclick="showTab('settings',this)">⚙</div>
</div>

<div id="home" class="panel active">
<div class="card"><div id="status">Checking...</div></div>
<div class="grid" id="homeGrid"></div>
</div>

<div id="dashboard" class="panel">
<h3 style="margin-bottom:12px;color:var(--primary)">📊 Dashboard</h3>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠ Low Stock</h3><div id="dashLowStock"></div></div>
<div class="card"><h3>🎁 Warranty Expiring</h3><div id="dashWarranty"></div></div>
</div>

<div id="chat" class="panel">
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! Ask about repairs, diagnostics, tools.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendMsg()">
<button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
<button onclick="sendMsg()">Send</button>
</div>
</div>

<div id="codes" class="panel">
<input type="text" class="form-input" id="codeSearch" placeholder="Search code..." oninput="searchCodes()">
<div id="codeResults"><div class="loading">Loading...</div></div>
</div>

<div id="problems" class="panel">
<input type="text" class="form-input" id="problemSearch" placeholder="Search problems..." oninput="filterProblems()">
<div id="problemList"><div class="loading">Loading...</div></div>
</div>

<div id="vin" class="panel">
<input type="text" class="form-input" id="vinInput" placeholder="Enter 17-char VIN" maxlength="17" style="text-transform:uppercase">
<button class="btn" onclick="decodeVin()">Decode VIN</button>
<div id="vinResult"></div>
</div>

<div id="paint" class="panel">
<div class="card"><p style="font-size:13px">Take photo of panel. AI identifies colour.</p></div>
<input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info">
<input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)">
<div id="paintPreview"></div>
<button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint</button>
<div id="paintResult"></div>
</div>

<div id="photo" class="panel">
<div class="card"><p style="font-size:13px">Take photo of issue. AI diagnoses.</p></div>
<input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info">
<input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)">
<div id="photoPreview"></div>
<button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze</button>
<div id="photoResult"></div>
</div>

<div id="jobs" class="panel">
<button class="btn no-print" onclick="showJobForm()">+ New Job</button>
<button class="btn no-print" style="background:#2196F3" onclick="exportJobsCSV()">📥 CSV</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jobCustomer" placeholder="Customer">
<input class="form-input" id="jobPhone" placeholder="Phone">
<input class="form-input" id="jobVehicle" placeholder="Vehicle">
<input class="form-input" id="jobVehicleReg" placeholder="Registration">
<input class="form-input" id="jobKm" type="number" placeholder="Odometer (km)">
<textarea class="form-input" id="jobComplaint" placeholder="Complaint" rows="2"></textarea>
<select class="form-input" id="jobAssigned"><option value="">— Unassigned —</option></select>
<input class="form-input" id="jobWarranty" type="number" placeholder="Warranty months" value="6">
<label style="font-size:12px;font-weight:bold">📸 Photos</label>
<input type="file" id="jobPhotos" accept="image/*" multiple capture="environment" class="form-input" onchange="addJobPhotos(event)">
<div class="thumb-row" id="jobPhotoThumbs"></div>
<label style="font-size:12px;font-weight:bold;margin-top:8px;display:block">✍️ Signature</label>
<button class="btn" style="background:#4CAF50" onclick="openSignature()">✍️ Capture Signature</button>
<div id="sigPreview" style="margin-bottom:10px"></div>
<button class="btn" style="margin-top:10px" onclick="createJob()">Create Job</button>
<button class="btn" style="background:#666" onclick="hideJobForm()">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<div id="customers" class="panel">
<button class="btn no-print" onclick="showCustomerForm()">+ New Customer</button>
<button class="btn no-print" style="background:#2196F3" onclick="exportCustomersCSV()">📥 CSV</button>
<div id="customerForm" style="display:none">
<div class="card">
<input class="form-input" id="custName" placeholder="Name">
<input class="form-input" id="custPhone" placeholder="Phone">
<input class="form-input" id="custEmail" placeholder="Email">
<input class="form-input" id="custAddress" placeholder="Address">
<button class="btn" onclick="createCustomer()">Save</button>
<button class="btn" style="background:#666" onclick="hideCustomerForm()">Cancel</button>
</div>
</div>
<div id="customerList"><div class="loading">Loading...</div></div>
</div>

<div id="appointments" class="panel">
<button class="btn no-print" onclick="showApptForm()">+ New Appointment</button>
<div id="apptForm" style="display:none">
<div class="card">
<input class="form-input" id="apptCustomer" placeholder="Customer">
<input class="form-input" id="apptPhone" placeholder="Phone">
<input class="form-input" id="apptVehicle" placeholder="Vehicle">
<input class="form-input" id="apptService" placeholder="Service">
<input class="form-input" id="apptDate" type="date">
<input class="form-input" id="apptTime" type="time">
<button class="btn" onclick="createAppt()">Book</button>
<button class="btn" style="background:#666" onclick="hideApptForm()">Cancel</button>
</div>
</div>
<div id="apptList"><div class="loading">Loading...</div></div>
</div>

<div id="quotes" class="panel">
<button class="btn no-print" onclick="showQuoteForm()">+ New Quote</button>
<div id="quoteForm" style="display:none">
<div class="card">
<input class="form-input" id="qCustomer" placeholder="Customer">
<input class="form-input" id="qVehicle" placeholder="Vehicle">
<textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea>
<input class="form-input" id="qLabour" type="number" placeholder="Labour (R)" value="0">
<input class="form-input" id="qParts" type="number" placeholder="Parts (R)" value="0">
<button class="btn" onclick="createQuote()">Save Quote</button>
<button class="btn" style="background:#666" onclick="hideQuoteForm()">Cancel</button>
</div>
</div>
<div id="quoteList"><div class="loading">Loading...</div></div>
</div>

<div id="invoices" class="panel">
<button class="btn no-print" onclick="showInvoiceForm()">+ New Invoice</button>
<div id="invoiceForm" style="display:none">
<div class="card">
<input class="form-input" id="invCustomer" placeholder="Customer">
<input class="form-input" id="invVehicle" placeholder="Vehicle">
<input class="form-input" id="invDesc" placeholder="Description">
<input class="form-input" id="invLabour" type="number" placeholder="Labour (R)">
<input class="form-input" id="invParts" type="number" placeholder="Parts (R)">
<button class="btn" onclick="createInvoice()">Generate</button>
<button class="btn" style="background:#666" onclick="hideInvoiceForm()">Cancel</button>
</div>
</div>
<div id="invoiceList"><div class="loading">Loading...</div></div>
</div>

<div id="parts" class="panel">
<input type="text" class="form-input" id="partsSearch" placeholder="Search parts..." oninput="filterParts()">
<div id="partsList"><div class="loading">Loading...</div></div>
</div>

<div id="inventory" class="panel">
<button class="btn no-print" onclick="showInvForm()">+ Add Item</button>
<div id="invForm" style="display:none">
<div class="card">
<input class="form-input" id="invPartNum" placeholder="Part number">
<input class="form-input" id="invPartName" placeholder="Name">
<input class="form-input" id="invCategory" placeholder="Category">
<input class="form-input" id="invQty" type="number" placeholder="Qty">
<input class="form-input" id="invMinQty" type="number" placeholder="Min qty">
<input class="form-input" id="invCostPrice" type="number" placeholder="Cost R">
<input class="form-input" id="invSellPrice" type="number" placeholder="Sell R">
<input class="form-input" id="invSupplier" placeholder="Supplier">
<button class="btn" onclick="addInventory()">Save</button>
<button class="btn" style="background:#666" onclick="hideInvForm()">Cancel</button>
</div>
</div>
<div id="inventoryList"><div class="loading">Loading...</div></div>
</div>

<div id="purchase" class="panel">
<button class="btn no-print" onclick="showPOForm()">+ New PO</button>
<div id="poForm" style="display:none">
<div class="card">
<input class="form-input" id="poSupplier" placeholder="Supplier">
<textarea class="form-input" id="poItems" placeholder="Items (one per line)" rows="3"></textarea>
<input class="form-input" id="poTotal" type="number" placeholder="Total R">
<button class="btn" onclick="createPO()">Save PO</button>
<button class="btn" style="background:#666" onclick="hidePOForm()">Cancel</button>
</div>
</div>
<div id="poList"><div class="loading">Loading...</div></div>
</div>

<div id="staff" class="panel">
<button class="btn no-print" onclick="showStaffForm()">+ Add Staff</button>
<div id="staffForm" style="display:none">
<div class="card">
<input class="form-input" id="staffName" placeholder="Name">
<input class="form-input" id="staffRole" placeholder="Role">
<input class="form-input" id="staffPhone" placeholder="Phone">
<input class="form-input" id="staffEmail" placeholder="Email">
<input class="form-input" id="staffRate" type="number" placeholder="Hourly rate R" value="150">
<button class="btn" onclick="addStaff()">Save</button>
<button class="btn" style="background:#666" onclick="hideStaffForm()">Cancel</button>
</div>
</div>
<div id="staffList"><div class="loading">Loading...</div></div>
</div>

<div id="clockin" class="panel">
<h3 style="margin-bottom:12px;color:var(--primary)">🕐 Clock In/Out</h3>
<div id="clockinList"><div class="loading">Loading...</div></div>
</div>

<div id="expenses" class="panel">
<button class="btn no-print" onclick="showExpenseForm()">+ Add Expense</button>
<div id="expenseForm" style="display:none">
<div class="card">
<select class="form-input" id="expCat">
<option>Rent</option><option>Utilities</option><option>Tools</option>
<option>Parts</option><option>Salaries</option><option>Fuel</option><option>Other</option>
</select>
<input class="form-input" id="expAmount" type="number" placeholder="Amount R">
<input class="form-input" id="expDate" type="date">
<textarea class="form-input" id="expNote" placeholder="Note" rows="2"></textarea>
<button class="btn" onclick="addExpense()">Save</button>
<button class="btn" style="background:#666" onclick="hideExpenseForm()">Cancel</button>
</div>
</div>
<div id="expenseList"><div class="loading">Loading...</div></div>
</div>

<div id="fuel" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">⛽ Fuel Log</h3>
<button class="btn no-print" onclick="showFuelForm()">+ Add Fill-Up</button>
<div id="fuelForm" style="display:none">
<div class="card">
<input class="form-input" id="fuelVehicle" placeholder="Vehicle">
<input class="form-input" id="fuelKm" type="number" placeholder="Odometer (km)">
<input class="form-input" id="fuelLitres" type="number" step="0.01" placeholder="Litres">
<input class="form-input" id="fuelCost" type="number" step="0.01" placeholder="Cost R">
<input class="form-input" id="fuelStation" placeholder="Station (optional)">
<input class="form-input" id="fuelDate" type="date">
<button class="btn" onclick="addFuel()">Save</button>
<button class="btn" style="background:#666" onclick="hideFuelForm()">Cancel</button>
</div>
</div>
<div id="fuelList"><div class="loading">Loading...</div></div>
</div>

<div id="warranty" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🎁 Warranty Tracker</h3>
<p style="font-size:12px;color:var(--text2);margin-bottom:12px">Active warranties on completed jobs</p>
<div id="warrantyList"><div class="loading">Loading...</div></div>
</div>

<div id="reminders" class="panel">
<h3 style="margin-bottom:12px;color:var(--primary)">🗓️ Service Reminders</h3>
<div id="remindersList"><div class="loading">Loading...</div></div>
</div>

<div id="wiring" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🔌 Wiring Library</h3>
<input type="text" class="form-input" id="wiringSearch" placeholder="Search circuits..." oninput="filterWiring()">
<div id="wiringList"><div class="loading">Loading...</div></div>
</div>

<div id="obd" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">⚡ OBD-II PIDs</h3>
<input type="text" class="form-input" id="obdSearch" placeholder="Search PIDs..." oninput="filterOBD()">
<div id="obdList"><div class="loading">Loading...</div></div>
</div>

<div id="bulbs" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">💡 Bulb Chart</h3>
<input type="text" class="form-input" id="bulbSearch" placeholder="Search vehicle..." oninput="filterBulbs()">
<div id="bulbList"><div class="loading">Loading...</div></div>
</div>

<div id="batteries" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🔋 Battery Sizes</h3>
<input type="text" class="form-input" id="battSearch" placeholder="Search vehicle..." oninput="filterBatt()">
<div id="battList"><div class="loading">Loading...</div></div>
</div>

<div id="tyres" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🛞 Tyre Sizes</h3>
<input type="text" class="form-input" id="tyreSearch" placeholder="Search vehicle..." oninput="filterTyre()">
<div id="tyreList"><div class="loading">Loading...</div></div>
</div>

<div id="fuses" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🔌 Fuse Boxes</h3>
<div id="fuseList"><div class="loading">Loading...</div></div>
</div>

<div id="service" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">⏰ Service Calculator</h3>
<div class="card">
<input class="form-input" id="svcKm" type="number" placeholder="Current odometer (km)">
<select class="form-input" id="svcType">
<option value="petrol">Petrol</option>
<option value="diesel">Diesel</option>
<option value="truck_diesel">Truck Diesel</option>
<option value="motorcycle">Motorcycle</option>
</select>
<button class="btn" onclick="calcService()">Calculate Next Service</button>
<div id="svcResult"></div>
</div>
</div>

<div id="inspect" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">✅ Inspection Checklists</h3>
<select class="form-input" id="inspectType" onchange="loadChecklist()">
<option value="pre_purchase">Pre-Purchase Inspection</option>
<option value="roadworthy">Roadworthy Checklist</option>
</select>
<div id="inspectList"><div class="loading">Select a checklist</div></div>
<button class="btn" onclick="printChecklist()">🖨 Print</button>
</div>

<div id="boltcalc" class="panel">
<div class="card">
<h3>🔧 Bolt Torque Calculator</h3>
<select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M18</option><option>M20</option></select>
<select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select>
<select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly</option></select>
<button class="btn" onclick="calcTorque()">Calculate</button>
<div id="boltResult"></div>
</div>
</div>

<div id="torque" class="panel">
<input type="text" class="form-input" id="torqueSearch" placeholder="Search..." oninput="filterTorque()">
<h3 style="margin-bottom:8px;font-size:14px">Bolt Torque</h3>
<div id="torqueTable"></div>
<h3 style="margin:16px 0 8px;font-size:14px">Sequences</h3>
<div id="torqueSeq"></div>
</div>

<div id="history" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🚗 Vehicle History</h3>
<input type="text" class="form-input" id="vehicleSearch" placeholder="Search reg or vehicle..." oninput="searchVehicleHistory()">
<div id="vehicleHistory"><div class="loading">Enter search term</div></div>
</div>

<div id="analytics" class="panel">
<h3 style="margin-bottom:12px;color:var(--primary)">📈 Analytics</h3>
<div id="analyticsContent"><div class="loading">Loading...</div></div>
</div>

<div id="tax" class="panel">
<h3 style="margin-bottom:8px;color:var(--primary)">🧾 Tax Report</h3>
<div class="card">
<input class="form-input" id="taxFrom" type="date">
<input class="form-input" id="taxTo" type="date">
<button class="btn" onclick="downloadTax()">📥 Download CSV</button>
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

<div id="settings" class="panel">
<div class="card">
<h3>🏢 Branding</h3>
<input class="form-input" id="wsLogo" placeholder="🔧" maxlength="4">
<input class="form-input" id="wsName" placeholder="Workshop name">
<input class="form-input" id="wsPhone" placeholder="Phone">
<input class="form-input" id="wsAddress" placeholder="Address">
<input class="form-input" id="wsEmail" placeholder="Email">
<input class="form-input" id="wsRate" type="number" placeholder="Labour rate R/hr">
<button class="btn" onclick="saveSettings()">Save</button>
</div>
</div>

<script>
// ═══════════════════════════════════
// TABS
// ═══════════════════════════════════
const TABS = ['home','dashboard','chat','codes','problems','vin','paint','photo','jobs','customers','appointments','quotes','invoices','parts','inventory','purchase','staff','clockin','expenses','fuel','warranty','reminders','wiring','obd','bulbs','batteries','tyres','fuses','service','inspect','boltcalc','torque','history','analytics','tax','settings'];
const HOME_ITEMS = [
['📊','Dashboard',1],['🤖','AI Chat',2],['📟','Codes',3],['📖','Problems',4],['🔍','VIN',5],['🎨','Paint',6],['📸','Photo Diag',7],
['📋','Jobs',8],['👥','Customers',9],['📅','Appointments',10],['💬','Quotes',11],['💰','Invoices',12],['🔩','Parts',13],
['📦','Inventory',14],['🛒','Purchase',15],['👷','Staff',16],['🕐','Clock In/Out',17],['💸','Expenses',18],
['⛽','Fuel Log',19],['🎁','Warranty',20],['🗓️','Reminders',21],
['🔌','Wiring',22],['⚡','OBD-II',23],['💡','Bulbs',24],['🔋','Batteries',25],['🛞','Tyres',26],['🔌','Fuses',27],
['⏰','Service Calc',28],['✅','Inspect',29],['🔧','Bolt Calc',30],['⚙️','Torque',31],['🚗','History',32],['📈','Analytics',33],['🧾','Tax',34],['⚙','Settings',35]
];
document.getElementById('homeGrid').innerHTML=HOME_ITEMS.map(x=>`<div class="grid-item" onclick="clickTab(${x[2]})"><div class="icon">${x[0]}</div><div class="label">${x[1]}</div></div>`).join('');

function showTab(name,el){
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(name).classList.add('active');
if(el)el.classList.add('active');
const loaders={codes:()=>!document.getElementById('codeResults').dataset.loaded&&searchCodes(),
problems:()=>!document.getElementById('problemList').dataset.loaded&&loadProblems(),
jobs:()=>{loadJobs();loadStaffDropdown();},
customers:loadCustomers,appointments:loadAppts,quotes:loadQuotes,invoices:loadInvoices,
parts:()=>!document.getElementById('partsList').dataset.loaded&&loadParts(),
inventory:loadInventory,purchase:loadPOs,staff:loadStaff,clockin:loadClockin,
expenses:loadExpenses,fuel:loadFuel,warranty:loadWarranty,
reminders:loadReminders,wiring:loadWiring,obd:loadOBD,
bulbs:loadBulbs,batteries:loadBatt,tyres:loadTyre,fuses:loadFuses,
inspect:()=>document.getElementById('inspectType').value==='pre_purchase'&&loadChecklist(),
boltcalc:()=>{},torque:loadTorque,history:()=>{},analytics:loadAnalytics,
tax:loadBizCard,settings:loadSettings,dashboard:loadDashboard};
if(loaders[name])try{loaders[name]()}catch(e){console.error(e)}
}
function clickTab(i){showTab(TABS[i],document.querySelectorAll('.tab')[i]);}

function toggleTheme(){document.body.classList.toggle('dark');const d=document.body.classList.contains('dark');localStorage.setItem('theme',d?'dark':'light');document.getElementById('themeBtn').textContent=d?'☀️':'🌙';}
if(localStorage.getItem('theme')==='dark'){document.body.classList.add('dark');document.getElementById('themeBtn').textContent='☀️';}

// ═══════════════════════════════════
// LANGUAGE
// ═══════════════════════════════════
let LANG=localStorage.getItem('lang')||'en';
let STRINGS={};
async function loadLang(){
try{const r=await fetch('/api/translations/'+LANG);const d=await r.json();
STRINGS=d.strings;document.getElementById('langSel').value=LANG;applyLang()}catch(e){}}
function setLang(){LANG=document.getElementById('langSel').value;localStorage.setItem('lang',LANG);loadLang()}
function t(k){return STRINGS[k]||k}
function applyLang(){
const tabKeys=['home','dashboard','chat','codes','problems','vin','paint','photo','jobs','customers',
'appointments','quotes','invoices','parts','inventory','purchase','staff','clockin',
'expenses','fuel','warranty','reminders','wiring','obd','bulbs','batteries','tyres','fuses',
'service','inspect','boltcalc','torque','history','analytics','tax','settings'];
const tabs=document.querySelectorAll('.tab');
tabKeys.forEach((k,i)=>{if(tabs[i]&&STRINGS[k])tabs[i].title=STRINGS[k]});
}
loadLang();

// ═══════════════════════════════════
// PHOTO COMPRESSION
// ═══════════════════════════════════
function compressImage(file,maxWidth,quality){
return new Promise((resolve)=>{
const reader=new FileReader();
reader.onload=(e)=>{
const img=new Image();
img.onload=()=>{
const canvas=document.createElement('canvas');
let{width,height}=img;
if(width>maxWidth){height=(height*maxWidth)/width;width=maxWidth}
canvas.width=width;canvas.height=height;
canvas.getContext('2d').drawImage(img,0,0,width,height);
resolve(canvas.toDataURL('image/jpeg',quality));
};
img.src=e.target.result;
};
reader.readAsDataURL(file);
});}

// ═══════════════════════════════════
// SIGNATURE
// ═══════════════════════════════════
let sigPad=null,sigCtx=null,sigDrawing=false,sigData='';
function openSignature(){
const modal=document.createElement('div');
modal.id='sigModal';
modal.style.cssText='position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px';
modal.innerHTML='<div style="background:white;border-radius:12px;padding:16px;width:100%;max-width:500px"><h3 style="color:#E65100;margin-bottom:8px">✍️ Customer Signature</h3><canvas id="sigPad" width="440" height="200" style="border:2px solid #ddd;border-radius:8px;width:100%;touch-action:none;background:white"></canvas><div style="margin-top:10px;display:flex;gap:8px"><button class="btn-sm gray" onclick="clearSig()" style="flex:1">Clear</button><button class="btn-sm green" onclick="saveSig()" style="flex:1">Confirm</button><button class="btn-sm red" onclick="closeSig()" style="flex:1">Cancel</button></div></div>';
document.body.appendChild(modal);
sigPad=document.getElementById('sigPad');
sigCtx=sigPad.getContext('2d');
sigCtx.strokeStyle='#000';sigCtx.lineWidth=2;sigCtx.lineCap='round';
const start=(e)=>{sigDrawing=true;sigCtx.beginPath();const p=getPos(e);sigCtx.moveTo(p.x,p.y);e.preventDefault()};
const draw=(e)=>{if(!sigDrawing)return;const p=getPos(e);sigCtx.lineTo(p.x,p.y);sigCtx.stroke();e.preventDefault()};
const stop=()=>{sigDrawing=false};
const getPos=(e)=>{
const rect=sigPad.getBoundingClientRect();
const x=(e.touches?e.touches[0].clientX:e.clientX)-rect.left;
const y=(e.touches?e.touches[0].clientY:e.clientY)-rect.top;
return{x:x*(sigPad.width/rect.width),y:y*(sigPad.height/rect.height)};
};
sigPad.addEventListener('mousedown',start);
sigPad.addEventListener('mousemove',draw);
sigPad.addEventListener('mouseup',stop);
sigPad.addEventListener('touchstart',start,{passive:false});
sigPad.addEventListener('touchmove',draw,{passive:false});
sigPad.addEventListener('touchend',stop);
}
function clearSig(){sigCtx.clearRect(0,0,sigPad.width,sigPad.height)}
function saveSig(){sigData=sigPad.toDataURL('image/png');document.getElementById('sigPreview').innerHTML='<img src="'+sigData+'" style="width:100%;border:1px solid #ddd;border-radius:8px;background:white">';closeSig()}
function closeSig(){const m=document.getElementById('sigModal');if(m)m.remove()}

// ═══════════════════════════════════
// HELPERS
// ═══════════════════════════════════
async function checkStatus(){try{await fetch('/health');document.getElementById('status').innerHTML='<span class="status-online">✓ Online</span>'}catch(e){document.getElementById('status').innerHTML='<span class="status-offline">✗ Offline</span>'}}
checkStatus();
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
async function jget(u){const r=await fetch(u);return r.json()}
async function jpost(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json()}
async function jput(u,b){const r=await fetch(u,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json()}
async function jdel(u){const r=await fetch(u,{method:'DELETE'});return r.json()}

// VOICE
let rec=null,isRec=false;
function toggleMic(){if(!('webkitSpeechRecognition'in window)&&!('SpeechRecognition'in window)){alert('Voice not supported');return}if(!rec){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;rec=new SR();rec.lang='en-ZA';rec.onresult=e=>{document.getElementById('chatInput').value=e.results[0][0].transcript;resetMic();sendMsg()};rec.onerror=resetMic;rec.onend=resetMic}
function resetMic(){isRec=false;document.getElementById('micBtn').classList.remove('recording');document.getElementById('micBtn').textContent='🎤'}
if(isRec){rec.stop();resetMic()}else{try{rec.start();isRec=true;document.getElementById('micBtn').classList.add('recording');document.getElementById('micBtn').textContent='⏹'}catch(e){alert(e.message)}}}

// CHAT
async function sendMsg(){const i=document.getElementById('chatInput');const m=i.value.trim();if(!m)return;const b=document.getElementById('chatBox');b.innerHTML+='<div class="msg user">'+esc(m)+'</div>';i.value='';b.scrollTop=b.scrollHeight;b.innerHTML+='<div class="msg ai" id="typ">...</div>';b.scrollTop=b.scrollHeight;try{const d=await jpost('/api/chat',{message:m});document.getElementById('typ').outerHTML='<div class="msg ai">'+esc(d.reply)+'</div>'}catch(e){document.getElementById('typ').outerHTML='<div class="msg ai">Error</div>'}b.scrollTop=b.scrollHeight}

// DASHBOARD
let rC=null,jC=null;
async function loadDashboard(){try{const d=await jget('/api/stats');document.getElementById('dashStats').innerHTML='<div class="stats-row"><div class="stat-card blue"><div class="num">'+d.jobs_total+'</div><div class="lbl">Jobs</div></div><div class="stat-card"><div class="num">'+d.jobs_open+'</div><div class="lbl">Open</div></div><div class="stat-card green"><div class="num">'+d.jobs_completed+'</div><div class="lbl">Done</div></div><div class="stat-card"><div class="num">'+d.customers+'</div><div class="lbl">Customers</div></div><div class="stat-card green"><div class="num">R'+d.revenue+'</div><div class="lbl">Revenue</div></div><div class="stat-card red"><div class="num">R'+d.expenses+'</div><div class="lbl">Expenses</div></div></div>';
if(rC)rC.destroy();const c1=document.getElementById('revenueChart');if(c1)rC=new Chart(c1,{type:'line',data:{labels:d.revenue_labels,datasets:[{data:d.revenue_data,borderColor:'#E65100',backgroundColor:'rgba(230,81,0,.15)',tension:.3,fill:true}]},options:{responsive:true,plugins:{legend:{display:false}}}});
if(jC)jC.destroy();const c2=document.getElementById('jobChart');if(c2)jC=new Chart(c2,{type:'doughnut',data:{labels:['New','Progress','Done'],datasets:[{data:[d.jobs_new,d.jobs_progress,d.jobs_completed],backgroundColor:['#666','#FF9800','#4CAF50']}]},options:{responsive:true}});
const ls=await jget('/api/inventory/low-stock');document.getElementById('dashLowStock').innerHTML=ls.items.length?ls.items.map(i=>'<div class="list-item"><strong>'+esc(i.name)+'</strong> — '+i.qty+' left</div>').join(''):'<p style="color:var(--text2)">All OK</p>';
const w=await jget('/api/warranty');const soon=w.warranties.filter(x=>x.status==='active').slice(0,5);document.getElementById('dashWarranty').innerHTML=soon.length?soon.map(x=>'<div class="list-item">'+esc(x.vehicle)+' — '+x.days_left+' days left</div>').join(''):'<p style="color:var(--text2)">None</p>';
}catch(e){}}

// CODES
async function searchCodes(){const q=document.getElementById('codeSearch').value;const c=document.getElementById('codeResults');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/fault-codes?search='+encodeURIComponent(q));c.dataset.loaded='1';c.innerHTML=d.codes.length?d.codes.map(x=>'<div class="card"><h3>'+x.code+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p><strong>'+esc(x.description)+'</strong></p><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p><strong>Steps:</strong></p>'+x.steps.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>'}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}}

// PROBLEMS
let probData=[];
async function loadProblems(){const d=await jget('/api/problems');probData=d.problems;document.getElementById('problemList').dataset.loaded='1';filterProblems()}
function filterProblems(){const q=(document.getElementById('problemSearch').value||'').toLowerCase();const f=probData.filter(x=>!q||x.title.toLowerCase().includes(q)||x.system.toLowerCase().includes(q));document.getElementById('problemList').innerHTML=f.length?f.map(x=>'<div class="card"><h3>'+esc(x.title)+'<span class="badge '+x.severity.toLowerCase()+'">'+x.severity+'</span></h3><p style="color:var(--text2);font-size:12px">'+esc(x.system)+'</p><p><strong>Causes:</strong></p>'+x.causes.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'<p><strong>Checks:</strong></p>'+x.checks.map(y=>'<div class="list-item">• '+esc(y)+'</div>').join('')+'</div>').join(''):'<div class="card"><p>No matches</p></div>'}

// VIN
async function decodeVin(){const vin=document.getElementById('vinInput').value.trim().toUpperCase();const c=document.getElementById('vinResult');if(vin.length!==17){c.innerHTML='<div class="card"><p style="color:red">VIN must be 17 chars</p></div>';return}c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/vin/'+vin);if(d.detail){c.innerHTML='<div class="card"><p style="color:red">'+d.detail+'</p></div>';return}c.innerHTML='<div class="card"><h3>🔍 Info</h3><p><strong>VIN:</strong> '+d.vin+'</p><p><strong>Manufacturer:</strong> '+d.manufacturer+'</p><p><strong>Country:</strong> '+d.country+'</p><p><strong>Year:</strong> '+d.year+'</p></div>'}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}}

// PAINT
let paintB64='';
async function previewPaint(e){const f=e.target.files[0];if(!f)return;paintB64=await compressImage(f,1200,0.75);document.getElementById('paintPreview').innerHTML='<img class="img-preview" src="'+paintB64+'">'}
async function matchPaint(){const btn=document.getElementById('paintBtn');const c=document.getElementById('paintResult');if(!paintB64){c.innerHTML='<div class="card"><p style="color:red">Select image</p></div>';return}btn.disabled=true;btn.textContent='Analyzing...';c.innerHTML='<div class="loading">Analyzing...</div>';try{const d=await jpost('/api/paint/match',{image_base64:paintB64,vehicle_info:document.getElementById('paintVehicle').value});if(!d.success){c.innerHTML='<div class="card"><p style="color:red">'+(d.error||'Failed')+'</p></div>'}else{const col=d.detected_colour;let h='<div class="card"><div class="swatch" style="background:'+col.hex_code+'"></div><h3>'+esc(col.name)+'</h3><p><strong>'+esc(col.finish)+'</strong> • '+esc(col.colour_family)+'</p><p style="font-family:monospace">'+col.hex_code+'</p><p>Confidence: <strong>'+d.confidence+'</strong></p></div>';if(d.brand_codes){h+='<div class="card"><h3>Brand Codes</h3>';d.brand_codes.forEach(b=>{h+='<div class="list-item"><strong>'+esc(b.brand)+':</strong> '+esc(b.code)+' — '+esc(b.name)+'</div>'});h+='</div>'}c.innerHTML=h}}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}btn.disabled=false;btn.textContent='🎨 Match Paint'}

// PHOTO DIAG
let diagB64='';
async function previewDiag(e){const f=e.target.files[0];if(!f)return;diagB64=await compressImage(f,1200,0.75);document.getElementById('photoPreview').innerHTML='<img class="img-preview" src="'+diagB64+'">'}
async function diagnosePhoto(){const btn=document.getElementById('photoBtn');const c=document.getElementById('photoResult');if(!diagB64){c.innerHTML='<div class="card"><p style="color:red">Select image</p></div>';return}btn.disabled=true;btn.textContent='Analyzing...';c.innerHTML='<div class="loading">...</div>';try{const d=await jpost('/api/diagnose/photo',{image_base64:diagB64,vehicle_info:document.getElementById('photoVehicle').value});if(!d.success){c.innerHTML='<div class="card"><p style="color:red">'+(d.error||'Failed')+'</p></div>'}else{let h='<div class="card"><h3>🔍 '+esc(d.problem||'Detected')+'</h3><p><strong>Confidence:</strong> '+d.confidence+'</p><p>'+esc(d.description||'')+'</p></div>';if(d.possible_causes){h+='<div class="card"><h3>Causes</h3>'+d.possible_causes.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>'}if(d.diagnostic_steps){h+='<div class="card"><h3>Steps</h3>'+d.diagnostic_steps.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>'}if(d.safety_warnings){h+='<div class="card" style="background:#FFEBEE"><h3 style="color:#C62828">⚠ Safety</h3>'+d.safety_warnings.map(x=>'<div class="list-item">⚠ '+esc(x)+'</div>').join('')+'</div>'}c.innerHTML=h}}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}btn.disabled=false;btn.textContent='📸 Analyze'}

// JOBS
let jobPhotos=[];
async function addJobPhotos(e){for(const f of Array.from(e.target.files)){jobPhotos.push(await compressImage(f,1000,0.7))}renderJobThumbs()}
function renderJobThumbs(){document.getElementById('jobPhotoThumbs').innerHTML=jobPhotos.map((p,i)=>'<div class="thumb-wrap"><img class="thumb" src="'+p+'"><button class="thumb-del" onclick="removeJobPhoto('+i+')">×</button></div>').join('')}
function removeJobPhoto(i){jobPhotos.splice(i,1);renderJobThumbs()}
function showJobForm(){document.getElementById('jobForm').style.display='block'}
function hideJobForm(){document.getElementById('jobForm').style.display='none';jobPhotos=[];renderJobThumbs();sigData='';document.getElementById('sigPreview').innerHTML=''}
async function loadStaffDropdown(){try{const d=await jget('/api/staff');const sel=document.getElementById('jobAssigned');sel.innerHTML='<option value="">— Unassigned —</option>'+d.staff.map(s=>'<option value="'+esc(s.name)+'">'+esc(s.name)+'</option>').join('')}catch(e){}}
async function createJob(){const c=document.getElementById('jobCustomer').value.trim();const v=document.getElementById('jobVehicle').value.trim();const comp=document.getElementById('jobComplaint').value.trim();if(!c||!v||!comp){alert('Fill required fields');return}try{await jpost('/api/jobs',{customer:c,phone:document.getElementById('jobPhone').value,vehicle:v,registration:document.getElementById('jobVehicleReg').value,km:parseInt(document.getElementById('jobKm').value)||0,complaint:comp,assigned_to:document.getElementById('jobAssigned').value,warranty_months:parseInt(document.getElementById('jobWarranty').value)||6,photos:jobPhotos,signature:sigData});['jobCustomer','jobPhone','jobVehicle','jobComplaint','jobVehicleReg','jobKm'].forEach(id=>document.getElementById(id).value='');sigData='';document.getElementById('sigPreview').innerHTML='';hideJobForm();loadJobs()}catch(e){alert(e.message)}}
async function loadJobs(){const c=document.getElementById('jobList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/jobs');if(!d.jobs.length){c.innerHTML='<div class="card"><p>No jobs</p></div>';return}c.innerHTML=d.jobs.reverse().map(j=>{const s=j.status.toLowerCase().replace(' ','');let ph=j.photos&&j.photos.length?'<div class="thumb-row">'+j.photos.map(p=>'<img class="thumb" src="'+p+'">').join('')+'</div>':'';let cost=j.total?'<div style="margin-top:8px;padding:8px;background:var(--bg);border-radius:6px;font-size:12px"><strong>Total: R'+j.total.toFixed(2)+'</strong></div>':'';let as=j.assigned_to?'<p style="color:var(--text2);font-size:12px">👷 '+esc(j.assigned_to)+'</p>':'';let sig=j.signature?'<div style="margin-top:8px"><strong style="font-size:12px">Customer signature:</strong><br><img src="'+j.signature+'" style="width:200px;border:1px solid #ddd;background:white;border-radius:6px;margin-top:4px"></div>':'';return '<div class="card" id="job-'+j.id+'"><h3>Job #'+j.id+' <span class="badge '+s+'">'+esc(j.status)+'</span></h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+(j.registration?' ('+esc(j.registration)+')':'')+'</p>'+as+'<p style="color:var(--text2)">'+esc(j.complaint)+'</p>'+ph+cost+sig+'<p style="font-size:11px;color:var(--text2);margin-top:6px">'+esc(j.created)+'</p><div class="no-print" style="margin-top:8px"><button class="btn-sm" onclick="upJob(\''+j.id+'\',\'In Progress\')">Progress</button><button class="btn-sm green" onclick="upJob(\''+j.id+'\',\'Completed\')">Done</button><button class="btn-sm" onclick="setCost(\''+j.id+'\')">💰 Cost</button><button class="btn-sm whatsapp" onclick="waJob(\''+j.id+'\')">📱</button><button class="btn-sm blue" onclick="printJob(\''+j.id+'\')">🖨</button></div></div>'}).join('')}catch(e){c.innerHTML='<div class="card"><p>Error</p></div>'}}
async function upJob(id,s){await jput('/api/jobs/'+id,{status:s,note:'Status → '+s});loadJobs()}
async function setCost(id){const h=prompt('Labour hours:','1');if(h===null)return;const p=prompt('Parts cost (R):','0');if(p===null)return;const rate=await getRate();await jpost('/api/jobs/'+id+'/cost',{labour_hours:parseFloat(h),labour_rate:rate,parts_cost:parseFloat(p)});loadJobs()}
async function getRate(){try{const r=await jget('/api/workshop');return r.labour_rate||450}catch(e){return 450}}
function waJob(id){jget('/api/jobs').then(d=>{const j=d.jobs.find(x=>x.id==id);if(!j)return;const txt='🔧 *Job #'+j.id+'*\n'+j.customer+'\n'+j.vehicle+'\n'+(j.registration?'Reg: '+j.registration+'\n':'')+'Issue: '+j.complaint+'\nStatus: '+j.status+(j.total?'\nTotal: R'+j.total.toFixed(2):'');window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank')})}
function printJob(id){const el=document.getElementById('job-'+id);const w=window.open('','','width=800,height=600');w.document.write('<html><head><title>Job #'+id+'</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}img{max-width:200px;margin:4px}</style></head><body><h1>'+document.getElementById('logoDisplay').textContent+' '+document.getElementById('wsNameDisplay').textContent+' — Job #'+id+'</h1>');w.document.write(el.innerHTML.replace(/<div class="no-print".*?<\/div>/gs,''));w.document.write('</body></html>');w.document.close();setTimeout(()=>w.print(),500)}

// CUSTOMERS
function showCustomerForm(){document.getElementById('customerForm').style.display='block'}
function hideCustomerForm(){document.getElementById('customerForm').style.display='none'}
async function createCustomer(){const n=document.getElementById('custName').value.trim();const p=document.getElementById('custPhone').value.trim();if(!n||!p){alert('Name+phone required');return}await jpost('/api/customers',{name:n,phone:p,email:document.getElementById('custEmail').value,address:document.getElementById('custAddress').value});['custName','custPhone','custEmail','custAddress'].forEach(id=>document.getElementById(id).value='');hideCustomerForm();loadCustomers()}
async function loadCustomers(){const c=document.getElementById('customerList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/customers');c.innerHTML=d.customers.length?d.customers.reverse().map(x=>'<div class="card"><h3>👤 '+esc(x.name)+'</h3><p>📞 '+esc(x.phone)+'</p>'+(x.email?'<p>📧 '+esc(x.email)+'</p>':'')+'<button class="btn-sm whatsapp" onclick="waCust(\''+esc(x.phone)+'\')">📱</button></div>').join(''):'<div class="card"><p>No customers</p></div>'}catch(e){}}
function waCust(p){window.open('https://wa.me/'+p.replace(/\D/g,''),'_blank')}

// APPOINTMENTS
function showApptForm(){document.getElementById('apptForm').style.display='block'}
function hideApptForm(){document.getElementById('apptForm').style.display='none'}
async function createAppt(){const c=document.getElementById('apptCustomer').value.trim();const d=document.getElementById('apptDate').value;const t=document.getElementById('apptTime').value;if(!c||!d||!t){alert('Required');return}await jpost('/api/appointments',{customer:c,phone:document.getElementById('apptPhone').value,vehicle:document.getElementById('apptVehicle').value,service:document.getElementById('apptService').value,date:d,time:t});['apptCustomer','apptPhone','apptVehicle','apptService','apptDate','apptTime'].forEach(id=>document.getElementById(id).value='');hideApptForm();loadAppts()}
async function loadAppts(){const c=document.getElementById('apptList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/appointments');const s=d.appointments.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));c.innerHTML=s.length?s.map(a=>'<div class="card"><h3>📅 '+esc(a.date)+' '+esc(a.time)+'</h3><p><strong>'+esc(a.customer)+'</strong></p>'+(a.vehicle?'<p>🚗 '+esc(a.vehicle)+'</p>':'')+'<button class="btn-sm red" onclick="delAppt(\''+a.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>None</p></div>'}catch(e){}}
async function delAppt(id){if(!confirm('Delete?'))return;await jdel('/api/appointments/'+id);loadAppts()}

// QUOTES
function showQuoteForm(){document.getElementById('quoteForm').style.display='block'}
function hideQuoteForm(){document.getElementById('quoteForm').style.display='none'}
async function createQuote(){const c=document.getElementById('qCustomer').value.trim();const d=document.getElementById('qDesc').value.trim();if(!c||!d){alert('Required');return}await jpost('/api/quotes',{customer:c,vehicle:document.getElementById('qVehicle').value,description:d,labour:parseFloat(document.getElementById('qLabour').value)||0,parts:parseFloat(document.getElementById('qParts').value)||0});['qCustomer','qVehicle','qDesc','qLabour','qParts'].forEach(id=>document.getElementById(id).value='');hideQuoteForm();loadQuotes()}
async function loadQuotes(){const c=document.getElementById('quoteList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/quotes');c.innerHTML=d.quotes.length?d.quotes.reverse().map(q=>'<div class="card"><h3>💬 Quote #'+q.id+'</h3><p><strong>'+esc(q.customer)+'</strong></p><p>'+esc(q.description)+'</p><div class="list-item">Labour: R'+q.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+q.parts.toFixed(2)+'</div><div class="list-item"><strong>Total: R'+q.total.toFixed(2)+'</strong></div><div style="margin-top:8px"><button class="btn-sm green" onclick="acceptQuote(\''+q.id+'\')">Accept → Invoice</button><button class="btn-sm red" onclick="delQuote(\''+q.id+'\')">Delete</button></div></div>').join(''):'<div class="card"><p>No quotes</p></div>'}catch(e){}}
async function acceptQuote(id){const r=await jpost('/api/quotes/'+id+'/accept',{});if(r.success){alert('Converted to invoice');loadQuotes()}}
async function delQuote(id){if(!confirm('Delete?'))return;await jdel('/api/quotes/'+id);loadQuotes()}

// INVOICES
function showInvoiceForm(){document.getElementById('invoiceForm').style.display='block'}
function hideInvoiceForm(){document.getElementById('invoiceForm').style.display='none'}
async function createInvoice(){const c=document.getElementById('invCustomer').value.trim();const d=document.getElementById('invDesc').value.trim();if(!c||!d){alert('Required');return}await jpost('/api/invoices',{customer:c,vehicle:document.getElementById('invVehicle').value,description:d,labour:parseFloat(document.getElementById('invLabour').value)||0,parts:parseFloat(document.getElementById('invParts').value)||0});['invCustomer','invVehicle','invDesc','invLabour','invParts'].forEach(id=>document.getElementById(id).value='');hideInvoiceForm();loadInvoices()}
async function loadInvoices(){const c=document.getElementById('invoiceList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/invoices');c.innerHTML=d.invoices.length?d.invoices.reverse().map(i=>{const s=i.paid?'paid':(i.amount_paid>0?'partial':'outstanding');return '<div class="card" id="inv-'+i.id+'"><h3>Invoice #'+i.id+' <span class="badge '+s+'">'+s.toUpperCase()+'</span></h3><p><strong>'+esc(i.customer)+'</strong></p><p>'+esc(i.description)+'</p><div class="list-item">Labour: R'+i.labour.toFixed(2)+'</div><div class="list-item">Parts: R'+i.parts.toFixed(2)+'</div><div class="list-item"><strong>TOTAL: R'+i.total.toFixed(2)+'</strong></div><div class="list-item">Paid: R'+(i.amount_paid||0).toFixed(2)+' | Balance: R'+(i.total-(i.amount_paid||0)).toFixed(2)+'</div><div class="no-print" style="margin-top:8px"><button class="btn-sm green" onclick="recordPay(\''+i.id+'\')">💰 Payment</button><button class="btn-sm whatsapp" onclick="waInv(\''+i.id+'\')">📱</button><button class="btn-sm blue" onclick="printInv(\''+i.id+'\')">🖨</button></div></div>'}).join(''):'<div class="card"><p>No invoices</p></div>'}catch(e){}}
async function recordPay(id){const a=prompt('Amount received (R):');if(!a)return;await jpost('/api/invoices/'+id+'/pay',{amount:parseFloat(a)});loadInvoices()}
function waInv(id){jget('/api/invoices').then(d=>{const i=d.invoices.find(x=>x.id==id);const txt='🔧 *'+document.getElementById('wsNameDisplay').textContent+'*\nInvoice #'+i.id+'\n'+i.customer+'\n'+i.description+'\nTotal: R'+i.total.toFixed(2);window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank')})}
function printInv(id){const el=document.getElementById('inv-'+id);const w=window.open('','','width=800,height=600');w.document.write('<html><head><title>Invoice #'+id+'</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}</style></head><body><h1>'+document.getElementById('logoDisplay').textContent+' '+document.getElementById('wsNameDisplay').textContent+' — Invoice #'+id+'</h1>');w.document.write(el.innerHTML.replace(/<div class="no-print".*?<\/div>/gs,''));w.document.write('</body></html>');w.document.close();setTimeout(()=>w.print(),500)}

// PARTS
let partsData=[];
async function loadParts(){const d=await jget('/api/parts');partsData=d.parts;document.getElementById('partsList').dataset.loaded='1';filterParts()}
function filterParts(){const q=(document.getElementById('partsSearch').value||'').toLowerCase();const f=partsData.filter(x=>!q||x.name.toLowerCase().includes(q)||x.number.toLowerCase().includes(q)||x.brand.toLowerCase().includes(q));document.getElementById('partsList').innerHTML=f.map(p=>'<div class="card"><h3>'+esc(p.name)+'</h3><p style="font-family:monospace;font-size:12px">'+esc(p.number)+'</p><p>'+esc(p.brand)+' | '+esc(p.category)+'</p><p style="font-size:16px;color:var(--primary)"><strong>R'+p.price+'</strong></p></div>').join('')||'<div class="card"><p>None</p></div>'}

// INVENTORY
function showInvForm(){document.getElementById('invForm').style.display='block'}
function hideInvForm(){document.getElementById('invForm').style.display='none'}
async function addInventory(){const n=document.getElementById('invPartName').value.trim();if(!n){alert('Name required');return}await jpost('/api/inventory',{part_number:document.getElementById('invPartNum').value,name:n,category:document.getElementById('invCategory').value,qty:parseInt(document.getElementById('invQty').value)||0,min_qty:parseInt(document.getElementById('invMinQty').value)||5,cost_price:parseFloat(document.getElementById('invCostPrice').value)||0,sell_price:parseFloat(document.getElementById('invSellPrice').value)||0,supplier:document.getElementById('invSupplier').value});['invPartNum','invPartName','invCategory','invQty','invMinQty','invCostPrice','invSellPrice','invSupplier'].forEach(id=>document.getElementById(id).value='');hideInvForm();loadInventory()}
async function loadInventory(){const c=document.getElementById('inventoryList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/inventory');c.innerHTML=d.items.length?d.items.map(i=>{const cls=i.qty<=i.min_qty?'warn':'ok';return '<div class="card"><h3>'+esc(i.name)+' <span class="badge '+cls+'">'+i.qty+'</span></h3><p style="font-family:monospace;font-size:12px">'+esc(i.part_number||'-')+'</p><p>Cost R'+i.cost_price.toFixed(2)+' | Sell R'+i.sell_price.toFixed(2)+'</p><div style="margin-top:8px"><button class="btn-sm green" onclick="adjInv(\''+i.id+'\',1)">+1</button><button class="btn-sm red" onclick="adjInv(\''+i.id+'\',-1)">-1</button><button class="btn-sm red" onclick="delInv(\''+i.id+'\')">×</button></div></div>'}).join(''):'<div class="card"><p>No items</p></div>'}catch(e){}}
async function adjInv(id,d){await jpost('/api/inventory/'+id+'/adjust',{delta:d});loadInventory()}
async function delInv(id){if(!confirm('Delete?'))return;await jdel('/api/inventory/'+id);loadInventory()}

// PURCHASE ORDERS
function showPOForm(){document.getElementById('poForm').style.display='block'}
function hidePOForm(){document.getElementById('poForm').style.display='none'}
async function createPO(){const s=document.getElementById('poSupplier').value.trim();const i=document.getElementById('poItems').value.trim();if(!s||!i){alert('Required');return}await jpost('/api/purchase-orders',{supplier:s,items:i,total:parseFloat(document.getElementById('poTotal').value)||0});['poSupplier','poItems','poTotal'].forEach(id=>document.getElementById(id).value='');hidePOForm();loadPOs()}
async function loadPOs(){const c=document.getElementById('poList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/purchase-orders');c.innerHTML=d.pos.length?d.pos.reverse().map(p=>'<div class="card"><h3>PO #'+p.id+' <span class="badge '+(p.status==='received'?'ok':'new')+'">'+p.status+'</span></h3><p><strong>'+esc(p.supplier)+'</strong></p><p>'+esc(p.items)+'</p><p>Total: R'+p.total.toFixed(2)+'</p><div style="margin-top:8px"><button class="btn-sm green" onclick="markPO(\''+p.id+'\',\'received\')">Received</button><button class="btn-sm red" onclick="delPO(\''+p.id+'\')">×</button></div></div>').join(''):'<div class="card"><p>No POs</p></div>'}catch(e){}}
async function markPO(id,s){await jput('/api/purchase-orders/'+id,{status:s});loadPOs()}
async function delPO(id){if(!confirm('Delete?'))return;await jdel('/api/purchase-orders/'+id);loadPOs()}

// STAFF
function showStaffForm(){document.getElementById('staffForm').style.display='block'}
function hideStaffForm(){document.getElementById('staffForm').style.display='none'}
async function addStaff(){const n=document.getElementById('staffName').value.trim();if(!n){alert('Name required');return}await jpost('/api/staff',{name:n,role:document.getElementById('staffRole').value,phone:document.getElementById('staffPhone').value,email:document.getElementById('staffEmail').value,hourly_rate:parseFloat(document.getElementById('staffRate').value)||150});['staffName','staffRole','staffPhone','staffEmail'].forEach(id=>document.getElementById(id).value='');hideStaffForm();loadStaff()}
async function loadStaff(){const c=document.getElementById('staffList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/staff');c.innerHTML=d.staff.length?d.staff.map(s=>'<div class="card"><h3>👷 '+esc(s.name)+'</h3><p>'+esc(s.role||'-')+'</p>'+(s.phone?'<p>📞 '+esc(s.phone)+'</p>':'')+'<p>Rate: R'+s.hourly_rate.toFixed(2)+'/hr</p><button class="btn-sm red" onclick="delStaff(\''+s.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>No staff</p></div>'}catch(e){}}
async function delStaff(id){if(!confirm('Delete?'))return;await jdel('/api/staff/'+id);loadStaff()}

// CLOCKIN
async function loadClockin(){const c=document.getElementById('clockinList');c.innerHTML='<div class="loading">...</div>';try{const sd=await jget('/api/staff');const cd=await jget('/api/clockins');c.innerHTML=sd.staff.length?sd.staff.map(s=>{const active=cd.clockins.find(x=>x.staff_id===s.id&&!x.clock_out);return '<div class="card"><h3>👷 '+esc(s.name)+'</h3>'+(active?'<p style="color:#4CAF50">🕐 In since '+esc(active.clock_in)+'</p><button class="btn-sm red" onclick="clockOut(\''+s.id+'\')">Clock Out</button>':'<button class="btn-sm green" onclick="clockIn(\''+s.id+'\')">Clock In</button>')+'</div>'}).join(''):'<div class="card"><p>Add staff first</p></div>'}catch(e){}}
async function clockIn(id){await jpost('/api/clockins',{staff_id:id});loadClockin()}
async function clockOut(id){await jpost('/api/clockins/'+id+'/out',{});loadClockin()}

// EXPENSES
function showExpenseForm(){document.getElementById('expenseForm').style.display='block'}
function hideExpenseForm(){document.getElementById('expenseForm').style.display='none'}
async function addExpense(){const a=parseFloat(document.getElementById('expAmount').value)||0;if(!a){alert('Amount required');return}await jpost('/api/expenses',{category:document.getElementById('expCat').value,amount:a,date:document.getElementById('expDate').value||new Date().toISOString().slice(0,10),note:document.getElementById('expNote').value});['expAmount','expDate','expNote'].forEach(id=>document.getElementById(id).value='');hideExpenseForm();loadExpenses()}
async function loadExpenses(){const c=document.getElementById('expenseList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/expenses');const total=d.expenses.reduce((s,x)=>s+x.amount,0);c.innerHTML='<div class="card" style="background:var(--primary);color:white"><h3 style="color:white">Total</h3><p style="font-size:24px;color:white;font-weight:bold">R'+total.toFixed(2)+'</p></div>'+(d.expenses.length?d.expenses.reverse().map(e=>'<div class="card"><h3>'+esc(e.category)+' <span class="badge new">R'+e.amount.toFixed(2)+'</span></h3><p>'+esc(e.note||'-')+'</p><p style="font-size:11px;color:var(--text2)">'+esc(e.date)+'</p><button class="btn-sm red" onclick="delExp(\''+e.id+'\')">×</button></div>').join(''):'<div class="card"><p>No expenses</p></div>')}catch(e){}}
async function delExp(id){if(!confirm('Delete?'))return;await jdel('/api/expenses/'+id);loadExpenses()}

// FUEL
function showFuelForm(){document.getElementById('fuelForm').style.display='block'}
function hideFuelForm(){document.getElementById('fuelForm').style.display='none'}
async function addFuel(){const v=document.getElementById('fuelVehicle').value.trim();const km=parseInt(document.getElementById('fuelKm').value)||0;const l=parseFloat(document.getElementById('fuelLitres').value)||0;if(!v||!km||!l){alert('Vehicle, km and litres required');return}await jpost('/api/fuel',{vehicle:v,km:km,litres:l,cost:parseFloat(document.getElementById('fuelCost').value)||0,station:document.getElementById('fuelStation').value,date:document.getElementById('fuelDate').value||new Date().toISOString().slice(0,10)});['fuelVehicle','fuelKm','fuelLitres','fuelCost','fuelStation','fuelDate'].forEach(id=>document.getElementById(id).value='');hideFuelForm();loadFuel()}
async function loadFuel(){const c=document.getElementById('fuelList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/fuel');c.innerHTML=d.logs.length?d.logs.reverse().map(f=>'<div class="card"><h3>⛽ '+esc(f.vehicle)+'</h3><div class="list-item">Odometer: <strong>'+f.km+' km</strong></div><div class="list-item">Litres: <strong>'+f.litres+' L</strong></div><div class="list-item">Cost: <strong>R'+f.cost.toFixed(2)+'</strong></div>'+(f.consumption>0?'<div class="list-item">Consumption: <strong>'+f.consumption+' L/100km</strong></div>':'')+(f.station?'<div class="list-item">Station: '+esc(f.station)+'</div>':'')+'<p style="font-size:11px;color:var(--text2)">'+esc(f.date)+'</p><button class="btn-sm red" onclick="delFuel(\''+f.id+'\')">Delete</button></div>').join(''):'<div class="card"><p>No fuel logs</p></div>'}catch(e){}}
async function delFuel(id){if(!confirm('Delete?'))return;await jdel('/api/fuel/'+id);loadFuel()}

// WARRANTY
async function loadWarranty(){const c=document.getElementById('warrantyList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/warranty');c.innerHTML=d.warranties.length?d.warranties.map(w=>{const cls=w.status==='active'?'ok':'warn';return '<div class="card"><h3>🎁 '+esc(w.vehicle)+' <span class="badge '+cls+'">'+w.status.toUpperCase()+'</span></h3><p><strong>'+esc(w.customer)+'</strong></p>'+(w.phone?'<p>📞 '+esc(w.phone)+'</p>':'')+'<div class="list-item">Job: #'+w.id+' on '+esc(w.job_date)+'</div><div class="list-item">Warranty: '+w.months+' months</div><div class="list-item">Expires: <strong>'+esc(w.expiry)+'</strong></div><div class="list-item">'+(w.days_left>0?'Expires in '+w.days_left+' days':'Expired '+Math.abs(w.days_left)+' days ago')+'</div></div>'}).join(''):'<div class="card"><p>No warranties</p></div>'}catch(e){}}

// REMINDERS
async function loadReminders(){const c=document.getElementById('remindersList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/reminders');c.innerHTML=d.reminders.length?d.reminders.map(r=>'<div class="card"><h3>🗓️ '+esc(r.vehicle)+'</h3><p>'+esc(r.customer)+'</p><p>Due: <strong>'+esc(r.due)+'</strong></p><p style="color:var(--text2);font-size:12px">Last: '+esc(r.last_service)+' ('+r.last_km+' km)</p><button class="btn-sm whatsapp" onclick="remindWA(\''+esc(r.phone||'')+'\',\''+esc(r.customer)+'\',\''+esc(r.vehicle)+'\')">📱 Remind</button></div>').join(''):'<div class="card"><p>No reminders due</p></div>'}catch(e){}}
function remindWA(phone,name,vehicle){const txt='Hi '+name+', your '+vehicle+' is due for service. Please book.';window.open(phone?'https://wa.me/'+phone.replace(/\D/g,'')+'?text='+encodeURIComponent(txt):'https://wa.me/?text='+encodeURIComponent(txt),'_blank')}

// WIRING
let wiringData=[];
async function loadWiring(){const d=await jget('/api/wiring');wiringData=d.circuits;filterWiring()}
function filterWiring(){const q=(document.getElementById('wiringSearch').value||'').toLowerCase();const f=wiringData.filter(x=>!q||x.name.toLowerCase().includes(q)||x.system.toLowerCase().includes(q));document.getElementById('wiringList').innerHTML=f.map(w=>'<div class="card"><h3>🔌 '+esc(w.name)+'</h3><p style="font-size:12px;color:var(--text2)">'+esc(w.system)+' — '+esc(w.description)+'</p><p><strong>Components:</strong></p>'+w.components.map(c=>'<div class="list-item">• '+esc(c)+'</div>').join('')+'<p><strong>Connections:</strong></p>'+w.connections.map(c=>'<div class="list-item" style="font-family:monospace;font-size:11px">'+esc(c)+'</div>').join('')+'</div>').join('')||'<div class="card"><p>None</p></div>'}

// OBD
let obdData=[];
async function loadOBD(){const d=await jget('/api/obd-pids');obdData=d.pids;filterOBD()}
function filterOBD(){const q=(document.getElementById('obdSearch').value||'').toLowerCase();const f=obdData.filter(x=>!q||x.name.toLowerCase().includes(q)||x.pid.includes(q));document.getElementById('obdList').innerHTML='<table class="torque-table"><tr><th>PID</th><th>Name</th><th>Desc</th></tr>'+f.map(x=>'<tr><td><strong>'+x.pid+'</strong></td><td>'+esc(x.name)+'</td><td style="font-size:11px">'+esc(x.desc)+'</td></tr>').join('')+'</table>'}

// BULBS
let bulbsData=[];
async function loadBulbs(){const d=await jget('/api/bulbs');bulbsData=d.bulbs;filterBulbs()}
function filterBulbs(){const q=(document.getElementById('bulbSearch').value||'').toLowerCase();const f=bulbsData.filter(x=>!q||x.vehicle.toLowerCase().includes(q));document.getElementById('bulbList').innerHTML=f.map(b=>'<div class="card"><h3>💡 '+esc(b.vehicle)+'</h3><div class="list-item">Low: <strong>'+esc(b.headlight_low)+'</strong></div><div class="list-item">High: <strong>'+esc(b.headlight_high)+'</strong></div><div class="list-item">Fog: <strong>'+esc(b.fog)+'</strong></div></div>').join('')||'<div class="card"><p>None</p></div>'}

// BATTERIES
let battData=[];
async function loadBatt(){const d=await jget('/api/batteries');battData=d.batteries;filterBatt()}
function filterBatt(){const q=(document.getElementById('battSearch').value||'').toLowerCase();const f=battData.filter(x=>!q||x.vehicle.toLowerCase().includes(q));document.getElementById('battList').innerHTML=f.map(b=>'<div class="card"><h3>🔋 '+esc(b.vehicle)+'</h3><div class="list-item">Group: <strong>'+esc(b.group)+'</strong></div><div class="list-item">CCA: <strong>'+b.cca+'</strong></div><div class="list-item">Ah: <strong>'+b.ah+'</strong></div></div>').join('')||'<div class="card"><p>None</p></div>'}

// TYRES
let tyreData=[];
async function loadTyre(){const d=await jget('/api/tyres');tyreData=d.tyres;filterTyre()}
function filterTyre(){const q=(document.getElementById('tyreSearch').value||'').toLowerCase();const f=tyreData.filter(x=>!q||x.vehicle.toLowerCase().includes(q));document.getElementById('tyreList').innerHTML=f.map(t=>'<div class="card"><h3>🛞 '+esc(t.vehicle)+'</h3><div class="list-item">Size: <strong>'+esc(t.size)+'</strong></div><div class="list-item">Front: <strong>'+esc(t.pressure_f)+'</strong></div><div class="list-item">Rear: <strong>'+esc(t.pressure_r)+'</strong></div></div>').join('')||'<div class="card"><p>None</p></div>'}

// FUSES
async function loadFuses(){const c=document.getElementById('fuseList');c.innerHTML='<div class="loading">...</div>';try{const d=await jget('/api/fuses');c.innerHTML=d.fuses.map(f=>'<div class="card"><h3>🔌 '+esc(f.vehicle)+'</h3><p style="font-size:12px;color:var(--text2)">'+esc(f.location)+'</p>'+f.common.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'</div>').join('')}catch(e){}}

// SERVICE CALC
async function calcService(){const km=parseInt(document.getElementById('svcKm').value)||0;const t=document.getElementById('svcType').value;if(!km){alert('Enter km');return}const d=await jpost('/api/service-calc',{current_km:km,vehicle_type:t});document.getElementById('svcResult').innerHTML='<div class="card" style="background:var(--primary);color:white"><h3 style="color:white">Next Service</h3><p style="font-size:24px;font-weight:bold;color:white">at '+d.next_service_km+' km</p><p style="color:white">or in '+d.months_interval+' months</p></div><div class="card"><h3>Items</h3>'+d.items.map(i=>'<div class="list-item">• '+esc(i)+'</div>').join('')+'</div>'}

// INSPECT
async function loadChecklist(){const t=document.getElementById('inspectType').value;const d=await jget('/api/checklists/'+t);document.getElementById('inspectList').innerHTML='<div class="card"><h3>'+esc(d.name)+'</h3>'+d.items.map((x,i)=>'<div class="checklist-item"><input type="checkbox" id="chk'+i+'"><label for="chk'+i+'">'+esc(x)+'</label></div>').join('')+'</div>'}
function printChecklist(){const w=window.open('','','width=800,height=600');w.document.write('<html><head><title>Checklist</title><style>body{font-family:Arial;padding:20px}h1{color:#E65100}div{padding:4px 0}</style></head><body><h1>'+document.getElementById('wsNameDisplay').textContent+'</h1>');w.document.write(document.getElementById('inspectList').innerHTML);w.document.write('</body></html>');w.document.close();setTimeout(()=>w.print(),500)}

// BOLT CALC
async function calcTorque(){const d=await jpost('/api/bolt-calc',{size:document.getElementById('boltSize').value,grade:document.getElementById('boltGrade').value,condition:document.getElementById('boltCondition').value});document.getElementById('boltResult').innerHTML='<div class="card" style="background:var(--primary);color:white"><h3 style="color:white">Recommended</h3><p style="font-size:30px;font-weight:bold;color:white">'+d.nm.toFixed(1)+' Nm</p><p style="color:white">'+d.ftlb.toFixed(1)+' ft·lb</p></div>'}

// TORQUE
let torqueData=[],seqData=[];
async function loadTorque(){if(!torqueData.length){const d=await jget('/api/torque');torqueData=d.bolts;seqData=d.sequences}filterTorque()}
function filterTorque(){const q=(document.getElementById('torqueSearch').value||'').toLowerCase();const f=torqueData.filter(x=>!q||x.size.toLowerCase().includes(q)||x.grade.toLowerCase().includes(q));document.getElementById('torqueTable').innerHTML='<table class="torque-table"><tr><th>Size</th><th>Grade</th><th>Nm</th><th>ft·lb</th><th>Use</th></tr>'+f.map(x=>'<tr><td><strong>'+esc(x.size)+'</strong></td><td>'+esc(x.grade)+'</td><td>'+x.nm+'</td><td>'+x.ftlb+'</td><td>'+esc(x.use)+'</td></tr>').join('')+'</table>';document.getElementById('torqueSeq').innerHTML=seqData.map(s=>'<div class="card"><h3>'+esc(s.component)+'</h3>'+s.steps.map(x=>'<div class="list-item">• '+esc(x)+'</div>').join('')+'<p style="font-size:12px;font-style:italic;margin-top:6px">'+esc(s.note)+'</p></div>').join('')}

// HISTORY
async function searchVehicleHistory(){const q=document.getElementById('vehicleSearch').value.trim().toLowerCase();const c=document.getElementById('vehicleHistory');if(!q){c.innerHTML='<div class="loading">Enter term</div>';return}const d=await jget('/api/jobs');const m=d.jobs.filter(j=>j.vehicle.toLowerCase().includes(q)||(j.registration||'').toLowerCase().includes(q));c.innerHTML=m.length?'<p style="margin-bottom:12px;color:var(--text2)">'+m.length+' record(s)</p>'+m.reverse().map(j=>'<div class="card"><h3>Job #'+j.id+'</h3><p><strong>'+esc(j.customer)+'</strong></p><p>🚗 '+esc(j.vehicle)+'</p><p>'+esc(j.complaint)+'</p><p><span class="badge '+j.status.toLowerCase().replace(' ','')+'">'+esc(j.status)+'</span></p></div>').join(''):'<div class="card"><p>No history</p></div>'}

// ANALYTICS
async function loadAnalytics(){const d=await jget('/api/analytics');let h='<div class="stats-row"><div class="stat-card blue"><div class="num">R'+d.avg_invoice.toFixed(0)+'</div><div class="lbl">Avg Invoice</div></div><div class="stat-card green"><div class="num">R'+d.total_revenue.toFixed(0)+'</div><div class="lbl">Revenue</div></div><div class="stat-card red"><div class="num">R'+d.total_expenses.toFixed(0)+'</div><div class="lbl">Expenses</div></div><div class="stat-card"><div class="num">R'+d.net_profit.toFixed(0)+'</div><div class="lbl">Net</div></div></div>';if(d.top_services.length)h+='<div class="card"><h3>🔥 Top Services</h3>'+d.top_services.map(s=>'<div class="list-item"><strong>'+esc(s.name)+'</strong> — '+s.count+'×</div>').join('')+'</div>';if(d.top_customers.length)h+='<div class="card"><h3>⭐ Top Customers</h3>'+d.top_customers.map(x=>'<div class="list-item"><strong>'+esc(x.name)+'</strong> — R'+x.total.toFixed(0)+'</div>').join('')+'</div>';document.getElementById('analyticsContent').innerHTML=h}

// TAX
async function loadBizCard(){const d=await jget('/api/workshop');document.getElementById('bcLogo').textContent=d.logo||'🔧';document.getElementById('bcName').textContent=d.name||'My Workshop';document.getElementById('bcPhone').textContent=d.phone||'';document.getElementById('bcAddress').textContent=d.address||''}
function downloadTax(){const f=document.getElementById('taxFrom').value;const t=document.getElementById('taxTo').value;window.location.href='/api/export/tax?from_date='+f+'&to_date='+t}
function printBizCard(){const w=window.open('','','width=600,height=400');w.document.write('<html><head><title>Biz Card</title></head><body style="padding:20px">'+document.getElementById('bizCard').outerHTML+'</body></html>');w.document.close();setTimeout(()=>w.print(),500)}

// SETTINGS
async function loadSettings(){const d=await jget('/api/workshop');document.getElementById('wsLogo').value=d.logo||'🔧';document.getElementById('wsName').value=d.name||'';document.getElementById('wsPhone').value=d.phone||'';document.getElementById('wsAddress').value=d.address||'';document.getElementById('wsEmail').value=d.email||'';document.getElementById('wsRate').value=d.labour_rate||450;applyBranding(d)}
function applyBranding(d){document.getElementById('logoDisplay').textContent=d.logo||'🔧';document.getElementById('wsNameDisplay').textContent=(d.name||'RAMSTECH').toUpperCase();const sub=[d.phone,d.address].filter(Boolean).join(' • ');document.getElementById('wsSubtitle').textContent=sub||'v9.0 — Complete Workshop Platform'}
async function saveSettings(){const p={logo:document.getElementById('wsLogo').value||'🔧',name:document.getElementById('wsName').value,phone:document.getElementById('wsPhone').value,address:document.getElementById('wsAddress').value,email:document.getElementById('wsEmail').value,labour_rate:parseFloat(document.getElementById('wsRate').value)||450};await jpost('/api/workshop',p);applyBranding(p);alert('Saved')}
loadSettings();

function exportJobsCSV(){window.location.href='/api/export/jobs'}
function exportCustomersCSV(){window.location.href='/api/export/customers'}
</script>
</body>
</html>"""
