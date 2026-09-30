P2 = r"""
<div id="home" class="panel active">
<div class="home-container">
<div class="hero-card">
<div id="status">Checking backend...</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px">
<button class="btn btn-success" onclick="loadDemo()" style="margin:0;font-size:13px;padding:12px">▶️ Load Demo</button>
<button class="btn btn-warn" onclick="clearDemo()" style="margin:0;font-size:13px;padding:12px">🗑️ Clear Demo</button>
</div>
</div>
<div id="categoryView"><div class="cat-title">Choose a Category</div><div class="cat-grid" id="categoryGrid"></div></div>
<div id="subView" style="display:none"><button class="back-btn" onclick="backToCategories()">← Back</button><div class="cat-title" id="subTitle"></div><div class="tile-grid" id="subGrid"></div></div>
</div>
</div>

<div id="dashboard" class="panel">
<div class="panel-title">📊 Dashboard</div>
<div id="dashStats"><div class="loading">Loading...</div></div>
<div class="card"><h3>💰 Revenue (7 days)</h3><canvas id="revenueChart"></canvas></div>
<div class="card"><h3>📋 Job Status</h3><canvas id="jobChart"></canvas></div>
<div class="card"><h3>⚠️ Low Stock</h3><div id="dashLowStock"></div></div>
<div class="card"><h3>🎁 Warranty Expiring</h3><div id="dashWarranty"></div></div>
</div>

<div id="chat" class="panel">
<div class="panel-title">🤖 AI Assistant</div>
<div class="chat-box" id="chatBox"><div class="msg ai">Hi! I'm RamsTech AI. Ask about repairs, diagnostics, or tools.</div></div>
<div class="input-row">
<input type="text" id="chatInput" placeholder="Ask about repairs..." onkeypress="if(event.key==='Enter')sendMsg()">
<button class="mic-btn" id="micBtn" onclick="toggleMic()">🎤</button>
<button onclick="sendMsg()">➤</button>
</div>
</div>

<div id="codes" class="panel"><div class="panel-title">📟 Fault Codes</div><input type="text" class="form-input" id="codeSearch" placeholder="🔍 Search code..." oninput="searchCodes()"><div id="codeResults"><div class="loading">Loading...</div></div></div>
<div id="problems" class="panel"><div class="panel-title">📖 Common Problems</div><input type="text" class="form-input" id="problemSearch" placeholder="🔍 Search..." oninput="filterProblems()"><div id="problemList"><div class="loading">Loading...</div></div></div>
<div id="vin" class="panel"><div class="panel-title">🔍 VIN Decoder</div><input type="text" class="form-input" id="vinInput" placeholder="Enter 17-char VIN" maxlength="17" style="text-transform:uppercase"><button class="btn" onclick="decodeVin()">Decode VIN</button><div id="vinResult"></div></div>

<div id="paint" class="panel"><div class="panel-title">🎨 Paint Match</div><div class="card"><p style="font-size:13px">📸 Take a photo of a vehicle panel.</p></div><input type="text" class="form-input" id="paintVehicle" placeholder="Vehicle info (optional)"><input type="file" id="paintImage" accept="image/*" capture="environment" class="form-input" onchange="previewPaint(event)"><div id="paintPreview"></div><button class="btn" id="paintBtn" onclick="matchPaint()">🎨 Match Paint Colour</button><div id="paintResult"></div></div>

<div id="photo" class="panel"><div class="panel-title">📸 Photo Diagnosis</div><div class="card"><p style="font-size:13px">📸 Take a photo of a mechanical issue.</p></div><input type="text" class="form-input" id="photoVehicle" placeholder="Vehicle info (optional)"><input type="file" id="photoImage" accept="image/*" capture="environment" class="form-input" onchange="previewDiag(event)"><div id="photoPreview"></div><button class="btn" id="photoBtn" onclick="diagnosePhoto()">📸 Analyze Photo</button><div id="photoResult"></div></div>

<div id="jobs" class="panel">
<div class="panel-title">📋 Job Cards</div>
<button class="btn no-print" onclick="showJobForm()">+ New Job Card</button>
<button class="btn btn-dark no-print" onclick="exportJobsCSV()">📥 Export CSV</button>
<div id="jobForm" style="display:none">
<div class="card">
<input class="form-input" id="jobCustomer" placeholder="Customer name">
<input class="form-input" id="jobPhone" placeholder="Phone">
<input class="form-input" id="jobVehicle" placeholder="Vehicle">
<input class="form-input" id="jobVehicleReg" placeholder="Registration">
<input class="form-input" id="jobKm" type="number" placeholder="Odometer (km)">
<textarea class="form-input" id="jobComplaint" placeholder="Complaint" rows="2"></textarea>
<select class="form-input" id="jobAssigned"><option value="">— Assign to staff —</option></select>
<input class="form-input" id="jobWarranty" type="number" placeholder="Warranty (months)" value="6">
<label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">📸 Photos</label>
<input type="file" id="jobPhotos" accept="image/*" multiple capture="environment" class="form-input" onchange="addJobPhotos(event)">
<div class="thumb-row" id="jobPhotoThumbs"></div>
<label style="font-size:13px;font-weight:700;margin-top:10px;display:block;margin-bottom:6px">✍️ Signature</label>
<button class="btn btn-success" onclick="openSignature()">✍️ Capture Signature</button>
<div id="sigPreview" style="margin-bottom:10px"></div>
<button class="btn btn-success" onclick="createJob()" style="margin-top:10px">✓ Create Job</button>
<button class="btn btn-dark" onclick="hideJobForm()">Cancel</button>
</div>
</div>
<div id="jobList"><div class="loading">Loading...</div></div>
</div>

<div id="customers" class="panel"><div class="panel-title">👥 Customers</div><button class="btn no-print" onclick="showCustomerForm()">+ New Customer</button><button class="btn btn-dark no-print" onclick="exportCustomersCSV()">📥 Export CSV</button><div id="customerForm" style="display:none"><div class="card"><input class="form-input" id="custName" placeholder="Full name"><input class="form-input" id="custPhone" placeholder="Phone"><input class="form-input" id="custEmail" placeholder="Email"><input class="form-input" id="custAddress" placeholder="Address"><button class="btn btn-success" onclick="createCustomer()">Save</button><button class="btn btn-dark" onclick="hideCustomerForm()">Cancel</button></div></div><div id="customerList"><div class="loading">Loading...</div></div></div>

<div id="appointments" class="panel"><div class="panel-title">📅 Appointments</div><button class="btn no-print" onclick="showApptForm()">+ New Appointment</button><div id="apptForm" style="display:none"><div class="card"><input class="form-input" id="apptCustomer" placeholder="Customer"><input class="form-input" id="apptPhone" placeholder="Phone"><input class="form-input" id="apptVehicle" placeholder="Vehicle"><input class="form-input" id="apptService" placeholder="Service"><input class="form-input" id="apptDate" type="date"><input class="form-input" id="apptTime" type="time"><button class="btn btn-success" onclick="createAppt()">Book</button><button class="btn btn-dark" onclick="hideApptForm()">Cancel</button></div></div><div id="apptList"><div class="loading">Loading...</div></div></div>

<div id="quotes" class="panel"><div class="panel-title">💬 Quotes</div><button class="btn no-print" onclick="showQuoteForm()">+ New Quote</button><div id="quoteForm" style="display:none"><div class="card"><input class="form-input" id="qCustomer" placeholder="Customer"><input class="form-input" id="qVehicle" placeholder="Vehicle"><textarea class="form-input" id="qDesc" placeholder="Work description" rows="2"></textarea><input class="form-input" id="qLabour" type="number" placeholder="Labour (R)" value="0"><input class="form-input" id="qParts" type="number" placeholder="Parts (R)" value="0"><button class="btn btn-success" onclick="createQuote()">Save</button><button class="btn btn-dark" onclick="hideQuoteForm()">Cancel</button></div></div><div id="quoteList"><div class="loading">Loading...</div></div></div>

<div id="invoices" class="panel"><div class="panel-title">💰 Invoices</div><button class="btn no-print" onclick="showInvoiceForm()">+ New Invoice</button><div id="invoiceForm" style="display:none"><div class="card"><input class="form-input" id="invCustomer" placeholder="Customer"><input class="form-input" id="invVehicle" placeholder="Vehicle"><input class="form-input" id="invDesc" placeholder="Description"><input class="form-input" id="invLabour" type="number" placeholder="Labour (R)"><input class="form-input" id="invParts" type="number" placeholder="Parts (R)"><button class="btn btn-success" onclick="createInvoice()">Generate</button><button class="btn btn-dark" onclick="hideInvoiceForm()">Cancel</button></div></div><div id="invoiceList"><div class="loading">Loading...</div></div></div>

<div id="parts" class="panel"><div class="panel-title">🔩 Parts Catalog</div><input type="text" class="form-input" id="partsSearch" placeholder="🔍 Search parts..." oninput="filterParts()"><div id="partsList"><div class="loading">Loading...</div></div></div>

<div id="inventory" class="panel"><div class="panel-title">📦 Inventory</div><button class="btn no-print" onclick="showInvForm()">+ Add Item</button><div id="invForm" style="display:none"><div class="card"><input class="form-input" id="invPartNum" placeholder="Part number"><input class="form-input" id="invPartName" placeholder="Name"><input class="form-input" id="invCategory" placeholder="Category"><input class="form-input" id="invQty" type="number" placeholder="Qty"><input class="form-input" id="invMinQty" type="number" placeholder="Min qty"><input class="form-input" id="invCostPrice" type="number" placeholder="Cost R"><input class="form-input" id="invSellPrice" type="number" placeholder="Sell R"><input class="form-input" id="invSupplier" placeholder="Supplier"><button class="btn btn-success" onclick="addInventory()">Save</button><button class="btn btn-dark" onclick="hideInvForm()">Cancel</button></div></div><div id="inventoryList"><div class="loading">Loading...</div></div></div>

<div id="purchase" class="panel"><div class="panel-title">🛒 Purchase Orders</div><button class="btn no-print" onclick="showPOForm()">+ New PO</button><div id="poForm" style="display:none"><div class="card"><input class="form-input" id="poSupplier" placeholder="Supplier"><textarea class="form-input" id="poItems" placeholder="Items" rows="3"></textarea><input class="form-input" id="poTotal" type="number" placeholder="Total R"><button class="btn btn-success" onclick="createPO()">Save</button><button class="btn btn-dark" onclick="hidePOForm()">Cancel</button></div></div><div id="poList"><div class="loading">Loading...</div></div></div>

<div id="staff" class="panel"><div class="panel-title">👷 Staff</div><button class="btn no-print" onclick="showStaffForm()">+ Add Staff</button><div id="staffForm" style="display:none"><div class="card"><input class="form-input" id="staffName" placeholder="Name"><input class="form-input" id="staffRole" placeholder="Role"><input class="form-input" id="staffPhone" placeholder="Phone"><input class="form-input" id="staffEmail" placeholder="Email"><input class="form-input" id="staffRate" type="number" placeholder="Hourly rate R" value="150"><button class="btn btn-success" onclick="addStaff()">Save</button><button class="btn btn-dark" onclick="hideStaffForm()">Cancel</button></div></div><div id="staffList"><div class="loading">Loading...</div></div></div>

<div id="clockin" class="panel"><div class="panel-title">🕐 Clock In/Out</div><div id="clockinList"><div class="loading">Loading...</div></div></div>

<div id="expenses" class="panel"><div class="panel-title">💸 Expenses</div><button class="btn no-print" onclick="showExpenseForm()">+ Add Expense</button><div id="expenseForm" style="display:none"><div class="card"><select class="form-input" id="expCat"><option>Rent</option><option>Utilities</option><option>Tools</option><option>Parts</option><option>Salaries</option><option>Fuel</option><option>Other</option></select><input class="form-input" id="expAmount" type="number" placeholder="Amount R"><input class="form-input" id="expDate" type="date"><textarea class="form-input" id="expNote" placeholder="Note" rows="2"></textarea><button class="btn btn-success" onclick="addExpense()">Save</button><button class="btn btn-dark" onclick="hideExpenseForm()">Cancel</button></div></div><div id="expenseList"><div class="loading">Loading...</div></div></div>

<div id="fuel" class="panel"><div class="panel-title">⛽ Fuel Log</div><button class="btn no-print" onclick="showFuelForm()">+ Add Fill-Up</button><div id="fuelForm" style="display:none"><div class="card"><input class="form-input" id="fuelVehicle" placeholder="Vehicle"><input class="form-input" id="fuelKm" type="number" placeholder="Odometer (km)"><input class="form-input" id="fuelLitres" type="number" step="0.01" placeholder="Litres"><input class="form-input" id="fuelCost" type="number" step="0.01" placeholder="Cost R"><input class="form-input" id="fuelStation" placeholder="Station"><input class="form-input" id="fuelDate" type="date"><button class="btn btn-success" onclick="addFuel()">Save</button><button class="btn btn-dark" onclick="hideFuelForm()">Cancel</button></div></div><div id="fuelList"><div class="loading">Loading...</div></div></div>

<div id="warranty" class="panel"><div class="panel-title">🎁 Warranty Tracker</div><p style="font-size:12px;color:var(--text2);margin-bottom:12px">Active warranties on completed jobs</p><div id="warrantyList"><div class="loading">Loading...</div></div></div>

<div id="reminders" class="panel"><div class="panel-title">🗓️ Service Reminders</div><div id="remindersList"><div class="loading">Loading...</div></div></div>

<div id="wiring" class="panel"><div class="panel-title">🔌 Wiring Library</div><input type="text" class="form-input" id="wiringSearch" placeholder="🔍 Search circuits..." oninput="filterWiring()"><div id="wiringList"><div class="loading">Loading...</div></div></div>

<div id="obd" class="panel"><div class="panel-title">⚡ OBD-II PIDs</div><input type="text" class="form-input" id="obdSearch" placeholder="🔍 Search PIDs..." oninput="filterOBD()"><div id="obdList"><div class="loading">Loading...</div></div></div>

<div id="bulbs" class="panel"><div class="panel-title">💡 Bulb Chart</div><input type="text" class="form-input" id="bulbSearch" placeholder="🔍 Search vehicle..." oninput="filterBulbs()"><div id="bulbList"><div class="loading">Loading...</div></div></div>

<div id="batteries" class="panel"><div class="panel-title">🔋 Battery Sizes</div><input type="text" class="form-input" id="battSearch" placeholder="🔍 Search vehicle..." oninput="filterBatt()"><div id="battList"><div class="loading">Loading...</div></div></div>

<div id="tyres" class="panel"><div class="panel-title">🛞 Tyre Sizes</div><input type="text" class="form-input" id="tyreSearch" placeholder="🔍 Search vehicle..." oninput="filterTyre()"><div id="tyreList"><div class="loading">Loading...</div></div></div>

<div id="fuses" class="panel"><div class="panel-title">🔌 Fuse Boxes</div><div id="fuseList"><div class="loading">Loading...</div></div></div>

<div id="service" class="panel"><div class="panel-title">⏰ Service Calculator</div><div class="card"><input class="form-input" id="svcKm" type="number" placeholder="Current odometer (km)"><select class="form-input" id="svcType"><option value="petrol">Petrol</option><option value="diesel">Diesel</option><option value="truck_diesel">Truck Diesel</option><option value="motorcycle">Motorcycle</option></select><button class="btn" onclick="calcService()">Calculate</button><div id="svcResult"></div></div></div>

<div id="inspect" class="panel"><div class="panel-title">✅ Inspection Checklists</div><select class="form-input" id="inspectType" onchange="loadChecklist()"><option value="pre_purchase">Pre-Purchase</option><option value="roadworthy">Roadworthy</option></select><div id="inspectList"><div class="loading">Select a checklist</div></div><button class="btn btn-dark" onclick="printChecklist()">🖨 Print</button></div>

<div id="boltcalc" class="panel"><div class="panel-title">🔧 Bolt Torque Calculator</div><div class="card"><label style="font-size:13px;font-weight:700">Bolt Size</label><select class="form-input" id="boltSize"><option>M6</option><option>M8</option><option selected>M10</option><option>M12</option><option>M14</option><option>M16</option><option>M18</option><option>M20</option></select><label style="font-size:13px;font-weight:700">Grade</label><select class="form-input" id="boltGrade"><option>8.8</option><option selected>10.9</option><option>12.9</option></select><label style="font-size:13px;font-weight:700">Condition</label><select class="form-input" id="boltCondition"><option value="dry">Dry</option><option value="oiled">Lightly oiled</option><option value="moly">Moly</option></select><button class="btn" onclick="calcTorque()">Calculate</button><div id="boltResult"></div></div></div>

<div id="torque" class="panel"><div class="panel-title">⚙️ Torque Specs</div><input type="text" class="form-input" id="torqueSearch" placeholder="🔍 Search..." oninput="filterTorque()"><h3 style="margin-bottom:8px;font-size:14px;color:var(--text2)">Bolt Torque</h3><div id="torqueTable"></div><h3 style="margin:16px 0 8px;font-size:14px;color:var(--text2)">Sequences</h3><div id="torqueSeq"></div></div>

<div id="history" class="panel"><div class="panel-title">🚗 Vehicle History</div><input type="text" class="form-input" id="vehicleSearch" placeholder="🔍 Search reg or vehicle..." oninput="searchVehicleHistory()"><div id="vehicleHistory"><div class="loading">Enter search term</div></div></div>

<div id="analytics" class="panel"><div class="panel-title">📈 Analytics</div><div id="analyticsContent"><div class="loading">Loading...</div></div></div>

<div id="tax" class="panel"><div class="panel-title">🧾 Tax & Reports</div><div class="card"><h3>Tax Report</h3><input class="form-input" id="taxFrom" type="date"><input class="form-input" id="taxTo" type="date"><button class="btn btn-dark" onclick="downloadTax()">📥 Download CSV</button></div><div class="card"><h3>Business Card</h3><div id="bizCard" style="padding:20px;background:white;color:black;border-radius:12px;border:2px solid #E65100;text-align:center"><div id="bcLogo" style="font-size:48px">🔧</div><h2 id="bcName" style="color:#E65100;margin:8px 0">My Workshop</h2><p id="bcPhone" style="font-size:14px">Phone</p><p id="bcAddress" style="font-size:12px;color:#666">Address</p></div><button class="btn" style="margin-top:12px" onclick="printBizCard()">🖨 Print Card</button></div></div>

<div id="settings" class="panel"><div class="panel-title">⚙️ Settings</div><div class="card"><h3>🏢 Branding</h3><input class="form-input" id="wsLogo" placeholder="🔧" maxlength="4"><input class="form-input" id="wsName" placeholder="Workshop name"><input class="form-input" id="wsPhone" placeholder="Phone"><input class="form-input" id="wsAddress" placeholder="Address"><input class="form-input" id="wsEmail" placeholder="Email"><input class="form-input" id="wsRate" type="number" placeholder="Labour rate R/hr"><button class="btn btn-success" onclick="saveSettings()">Save</button></div></div>

<div class="bottom-nav no-print">
<div class="bnav-item active" onclick="showTab('home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">Home</div></div>
<div class="bnav-item" onclick="showTab('dashboard',this)"><div class="bnav-icon">📊</div><div class="bnav-label">Dash</div></div>
<div class="bnav-item" onclick="showTab('chat',this)"><div class="bnav-icon">🤖</div><div class="bnav-label">AI</div></div>
<div class="bnav-item" onclick="showTab('jobs',this)"><div class="bnav-icon">📋</div><div class="bnav-label">Jobs</div></div>
<div class="bnav-item" onclick="showTab('settings',this)"><div class="bnav-icon">⚙️</div><div class="bnav-label">More</div></div>
</div>
"""
