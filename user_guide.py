"""Printable user guide + sell sheet, served as HTML at /guide and /sell."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/guide", response_class=HTMLResponse)
def user_guide():
    return HTMLResponse(content=_GUIDE_HTML)


@router.get("/sell", response_class=HTMLResponse)
def sell_sheet():
    return HTMLResponse(content=_SELL_HTML)


_GUIDE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RamsTech Workshop — User Guide</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
color:#1a1a2e;background:#f5f5f5;padding:20px;line-height:1.6;}
.page{max-width:210mm;margin:0 auto 30px;background:#fff;padding:20mm 18mm;
box-shadow:0 4px 16px rgba(0,0,0,.1);}
h1{font-size:26px;color:#E65100;margin-bottom:4px;line-height:1.2;}
h2{font-size:20px;color:#0B1F3A;margin-top:28px;margin-bottom:10px;
border-bottom:2px solid #E65100;padding-bottom:6px;}
h3{font-size:15px;color:#0B1F3A;margin-top:18px;margin-bottom:6px;}
h4{font-size:13px;color:#E65100;margin-top:14px;margin-bottom:4px;text-transform:uppercase;letter-spacing:.06em;}
p{font-size:13px;margin-bottom:8px;}
ul,ol{margin:6px 0 12px 22px;font-size:13px;}
li{margin-bottom:4px;}
.tag{display:inline-block;padding:3px 10px;background:#E65100;color:#fff;
font-size:11px;font-weight:700;border-radius:12px;letter-spacing:.05em;}
.box{background:#fff8f0;border-left:4px solid #E65100;padding:12px 14px;
margin:12px 0;font-size:13px;border-radius:0 6px 6px 0;}
.warn{background:#fef2f2;border-left-color:#ef4444;}
.tip{background:#f0fdf4;border-left-color:#10b981;}
.header{display:flex;justify-content:space-between;align-items:flex-start;
border-bottom:3px solid #E65100;padding-bottom:12px;margin-bottom:20px;}
.header .logo{font-size:48px;}
.meta{font-size:11px;color:#888;margin-top:6px;}
.toc{background:#f8fafc;border:1px solid #e2e8f0;padding:14px 18px;
border-radius:8px;margin:16px 0;}
.toc h3{margin-top:0;border:none;padding:0;}
.toc ol{margin-left:20px;font-size:12px;}
.toc li{margin-bottom:2px;}
kbd{background:#0B1F3A;color:#fff;padding:2px 7px;border-radius:4px;
font-family:monospace;font-size:11px;font-weight:700;}
@media print{
body{background:#fff;padding:0;}
.page{box-shadow:none;padding:15mm;max-width:100%;}
.page:not(:last-child){page-break-after:always;}
}
</style>
</head>
<body>

<div class="page">
  <div class="header">
    <div>
      <h1>RamsTech Workshop</h1>
      <div style="font-size:14px;color:#666;">Staff User Guide — v1.0</div>
      <div class="meta">Printed: <span id="d"></span></div>
    </div>
    <div class="logo">🔧</div>
  </div>

  <div class="toc">
    <h3>Contents</h3>
    <ol>
      <li>Getting Started (Install + Login)</li>
      <li>Daily Workflow — Owner / Manager</li>
      <li>Daily Workflow — Reception</li>
      <li>Daily Workflow — Technician</li>
      <li>Creating a Job (3 ways)</li>
      <li>The Job Lifecycle</li>
      <li>Parts, Stock, and Suppliers</li>
      <li>Invoices &amp; Money</li>
      <li>AI Assistant</li>
      <li>Reports &amp; Evidence</li>
      <li>Troubleshooting</li>
      <li>Quick Reference</li>
    </ol>
  </div>

  <h2>1. Getting Started</h2>

  <h3>Install the App</h3>
  <ol>
    <li>Open <strong>Chrome</strong> on your phone</li>
    <li>Go to <strong>ramstech.onrender.com</strong></li>
    <li>Tap the <strong>⋮</strong> menu (top-right) → <strong>Install app</strong></li>
    <li>Tap <strong>Install</strong></li>
    <li>An orange <strong>RT</strong> icon appears on your home screen</li>
  </ol>
  <p>From now on, tap the RT icon to open the app — it opens full-screen like a native app.</p>

  <h3>Login</h3>
  <ol>
    <li>Open the app → the lock screen appears</li>
    <li>Choose <strong>Owner / Manager</strong> or <strong>Technician</strong></li>
    <li>Enter your 4-digit PIN</li>
    <li>Tap <strong>Sign In</strong></li>
  </ol>
  <div class="box">
    <strong>Technicians:</strong> You only see your own jobs. Everything else is hidden.
    <br><strong>Owner:</strong> You see everything.
  </div>

  <h3>First-Time Setup (Owner only)</h3>
  <ol>
    <li>Go to <strong>More → Settings</strong></li>
    <li>Fill in your workshop name, phone, email, address</li>
    <li>Set your <strong>labour rate</strong> (default R450/hour)</li>
    <li>Tap <strong>Save Settings</strong></li>
    <li>Tap <strong>👥 Manage Staff &amp; PINs</strong></li>
    <li>Add each staff member with a unique 4-digit PIN</li>
  </ol>

  <h2>2. Daily Workflow — Owner / Manager</h2>

  <h4>Morning</h4>
  <ol>
    <li>Open app → sign in as Owner</li>
    <li>Check <strong>Dashboard</strong> (bottom nav) for today's jobs</li>
    <li>Tap <strong>Jobs</strong> → check <strong>Pending Quotes</strong> for anything needing approval</li>
    <li>Check <strong>Follow-ups</strong> (Operations) for warranty expiring or reminders due</li>
  </ol>

  <h4>Throughout the Day</h4>
  <ul>
    <li>Approve any customer quotes waiting on the owner signature</li>
    <li>Watch the <strong>Kanban board</strong> for jobs stuck in the same column</li>
    <li>Assign techs via ⚙ Workflow → <strong>Assign Technician</strong></li>
    <li>QC pass every completed job (PIN required) — the system then offers to WhatsApp the customer and generate the invoice</li>
  </ul>

  <h4>Evening</h4>
  <ol>
    <li>Review <strong>Dashboard</strong> — revenue today, jobs completed</li>
    <li>Record any expenses (Operations → Expenses)</li>
    <li>Check <strong>Money</strong> tab — send unpaid invoices via WhatsApp</li>
  </ol>

  <h2>3. Daily Workflow — Reception</h2>

  <h4>Customer Walks In</h4>
  <ol>
    <li>Tap <strong>Jobs</strong> → <strong>➕ New Job Card</strong></li>
    <li>Choose <strong>Photo</strong>, <strong>Voice</strong>, or <strong>Manual</strong>:
      <ul>
        <li><strong>Photo:</strong> Snap the VIN sticker, plate, or dashboard — AI fills everything</li>
        <li><strong>Voice:</strong> Describe the job out loud — AI writes it up</li>
        <li><strong>Manual:</strong> Type the details yourself</li>
      </ul>
    </li>
    <li>Confirm the details → <strong>Create Job Card</strong></li>
    <li>Assign a technician</li>
    <li>Hand the phone to the customer for signature (⚙ Workflow → Customer Signature)</li>
  </ol>

  <h4>Customer Calls</h4>
  <ul>
    <li>Tap <strong>Search</strong> (🔍 top-left) → type their name, phone, or registration</li>
    <li>Results show jobs, invoices, and history instantly</li>
    <li>Tap a job to see status — tell the customer exactly where they stand</li>
  </ul>

  <h4>Customer Collects</h4>
  <ol>
    <li>Manager confirms QC passed → green card appears</li>
    <li>Tap <strong>Generate Invoice</strong></li>
    <li>Tap <strong>WhatsApp Customer</strong> → message auto-sent "ready for pickup"</li>
    <li>When they pay, go to <strong>Money → Invoice → 💰 Payment</strong></li>
  </ol>

  <h2>4. Daily Workflow — Technician</h2>

  <h4>Start of Shift</h4>
  <ol>
    <li>Open app → tap <strong>Technician</strong> → enter your PIN</li>
    <li>You see only your assigned jobs</li>
    <li>Optionally clock in via <strong>Operations → Staff → Clock In</strong></li>
  </ol>

  <h4>On a Job</h4>
  <ol>
    <li>Tap the job card to open it</li>
    <li>Tap <strong>▶ Start Work</strong> → enter your PIN</li>
    <li>Work on the vehicle</li>
    <li>Update progress: tap <strong>25% / 50% / 75% / 100%</strong> as you go</li>
    <li>Take photos as evidence — tap <strong>📸</strong> on the job card</li>
    <li>When done: tap <strong>✓ Complete Work</strong> → PIN</li>
  </ol>
  <div class="box tip">
    <strong>Tip:</strong> Every action is timestamped with your name. This protects you if a customer ever questions the work.
  </div>

  <h4>If You Need Parts</h4>
  <ol>
    <li>Tap 🔍 (Parts Search) → type the part number</li>
    <li>If in stock: it shows quantity and price</li>
    <li>If not in stock: tap <strong>🔍 Search AutoZone / Goldwagen / Midas</strong> to see supplier prices</li>
    <li>Tell reception or manager to create a Purchase Order</li>
  </ol>

  <h4>When You Need Help</h4>
  <ol>
    <li>Open <strong>Diagnostics → Fault Codes</strong></li>
    <li>Type the OBD code (e.g. P0301) or scan the reader screen</li>
    <li>See ranked causes, tests, and repair steps</li>
    <li>Or tap 🤖 AI Assistant → describe the symptom</li>
  </ol>

  <h2>5. Creating a Job — 3 Ways</h2>

  <h3>📸 From Photo</h3>
  <ol>
    <li>Jobs → ➕ New Job Card → <strong>From Photo</strong></li>
    <li>Point at VIN sticker, plate, or dashboard</li>
    <li>AI extracts: VIN, reg, make, model, year, km</li>
    <li>Edit anything wrong → <strong>Create Job Card</strong></li>
  </ol>

  <h3>🎤 By Voice</h3>
  <ol>
    <li>Jobs → ➕ New Job Card → <strong>By Voice</strong></li>
    <li>Tap the big red mic button</li>
    <li>Speak: <em>"John Smith's Toyota Hilux, CA123456, needs a service, noise when braking"</em></li>
    <li>Tap again to stop → AI parses → confirm → Create</li>
  </ol>

  <h3>✍️ Manually</h3>
  <ol>
    <li>Jobs → ➕ New Job Card → <strong>Manually</strong></li>
    <li>Fill in customer, phone, vehicle, registration, complaint</li>
    <li>Save</li>
  </ol>

  <h2>6. The Job Lifecycle</h2>
  <p>A job moves through these stages automatically:</p>
  <ol>
    <li><strong>New</strong> — just created</li>
    <li><strong>Diagnosing</strong> — tech inspecting</li>
    <li><strong>Awaiting Approval</strong> — quote sent to customer</li>
    <li><strong>Awaiting Parts</strong> — waiting for delivery</li>
    <li><strong>In Progress</strong> — active work</li>
    <li><strong>QC</strong> — quality check</li>
    <li><strong>Ready for Pickup</strong> — customer notified</li>
    <li><strong>Completed</strong> — collected</li>
    <li><strong>Invoiced</strong> — payment expected</li>
  </ol>
  <p>View all jobs in this pipeline on the <strong>Kanban board</strong> (Jobs → Kanban View).</p>

  <h2>7. Parts, Stock, and Suppliers</h2>

  <h4>Search Parts</h4>
  <p>Reference → Parts → <strong>🔍 Search Parts</strong> → type part number or description</p>

  <h4>Scan Part Barcode</h4>
  <p>Reference → Parts → <strong>📷 Scan Part Barcode</strong> → point at barcode</p>

  <h4>Order from Supplier</h4>
  <ol>
    <li>Operations → Purchase → <strong>📦 New Purchase Order</strong></li>
    <li>Pick a supplier (add them once in the Suppliers tab)</li>
    <li>Add line items: part number, description, qty, unit price</li>
    <li>Save Draft → <strong>Mark Sent</strong> → <strong>Share</strong> via WhatsApp to supplier</li>
    <li>When delivered: <strong>Receive Into Stock</strong> → inventory updates automatically</li>
  </ol>

  <h4>Online Supplier Search</h4>
  <p>Purchase Orders → <strong>🔍 Online</strong> tab → type part number → tap AutoZone, Goldwagen, Midas, etc.</p>

  <h2>8. Invoices &amp; Money</h2>

  <h4>Generate Invoice</h4>
  <p>Automatic: when QC is passed, a green card appears → tap <strong>Generate Invoice</strong>.</p>

  <h4>Print Invoice</h4>
  <ul>
    <li>From job card: tap <strong>🖨 Invoice</strong></li>
    <li>From workflow panel: tap <strong>🖨 Print Invoice</strong></li>
    <li>From Money tab: tap the job → 🖨</li>
  </ul>
  <p>Invoice opens in a new tab → tap <strong>Print / Save PDF</strong>.</p>

  <h4>Record Payment</h4>
  <p>Money tab → tap the invoice → <strong>💰 Payment</strong> → enter amount.</p>

  <h2>9. AI Assistant</h2>

  <h4>Three ways to use it</h4>
  <ol>
    <li><strong>🔤 Code:</strong> Type an OBD code (P0301) → get description, causes, tests, repairs</li>
    <li><strong>🩺 Symptom:</strong> Describe what's wrong → AI suggests codes to check</li>
    <li><strong>💬 Ask:</strong> Free-form question, e.g. "how do I test a camshaft sensor?"</li>
  </ol>

  <h4>Photo Diagnosis</h4>
  <p>Diagnostics → Photo Diag → take photo of part/leak/damage → AI diagnoses</p>

  <h4>Voice Input</h4>
  <p>Inside AI panel, tap 🎤 → speak your question</p>

  <h2>10. Reports &amp; Evidence</h2>

  <h4>Audit Report (per job)</h4>
  <p>Every job card has a red <strong>📋 Audit Report</strong> button. Opens a printable record with:</p>
  <ul>
    <li>Customer + vehicle details</li>
    <li>Work performed</li>
    <li>Every technician who touched it (with timestamps)</li>
    <li>Both signatures (customer + owner)</li>
    <li>Full action timeline</li>
    <li>Cost breakdown</li>
    <li>Photos</li>
  </ul>
  <p>Use this if a customer disputes the work — it's legally defensible proof.</p>

  <h4>Dashboard</h4>
  <p>Bottom nav → <strong>Dash</strong> — daily revenue, jobs by status, low stock alerts, warranty expiring</p>

  <h4>Analytics</h4>
  <p>Business → Analytics — top services, top customers, revenue vs expenses</p>

  <h4>CSV Exports</h4>
  <p>Jobs → Export CSV (also in Customers, Tax tabs)</p>

  <h2>11. Troubleshooting</h2>

  <h4>App won't load</h4>
  <ul>
    <li>Close Chrome completely and reopen</li>
    <li>Check internet signal</li>
    <li>If still failing, wait 60 seconds — Render may be waking up</li>
  </ul>

  <h4>PIN rejected</h4>
  <ul>
    <li>Check caps lock / number pad</li>
    <li>Ask manager to reset your PIN via Staff Management</li>
  </ul>

  <h4>Data missing</h4>
  <ul>
    <li>Swipe down to refresh the screen</li>
    <li>Go offline then online to force a re-sync</li>
  </ul>

  <h4>Offline — "Change pending" pill stuck</h4>
  <ul>
    <li>Wait for signal to return</li>
    <li>Tap the orange pill to force a sync attempt</li>
  </ul>

  <h4>Photos won't upload</h4>
  <ul>
    <li>Check data signal</li>
    <li>Photos are saved locally and will upload when online</li>
  </ul>

  <h4>Camera doesn't scan barcode</h4>
  <ul>
    <li>Clean the lens</li>
    <li>Move closer/further</li>
    <li>If still failing: tap <strong>⌨️ Type</strong> to enter manually</li>
  </ul>

  <h2>12. Quick Reference</h2>

  <h4>Bottom Navigation</h4>
  <ul>
    <li><strong>HOME</strong> — categories of features</li>
    <li><strong>DASH</strong> — daily stats</li>
    <li><strong>AI</strong> — chat with assistant</li>
    <li><strong>JOBS</strong> — job cards + intake</li>
    <li><strong>MORE</strong> — settings</li>
  </ul>

  <h4>Floating Buttons</h4>
  <ul>
    <li><strong>🔍 Search</strong> (top-left) — find anything</li>
    <li><strong>⚙️ Theme</strong> (top-right) — change colours</li>
    <li><strong>🤖 AI</strong> (bottom-right) — AI panel on diagnostic tabs</li>
    <li><strong>👷 Tech Mode</strong> (bottom-left of Jobs) — technician panel</li>
  </ul>

  <h4>Golden Rules</h4>
  <ol>
    <li><strong>Sign before work.</strong> Customer authorises the quote before you touch the vehicle.</li>
    <li><strong>Photo evidence.</strong> Snap before, during, after — protects everyone.</li>
    <li><strong>Enter your PIN.</strong> Every action tied to your name protects you.</li>
    <li><strong>Update progress.</strong> Manager sees the true state of every job.</li>
    <li><strong>Complete → QC → Invoice → Collect.</strong> Never skip a stage.</li>
  </ol>

  <div class="box">
    <strong>Emergency contact:</strong> If the app is broken or you can't access something, call the workshop owner directly. Don't try to work around it.
  </div>

</div>

<script>document.getElementById('d').textContent = new Date().toLocaleDateString();</script>
</body>
</html>"""


_SELL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RamsTech — Sell Sheet</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
color:#1a1a2e;background:#f5f5f5;padding:20px;line-height:1.55;}
.page{max-width:210mm;margin:0 auto;background:#fff;padding:18mm 16mm;
box-shadow:0 4px 16px rgba(0,0,0,.1);}
h1{font-size:32px;color:#E65100;margin-bottom:4px;line-height:1.1;}
h2{font-size:18px;color:#0B1F3A;margin-top:22px;margin-bottom:10px;
border-bottom:2px solid #E65100;padding-bottom:5px;}
h3{font-size:14px;color:#0B1F3A;margin-top:14px;margin-bottom:6px;}
p{font-size:13px;margin-bottom:8px;}
ul{margin:6px 0 12px 20px;font-size:13px;}
li{margin-bottom:3px;}
.hero{display:flex;justify-content:space-between;align-items:flex-start;
border-bottom:3px solid #E65100;padding-bottom:14px;margin-bottom:16px;}
.hero .logo{font-size:56px;}
.tagline{font-size:16px;color:#666;margin-bottom:12px;font-weight:500;}
.price-row{display:flex;gap:12px;margin:16px 0;}
.price-card{flex:1;border:2px solid #0B1F3A;border-radius:10px;
padding:14px;text-align:center;}
.price-card.featured{border-color:#E65100;background:#fff8f0;
position:relative;transform:scale(1.04);}
.price-card.featured::before{content:'MOST POPULAR';
position:absolute;top:-11px;left:50%;transform:translateX(-50%);
background:#E65100;color:#fff;padding:3px 12px;font-size:10px;
font-weight:800;letter-spacing:.08em;border-radius:10px;}
.price-card h3{font-size:12px;text-transform:uppercase;letter-spacing:.1em;
color:#666;margin:0 0 6px;}
.price-card .amount{font-size:26px;font-weight:900;color:#E65100;margin:6px 0;}
.price-card .sub{font-size:11px;color:#888;}
.price-card ul{text-align:left;font-size:11.5px;margin:10px 0 0 16px;}
.cta{background:#0B1F3A;color:#fff;padding:16px;border-radius:10px;
text-align:center;margin-top:18px;}
.cta h3{color:#fff;font-size:15px;margin:0 0 6px;}
.cta p{color:#cbd5e1;margin:4px 0;font-size:12px;}
.cta .contact{font-size:16px;font-weight:800;color:#00A8E8;
margin-top:8px;letter-spacing:.03em;}
.feature-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0;}
.feature{background:#f8fafc;padding:10px 12px;border-radius:8px;font-size:12px;
border-left:3px solid #E65100;}
.feature strong{color:#0B1F3A;display:block;margin-bottom:2px;}
.proof{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
padding:12px 14px;margin:14px 0;font-size:12.5px;}
.proof .big{font-size:22px;font-weight:900;color:#059669;line-height:1;}
.footer{margin-top:20px;padding-top:10px;border-top:1px solid #eee;
font-size:10.5px;color:#888;text-align:center;}
@media print{body{background:#fff;padding:0;}
.page{box-shadow:none;padding:15mm;max-width:100%;}}
</style>
</head>
<body>
<div class="page">

  <div class="hero">
    <div>
      <h1>RamsTech Workshop</h1>
      <div class="tagline">The AI-powered workshop manager built for South Africa</div>
      <p style="font-size:13px;color:#666;">Quotes → jobs → technicians → invoices → reports. All from a phone.</p>
    </div>
    <div class="logo">🔧</div>
  </div>

  <h2>What It Does</h2>
  <div class="feature-row">
    <div class="feature"><strong>📸 Photo to Job Card</strong>Snap a VIN or plate — AI fills the whole card.</div>
    <div class="feature"><strong>🎤 Voice to Job Card</strong>Describe the job — AI writes it up.</div>
    <div class="feature"><strong>🤖 AI Diagnostics</strong>300+ fault codes, 160+ repairs, 50 procedures.</div>
    <div class="feature"><strong>✍️ Two-Signature Quotes</strong>Customer + owner sign. Job auto-created.</div>
    <div class="feature"><strong>👷 Technician PINs</strong>Every action tied to a name and time.</div>
    <div class="feature"><strong>📋 Full Audit Trail</strong>Printable evidence report per job.</div>
    <div class="feature"><strong>📦 Parts Ordering</strong>Search stock, order from AutoZone / Goldwagen / Midas.</div>
    <div class="feature"><strong>💰 Auto-Invoicing</strong>Generated from job data, ready to WhatsApp.</div>
    <div class="feature"><strong>📡 Works Offline</strong>Save jobs with no signal — sync when online.</div>
    <div class="feature"><strong>📱 Install as App</strong>Add to home screen. No Play Store needed.</div>
  </div>

  <h2>Who It's For</h2>
  <ul>
    <li>Independent workshops (1–20 staff)</li>
    <li>Fleet operators with in-house mechanics</li>
    <li>Mobile mechanics and roadside services</li>
    <li>Specialist shops — diesel, auto electrical, aircon</li>
  </ul>

  <h2>Pricing</h2>
  <div class="price-row">
    <div class="price-card">
      <h3>Solo</h3>
      <div class="amount">R399</div>
      <div class="sub">per month</div>
      <ul>
        <li>1 user</li>
        <li>Unlimited jobs</li>
        <li>AI assistant</li>
        <li>Mobile app</li>
      </ul>
    </div>
    <div class="price-card featured">
      <h3>Pro</h3>
      <div class="amount">R699</div>
      <div class="sub">per month</div>
      <ul>
        <li>Up to 5 users</li>
        <li>Everything in Solo</li>
        <li>Technician mode</li>
        <li>Audit reports</li>
        <li>Parts ordering</li>
        <li>Priority support</li>
      </ul>
    </div>
    <div class="price-card">
      <h3>Fleet</h3>
      <div class="amount">R1,499</div>
      <div class="sub">per month</div>
      <ul>
        <li>Unlimited users</li>
        <li>Everything in Pro</li>
        <li>Multi-vehicle accounts</li>
        <li>Fleet dashboard</li>
        <li>On-site training</li>
      </ul>
    </div>
  </div>
  <p style="text-align:center;font-size:12px;color:#888;">All plans include free setup and 30-day trial. No card required to start.</p>

  <div class="proof">
    <div class="big">Save 1–2 hours per day</div>
    <p style="margin-top:6px;font-size:12.5px;">
      Average workshop bills R450/hour. Just one extra job per week covers the monthly cost of Pro.
      Full audit trail protects you against disputes. Real-time job visibility ends lost paperwork.
    </p>
  </div>

  <h2>Why Workshops Choose Us</h2>
  <ul>
    <li><strong>Built for South Africa.</strong> Rand pricing, SA parts suppliers, WhatsApp integration.</li>
    <li><strong>Mobile-first.</strong> Runs on any Android or iPhone — no expensive hardware.</li>
    <li><strong>AI included.</strong> No competitor in SA offers AI diagnostics at this price.</li>
    <li><strong>You own your data.</strong> Export everything to CSV anytime.</li>
    <li><strong>No lock-in.</strong> Cancel anytime. Your records stay yours.</li>
  </ul>

  <h2>Get Started in 3 Steps</h2>
  <ol style="font-size:13px;margin-left:20px;">
    <li>Book a 15-minute demo — we show it on your own workshop data</li>
    <li>30-day free trial with full access</li>
    <li>If it saves you time, subscribe. If not, walk away — no hard feelings.</li>
  </ol>

  <div class="cta">
    <h3>Ready to see it in action?</h3>
    <p>Call or WhatsApp for a live demo today</p>
    <div class="contact">📞 075 434 9233</div>
    <p style="margin-top:8px;">🌐 ramstech.onrender.com &nbsp;|&nbsp; ✉️ info@ramsautosolutions.co.za</p>
  </div>

  <div class="footer">
    RamsTech Workshop — Built in Gauteng, for South African workshops.<br>
    Ask about our founding customer discount: first 10 workshops get 40% off for life.
  </div>

</div>
</body>
</html>"""
