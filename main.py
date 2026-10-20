from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse, Response, RedirectResponse
from datetime import datetime, timedelta
import openai, os, json, uuid, csv, io, urllib.request, urllib.parse, urllib.error, hmac, hashlib, base64

import db
from data import (FAULT_CODES, WMI_DB, YEAR_CODES, TORQUE_SPECS, TORQUE_SEQUENCES,
                  PARTS_CATALOG, COMMON_PROBLEMS, WIRING_LIBRARY, OBD_PIDS,
                  BULB_CHART, BATTERY_SIZES, TYRE_SIZES, FUSE_BOXES,
                  INSPECTION_CATEGORIES, SERVICE_INTERVALS, TRANSLATIONS)
from pages import HTML_PAGE

# ═══════════════════════════════════════════════════════════════
# UI MODULES — Only the essential ones
# ═══════════════════════════════════════════════════════════════
AI_PANEL_HTML = ""
PWA_HTML = ""

try:
    from ai_panel import AI_PANEL_HTML
except Exception as _e: print(f"[main] ai_panel unavailable: {_e}")

try:
    from pwa import router as _pwa_router, PWA_HTML
except Exception as _e: print(f"[main] pwa unavailable: {_e}")

app = FastAPI(title="RamsTech")

# ═══════════════════════════════════════════════════════════════
# CORE SETUP & DB
# ═══════════════════════════════════════════════════════════════
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
db.init()

MEM = {k: {} for k in ["jobs", "customers", "appointments", "quotes", "invoices",
                       "inventory", "purchase_orders", "staff", "clockins", "expenses",
                       "fuel_logs", "workshops", "damage_reports"]}
WORKSHOP = {"name": "My Workshop", "phone": "", "address": "", "email": "", "logo": "RT", "labour_rate": 450}

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

def store_list(t):
    if db.is_ready(): return db.get_all(t)
    return list(MEM[t].values())

def store_get(t, i):
    if db.is_ready(): return db.get_one(t, i)
    return MEM[t].get(i)

def store_save(t, i, row):
    if db.is_ready():
        exists = db.get_one(t, i)
        return db.update(t, i, row) if exists else db.insert(t, row)
    MEM[t][i] = row
    return row

def store_delete(t, i):
    if db.is_ready(): return db.delete(t, i)
    MEM[t].pop(i, None)
    return True

def get_workshop_data():
    if db.is_ready():
        w = db.get_workshop()
        if w: return w
    return WORKSHOP

def save_workshop_data(d):
    if db.is_ready(): return db.save_workshop(d)
    WORKSHOP.update(d)
    return d

# ═══════════════════════════════════════════════════════════════
# HOME & INJECTIONS
# ═══════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def home():
    html = HTML_PAGE
    idx = html.rfind("</body>")
    if idx == -1: return html

    inject = ""
    if AI_PANEL_HTML: inject += AI_PANEL_HTML
    if PWA_HTML: inject += PWA_HTML

    return html[:idx] + inject + html[idx:]

@app.get("/health")
def health():
    return {"status": "healthy", "database": ("supabase" if db.is_ready() else "memory")}


# ═══════════════════════════════════════════════════════════════
# INVOICES PDF GENERATOR
# ═══════════════════════════════════════════════════════════════
def _meta(job):
    sig = job.get("signature") or ""
    if sig.startswith("{"):
        try: return json.loads(sig)
        except Exception: pass
    return {"customer_sig": sig, "owner_sig": "", "stage": "", "progress": 0, "tech": "", "started_by": "", "completed_by": "", "qc_by": ""}

@app.get("/api/workflow/invoice-html/{jid}", response_class=HTMLResponse)
def invoice_html(jid: str):
    job = store_get("jobs", jid)
    if not job: raise HTTPException(404, "Job not found")
    meta = _meta(job)
    w = get_workshop_data()

    logo = w.get("logo") or "🔧"
    name = w.get("name") or "RAMSTECH"
    phone = w.get("phone") or ""
    address = w.get("address") or ""
    email = w.get("email") or ""

    labour = float(job.get("labour_cost") or 0)
    parts = float(job.get("parts_cost") or 0)
    subtotal = float(job.get("subtotal") or 0)
    vat = float(job.get("vat") or 0)
    total = float(job.get("total") or 0)
    created = job.get("created") or ""
    inv_no = "INV-" + jid.upper()
    cust_sig = meta.get("customer_sig") or ""
    owner_sig = meta.get("owner_sig") or ""

    def sig_block(label, sig):
        if sig and sig.startswith("data:image"):
            return f'<div class="sigbox"><img src="{sig}"><div class="siglabel">{label}</div></div>'
        return f'<div class="sigbox empty"><div class="siglabel">{label} — not signed</div></div>'

    timeline_rows = "".join([f"<tr><td>{entry}</td></tr>" for entry in (job.get("timeline") or [])])

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{inv_no}</title>
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{font-family:-apple-system,sans-serif;background:#f0f2f5;color:#1a1a2e;padding:16px;}}.page{{max-width:800px;margin:0 auto;background:#fff;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,.08);border-radius:12px;}}.header{{display:flex;justify-content:space-between;padding-bottom:20px;border-bottom:3px solid #E65100;margin-bottom:24px;}}.brand{{display:flex;gap:14px;align-items:center;}}.logo{{font-size:48px;}}.brand h1{{font-size:22px;color:#E65100;font-weight:800;}}.inv-meta{{text-align:right;}}.inv-meta h2{{font-size:22px;font-weight:800;}}.section{{margin-bottom:20px;}}.section h3{{font-size:12px;color:#E65100;text-transform:uppercase;margin-bottom:10px;border-bottom:1px solid #e5e7eb;}}.row{{display:flex;gap:20px;}}.col{{flex:1;}}.field{{font-size:13px;margin-bottom:6px;}}.field b{{color:#666;min-width:90px;display:inline-block;}}table.items{{width:100%;border-collapse:collapse;margin-top:8px;}}table.items th{{background:#E65100;color:#fff;padding:10px;font-size:12px;}}table.items td{{padding:10px;border-bottom:1px solid #eee;font-size:13px;}}table.items td.amt{{text-align:right;font-weight:600;}}table.totals{{width:100%;margin-top:16px;}}table.totals td{{padding:8px 10px;font-size:13px;}}table.totals td:last-child{{text-align:right;font-weight:600;}}table.totals tr.grand{{background:#fff5ec;}}table.totals tr.grand td{{font-size:16px;font-weight:800;color:#E65100;border-top:2px solid #E65100;}}.sigs{{display:flex;gap:16px;margin-top:14px;}}.sigbox{{flex:1;border:1px solid #ddd;border-radius:8px;padding:10px;text-align:center;min-height:100px;display:flex;flex-direction:column;justify-content:flex-end;}}.sigbox img{{max-width:100%;max-height:80px;}}.siglabel{{font-size:11px;color:#666;}}.print-bar{{position:fixed;top:12px;right:12px;display:flex;gap:8px;z-index:100;}}.print-bar button{{padding:10px 18px;background:#E65100;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;}}@media print{{body{{background:#fff;padding:0;}}.page{{box-shadow:none;padding:0;}}.print-bar{{display:none;}}}}</style></head><body>
<div class="print-bar"><button onclick="window.print()">🖨 Print</button><button onclick="window.close()">Close</button></div>
<div class="page">
<div class="header"><div class="brand"><div class="logo">{logo}</div><div><h1>{name}</h1><div class="sub">{phone}<br>{address}<br>{email}</div></div></div><div class="inv-meta"><h2>{inv_no}</h2><p>Date: {created}</p><p>Job: #{jid}</p><p><span style="background:#10b981;color:#fff;padding:4px 12px;border-radius:12px;font-size:11px;">{job.get('status','')}</span></p></div></div>
<div class="section"><h3>Customer & Vehicle</h3><div class="row"><div class="col"><div class="field"><b>Customer:</b> {job.get('customer','')}</div><div class="field"><b>Phone:</b> {job.get('phone','')}</div></div><div class="col"><div class="field"><b>Vehicle:</b> {job.get('vehicle','')}</div><div class="field"><b>Registration:</b> {job.get('registration','')}</div></div></div></div>
<div class="section"><h3>Work Performed</h3><div class="field">{job.get('complaint','')}</div>
<table class="items"><thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead><tbody><tr><td>Labour</td><td class="amt">R {labour:,.2f}</td></tr><tr><td>Parts</td><td class="amt">R {parts:,.2f}</td></tr></tbody></table>
<table class="totals"><tr><td>Subtotal</td><td>R {subtotal:,.2f}</td></tr><tr><td>VAT (15%)</td><td>R {vat:,.2f}</td></tr><tr class="grand"><td>TOTAL DUE</td><td>R {total:,.2f}</td></tr></table></div>
<div class="section"><h3>Signatures</h3><div class="sigs">{sig_block("Customer Approval", cust_sig)}{sig_block("Owner Approval", owner_sig)}</div></div>
<div class="footer" style="text-align:center;font-size:11px;color:#888;margin-top:32px;">{name} — Thank you for your business.</div>
</div></body></html>"""
    return HTMLResponse(content=html)


# ═══════════════════════════════════════════════════════════════
# PAYMENTS ROUTER
# ═══════════════════════════════════════════════════════════════
router_pay = APIRouter(tags=["payments"])

def detect_provider():
    if os.getenv("YOCO_SECRET_KEY", "").strip(): return "yoco"
    if os.getenv("PAYFAST_MERCHANT_ID", "").strip(): return "payfast"
    if os.getenv("STRIPE_SECRET_KEY", "").strip(): return "stripe"
    return "console"

def _public_base(): return os.getenv("PUBLIC_BASE_URL", "https://ramstech.onrender.com").rstrip("/")

def create_payment_link(invoice):
    try:
        amt = float(invoice.get("total", 0)) - float(invoice.get("amount_paid", 0))
        if amt <= 0.005: return {"success": False, "error": "Nothing outstanding"}
        provider = detect_provider()
        cents = int(round(amt * 100))
        inv_id = invoice.get("id", "")
        desc = f"Invoice {inv_id} — {invoice.get('description', '')[:40]}"

        if provider == "yoco": return _yoco_checkout(inv_id, cents, desc)
        if provider == "payfast": return _payfast_link(inv_id, amt, desc)
        if provider == "stripe": return _stripe_link(inv_id, cents, desc)
        return {"success": True, "provider": "console", "url": f"{_public_base()}/pay/demo?inv={inv_id}&amount={amt:.2f}", "ref": f"console_{inv_id}"}
    except Exception as e: return {"success": False, "error": str(e)}

def _yoco_checkout(invoice_id, amount_cents, description):
    key = os.getenv("YOCO_SECRET_KEY", "").strip()
    payload = {"amount": amount_cents, "currency": "ZAR", "successUrl": f"{_public_base()}/pay/success?inv={invoice_id}", "cancelUrl": f"{_public_base()}/pay/cancelled?inv={invoice_id}", "failureUrl": f"{_public_base()}/pay/failed?inv={invoice_id}", "metadata": {"invoiceId": invoice_id}}
    req = urllib.request.Request("https://online.yoco.com/v1/checkouts", data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "provider": "yoco", "url": d.get("redirectUrl"), "ref": d.get("id")}
    except Exception as e: return {"success": False, "provider": "yoco", "error": str(e)}

def _payfast_link(invoice_id, amount_rands, description):
    merchant_id = os.getenv("PAYFAST_MERCHANT_ID", "").strip()
    merchant_key = os.getenv("PAYFAST_MERCHANT_KEY", "").strip()
    form = {"merchant_id": merchant_id, "merchant_key": merchant_key, "return_url": f"{_public_base()}/pay/success?inv={invoice_id}", "cancel_url": f"{_public_base()}/pay/cancelled?inv={invoice_id}", "notify_url": f"{_public_base()}/api/payments/webhook/payfast", "m_payment_id": invoice_id, "amount": f"{amount_rands:.2f}", "item_name": f"Invoice {invoice_id}"}
    return {"success": True, "provider": "payfast", "url": "https://www.payfast.co.za/eng/process?" + urllib.parse.urlencode(form), "ref": invoice_id}

def _stripe_link(invoice_id, amount_cents, description):
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    form = {"mode": "payment", "success_url": f"{_public_base()}/pay/success?inv={invoice_id}", "cancel_url": f"{_public_base()}/pay/cancelled?inv={invoice_id}", "line_items[0][quantity]": "1", "line_items[0][price_data][currency]": "zar", "line_items[0][price_data][unit_amount]": str(amount_cents), "line_items[0][price_data][product_data][name]": f"Invoice {invoice_id}"}
    req = urllib.request.Request("https://api.stripe.com/v1/checkout/sessions", data=urllib.parse.urlencode(form).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "provider": "stripe", "url": d.get("url"), "ref": d.get("id")}
    except Exception as e: return {"success": False, "provider": "stripe", "error": str(e)}

def _mark_paid(invoice_id, amount, provider, ref):
    inv = store_get("invoices", invoice_id)
    if not inv: return {"success": False, "error": "Invoice not found"}
    if inv.get("paid"): return {"success": True, "already": True}
    inv["amount_paid"] = float(inv.get("amount_paid", 0)) + float(amount)
    inv["paid"] = inv["amount_paid"] >= float(inv.get("total", 0)) - 0.005
    store_save("invoices", invoice_id, inv)
    return {"success": True, "invoice_id": invoice_id, "paid": inv["paid"]}

@router_pay.get("/pay/{invoice_id}")
def pay_redirect(invoice_id: str):
    inv = store_get("invoices", invoice_id)
    if not inv: raise HTTPException(404, "Invoice not found")
    link = create_payment_link(inv)
    if not link.get("success"): raise HTTPException(500, link.get("error"))
    inv["payment_link"] = link
    store_save("invoices", invoice_id, inv)
    return RedirectResponse(link["url"], status_code=302)

@router_pay.post("/api/payments/webhook/yoco")
async def webhook_yoco(request: Request):
    event = await request.json()
    if "succeeded" not in event.get("type", "").lower(): return {"success": True}
    payload = event.get("payload") or {}
    return _mark_paid(payload.get("metadata", {}).get("invoiceId"), payload.get("amount", 0)/100, "yoco", payload.get("id"))

@router_pay.post("/api/payments/webhook/stripe")
async def webhook_stripe(request: Request):
    event = await request.json()
    if event.get("type") != "checkout.session.completed": return {"success": True}
    session = event.get("data", {}).get("object", {})
    return _mark_paid(session.get("metadata", {}).get("invoiceId"), session.get("amount_total", 0)/100, "stripe", session.get("id"))

app.include_router(router_pay)


# ═══════════════════════════════════════════════════════════════
# BATCH 2: STAFF ROLES & KANBAN
# ═══════════════════════════════════════════════════════════════
ROLES = {
    "owner": {"label": "Owner", "capabilities": ["*"]},
    "manager": {"label": "Manager", "capabilities": ["view_jobs", "edit_jobs", "view_customers", "view_invoices"]},
    "technician": {"label": "Technician", "capabilities": ["view_own_jobs", "edit_own_jobs", "clock_in"]},
}
KANBAN_STATUSES = ["New", "Diagnosing", "Awaiting Approval", "Awaiting Parts", "In Progress", "QC", "Ready for Pickup", "Completed", "Invoiced"]

@app.get("/api/roles")
def list_roles(): return {"roles": [{"id": k, "label": v["label"]} for k, v in ROLES.items()]}

@app.get("/api/whoami")
def whoami(): return {"authenticated": True, "user": "Owner", "role": "owner", "capabilities": ["*"]}

@app.post("/api/staff/{sid}/pin")
async def set_staff_pin(sid: str, r: Request):
    d = await r.json(); pin = str(d.get("pin") or "").strip()
    if not pin or len(pin) < 4 or not pin.isdigit(): raise HTTPException(400, "PIN must be 4 digits")
    staff = store_get("staff", sid)
    if not staff: raise HTTPException(404, "Staff not found")
    staff["pin"] = pin; store_save("staff", sid, staff); return {"success": True}

@app.get("/api/jobs/kanban")
def jobs_kanban():
    jobs = store_list("jobs")
    columns = {s: [] for s in KANBAN_STATUSES}
    for j in jobs:
        s = j.get("status") or "New"
        if s not in columns: columns[s] = []
        columns[s].append({"id": j.get("id"), "customer": j.get("customer", ""), "vehicle": j.get("vehicle", "")})
    return {"statuses": KANBAN_STATUSES, "columns": columns}

@app.post("/api/jobs/{jid}/status")
async def set_job_status(jid: str, r: Request):
    d = await r.json(); new_status = (d.get("status") or "").strip()
    if new_status not in KANBAN_STATUSES: raise HTTPException(400, "Invalid status")
    job = store_get("jobs", jid)
    if not job: raise HTTPException(404, "Job not found")
    job["status"] = new_status
    store_save("jobs", jid, job)
    return {"success": True, "job": job}


# ═══════════════════════════════════════════════════════════════
# ALL YOUR OTHER CORE ROUTES
# ═══════════════════════════════════════════════════════════════
@app.get("/api/translations/{lang}")
def get_translations(lang: str): return {"lang": lang, "strings": TRANSLATIONS.get(lang, TRANSLATIONS["en"])}

@app.get("/api/stats")
def get_stats():
    jobs = store_list("jobs"); invs = store_list("invoices"); exps = store_list("expenses"); custs = store_list("customers")
    rev = sum(float(i.get("total", 0)) for i in invs); exp = sum(float(e.get("amount", 0)) for e in exps)
    return {"jobs_total": len(jobs), "jobs_open": sum(1 for j in jobs if j.get("status") != "Completed"), "jobs_completed": sum(1 for j in jobs if j.get("status") == "Completed"), "jobs_new": sum(1 for j in jobs if j.get("status") == "New"), "jobs_progress": sum(1 for j in jobs if j.get("status") == "In Progress"), "customers": len(custs), "revenue": round(rev, 2), "expenses": round(exp, 2), "revenue_labels": [], "revenue_data": []}

@app.get("/api/jobs")
def list_jobs(): return {"jobs": store_list("jobs")}

@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json(); jid = str(uuid.uuid4())[:8]
    job = {"id": jid, "customer": d.get("customer", ""), "phone": d.get("phone", ""), "vehicle": d.get("vehicle", ""), "registration": d.get("registration", ""), "km": int(d.get("km", 0)), "complaint": d.get("complaint", ""), "assigned_to": d.get("assigned_to", ""), "photos": d.get("photos", [])[:5], "signature": d.get("signature", ""), "warranty_months": int(d.get("warranty_months", 6)), "status": "New", "timeline": [now() + " — Job created"], "labour_hours": 0, "labour_rate": get_workshop_data().get("labour_rate", 450), "parts_cost": 0, "labour_cost": 0, "subtotal": 0, "vat": 0, "total": 0, "created": now()}
    store_save("jobs", jid, job); return {"success": True, "job": job}

@app.get("/api/customers")
def list_customers(): return {"customers": store_list("customers")}

@app.post("/api/customers")
async def create_customer(r: Request):
    d = await r.json(); cid = str(uuid.uuid4())[:8]
    c = {"id": cid, "name": d.get("name", ""), "phone": d.get("phone", ""), "email": d.get("email", ""), "address": d.get("address", ""), "created": today()}
    store_save("customers", cid, c); return {"success": True, "customer": c}

@app.get("/api/invoices")
def list_invoices(): return {"invoices": store_list("invoices")}

@app.post("/api/invoices")
async def create_invoice(r: Request):
    d = await r.json(); iid = str(uuid.uuid4())[:8]
    i = {"id": iid, "customer": d.get("customer", ""), "vehicle": d.get("vehicle", ""), "description": d.get("description", ""), "labour": float(d.get("labour", 0)), "parts": float(d.get("parts", 0)), "subtotal": float(d.get("labour", 0)) + float(d.get("parts", 0)), "vat": (float(d.get("labour", 0)) + float(d.get("parts", 0))) * 0.15, "total": (float(d.get("labour", 0)) + float(d.get("parts", 0))) * 1.15, "amount_paid": 0, "paid": False, "created": now()}
    store_save("invoices", iid, i); return {"success": True, "invoice": i}

@app.get("/api/workshop")
def get_workshop(): return get_workshop_data()

@app.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message", "")
    if not OPENAI_KEY: return {"reply": "AI not configured"}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": msg}], max_tokens=800)
        return {"reply": resp.choices[0].message.content}
    except Exception as e: return {"reply": f"Error: {str(e)}"}
