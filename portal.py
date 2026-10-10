"""
Customer self-serve portal.

Public link: /portal/{phone}
  — looks up customer by phone number (any SA format)
  — shows all invoices, outstanding balance, service history
  — pay button on each unpaid invoice (uses payments.py)
  — book-a-service form (creates an appointment)

No login required. Phone number IS the identifier.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from datetime import datetime
import re
import uuid

router = APIRouter(tags=["portal"])


def _list(table):
    from main import store_list
    return store_list(table)


def _save(table, i, row):
    from main import store_save
    return store_save(table, i, row)


def _normalize(phone):
    if not phone:
        return ""
    d = re.sub(r"\D", "", str(phone))
    if d.startswith("27") and len(d) == 11:
        d = d[2:]
    if d.startswith("0") and len(d) == 10:
        d = d[1:]
    return d


def _matches(a, b):
    na, nb = _normalize(a), _normalize(b)
    return bool(na) and bool(nb) and na == nb


def _outstanding(inv):
    return max(0.0, float(inv.get("total", 0)) - float(inv.get("amount_paid", 0)))


def _is_overdue(inv):
    if _outstanding(inv) <= 0.005:
        return False
    due = inv.get("due_date")
    if not due:
        return False
    try:
        return datetime.strptime(due[:10], "%Y-%m-%d") < datetime.now()
    except Exception:
        return False


def _find_customer(phone):
    invoices = _list("invoices")
    customers = _list("customers")
    jobs = _list("jobs")

    cust = None
    for c in customers:
        if _matches(c.get("phone", ""), phone):
            cust = c
            break
    if not cust:
        for inv in invoices:
            if _matches(inv.get("phone", ""), phone):
                cust = {"name": inv.get("customer", ""),
                        "phone": inv.get("phone", ""),
                        "email": ""}
                break
    if not cust:
        return None

    name = (cust.get("name") or "").strip()

    my_invoices = [i for i in invoices
                   if _matches(i.get("phone", ""), phone)
                   or (i.get("customer", "").strip() == name
                       and not i.get("phone"))]

    my_jobs = [j for j in jobs
               if _matches(j.get("phone", ""), phone)
               or (j.get("customer", "").strip() == name
                   and not j.get("phone"))]

    return {"customer": cust, "invoices": my_invoices, "jobs": my_jobs}


def _summary(invoices):
    total_billed = sum(float(i.get("total", 0)) for i in invoices)
    total_paid = sum(float(i.get("amount_paid", 0)) for i in invoices)
    outstanding = sum(_outstanding(i) for i in invoices)
    overdue = sum(_outstanding(i) for i in invoices if _is_overdue(i))
    return {
        "total_billed": round(total_billed, 2),
        "total_paid": round(total_paid, 2),
        "outstanding": round(outstanding, 2),
        "overdue": round(overdue, 2),
        "count": len(invoices),
        "paid_count": sum(1 for i in invoices if i.get("paid")),
    }


# ═══════════════════════════════════════════════════════════════
# PUBLIC JSON API (portal JS fetches this)
# ═══════════════════════════════════════════════════════════════
@router.get("/api/portal/{phone}")
def portal_data(phone: str):
    found = _find_customer(phone)
    if not found:
        raise HTTPException(404, "No records for this phone number")

    cust = found["customer"]
    invs = sorted(found["invoices"],
                  key=lambda x: x.get("created", ""), reverse=True)
    jobs = sorted(found["jobs"],
                  key=lambda x: x.get("created", ""), reverse=True)

    from main import get_workshop_data
    w = get_workshop_data() or {}

    return {
        "customer": {
            "name": cust.get("name", ""),
            "phone": cust.get("phone", phone),
            "email": cust.get("email", ""),
        },
        "workshop": {
            "name": w.get("name", "Workshop"),
            "phone": w.get("phone", ""),
            "email": w.get("email", ""),
            "address": w.get("address", ""),
            "logo": w.get("logo", "RT"),
        },
        "summary": _summary(invs),
        "invoices": [{
            "id": i.get("id", ""),
            "created": (i.get("created") or "")[:10],
            "due_date": i.get("due_date", ""),
            "description": i.get("description", ""),
            "vehicle": i.get("vehicle", ""),
            "total": float(i.get("total", 0)),
            "paid": float(i.get("amount_paid", 0)),
            "outstanding": round(_outstanding(i), 2),
            "is_paid": bool(i.get("paid")),
            "is_overdue": _is_overdue(i),
        } for i in invs],
        "jobs": [{
            "id": j.get("id", ""),
            "created": (j.get("created") or "")[:10],
            "vehicle": j.get("vehicle", ""),
            "complaint": j.get("complaint", ""),
            "status": j.get("status", ""),
            "km": j.get("km", 0),
        } for j in jobs[:10]],
    }


@router.post("/api/portal/{phone}/book")
async def portal_book(phone: str, r: Request):
    d = await r.json()
    found = _find_customer(phone)
    if not found:
        raise HTTPException(404, "Unknown phone number")

    aid = str(uuid.uuid4())[:8]
    appt = {
        "id": aid,
        "customer": found["customer"].get("name", ""),
        "phone": found["customer"].get("phone", phone),
        "vehicle": (d.get("vehicle") or "").strip(),
        "service": (d.get("service") or "General service").strip(),
        "date": (d.get("date") or "").strip(),
        "time": (d.get("time") or "").strip(),
        "notes": (d.get("notes") or "").strip(),
        "source": "portal",
        "status": "pending",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    _save("appointments", aid, appt)

    try:
        from push_notify import send_push_to_all
        send_push_to_all(
            "New booking from portal",
            f"{appt['customer']} — {appt['vehicle']} on {appt['date']} {appt['time']}",
            "/",
        )
    except Exception:
        pass

    return {"success": True, "appointment": appt}


# ═══════════════════════════════════════════════════════════════
# PORTAL PAGE — mobile-first, no login
# ═══════════════════════════════════════════════════════════════
@router.get("/portal/{phone}", response_class=HTMLResponse)
def portal_page(phone: str):
    return HTMLResponse(_portal_html(phone))


def _portal_html(phone):
    return """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#111">
<title>My Account — RamsTech</title>
<style>
  *{box-sizing:border-box}
  body{
    font-family:-apple-system,"Segoe UI",Roboto,sans-serif;
    margin:0;padding:0;background:#f5f5f5;color:#1a1a1a;
    -webkit-font-smoothing:antialiased;
  }
  .wrap{max-width:560px;margin:0 auto;padding:20px 16px 60px}
  .hero{
    background:#111;color:#fff;border-radius:20px;
    padding:28px 24px;margin-bottom:20px;
  }
  .hero h1{margin:0 0 6px;font-size:22px;letter-spacing:-0.4px}
  .hero .sub{color:#aaa;font-size:13px;margin:0}
  .hero .total{
    margin-top:20px;padding-top:20px;border-top:1px solid #333;
  }
  .hero .total .lbl{
    font-size:11px;text-transform:uppercase;letter-spacing:1.2px;
    color:#888;font-weight:700;
  }
  .hero .total .val{
    font-size:36px;font-weight:900;letter-spacing:-1px;
    margin-top:4px;
  }
  .hero .total .val.overdue{color:#f87171}
  .hero .stats{
    display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;
    margin-top:20px;
  }
  .hero .stat{
    background:rgba(255,255,255,0.06);padding:10px 12px;
    border-radius:10px;
  }
  .hero .stat .lbl{
    font-size:10px;text-transform:uppercase;letter-spacing:0.8px;
    color:#888;font-weight:700;
  }
  .hero .stat .num{
    font-size:16px;font-weight:800;margin-top:4px;
  }
  h2{
    font-size:13px;text-transform:uppercase;letter-spacing:1.2px;
    color:#666;font-weight:800;margin:28px 0 12px;
  }
  .card{
    background:#fff;border-radius:14px;padding:18px;
    margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,0.04);
  }
  .inv-head{
    display:flex;justify-content:space-between;align-items:flex-start;
    margin-bottom:10px;
  }
  .inv-id{font-weight:800;font-size:15px}
  .inv-date{font-size:12px;color:#888;margin-top:2px}
  .inv-amt{
    text-align:right;font-weight:900;font-size:20px;
    letter-spacing:-0.5px;
  }
  .inv-amt.overdue{color:#dc2626}
  .inv-desc{font-size:13px;color:#555;margin:8px 0 12px;line-height:1.5}
  .badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
  .badge{
    display:inline-block;padding:3px 10px;border-radius:20px;
    font-size:10px;font-weight:800;letter-spacing:0.5px;
    text-transform:uppercase;
  }
  .badge.paid{background:#dcfce7;color:#166534}
  .badge.current{background:#dbeafe;color:#1e40af}
  .badge.overdue{background:#fecaca;color:#991b1b}
  .badge.due{background:#fef9c3;color:#854d0e}
  .btn{
    display:block;width:100%;text-align:center;padding:13px;
    background:#16a34a;color:#fff;border:none;border-radius:10px;
    font-weight:800;font-size:14px;cursor:pointer;
    text-decoration:none;letter-spacing:0.3px;
  }
  .btn:hover{background:#15803d}
  .btn.secondary{background:#111;color:#fff}
  .btn.secondary:hover{background:#000}
  .btn:disabled{background:#ccc;cursor:not-allowed}
  .paid-note{
    text-align:center;color:#16a34a;font-weight:700;font-size:13px;
    padding:12px;background:#f0fdf4;border-radius:10px;
  }
  .job{
    display:flex;justify-content:space-between;align-items:center;
    padding:12px 0;border-bottom:1px solid #f0f0f0;
  }
  .job:last-child{border-bottom:none}
  .job .v{font-weight:700;font-size:14px}
  .job .c{font-size:12px;color:#777;margin-top:2px}
  .job .s{
    font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;
    background:#f5f5f5;color:#555;text-transform:uppercase;
    letter-spacing:0.5px;
  }
  .job .s.Completed{background:#dcfce7;color:#166534}
  .job .s.Progress{background:#dbeafe;color:#1e40af}
  form label{
    display:block;font-size:12px;font-weight:700;
    text-transform:uppercase;letter-spacing:0.8px;
    color:#666;margin-bottom:6px;margin-top:14px;
  }
  form input,form select,form textarea{
    width:100%;padding:12px;border:1px solid #ddd;border-radius:10px;
    font-size:15px;font-family:inherit;background:#fafafa;
  }
  form input:focus,form select:focus,form textarea:focus{
    outline:none;border-color:#111;background:#fff;
  }
  .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .empty{
    text-align:center;padding:40px 20px;color:#888;font-size:14px;
  }
  .loading{
    text-align:center;padding:60px 20px;color:#888;
  }
  .footer{
    text-align:center;margin-top:40px;padding-top:20px;
    border-top:1px solid #eee;font-size:12px;color:#888;
  }
  .footer a{color:#111;font-weight:600;text-decoration:none}
  .success-msg{
    background:#f0fdf4;color:#166534;padding:14px;border-radius:10px;
    font-weight:700;font-size:13px;margin-bottom:12px;
  }
  @media print{
    body{background:#fff}
    .btn,.footer{display:none !important}
    .hero{background:#fff;color:#111;border:2px solid #111}
    .hero .sub,.hero .total .lbl,.hero .stat .lbl{color:#666}
    .hero .total{border-top-color:#eee}
    .card{box-shadow:none;border:1px solid #eee}
  }
</style></head>
<body>
<div class="wrap" id="root">
  <div class="loading">Loading your account…</div>
</div>

<script>
const PHONE = """ + repr(phone) + """;
const API = "/api/portal/" + encodeURIComponent(PHONE);

function money(n){
  return "R" + Number(n||0).toLocaleString("en-ZA",
    {minimumFractionDigits:2, maximumFractionDigits:2});
}
function esc(s){
  return String(s||"").replace(/[&<>"']/g, m => (
    {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
}

async function load(){
  try {
    const r = await fetch(API);
    if (!r.ok) {
      document.getElementById("root").innerHTML =
        '<div class="empty">No account found for this link.<br><br>' +
        'If this looks wrong, contact the workshop directly.</div>';
      return;
    }
    const d = await r.json();
    render(d);
  } catch(e) {
    document.getElementById("root").innerHTML =
      '<div class="empty">Could not load your account.<br>' +
      esc(e.message) + '</div>';
  }
}

function render(d){
  const w = d.workshop;
  const s = d.summary;
  const overdueClass = s.overdue > 0 ? "overdue" : "";

  let html = '';

  html += `
    <div class="hero">
      <h1>Hi ${esc(d.customer.name || "there")}</h1>
      <p class="sub">${esc(w.name || "Workshop")} · your account</p>

      <div class="total">
        <div class="lbl">Outstanding balance</div>
        <div class="val ${overdueClass}">${money(s.outstanding)}</div>
      </div>

      <div class="stats">
        <div class="stat"><div class="lbl">Invoices</div><div class="num">${s.count}</div></div>
        <div class="stat"><div class="lbl">Paid</div><div class="num">${s.paid_count}</div></div>
        <div class="stat"><div class="lbl">Overdue</div><div class="num">${money(s.overdue)}</div></div>
      </div>
    </div>`;

  if (s.outstanding > 0.005) {
    html += `<a class="btn" href="#invoices" onclick="document.getElementById('invoices').scrollIntoView({behavior:'smooth'});return false;">Pay outstanding balance →</a>`;
  }

  html += `<h2 id="invoices">Your invoices</h2>`;
  if (!d.invoices.length) {
    html += `<div class="card empty">No invoices yet.</div>`;
  } else {
    d.invoices.forEach(inv => {
      const cls = inv.is_paid ? "paid" : inv.is_overdue ? "overdue" : "current";
      const label = inv.is_paid ? "Paid" :
                    inv.is_overdue ? "Overdue" : "Due " + (inv.due_date || "");
      html += `
        <div class="card">
          <div class="inv-head">
            <div>
              <div class="inv-id">${esc(inv.id)}</div>
              <div class="inv-date">${esc(inv.created)}${inv.vehicle ? " · " + esc(inv.vehicle) : ""}</div>
            </div>
            <div class="inv-amt ${inv.is_overdue ? "overdue" : ""}">${money(inv.total)}</div>
          </div>
          ${inv.description ? `<div class="inv-desc">${esc(inv.description)}</div>` : ""}
          <div class="badges">
            <span class="badge ${cls}">${esc(label)}</span>
            ${inv.paid > 0 && !inv.is_paid
              ? `<span class="badge current">R${inv.paid.toFixed(2)} paid</span>` : ""}
          </div>
          ${inv.is_paid
            ? `<div class="paid-note">✓ Paid in full — thank you</div>`
            : `<a class="btn" href="/pay/${esc(inv.id)}">Pay ${money(inv.outstanding)} now</a>`}
        </div>`;
    });
  }

  if (d.jobs.length) {
    html += `<h2>Recent services</h2><div class="card">`;
    d.jobs.forEach(j => {
      const sc = (j.status || "").replace(" ", "");
      html += `
        <div class="job">
          <div>
            <div class="v">${esc(j.vehicle || "Vehicle")}</div>
            <div class="c">${esc(j.created)} · ${esc(j.complaint || "")}</div>
          </div>
          <div class="s ${sc}">${esc(j.status || "New")}</div>
        </div>`;
    });
    html += `</div>`;
  }

  html += `
    <h2>Book your next service</h2>
    <div class="card">
      <div id="book-msg"></div>
      <form onsubmit="return bookService(event)">
        <label>Vehicle</label>
        <input name="vehicle" placeholder="e.g. Toyota Hilux 2.8 GD-6" required>

        <label>Service needed</label>
        <select name="service">
          <option>General service</option>
          <option>Oil & filter change</option>
          <option>Brake inspection</option>
          <option>Diagnostic check</option>
          <option>Tyre fitment / rotation</option>
          <option>Aircon service</option>
          <option>Other (describe below)</option>
        </select>

        <div class="row">
          <div>
            <label>Preferred date</label>
            <input name="date" type="date" required>
          </div>
          <div>
            <label>Preferred time</label>
            <input name="time" type="time" required>
          </div>
        </div>

        <label>Anything else we should know?</label>
        <textarea name="notes" rows="3" placeholder="Sounds, warnings, recent issues…"></textarea>

        <button class="btn secondary" style="margin-top:16px" type="submit">Request booking</button>
      </form>
    </div>`;

  html += `
    <div class="footer">
      ${esc(w.name || "Workshop")}<br>
      ${w.phone ? esc(w.phone) + " · " : ""}${w.email ? esc(w.email) + "<br>" : ""}
      ${w.address ? esc(w.address) + "<br>" : ""}
      <br>
      Powered by <a href="/">RamsTech</a>
    </div>`;

  document.getElementById("root").innerHTML = html;
}

async function bookService(e){
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector("button[type=submit]");
  btn.disabled = true; btn.textContent = "Sending…";

  const data = {
    vehicle: form.vehicle.value,
    service: form.service.value,
    date: form.date.value,
    time: form.time.value,
    notes: form.notes.value,
  };

  try {
    const r = await fetch(API + "/book", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data),
    });
    const d = await r.json();
    if (d.success) {
      document.getElementById("book-msg").innerHTML =
        '<div class="success-msg">✓ Booking request sent! The workshop will confirm shortly.</div>';
      form.reset();
      btn.textContent = "Request booking";
      btn.disabled = false;
    } else {
      throw new Error(d.error || "Failed");
    }
  } catch(err) {
    document.getElementById("book-msg").innerHTML =
      '<div class="success-msg" style="background:#fef2f2;color:#991b1b">Error: ' +
      esc(err.message) + '</div>';
    btn.textContent = "Request booking";
    btn.disabled = false;
  }
  return false;
}

load();
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# INJECTED — Share portal button in the debtors modal
# ═══════════════════════════════════════════════════════════════
PORTAL_HTML = """
<script>
(function(){
  function injectShareBtn(){
    const actions = document.querySelector('.rt-db-actions');
    if (!actions || document.getElementById('rt-portal-share')) return false;
    const btn = document.createElement('button');
    btn.id = 'rt-portal-share';
    btn.textContent = '🔗 Share portal';
    btn.style.marginLeft = '8px';
    btn.onclick = async () => {
      const name = prompt('Customer name to share portal link with:');
      if (!name) return;
      try {
        const r = await fetch('/api/debtors');
        const d = await r.json();
        const cust = d.customers.find(c => c.customer === name);
        if (!cust) { alert('Customer not found in debtors list.'); return; }
        if (!cust.phone) { alert('No phone number on file for this customer.'); return; }
        const base = window.location.origin;
        const url = base + '/portal/' + encodeURIComponent(cust.phone);
        const msg = 'Hi ' + cust.customer + ', here is your account portal where you can view invoices and pay online:\\n\\n' + url;
        try {
          await navigator.clipboard.writeText(msg);
          alert('Message copied. Paste into WhatsApp:\\n\\n' + url);
        } catch(e) {
          prompt('Copy this link:', url);
        }
      } catch(e) { alert('Error: ' + e.message); }
    };
    actions.appendChild(btn);
    return true;
  }
  const obs = new MutationObserver(() => injectShareBtn());
  obs.observe(document.body, {childList: true, subtree: true});
  setTimeout(injectShareBtn, 1500);
})();
</script>
"""


def portal_status():
    return {"portal_enabled": True, "public_route": "/portal/{phone}"}
