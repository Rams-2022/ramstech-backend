from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse, Response, RedirectResponse
from datetime import datetime, timedelta
import openai, os, json, uuid, csv, io, urllib.request, urllib.parse, urllib.error, hmac, hashlib, base64

app = FastAPI(title="RamsTech")

try:
    import db
    from data import (FAULT_CODES, WMI_DB, YEAR_CODES, TORQUE_SPECS, TORQUE_SEQUENCES,
                      PARTS_CATALOG, COMMON_PROBLEMS, WIRING_LIBRARY, OBD_PIDS,
                      BULB_CHART, BATTERY_SIZES, TYRE_SIZES, FUSE_BOXES,
                      INSPECTION_CATEGORIES, SERVICE_INTERVALS, TRANSLATIONS)
except Exception as e: print(f"[CRITICAL] Core data import failed: {e}")

HTML_PAGE = "<html><body><h1>App is loading...</h1></body></html>"
try: from pages import HTML_PAGE
except Exception as e: print(f"[CRITICAL] pages.py failed to load: {e}")

AI_PANEL_HTML, PWA_HTML = "", ""
try: from ai_panel import AI_PANEL_HTML
except Exception as e: print(f"[WARN] ai_panel unavailable: {e}")
try: from pwa import router as _pwa_router, PWA_HTML
except Exception as e: print(f"[WARN] pwa unavailable: {e}")

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
try: db.init()
except: pass

MEM = {k: {} for k in ["jobs", "customers", "appointments", "quotes", "invoices", "inventory", "purchase_orders", "staff", "clockins", "expenses", "fuel_logs", "workshops", "damage_reports", "inspections"]}
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
def health(): return {"status": "healthy", "database": ("supabase" if db.is_ready() else "memory")}

# ═══════════════════════════════════════════════════════════════
# INVOICES & PAYMENTS
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
    meta = _meta(job); w = get_workshop_data()
    logo, name = w.get("logo") or "🔧", w.get("name") or "RAMSTECH"
    phone, address, email = w.get("phone") or "", w.get("address") or "", w.get("email") or ""
    labour, parts = float(job.get("labour_cost") or 0), float(job.get("parts_cost") or 0)
    subtotal, vat, total = float(job.get("subtotal") or 0), float(job.get("vat") or 0), float(job.get("total") or 0)
    created, inv_no = job.get("created") or "", "INV-" + jid.upper()
    cust_sig, owner_sig = meta.get("customer_sig") or "", meta.get("owner_sig") or ""
    def sig_block(label, sig):
        if sig and sig.startswith("data:image"): return f'<div class="sigbox"><img src="{sig}"><div class="siglabel">{label}</div></div>'
        return f'<div class="sigbox empty"><div class="siglabel">{label} — not signed</div></div>'
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
        inv_id = invoice.get("id", ""); desc = f"Invoice {inv_id}"; provider = detect_provider(); cents = int(round(amt * 100))
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
    merchant_id = os.getenv("PAYFAST_MERCHANT_ID", "").strip(); merchant_key = os.getenv("PAYFAST_MERCHANT_KEY", "").strip()
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
def _success_page(title, message, color="#16a34a", icon="✓"):
    return HTMLResponse(f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{font-family:-apple-system,sans-serif;margin:0;padding:40px 20px;background:#f5f5f5;text-align:center;color:#1a1a1a}}
.card{{max-width:400px;margin:60px auto;background:#fff;border-radius:16px;padding:40px 28px;box-shadow:0 4px 20px rgba(0,0,0,0.06)}}
.icon{{font-size:56px;color:{color};margin-bottom:16px}} h1{{margin:0 0 8px;font-size:22px;}}
p{{margin:0;color:#666;line-height:1.6;font-size:15px}}</style></head><body>
<div class="card"><div class="icon">{icon}</div><h1>{title}</h1><p>{message}</p></div></body></html>""")
@router_pay.get("/pay/success")
def pay_success(inv: str = ""): return _success_page("Payment received", f"Thank you! Invoice {inv} has been marked as paid.")
@router_pay.get("/pay/cancelled")
def pay_cancelled(inv: str = ""): return _success_page("Payment cancelled", "No charge was made. You can pay any time.", color="#f59e0b", icon="!")
@router_pay.get("/pay/demo")
def pay_demo(inv: str = "", amount: str = "0"): return _success_page("Demo mode", f"Console mode is active. Would have charged R{amount} for invoice {inv}.", color="#666", icon="⚙")
@router_pay.get("/pay/{invoice_id}")
def pay_redirect(invoice_id: str):
    inv = store_get("invoices", invoice_id)
    if not inv: raise HTTPException(404, "Invoice not found")
    link = create_payment_link(inv)
    if not link.get("success"): raise HTTPException(500, link.get("error"))
    inv["payment_link"] = link; store_save("invoices", invoice_id, inv)
    return RedirectResponse(link["url"], status_code=302)
app.include_router(router_pay)

# ═══════════════════════════════════════════════════════════════
# INSPECTIONS
# ═══════════════════════════════════════════════════════════════
@app.get("/api/inspections")
def list_inspections(): return {"inspections": store_list("inspections")}

@app.post("/api/inspections")
async def create_inspection(r: Request):
    d = await r.json()
    iid = str(uuid.uuid4())[:8]
    insp = {
        "id": iid,
        "customer": d.get("customer", ""),
        "vehicle": d.get("vehicle", ""),
        "checklist": d.get("checklist", []),
        "notes": d.get("notes", ""),
        "photos": d.get("photos", [])[:3],
        "created": now()
    }
    store_save("inspections", iid, insp)
    return {"success": True, "inspection": insp}

# ═══════════════════════════════════════════════════════════════
# INVENTORY, APPOINTMENTS, CLOCK-INS
# ═══════════════════════════════════════════════════════════════
@app.get("/api/inventory")
def list_inv(): return {"items": store_list("inventory")}
@app.post("/api/inventory")
async def add_inv(r: Request):
    d = await r.json(); iid = str(uuid.uuid4())[:8]
    item = {"id": iid, "part_number": d.get("part_number", ""), "name": d.get("name", ""), "category": d.get("category", ""), "qty": int(d.get("qty", 0)), "min_qty": int(d.get("min_qty", 5)), "cost_price": float(d.get("cost_price", 0)), "sell_price": float(d.get("sell_price", 0)), "supplier": d.get("supplier", ""), "created": today()}
    store_save("inventory", iid, item); return {"success": True, "item": item}
@app.post("/api/inventory/{iid}/adjust")
async def adj_inv(iid: str, r: Request):
    d = await r.json(); item = store_get("inventory", iid)
    if not item: raise HTTPException(404)
    item["qty"] = max(0, int(item["qty"]) + int(d.get("delta", 0)))
    store_save("inventory", iid, item); return {"success": True, "item": item}

@app.get("/api/appointments")
def list_appts(): return {"appointments": store_list("appointments")}
@app.post("/api/appointments")
async def create_appt(r: Request):
    d = await r.json(); aid = str(uuid.uuid4())[:8]
    a = {"id": aid, **{k: d.get(k, "") for k in ["customer", "phone", "vehicle", "service", "date", "time"]}}
    store_save("appointments", aid, a); return {"success": True, "appointment": a}
@app.delete("/api/appointments/{aid}")
def del_appt(aid: str): store_delete("appointments", aid); return {"success": True}

@app.get("/api/clockins")
def list_clockins(): return {"clockins": store_list("clockins")}
@app.post("/api/clockins")
async def clock_in(r: Request):
    d = await r.json(); cid = str(uuid.uuid4())[:8]
    c = {"id": cid, "staff_id": d.get("staff_id", ""), "clock_in": now(), "clock_out": None}
    store_save("clockins", cid, c); return {"success": True, "clockin": c}
@app.post("/api/clockins/{sid}/out")
async def clock_out(sid: str):
    for c in store_list("clockins"):
        if c["staff_id"] == sid and not c.get("clock_out"):
            c["clock_out"] = now(); store_save("clockins", c["id"], c)
            return {"success": True, "clockin": c}
    raise HTTPException(404, "No active clock-in")

# ═══════════════════════════════════════════════════════════════
# STAFF MANAGEMENT
# ═══════════════════════════════════════════════════════════════
@app.get("/api/staff")
def list_staff(): return {"staff": store_list("staff")}

@app.post("/api/staff")
async def create_staff(r: Request):
    d = await r.json(); sid = str(uuid.uuid4())[:8]
    s = {"id": sid, "name": d.get("name", ""), "role": d.get("role", ""), "pin": d.get("pin", "")}
    store_save("staff", sid, s)
    return {"success": True, "staff": s}

@app.delete("/api/staff/{sid}")
def delete_staff(sid: str):
    store_delete("staff", sid)
    return {"success": True}

@app.post("/api/staff/{sid}/pin")
async def set_staff_pin(sid: str, r: Request):
    d = await r.json(); pin = str(d.get("pin") or "").strip()
    if not pin or len(pin) < 4: raise HTTPException(400, "PIN must be 4 digits")
    staff = store_get("staff", sid)
    if not staff: raise HTTPException(404, "Staff not found")
    staff["pin"] = pin; store_save("staff", sid, staff); return {"success": True}

# ═══════════════════════════════════════════════════════════════
# CORE ROUTES, DATA LOOKUPS & ANALYTICS
# ═══════════════════════════════════════════════════════════════
KANBAN_STATUSES = ["New", "Diagnosing", "Awaiting Approval", "Awaiting Parts", "In Progress", "QC", "Ready for Pickup", "Completed", "Invoiced"]

@app.get("/api/whoami")
def whoami(): return {"authenticated": True, "user": "Owner", "role": "owner", "capabilities": ["*"]}

@app.get("/api/jobs/kanban")
def jobs_kanban():
    jobs = store_list("jobs"); columns = {s: [] for s in KANBAN_STATUSES}
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
    job["status"] = new_status; store_save("jobs", jid, job)
    return {"success": True, "job": job}

@app.get("/api/translations/{lang}")
def get_translations(lang: str): return {"lang": lang, "strings": TRANSLATIONS.get(lang, TRANSLATIONS["en"])}

@app.get("/api/stats")
def get_stats():
    jobs, invs = store_list("jobs"), store_list("invoices")
    exps, custs = store_list("expenses"), store_list("customers")
    rev = sum(float(i.get("total", 0)) for i in invs)
    exp = sum(float(e.get("amount", 0)) for e in exps)
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; data = [1500, 2300, 1800, 3200, 2800, 4500, 3900] 
    return {"jobs_total": len(jobs), "jobs_open": sum(1 for j in jobs if j.get("status") != "Completed"), "jobs_completed": sum(1 for j in jobs if j.get("status") == "Completed"), "jobs_new": sum(1 for j in jobs if j.get("status") == "New"), "jobs_progress": sum(1 for j in jobs if j.get("status") == "In Progress"), "customers": len(custs), "revenue": round(rev, 2), "expenses": round(exp, 2), "revenue_labels": labels, "revenue_data": data}

@app.get("/api/analytics")
def get_analytics():
    jobs = store_list("jobs"); invs = store_list("invoices"); exps = store_list("expenses")
    rev = sum(float(i.get("total", 0)) for i in invs)
    exp = sum(float(e.get("amount", 0)) for e in exps)
    net = rev - exp
    avg_job = rev / len(invs) if invs else 0
    
    labels, data = [], []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])
        data.append(sum(float(inv.get("total", 0)) for inv in invs if (inv.get("created") or "").startswith(day)))
        
    status_counts = {s: 0 for s in KANBAN_STATUSES}
    for j in jobs:
        st = j.get("status", "New")
        if st in status_counts: status_counts[st] += 1
        
    mech_stats = {}
    for j in jobs:
        m = j.get("assigned_to") or "Unassigned"
        mech_stats[m] = mech_stats.get(m, 0) + 1
    top_mechs = sorted(mech_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    
    svc_stats = {}
    for j in jobs:
        s = (j.get("complaint") or "General")[:20]
        svc_stats[s] = svc_stats.get(s, 0) + 1
    top_svcs = sorted(svc_stats.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "revenue": rev, "expenses": exp, "net_profit": net, "avg_job": avg_job,
        "rev_labels": labels, "rev_data": data,
        "status_labels": list(status_counts.keys()), "status_data": list(status_counts.values()),
        "mech_labels": [m[0] for m in top_mechs], "mech_data": [m[1] for m in top_mechs],
        "svc_labels": [s[0] for s in top_svcs], "svc_data": [s[1] for s in top_svcs]
    }

@app.get("/api/jobs")
def list_jobs(): return {"jobs": store_list("jobs")}
@app.post("/api/jobs")
async def create_job(r: Request):
    d = await r.json(); jid = str(uuid.uuid4())[:8]
    job = {"id": jid, "customer": d.get("customer", ""), "phone": d.get("phone", ""), "vehicle": d.get("vehicle", ""), "registration": d.get("registration", ""), "km": int(d.get("km", 0)), "complaint": d.get("complaint", ""), "assigned_to": d.get("assigned_to", ""), "photos": d.get("photos", [])[:5], "signature": d.get("signature", ""), "warranty_months": int(d.get("warranty_months", 6)), "status": "New", "timeline": [now() + " — Job created"], "labour_hours": 0, "labour_rate": get_workshop_data().get("labour_rate", 450), "parts_cost": 0, "labour_cost": 0, "subtotal": 0, "vat": 0, "total": 0, "created": now()}
    store_save("jobs", jid, job); return {"success": True, "job": job}
@app.put("/api/jobs/{jid}")
async def update_job(jid: str, r: Request):
    d = await r.json(); job = store_get("jobs", jid)
    if not job: raise HTTPException(404)
    if "status" in d: job["status"] = d["status"]
    store_save("jobs", jid, job); return {"success": True, "job": job}
@app.post("/api/jobs/{jid}/cost")
async def set_job_cost(jid: str, r: Request):
    d = await r.json(); job = store_get("jobs", jid)
    if not job: raise HTTPException(404)
    h = float(d.get("labour_hours", 0)); rate = float(d.get("labour_rate", 450)); parts = float(d.get("parts_cost", 0))
    labour = h * rate; subtotal = labour + parts; vat = subtotal * 0.15; total = subtotal + vat
    job.update({"labour_hours": h, "labour_rate": rate, "parts_cost": parts, "labour_cost": labour, "subtotal": subtotal, "vat": vat, "total": total})
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
@app.post("/api/workshop")
async def save_workshop(r: Request):
    d = await r.json(); save_workshop_data(d); return {"success": True, "workshop": get_workshop_data()}

@app.get("/api/fault-codes")
def search_fault_codes(search: str = ""):
    q = search.strip().lower()
    if not q: return {"codes": []}
    results = []
    for code, data in FAULT_CODES.items():
        if q in code.lower() or q in data.get("description", "").lower():
            results.append(data)
    return {"codes": results}

@app.get("/api/problems")
def get_problems(): return {"problems": COMMON_PROBLEMS}

@app.get("/api/parts-search")
def search_parts(q: str = ""):
    q = q.lower().strip()
    if not q: return {"results": []}
    results = []
    for part in PARTS_CATALOG:
        if (q in part.get("name", "").lower() or 
            q in part.get("number", "").lower() or 
            q in part.get("brand", "").lower() or
            q in part.get("category", "").lower()):
            results.append({
                "name": part.get("name"),
                "part_number": part.get("number"),
                "brand": part.get("brand"),
                "sell_price": float(part.get("price", 0))
            })
    return {"results": results}

@app.get("/api/vin/{vin}")
def decode_vin(vin: str):
    vin = vin.upper()
    if len(vin) != 17: raise HTTPException(400, "VIN must be 17 characters")
    wmi = vin[:3]; year_code = vin[9]
    make, country = WMI_DB.get(wmi, ("Unknown", "Unknown"))
    year = YEAR_CODES.get(year_code, "Unknown")
    return {"vin": vin, "manufacturer": make, "country": country, "year": year}

# ═══════════════════════════════════════════════════════════════
# AI PANEL ENDPOINTS
# ═══════════════════════════════════════════════════════════════
@app.post("/api/fault-codes/ai")
async def ai_explain_code(r: Request):
    d = await r.json(); code = d.get("code", ""); vehicle = d.get("vehicle", "")
    if not OPENAI_KEY: return {"reply": "AI not configured on server (missing API key)."}
    prompt = f"You are an expert mechanic. Explain the OBD fault code {code}. {'Vehicle: ' + vehicle if vehicle else ''}. Provide: 1. What it means. 2. Common causes. 3. Diagnostic steps to fix it. Keep it brief."
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=500)
        return {"reply": resp.choices[0].message.content}
    except Exception as e: return {"reply": f"Error communicating with AI: {str(e)}"}

@app.post("/api/fault-codes/ai-search")
async def ai_search_symptom(r: Request):
    d = await r.json(); query = d.get("query", "").lower(); vehicle = d.get("vehicle", "")
    local_matches = []
    for code, data in FAULT_CODES.items():
        if query in data.get("description", "").lower() or any(query in sym.lower() for sym in data.get("symptoms", [])):
            local_matches.append({"code": code, "description": data["description"]})
    if not OPENAI_KEY: return {"reply": "AI not configured.", "local_matches": local_matches[:5]}
    prompt = f"You are an expert mechanic. A customer describes this symptom: '{query}'. {'Vehicle: ' + vehicle if vehicle else ''}. List the most likely OBD fault codes and what the technician should check. Be concise."
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=500)
        return {"reply": resp.choices[0].message.content, "local_matches": local_matches[:5]}
    except Exception as e: return {"reply": f"Error: {str(e)}", "local_matches": local_matches[:5]}

@app.post("/api/ai-context")
async def ai_context(r: Request):
    d = await r.json(); message = d.get("message", ""); vehicle = d.get("vehicle", ""); img_b64 = d.get("image_base64")
    if not OPENAI_KEY: return {"reply": "AI not configured."}
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        if img_b64:
            if img_b64.startswith("data:"): img_b64 = img_b64.split(",", 1)[1]
            prompt = f"Expert mechanic. {('Vehicle: ' + vehicle) if vehicle else ''}. The user says: '{message}'. Diagnose the issue in this photo."
            resp = c.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": prompt},{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}], max_tokens=800)
        else:
            prompt = f"Expert mechanic. {('Vehicle: ' + vehicle) if vehicle else ''}. Answer this: {message}"
            resp = c.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=800)
        return {"reply": resp.choices[0].message.content}
    except Exception as e: return {"reply": f"Error: {str(e)}"}

@app.post("/api/chat")
async def chat(r: Request):
    d = await r.json(); msg = d.get("message", "")
    if not OPENAI_KEY: return {"reply": "AI not configured"}
    
    system_prompt = (
        "You are RAMSTECH AI, an elite master mechanic and technical advisor. "
        "You specialize in automotive and heavy-duty systems including: "
        "Mechanics (engines, drivetrain), Hydraulics, Pneumatics, Transmissions, "
        "Electrical (12V/24V, wiring, sensors), Suspension, and Tool usage. "
        "You also provide step-by-step procedures for completing jobs. "
        "\n\nWhen answering, format your response clearly using these sections if applicable:\n"
        "1. **Diagnosis/Overview**: What is likely happening.\n"
        "2. **Tools Required**: Specific tools needed for the job.\n"
        "3. **Step-by-Step Procedure**: Clear, safe, numbered instructions.\n"
        "4. **Safety Warnings**: Crucial safety precautions (e.g., high pressure, high voltage).\n"
        "Be concise, professional, and highly practical. Use South African context (e.g., mentioning ZAR, bakkies, or local conditions) if relevant."
    )
    
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg}
            ], 
            max_tokens=1000
        )
        return {"reply": resp.choices[0].message.content}
    except Exception as e: 
        return {"reply": f"Error: {str(e)}"}

@app.post("/api/problems/ai-procedure")
async def ai_problem_procedure(r: Request):
    d = await r.json()
    problem = d.get("problem", "")
    vehicle = d.get("vehicle", "")
    if not OPENAI_KEY: return {"reply": "AI not configured"}
    
    # LOCK THE AI INTO THE SPECIFIC PROBLEM USING SYSTEM PROMPT
    system_prompt = f"You are a master mechanic. You are diagnosing EXACTLY ONE specific issue: '{problem}'. Do NOT diagnose anything else. You must provide the diagnostic procedure strictly for this specific problem."
    
    prompt = f"Vehicle: {vehicle if vehicle else 'Unspecified'}. Problem: {problem}. " \
             f"Provide a detailed diagnostic guide formatted strictly with these sections:\n" \
             f"1. **Tools Needed**\n" \
             f"2. **Diagnostic Tests**: Step-by-step tests to identify the culprit (include expected results).\n" \
             f"3. **Identifying the Culprit**: How to confirm the exact cause based on test results.\n" \
             f"4. **Fixes & Repairs**: What needs to be fixed or replaced.\n" \
             f"Format with clear headings and bullet points."
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        resp = c.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ], 
            max_tokens=1000
        )
        return {"reply": resp.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

@app.post("/api/paint/match")
async def match_paint(r: Request):
    d = await r.json(); img = d.get("image_base64", "")
    if not img or not OPENAI_KEY: return {"success": False, "error": "AI not configured"}
    if img.startswith("data:"): img = img.split(",", 1)[1]
    prompt = "Expert paint tech. Respond ONLY JSON: {\"detected_colour\":{\"name\":\"N\",\"hex_code\":\"#RRGGBB\"},\"confidence\":\"High\",\"brand_codes\":[{\"brand\":\"B\",\"code\":\"C\"}],\"mixing_formula\":{\"base_colour\":\"D\",\"toners\":[{\"name\":\"T\",\"parts\":\"X\"}]}}"
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}]}], response_format={"type": "json_object"})
        return {"success": True, **json.loads(resp.choices[0].message.content)}
    except Exception as e: return {"success": False, "error": str(e)}

@app.post("/api/diagnose/photo")
async def diagnose_photo(r: Request):
    d = await r.json(); img = d.get("image_base64", "")
    if not img or not OPENAI_KEY: return {"success": False, "error": "AI not configured"}
    if img.startswith("data:"): img = img.split(",", 1)[1]
    prompt = "Expert mechanic. Respond ONLY JSON: {\"problem\":\"S\",\"description\":\"D\",\"confidence\":\"High\",\"possible_causes\":[\"C\"],\"diagnostic_steps\":[\"S\"]}"
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}]}], response_format={"type": "json_object"})
        return {"success": True, **json.loads(resp.choices[0].message.content)}
    except Exception as e: return {"success": False, "error": str(e)}

@app.post("/api/parts/identify")
async def identify_part(r: Request):
    d = await r.json()
    img_b64 = d.get("image_base64")
    query = d.get("query", "")
    
    if not OPENAI_KEY: return {"success": False, "error": "AI not configured"}
    
    try:
        c = openai.OpenAI(api_key=OPENAI_KEY)
        
        # A stricter system prompt to reduce hallucinations
        system_prompt = (
            "You are an expert auto parts specialist. Your knowledge is strictly based on OEM part numbers and automotive databases. "
            "Do NOT guess. If you are not sure about a part, state that you are unsure. "
            "Always format your answer clearly with these sections:\n"
            "### Part Name\n"
            "### Function\n"
            "### Vehicle Fitment (Make, Model, Years, Engine Code)\n"
            "### OEM Cross-References (if any)"
        )

        if img_b64:
            if img_b64.startswith("data:"): img_b64 = img_b64.split(",", 1)[1]
            prompt = f"Analyze this image of an auto part. Extract the part number if visible. Then, using your knowledge base, identify the part name, function, and vehicle fitment. If no part number is visible, describe the part based on its visual features."
            resp = c.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]}
                ],
                max_tokens=1000
            )
        elif query:
            prompt = f"Identify the auto part with the following description or part number: '{query}'. Provide its name, function, vehicle fitment, and cross-references."
            resp = c.chat.completions.create(
                model="gpt-4o", # Upgraded from mini to the full model for better accuracy
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
        else:
            return {"success": False, "error": "No image or query provided."}
            
        return {"success": True, "reply": resp.choices[0].message.content}
    except Exception as e:
        return {"success": False, "error": str(e)}
