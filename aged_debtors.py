"""
Aged Debtors Report
Shows who owes money, how much, and for how long.
Buckets: Current (0–30), 30d, 60d, 90d, 120d+
Reminders sent via whatsapp.py (auto-detects Clickatell / Twilio / Meta / console).
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import csv, io

# ── WhatsApp sender (fail-safe) ──────────────────────────────────
try:
    from whatsapp import send_whatsapp, provider_status
except Exception as _e:
    print(f"[aged_debtors] whatsapp unavailable: {_e}")

    def send_whatsapp(to, body, media_url=None):
        print(f"[whatsapp:fallback] → {to}\n{body}")
        return {"success": True, "provider": "fallback", "message_id": None,
                "error": None, "to": str(to or "")}

    def provider_status():
        return {"provider": "unavailable"}


router = APIRouter(tags=["debtors"])


# ── lazy bridge to main's storage layer (avoids circular import) ──
def _list(table):
    from main import store_list
    return store_list(table)


def _save(table, i, row):
    from main import store_save
    return store_save(table, i, row)


# ── ageing configuration ─────────────────────────────────────────
DEFAULT_TERMS_DAYS = 30

BUCKETS = [
    ("current", "Current",        -99999,  30),
    ("30",      "30 days",         31,     60),
    ("60",      "60 days",         61,     90),
    ("90",      "90 days",         91,    120),
    ("120",     "120+ days",      121,  99999),
]


def _parse_date(s):
    if not s:
        return None
    s = s.strip()
    for fmt, cut in (("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10),
                     ("%Y-%m-%dT%H:%M:%S", 19)):
        try:
            return datetime.strptime(s[:cut], fmt)
        except ValueError:
            continue
    return None


def _age_days(inv):
    """Days overdue relative to due date (or created + terms)."""
    due = _parse_date(inv.get("due_date"))
    if due:
        return (datetime.now() - due).days
    created = _parse_date(inv.get("created"))
    if not created:
        return 0
    terms = int(inv.get("payment_terms", DEFAULT_TERMS_DAYS))
    return (datetime.now() - (created + timedelta(days=terms))).days


def _bucket_for(days):
    for key, _, lo, hi in BUCKETS:
        if lo <= days <= hi:
            return key
    return "120"


def _outstanding(inv):
    return max(0.0, float(inv.get("total", 0)) - float(inv.get("amount_paid", 0)))


# ── main report ──────────────────────────────────────────────────
@router.get("/api/debtors")
def aged_debtors():
    invoices = _list("invoices")
    customers = {c.get("name", "").strip(): c for c in _list("customers")}

    report = {}
    grand_total = 0.0
    bucket_totals = {k: 0.0 for k, *_ in BUCKETS}

    for inv in invoices:
        outstanding = _outstanding(inv)
        if outstanding <= 0.005:
            continue

        name = (inv.get("customer") or "Unknown").strip() or "Unknown"
        days = _age_days(inv)
        bucket = _bucket_for(days)
        cust = customers.get(name, {})

        row = report.setdefault(name, {
            "customer": name,
            "phone": inv.get("phone", "") or cust.get("phone", ""),
            "email": cust.get("email", ""),
            "invoices": [],
            "total": 0.0,
            "oldest_days": 0,
            "last_reminder": None,
            **{k: 0.0 for k, *_ in BUCKETS},
        })

        row[bucket] += outstanding
        row["total"] += outstanding
        row["oldest_days"] = max(row["oldest_days"], days)
        row["invoices"].append({
            "id": inv.get("id", ""),
            "created": (inv.get("created") or "")[:10],
            "due_date": inv.get("due_date", ""),
            "description": inv.get("description", ""),
            "total": float(inv.get("total", 0)),
            "paid": float(inv.get("amount_paid", 0)),
            "outstanding": round(outstanding, 2),
            "days_overdue": days,
            "bucket": bucket,
            "reminders": inv.get("reminders", []),
        })

        # track most recent reminder across this customer's invoices
        for rem in inv.get("reminders", []):
            sent = rem.get("sent")
            if sent and (not row["last_reminder"] or sent > row["last_reminder"]):
                row["last_reminder"] = sent

        grand_total += outstanding
        bucket_totals[bucket] += outstanding

    rows = sorted(report.values(), key=lambda r: -r["oldest_days"])

    return {
        "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "grand_total": round(grand_total, 2),
        "customer_count": len(rows),
        "invoice_count": sum(len(r["invoices"]) for r in rows),
        "buckets": [
            {"key": k, "label": label, "total": round(bucket_totals[k], 2)}
            for k, label, *_ in BUCKETS
        ],
        "customers": rows,
    }


# ── statement for one customer ───────────────────────────────────
@router.get("/api/debtors/{customer_name}")
def customer_statement(customer_name: str):
    name = customer_name.strip()
    invoices = [i for i in _list("invoices")
                if (i.get("customer") or "").strip() == name]
    if not invoices:
        raise HTTPException(404, "Customer not found")

    rows = []
    for inv in invoices:
        rows.append({
            "id": inv.get("id", ""),
            "created": (inv.get("created") or "")[:10],
            "due_date": inv.get("due_date", ""),
            "description": inv.get("description", ""),
            "total": float(inv.get("total", 0)),
            "paid": float(inv.get("amount_paid", 0)),
            "outstanding": round(_outstanding(inv), 2),
            "days_overdue": _age_days(inv),
        })
    rows.sort(key=lambda r: r["created"])

    return {
        "customer": name,
        "invoices": rows,
        "total_billed": round(sum(r["total"] for r in rows), 2),
        "total_paid": round(sum(r["paid"] for r in rows), 2),
        "total_outstanding": round(sum(r["outstanding"] for r in rows), 2),
    }


# ── send reminder (WhatsApp / SMS / console) ─────────────────────
@router.post("/api/debtors/{customer_name}/remind")
async def send_reminder(customer_name: str, r: Request):
    try:
        d = await r.json()
    except Exception:
        d = {}
    channel = d.get("channel", "whatsapp")
    custom = (d.get("message") or "").strip()

    statement = customer_statement(customer_name)
    total = statement["total_outstanding"]
    oldest = max((inv["days_overdue"] for inv in statement["invoices"]), default=0)
    invoices = [inv for inv in _list("invoices")
                if (inv.get("customer") or "").strip() == customer_name.strip()
                and _outstanding(inv) > 0]

    # resolve phone from invoice or customer record
    phone = ""
    for inv in invoices:
        if inv.get("phone"):
            phone = inv["phone"]; break
    if not phone:
        for c in _list("customers"):
            if (c.get("name") or "").strip() == customer_name.strip():
                phone = c.get("phone", ""); break

    tone = "urgent" if oldest >= 90 else "firm" if oldest >= 60 else "friendly"
    msg = custom or _build_reminder(customer_name, total, oldest, tone)

    # ── SEND ─────────────────────────────────────────────────────
    if channel == "console":
        print(f"[debtors] console → {customer_name}: {msg}")
        send_result = {"success": True, "provider": "console",
                       "message_id": None, "error": None, "to": phone}
    elif not phone:
        print(f"[debtors] no phone for {customer_name}, logging only: {msg}")
        send_result = {"success": False, "provider": "none", "message_id": None,
                       "error": "No phone number on file", "to": ""}
    else:
        send_result = send_whatsapp(phone, msg)

    # ── LOG ──────────────────────────────────────────────────────
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for inv in invoices:
        rem = inv.get("reminders", [])
        rem.append({
            "sent": stamp,
            "channel": channel,
            "tone": tone,
            "provider": send_result.get("provider", ""),
            "message_id": send_result.get("message_id"),
            "success": send_result.get("success", False),
            "error": send_result.get("error"),
        })
        inv["reminders"] = rem
        _save("invoices", inv["id"], inv)

    return {
        "success": send_result.get("success", False),
        "channel": channel,
        "tone": tone,
        "message": msg,
        "total": total,
        "to": send_result.get("to", phone),
        "provider": send_result.get("provider", ""),
        "message_id": send_result.get("message_id"),
        "error": send_result.get("error"),
    }


def _build_reminder(name, total, days, tone):
    if tone == "urgent":
        return (f"Hi {name}, your account balance of R{total:,.2f} is now "
                f"{days} days overdue. Please arrange payment or contact us "
                f"to discuss a payment plan.")
    if tone == "firm":
        return (f"Hi {name}, your outstanding balance is R{total:,.2f} "
                f"({days} days). Please settle at your earliest convenience, "
                f"or reply to arrange a plan.")
    return (f"Hi {name}, friendly reminder: R{total:,.2f} outstanding on your "
            f"account. No rush — settle when convenient. Thank you!")


# ── WhatsApp status (which provider is active) ───────────────────
@router.get("/api/whatsapp/status")
def whatsapp_status():
    return provider_status()


# ── CSV export ───────────────────────────────────────────────────
@router.get("/api/debtors/export/csv")
def export_debtors_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Customer", "Invoice ID", "Date", "Due Date", "Description",
                "Total", "Paid", "Outstanding", "Days Overdue", "Bucket"])

    for inv in _list("invoices"):
        outstanding = _outstanding(inv)
        if outstanding <= 0.005:
            continue
        days = _age_days(inv)
        w.writerow([
            inv.get("customer", ""), inv.get("id", ""),
            (inv.get("created") or "")[:10], inv.get("due_date", ""),
            inv.get("description", ""),
            f"{float(inv.get('total', 0)):.2f}",
            f"{float(inv.get('amount_paid', 0)):.2f}",
            f"{outstanding:.2f}", days, _bucket_for(days),
        ])

    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename=aged_debtors_{datetime.now().strftime('%Y%m%d')}.csv"})


# ═══════════════════════════════════════════════════════════════
# UI PANEL — injected into home page before </body>
# ═══════════════════════════════════════════════════════════════
AGED_DEBTORS_HTML = """
<style>
  #rt-debtors-btn {
    position: fixed; bottom: 24px; left: 24px; z-index: 9998;
    background: #111; color: #fff; border: none; border-radius: 40px;
    padding: 12px 20px; font-weight: 700; font-size: 13px;
    cursor: pointer; box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  #rt-debtors-btn:hover { transform: translateY(-2px); }
  #rt-debtors-overlay {
    display: none; position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,0.5); padding: 24px; overflow-y: auto;
  }
  #rt-debtors-overlay.open { display: block; }
  .rt-debtors-modal {
    max-width: 1100px; margin: 0 auto; background: #fff;
    border-radius: 14px; padding: 28px 32px;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    color: #1a1a1a; position: relative;
  }
  .rt-debtors-modal h2 { margin: 0 0 6px; font-size: 24px; letter-spacing: -0.5px; }
  .rt-debtors-modal .rt-db-sub { color: #777; font-size: 13px; margin: 0 0 24px; }
  .rt-db-close {
    position: absolute; top: 20px; right: 24px; background: none;
    border: none; font-size: 24px; cursor: pointer; color: #999;
  }
  .rt-db-kpis {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px; margin-bottom: 24px;
  }
  .rt-db-kpi {
    border: 1px solid #e5e5e5; border-radius: 10px; padding: 16px;
    background: #fafafa;
  }
  .rt-db-kpi.danger { border-color: #dc2626; background: #fef2f2; }
  .rt-db-kpi .lbl {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: #888; font-weight: 700; margin-bottom: 6px;
  }
  .rt-db-kpi .val { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .rt-db-kpi.danger .val { color: #dc2626; }
  .rt-db-actions {
    display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;
  }
  .rt-db-actions button {
    padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600;
    cursor: pointer; border: 1px solid #ddd; background: #fff; color: #333;
  }
  .rt-db-actions button:hover { background: #f5f5f5; }
  .rt-db-actions button.primary { background: #111; color: #fff; border-color: #111; }
  .rt-db-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .rt-db-table th {
    text-align: left; padding: 10px 8px; border-bottom: 2px solid #111;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px;
    color: #666; font-weight: 700;
  }
  .rt-db-table th.num { text-align: right; }
  .rt-db-table td {
    padding: 12px 8px; border-bottom: 1px solid #eee; vertical-align: middle;
  }
  .rt-db-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .rt-db-table tr.cust-row { cursor: pointer; }
  .rt-db-table tr.cust-row:hover { background: #fafafa; }
  .rt-db-table tr.invoice-row { background: #f9f9f9; font-size: 12px; }
  .rt-db-table tr.invoice-row td { padding: 8px 8px 8px 32px; color: #555; }
  .rt-db-name { font-weight: 700; }
  .rt-db-phone { font-size: 12px; color: #888; }
  .rt-badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .rt-badge.current { background: #dcfce7; color: #166534; }
  .rt-badge.b30 { background: #fef9c3; color: #854d0e; }
  .rt-badge.b60 { background: #fed7aa; color: #9a3412; }
  .rt-badge.b90 { background: #fecaca; color: #991b1b; }
  .rt-badge.b120 { background: #7f1d1d; color: #fff; }
  .rt-db-remind {
    background: #16a34a; color: #fff; border: none; padding: 6px 12px;
    border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;
  }
  .rt-db-remind:hover { background: #15803d; }
  .rt-db-remind:disabled { background: #ccc; cursor: not-allowed; }
  .rt-db-empty { text-align: center; padding: 60px 20px; color: #888; }
  .rt-db-empty .big { font-size: 48px; margin-bottom: 12px; }
  @media print {
    #rt-debtors-btn, .rt-db-actions, .rt-db-close, .rt-db-remind { display: none !important; }
    #rt-debtors-overlay { position: static; background: #fff; padding: 0; }
    .rt-debtors-modal { box-shadow: none; max-width: 100%; padding: 0; }
  }
</style>

<button id="rt-debtors-btn" onclick="rtDebtorsOpen()">💰 Debtors</button>

<div id="rt-debtors-overlay" onclick="if(event.target===this)rtDebtorsClose()">
  <div class="rt-debtors-modal">
    <button class="rt-db-close" onclick="rtDebtorsClose()">×</button>
    <h2>Aged Debtors</h2>
    <p class="rt-db-sub" id="rt-db-asof">Loading…</p>

    <div class="rt-db-kpis" id="rt-db-kpis"></div>

    <div class="rt-db-actions">
      <button class="primary" onclick="rtDebtorsExport()">⬇ Export CSV</button>
      <button onclick="window.print()">🖨 Print</button>
      <button onclick="rtDebtorsLoad()">↻ Refresh</button>
    </div>

    <div id="rt-db-body"></div>
  </div>
</div>

<script>
(function(){
  const API = "/api/debtors";
  let DATA = null;

  window.rtDebtorsOpen = function(){
    document.getElementById("rt-debtors-overlay").classList.add("open");
    rtDebtorsLoad();
  };
  window.rtDebtorsClose = function(){
    document.getElementById("rt-debtors-overlay").classList.remove("open");
  };
  window.rtDebtorsLoad = async function(){
    document.getElementById("rt-db-body").innerHTML = "<p style='padding:40px;text-align:center;color:#888'>Loading…</p>";
    try {
      const r = await fetch(API);
      DATA = await r.json();
      render();
    } catch(e) {
      document.getElementById("rt-db-body").innerHTML =
        "<p style='color:#c00'>Error: " + e.message + "</p>";
    }
  };

  function money(n){ return "R" + Number(n||0).toLocaleString("en-ZA",{minimumFractionDigits:2, maximumFractionDigits:2}); }

  function esc(s){
    return String(s||"").replace(/[&<>"']/g, m => (
      {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  }

  function relTime(s){
    if (!s) return "";
    const t = new Date(s.replace(" ", "T"));
    const sec = Math.floor((Date.now() - t.getTime()) / 1000);
    if (sec < 60) return "just now";
    if (sec < 3600) return Math.floor(sec/60) + "m ago";
    if (sec < 86400) return Math.floor(sec/3600) + "h ago";
    if (sec < 604800) return Math.floor(sec/86400) + "d ago";
    return s.slice(0, 10);
  }

  function render(){
    if (!DATA) return;
    document.getElementById("rt-db-asof").textContent =
      "As of " + DATA.as_of + " · " + DATA.customer_count +
      " customers · " + DATA.invoice_count + " invoices";

    // KPIs
    const kpis = document.getElementById("rt-db-kpis");
    let khtml = `<div class="rt-db-kpi"><div class="lbl">Total Outstanding</div>
      <div class="val">${money(DATA.grand_total)}</div></div>`;
    DATA.buckets.forEach(b => {
      if (b.key === "current") return; // skip current in KPI row, shown in table
      const danger = (b.key === "90" || b.key === "120") && b.total > 0;
      khtml += `<div class="rt-db-kpi ${danger?'danger':''}">
        <div class="lbl">${b.label}</div>
        <div class="val">${money(b.total)}</div></div>`;
    });
    kpis.innerHTML = khtml;

    // Body
    const body = document.getElementById("rt-db-body");
    if (!DATA.customers.length){
      body.innerHTML = `<div class="rt-db-empty"><div class="big">🎉</div>
        <div>No outstanding debtors. Everyone's paid up.</div></div>`;
      return;
    }

    let html = `<table class="rt-db-table">
      <thead><tr>
        <th>Customer</th>
        <th class="num">Current</th>
        <th class="num">30d</th>
        <th class="num">60d</th>
        <th class="num">90d</th>
        <th class="num">120+</th>
        <th class="num">Total</th>
        <th></th>
      </tr></thead><tbody>`;

    DATA.customers.forEach((c, i) => {
      html += `<tr class="cust-row" onclick="rtDebtorsToggle(${i})">
        <td>
          <div class="rt-db-name">${esc(c.customer)}</div>
          <div class="rt-db-phone">
            ${esc(c.phone||"")}
            ${c.oldest_days > 0 ? ' · <span style="color:#c00">'+c.oldest_days+'d overdue</span>' : ''}
            ${c.last_reminder
              ? ' · <span style="color:#16a34a" title="Last reminder sent">🔔 '+relTime(c.last_reminder)+'</span>'
              : ' · <span style="color:#aaa">no reminders sent</span>'}
          </div>
        </td>
        <td class="num">${c.current>0?money(c.current):"—"}</td>
        <td class="num">${c["30"]>0?money(c["30"]):"—"}</td>
        <td class="num">${c["60"]>0?money(c["60"]):"—"}</td>
        <td class="num">${c["90"]>0?money(c["90"]):"—"}</td>
        <td class="num">${c["120"]>0?money(c["120"]):"—"}</td>
        <td class="num"><strong>${money(c.total)}</strong></td>
        <td><button class="rt-db-remind" onclick="event.stopPropagation();rtDebtorsRemind('${esc(c.customer)}',this)">Remind</button></td>
      </tr>
      <tr class="invoice-row" id="rt-db-inv-${i}" style="display:none">
        <td colspan="8">
          ${c.invoices.map(inv => `
            <div style="padding:6px 0;border-bottom:1px dashed #eee">
              <span class="rt-badge ${inv.bucket==='current'?'current':'b'+inv.bucket}">${inv.days_overdue>0?inv.days_overdue+'d':'Current'}</span>
              <strong style="margin-left:8px">${inv.id}</strong>
              · ${inv.created}${inv.due_date?' (due '+inv.due_date+')':''} · ${esc(inv.description||"—")}
              · Outstanding <strong>${money(inv.outstanding)}</strong>
              ${inv.reminders && inv.reminders.length ? ' · 🔔 '+inv.reminders.length+' reminder(s)' : ''}
            </div>
          `).join("")}
        </td>
      </tr>`;
    });

    html += `</tbody></table>`;
    body.innerHTML = html;
  }

  window.rtDebtorsToggle = function(i){
    const row = document.getElementById("rt-db-inv-" + i);
    if (row) row.style.display = row.style.display === "none" ? "table-row" : "none";
  };

  window.rtDebtorsRemind = async function(name, btn){
    btn.disabled = true; btn.textContent = "Sending…";
    try {
      const r = await fetch(API + "/" + encodeURIComponent(name) + "/remind",
        {method:"POST", headers:{"Content-Type":"application/json"}, body:"{}"});
      const d = await r.json();
      if (d.success) {
        btn.textContent = "✓ Sent";
        btn.style.background = "#15803d";
      } else {
        btn.textContent = "✗ " + (d.error||"Failed").slice(0, 20);
        btn.style.background = "#dc2626";
      }
      setTimeout(() => { rtDebtorsLoad(); }, 900);
      console.log("Reminder:", d);
    } catch(e) {
      btn.textContent = "Error"; btn.disabled = false;
    }
  };

  window.rtDebtorsExport = function(){
    window.location.href = API + "/export/csv";
  };
})();
</script>
"""
