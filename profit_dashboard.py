"""
Profit dashboard — where the money actually comes from.

Answers:
  • Which jobs made money, which lost money?
  • Which technicians are most profitable per hour?
  • Which service types have the best margins?
  • What's the average margin across the workshop?

Calculation model:
  Revenue (ex VAT) = job.subtotal
  Labour cost      = labour_hours × tech hourly rate (fallback: R150/hr)
  Parts cost       = parts_cost × parts_cost_ratio (default 0.65)
  Gross profit     = subtotal − labour cost − parts cost
  Margin %         = gross profit / subtotal × 100

Configurable via workshop record key "profit_settings":
  tech_default_rate   int   default 150
  parts_cost_ratio    float default 0.65
  overhead_per_hour   int   default 0
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import csv, io, re

router = APIRouter(tags=["profit"])


def _list(table):
    from main import store_list
    return store_list(table)


DEFAULT_SETTINGS = {
    "tech_default_rate": 150,
    "parts_cost_ratio": 0.65,
    "overhead_per_hour": 0,
}


def _get_settings():
    from main import get_workshop_data
    w = get_workshop_data() or {}
    s = w.get("profit_settings") or {}
    merged = dict(DEFAULT_SETTINGS)
    merged.update(s)
    return merged


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


def _norm_name(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _find_tech_rate(assigned, staff_list, default):
    """Match assigned_to against staff by fuzzy name."""
    if not assigned:
        return default, None
    target = _norm_name(assigned)
    for s in staff_list:
        sname = _norm_name(s.get("name", ""))
        if sname and (sname == target
                      or sname in target
                      or target in sname):
            return float(s.get("hourly_rate", default) or default), s
    return default, None


def _job_profit(job, staff_list, settings):
    """Return profit breakdown for a single job."""
    subtotal = float(job.get("subtotal", 0) or 0)
    # fallback if subtotal not set but total is
    if subtotal <= 0 and job.get("total"):
        subtotal = float(job["total"]) / 1.15  # strip VAT

    labour_hours = float(job.get("labour_hours", 0) or 0)
    parts_cost = float(job.get("parts_cost", 0) or 0)

    tech_rate, tech = _find_tech_rate(
        job.get("assigned_to", ""),
        staff_list,
        settings["tech_default_rate"],
    )
    labour_cost = labour_hours * tech_rate
    parts_real_cost = parts_cost * settings["parts_cost_ratio"]
    overhead = labour_hours * settings["overhead_per_hour"]

    total_cost = labour_cost + parts_real_cost + overhead
    profit = subtotal - total_cost
    margin = (profit / subtotal * 100) if subtotal > 0 else 0

    return {
        "id": job.get("id", ""),
        "created": (job.get("created") or "")[:10],
        "customer": job.get("customer", ""),
        "vehicle": job.get("vehicle", ""),
        "complaint": job.get("complaint", ""),
        "status": job.get("status", ""),
        "assigned_to": job.get("assigned_to", "") or "Unassigned",
        "tech_rate": tech_rate,
        "labour_hours": round(labour_hours, 2),
        "labour_cost": round(labour_cost, 2),
        "parts_charged": round(parts_cost, 2),
        "parts_real_cost": round(parts_real_cost, 2),
        "overhead": round(overhead, 2),
        "revenue": round(subtotal, 2),
        "total_cost": round(total_cost, 2),
        "profit": round(profit, 2),
        "margin": round(margin, 1),
        "is_loss": profit < 0,
    }


def _in_range(date_str, from_date, to_date):
    if not date_str:
        return True
    if from_date and date_str < from_date:
        return False
    if to_date and date_str > to_date:
        return False
    return True


# ═══════════════════════════════════════════════════════════════
# CORE — collect + aggregate
# ═══════════════════════════════════════════════════════════════
def _gather(from_date=None, to_date=None):
    jobs = _list("jobs")
    staff = _list("staff")
    settings = _get_settings()

    items = []
    for j in jobs:
        d = (j.get("created") or "")[:10]
        if not _in_range(d, from_date, to_date):
            continue
        # only count completed jobs for profit (or any job with cost data)
        if j.get("status") != "Completed" and not j.get("subtotal"):
            continue
        items.append(_job_profit(j, staff, settings))

    return items, settings


def _aggregate(items):
    if not items:
        return {
            "revenue": 0, "cost": 0, "profit": 0, "margin": 0,
            "job_count": 0, "avg_profit_per_job": 0,
            "avg_margin": 0, "loss_jobs": 0, "best_job": None,
            "worst_job": None, "labour_hours": 0,
        }

    rev = sum(i["revenue"] for i in items)
    cost = sum(i["total_cost"] for i in items)
    profit = rev - cost
    hours = sum(i["labour_hours"] for i in items)
    loss_jobs = sum(1 for i in items if i["is_loss"])
    sorted_by_profit = sorted(items, key=lambda x: x["profit"], reverse=True)

    return {
        "revenue": round(rev, 2),
        "cost": round(cost, 2),
        "profit": round(profit, 2),
        "margin": round((profit / rev * 100) if rev else 0, 1),
        "job_count": len(items),
        "avg_profit_per_job": round(profit / len(items), 2) if items else 0,
        "avg_margin": round(
            sum(i["margin"] for i in items) / len(items), 1
        ) if items else 0,
        "loss_jobs": loss_jobs,
        "labour_hours": round(hours, 1),
        "best_job": sorted_by_profit[0] if sorted_by_profit else None,
        "worst_job": sorted_by_profit[-1] if sorted_by_profit else None,
    }


def _by_tech(items):
    groups = {}
    for i in items:
        key = i["assigned_to"] or "Unassigned"
        g = groups.setdefault(key, {
            "name": key, "jobs": 0, "revenue": 0, "cost": 0,
            "profit": 0, "hours": 0, "loss_jobs": 0,
        })
        g["jobs"] += 1
        g["revenue"] += i["revenue"]
        g["cost"] += i["total_cost"]
        g["profit"] += i["profit"]
        g["hours"] += i["labour_hours"]
        if i["is_loss"]:
            g["loss_jobs"] += 1

    rows = []
    for g in groups.values():
        margin = (g["profit"] / g["revenue"] * 100) if g["revenue"] else 0
        per_hour = (g["profit"] / g["hours"]) if g["hours"] else 0
        rows.append({
            "name": g["name"],
            "jobs": g["jobs"],
            "hours": round(g["hours"], 1),
            "revenue": round(g["revenue"], 2),
            "profit": round(g["profit"], 2),
            "margin": round(margin, 1),
            "profit_per_hour": round(per_hour, 2),
            "loss_jobs": g["loss_jobs"],
        })
    return sorted(rows, key=lambda x: -x["profit"])


def _by_service(items):
    groups = {}
    for i in items:
        raw = (i["complaint"] or "Unspecified").strip()
        key = raw[:40] if raw else "Unspecified"
        g = groups.setdefault(key, {
            "name": key, "jobs": 0, "revenue": 0, "profit": 0,
        })
        g["jobs"] += 1
        g["revenue"] += i["revenue"]
        g["profit"] += i["profit"]

    rows = []
    for g in groups.values():
        margin = (g["profit"] / g["revenue"] * 100) if g["revenue"] else 0
        rows.append({
            "name": g["name"],
            "jobs": g["jobs"],
            "revenue": round(g["revenue"], 2),
            "profit": round(g["profit"], 2),
            "margin": round(margin, 1),
            "avg_profit": round(g["profit"] / g["jobs"], 2) if g["jobs"] else 0,
        })
    return sorted(rows, key=lambda x: -x["profit"])


def _by_day(items, days=30):
    """Profit trend over last N days."""
    today = datetime.now().date()
    labels = []
    revenue = []
    profit = []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(d[5:])  # "MM-DD"
        day_items = [x for x in items if x["created"] == d]
        revenue.append(round(sum(x["revenue"] for x in day_items), 2))
        profit.append(round(sum(x["profit"] for x in day_items), 2))
    return {"labels": labels, "revenue": revenue, "profit": profit}


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════
@router.get("/api/profit/overview")
def profit_overview(from_date: str = None, to_date: str = None,
                    days: int = 30):
    items, settings = _gather(from_date, to_date)
    return {
        "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "range": {"from": from_date, "to": to_date},
        "settings": settings,
        "summary": _aggregate(items),
        "by_tech": _by_tech(items),
        "by_service": _by_service(items),
        "trend": _by_day(items, days=min(max(days, 7), 90)),
    }


@router.get("/api/profit/jobs")
def profit_jobs(from_date: str = None, to_date: str = None):
    items, _ = _gather(from_date, to_date)
    items.sort(key=lambda x: x["profit"])
    return {"count": len(items), "jobs": items}


@router.get("/api/profit/settings")
def get_profit_settings():
    return _get_settings()


@router.post("/api/profit/settings")
async def save_profit_settings(r: Request):
    from main import get_workshop_data, save_workshop_data
    d = await r.json()
    w = dict(get_workshop_data() or {})
    s = dict(w.get("profit_settings") or {})
    for k in ("tech_default_rate", "parts_cost_ratio", "overhead_per_hour"):
        if k in d:
            s[k] = d[k]
    w["profit_settings"] = s
    save_workshop_data(w)
    return {"success": True, "settings": _get_settings()}


@router.get("/api/profit/export/csv")
def export_profit_csv(from_date: str = None, to_date: str = None):
    items, _ = _gather(from_date, to_date)
    items.sort(key=lambda x: x["profit"])

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Job ID", "Date", "Customer", "Vehicle", "Assigned",
                "Status", "Hours", "Labour Cost", "Parts Cost",
                "Revenue", "Total Cost", "Profit", "Margin %", "Loss?"])
    for i in items:
        w.writerow([
            i["id"], i["created"], i["customer"], i["vehicle"],
            i["assigned_to"], i["status"], i["labour_hours"],
            f"{i['labour_cost']:.2f}", f"{i['parts_real_cost']:.2f}",
            f"{i['revenue']:.2f}", f"{i['total_cost']:.2f}",
            f"{i['profit']:.2f}", f"{i['margin']:.1f}",
            "YES" if i["is_loss"] else "",
        ])
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename=profit_{datetime.now().strftime('%Y%m%d')}.csv"})


# ═══════════════════════════════════════════════════════════════
# UI PANEL
# ═══════════════════════════════════════════════════════════════
PROFIT_DASHBOARD_HTML = """
<style>
  #rt-profit-btn {
    position: fixed; bottom: 24px; left: 200px; z-index: 9998;
    background: #111; color: #fff; border: none; border-radius: 40px;
    padding: 12px 20px; font-weight: 700; font-size: 13px;
    cursor: pointer; box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  #rt-profit-btn:hover { transform: translateY(-2px); }
  #rt-profit-overlay {
    display: none; position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,0.55); padding: 24px; overflow-y: auto;
  }
  #rt-profit-overlay.open { display: block; }
  .rt-profit-modal {
    max-width: 1200px; margin: 0 auto; background: #fff;
    border-radius: 14px; padding: 28px 32px;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    color: #1a1a1a; position: relative;
  }
  .rt-profit-modal h2 { margin: 0 0 6px; font-size: 24px; letter-spacing: -0.5px; }
  .rt-profit-modal .rt-pf-sub { color: #777; font-size: 13px; margin: 0 0 24px; }
  .rt-pf-close {
    position: absolute; top: 20px; right: 24px; background: none;
    border: none; font-size: 24px; cursor: pointer; color: #999;
  }
  .rt-pf-filters {
    display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
    margin-bottom: 20px; padding: 14px 16px; background: #fafafa;
    border-radius: 10px;
  }
  .rt-pf-filters label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    font-weight: 700; color: #666;
  }
  .rt-pf-filters input[type=date] {
    padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px;
    font-size: 13px;
  }
  .rt-pf-filters button {
    padding: 6px 12px; border-radius: 6px; font-size: 13px;
    font-weight: 600; cursor: pointer; border: 1px solid #ddd;
    background: #fff;
  }
  .rt-pf-filters button.primary { background: #111; color: #fff; border-color: #111; }
  .rt-pf-kpis {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px; margin-bottom: 24px;
  }
  .rt-pf-kpi {
    border: 1px solid #e5e5e5; border-radius: 10px; padding: 16px;
    background: #fafafa;
  }
  .rt-pf-kpi.good { border-color: #16a34a; background: #f0fdf4; }
  .rt-pf-kpi.bad { border-color: #dc2626; background: #fef2f2; }
  .rt-pf-kpi .lbl {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: #888; font-weight: 700; margin-bottom: 6px;
  }
  .rt-pf-kpi .val {
    font-size: 22px; font-weight: 800; letter-spacing: -0.5px;
  }
  .rt-pf-kpi.good .val { color: #16a34a; }
  .rt-pf-kpi.bad .val { color: #dc2626; }
  .rt-pf-kpi .sub { font-size: 11px; color: #888; margin-top: 4px; }

  .rt-pf-section-title {
    font-size: 15px; font-weight: 800; letter-spacing: -0.2px;
    margin: 28px 0 12px; display: flex; align-items: center;
    gap: 8px;
  }
  .rt-pf-section-title .badge {
    background: #111; color: #fff; font-size: 10px; font-weight: 800;
    padding: 3px 8px; border-radius: 20px; letter-spacing: 0.5px;
  }

  .rt-pf-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .rt-pf-table th {
    text-align: left; padding: 10px 8px; border-bottom: 2px solid #111;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px;
    color: #666; font-weight: 700;
  }
  .rt-pf-table th.num { text-align: right; }
  .rt-pf-table td {
    padding: 10px 8px; border-bottom: 1px solid #eee; vertical-align: middle;
  }
  .rt-pf-table td.num {
    text-align: right; font-variant-numeric: tabular-nums;
  }
  .rt-pf-table tr:hover { background: #fafafa; }
  .rt-pf-table tr.loss td { background: #fef2f2; }
  .rt-pf-table tr.loss:hover td { background: #fee2e2; }
  .rt-pf-positive { color: #16a34a; font-weight: 700; }
  .rt-pf-negative { color: #dc2626; font-weight: 700; }
  .rt-pf-margin {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 11px; font-weight: 800;
  }
  .rt-pf-margin.high { background: #dcfce7; color: #166534; }
  .rt-pf-margin.mid  { background: #fef9c3; color: #854d0e; }
  .rt-pf-margin.low  { background: #fecaca; color: #991b1b; }
  .rt-pf-bar-wrap {
    display: flex; align-items: center; gap: 8px;
  }
  .rt-pf-bar {
    height: 6px; border-radius: 4px; background: #16a34a;
    min-width: 2px;
  }
  .rt-pf-bar.neg { background: #dc2626; }

  .rt-pf-chart {
    display: flex; align-items: flex-end; gap: 2px;
    height: 100px; padding: 10px 0; border-bottom: 1px solid #eee;
  }
  .rt-pf-chart .bar {
    flex: 1; background: #111; border-radius: 2px 2px 0 0;
    min-height: 2px; position: relative;
  }
  .rt-pf-chart .bar.profit { background: #16a34a; }
  .rt-pf-chart-legend {
    display: flex; gap: 20px; font-size: 11px; color: #666;
    margin-top: 8px; font-weight: 600;
  }
  .rt-pf-chart-legend .dot {
    display: inline-block; width: 10px; height: 10px; border-radius: 2px;
    margin-right: 4px; vertical-align: middle;
  }
  .rt-pf-two-col {
    display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
  }
  @media (max-width: 800px) {
    .rt-pf-two-col { grid-template-columns: 1fr; }
  }
  .rt-pf-empty {
    text-align: center; padding: 40px 20px; color: #888; font-size: 14px;
  }
  .rt-pf-info {
    background: #f0f9ff; border-left: 4px solid #0284c7;
    padding: 12px 16px; border-radius: 8px; font-size: 13px;
    color: #075985; margin-bottom: 20px;
  }

  @media print {
    #rt-profit-btn, .rt-pf-filters, .rt-pf-close,
    .rt-pf-actions { display: none !important; }
    #rt-profit-overlay { position: static; background: #fff; padding: 0; }
    .rt-profit-modal { box-shadow: none; max-width: 100%; padding: 0; }
    .rt-pf-kpi { border: 1px solid #ddd !important; background: #fff !important; }
  }
</style>

<button id="rt-profit-btn" onclick="rtProfitOpen()">📊 Profit</button>

<div id="rt-profit-overlay" onclick="if(event.target===this)rtProfitClose()">
  <div class="rt-profit-modal">
    <button class="rt-pf-close" onclick="rtProfitClose()">×</button>
    <h2>Profit Dashboard</h2>
    <p class="rt-pf-sub" id="rt-pf-asof">Loading…</p>

    <div class="rt-pf-filters">
      <label>From</label>
      <input type="date" id="rt-pf-from">
      <label>To</label>
      <input type="date" id="rt-pf-to">
      <button class="primary" onclick="rtProfitLoad()">Apply</button>
      <button onclick="rtProfitPreset(7)">7d</button>
      <button onclick="rtProfitPreset(30)">30d</button>
      <button onclick="rtProfitPreset(90)">90d</button>
      <button onclick="rtProfitPreset(0)">All time</button>
      <button onclick="rtProfitExport()">⬇ CSV</button>
      <button onclick="window.print()">🖨 Print</button>
      <button onclick="rtProfitSettings()" style="margin-left:auto">⚙ Settings</button>
    </div>

    <div id="rt-pf-body">
      <div class="rt-pf-empty">Loading…</div>
    </div>
  </div>
</div>

<script>
(function(){
  let DATA = null;

  window.rtProfitOpen = function(){
    document.getElementById("rt-profit-overlay").classList.add("open");
    if (!document.getElementById("rt-pf-from").value) rtProfitPreset(30);
    else rtProfitLoad();
  };
  window.rtProfitClose = function(){
    document.getElementById("rt-profit-overlay").classList.remove("open");
  };

  window.rtProfitPreset = function(days){
    const to = document.getElementById("rt-pf-to");
    const from = document.getElementById("rt-pf-from");
    if (days === 0) {
      from.value = ""; to.value = "";
    } else {
      const d = new Date();
      const f = new Date();
      f.setDate(f.getDate() - days);
      from.value = f.toISOString().slice(0,10);
      to.value = d.toISOString().slice(0,10);
    }
    rtProfitLoad();
  };

  window.rtProfitLoad = async function(){
    const from = document.getElementById("rt-pf-from").value;
    const to = document.getElementById("rt-pf-to").value;
    const q = new URLSearchParams();
    if (from) q.set("from_date", from);
    if (to) q.set("to_date", to);
    document.getElementById("rt-pf-body").innerHTML =
      "<div class='rt-pf-empty'>Crunching numbers…</div>";
    try {
      const r = await fetch("/api/profit/overview?" + q.toString());
      DATA = await r.json();
      render();
    } catch(e) {
      document.getElementById("rt-pf-body").innerHTML =
        "<div class='rt-pf-empty' style='color:#c00'>Error: " + e.message + "</div>";
    }
  };

  function money(n){
    const v = Number(n||0);
    const sign = v < 0 ? "−" : "";
    return sign + "R" + Math.abs(v).toLocaleString("en-ZA",
      {minimumFractionDigits:2, maximumFractionDigits:2});
  }
  function money0(n){
    const v = Number(n||0);
    const sign = v < 0 ? "−" : "";
    return sign + "R" + Math.abs(v).toLocaleString("en-ZA",
      {minimumFractionDigits:0, maximumFractionDigits:0});
  }
  function esc(s){
    return String(s||"").replace(/[&<>"']/g, m => (
      {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  }
  function marginClass(m){
    if (m >= 30) return "high";
    if (m >= 15) return "mid";
    return "low";
  }

  function render(){
    if (!DATA) return;
    const s = DATA.summary;
    document.getElementById("rt-pf-asof").textContent =
      "As of " + DATA.as_of +
      (DATA.range.from || DATA.range.to
        ? " · " + (DATA.range.from || "start") + " → " + (DATA.range.to || "today")
        : " · all time") +
      " · " + s.job_count + " completed jobs";

    let html = "";

    // SETTINGS INFO
    html += `<div class="rt-pf-info">
      Cost model: labour @ R${DATA.settings.tech_default_rate}/hr default ·
      parts cost ratio ${(DATA.settings.parts_cost_ratio*100).toFixed(0)}% of charge ·
      overhead R${DATA.settings.overhead_per_hour}/hr ·
      <a href="#" onclick="rtProfitSettings();return false" style="color:#0284c7">change</a>
    </div>`;

    // KPIs
    const profitClass = s.profit >= 0 ? "good" : "bad";
    html += `<div class="rt-pf-kpis">
      <div class="rt-pf-kpi"><div class="lbl">Revenue (ex VAT)</div>
        <div class="val">${money0(s.revenue)}</div>
        <div class="sub">${s.job_count} jobs</div></div>

      <div class="rt-pf-kpi"><div class="lbl">Total Cost</div>
        <div class="val">${money0(s.cost)}</div>
        <div class="sub">labour + parts + overhead</div></div>

      <div class="rt-pf-kpi ${profitClass}"><div class="lbl">Gross Profit</div>
        <div class="val">${money0(s.profit)}</div>
        <div class="sub">${s.margin}% margin</div></div>

      <div class="rt-pf-kpi"><div class="lbl">Avg Profit / Job</div>
        <div class="val">${money0(s.avg_profit_per_job)}</div>
        <div class="sub">${s.avg_margin}% avg margin</div></div>

      <div class="rt-pf-kpi ${s.loss_jobs > 0 ? 'bad' : ''}">
        <div class="lbl">Loss-making Jobs</div>
        <div class="val">${s.loss_jobs}</div>
        <div class="sub">${s.job_count ? Math.round(s.loss_jobs/s.job_count*100) : 0}% of jobs</div>
      </div>

      <div class="rt-pf-kpi"><div class="lbl">Labour Hours</div>
        <div class="val">${s.labour_hours}</div>
        <div class="sub">${s.labour_hours > 0 ? money0(s.profit/s.labour_hours) + "/hr" : "—"}</div>
      </div>
    </div>`;

    if (!s.job_count) {
      html += `<div class="rt-pf-empty">No completed jobs in this range.</div>`;
      document.getElementById("rt-pf-body").innerHTML = html;
      return;
    }

    // TREND CHART
    const t = DATA.trend;
    const maxRev = Math.max(...t.revenue, 1);
    const maxProf = Math.max(...t.profit.map(Math.abs), 1);
    const maxVal = Math.max(maxRev, maxProf);
    html += `<div class="rt-pf-section-title">Profit trend <span class="badge">${t.labels.length} days</span></div>`;
    html += `<div class="rt-pf-chart">`;
    for (let i = 0; i < t.labels.length; i++) {
      const revH = Math.max(2, (t.revenue[i] / maxVal) * 100);
      const profH = Math.max(2, (Math.abs(t.profit[i]) / maxVal) * 100);
      const profClass = t.profit[i] < 0 ? " neg" : " profit";
      html += `<div class="bar" style="height:${revH}%"
        title="${t.labels[i]} · Revenue ${money(t.revenue[i])}"></div>`;
    }
    html += `</div>`;
    html += `<div class="rt-pf-chart-legend">
      <span><span class="dot" style="background:#111"></span>Daily revenue</span>
    </div>`;

    // TWO COLUMN: TECH + SERVICE
    html += `<div class="rt-pf-two-col">`;

    // BY TECH
    html += `<div>
      <div class="rt-pf-section-title">Profit by technician</div>
      <table class="rt-pf-table">
        <thead><tr>
          <th>Technician</th>
          <th class="num">Jobs</th>
          <th class="num">Hours</th>
          <th class="num">Profit</th>
          <th class="num">R/hr</th>
          <th class="num">Margin</th>
        </tr></thead><tbody>`;
    DATA.by_tech.forEach(t => {
      html += `<tr>
        <td><strong>${esc(t.name)}</strong>${t.loss_jobs > 0 ? ' <span style="color:#dc2626;font-size:11px">(' + t.loss_jobs + ' loss)</span>' : ''}</td>
        <td class="num">${t.jobs}</td>
        <td class="num">${t.hours}</td>
        <td class="num ${t.profit >= 0 ? 'rt-pf-positive' : 'rt-pf-negative'}">${money(t.profit)}</td>
        <td class="num">${t.hours ? money(t.profit_per_hour) : "—"}</td>
        <td class="num"><span class="rt-pf-margin ${marginClass(t.margin)}">${t.margin}%</span></td>
      </tr>`;
    });
    html += `</tbody></table></div>`;

    // BY SERVICE
    html += `<div>
      <div class="rt-pf-section-title">Profit by service type</div>
      <table class="rt-pf-table">
        <thead><tr>
          <th>Service</th>
          <th class="num">Jobs</th>
          <th class="num">Revenue</th>
          <th class="num">Profit</th>
          <th class="num">Avg</th>
          <th class="num">Margin</th>
        </tr></thead><tbody>`;
    DATA.by_service.slice(0, 12).forEach(t => {
      html += `<tr>
        <td><strong>${esc(t.name)}</strong></td>
        <td class="num">${t.jobs}</td>
        <td class="num">${money0(t.revenue)}</td>
        <td class="num ${t.profit >= 0 ? 'rt-pf-positive' : 'rt-pf-negative'}">${money0(t.profit)}</td>
        <td class="num">${money0(t.avg_profit)}</td>
        <td class="num"><span class="rt-pf-margin ${marginClass(t.margin)}">${t.margin}%</span></td>
      </tr>`;
    });
    html += `</tbody></table></div>`;

    html += `</div>`;  // two col

    // WORST JOBS
    html += `<div class="rt-pf-section-title">Loss-making jobs <span class="badge">fix these first</span></div>`;
    fetch("/api/profit/jobs?" + new URLSearchParams(
      Object.fromEntries(Object.entries(DATA.range)
        .filter(([k,v]) => v))).toString())
      .then(r => r.json())
      .then(jd => {
        const losers = jd.jobs.filter(j => j.is_loss).slice(0, 15);
        if (!losers.length) {
          document.getElementById("rt-pf-losers").innerHTML =
            `<div class="rt-pf-empty">🎉 No loss-making jobs in this range.</div>`;
          return;
        }
        let lh = `<table class="rt-pf-table">
          <thead><tr>
            <th>Job</th><th>Date</th><th>Customer</th><th>Vehicle</th>
            <th>Tech</th><th class="num">Revenue</th>
            <th class="num">Cost</th><th class="num">Profit</th><th class="num">Margin</th>
          </tr></thead><tbody>`;
        losers.forEach(j => {
          lh += `<tr class="loss">
            <td>${esc(j.id)}</td>
            <td>${esc(j.created)}</td>
            <td>${esc(j.customer)}</td>
            <td>${esc(j.vehicle)}</td>
            <td>${esc(j.assigned_to)}</td>
            <td class="num">${money(j.revenue)}</td>
            <td class="num">${money(j.total_cost)}</td>
            <td class="num rt-pf-negative">${money(j.profit)}</td>
            <td class="num"><span class="rt-pf-margin low">${j.margin}%</span></td>
          </tr>`;
        });
        lh += `</tbody></table>`;
        document.getElementById("rt-pf-losers").innerHTML = lh;
      })
      .catch(() => {});
    html += `<div id="rt-pf-losers"><div class="rt-pf-empty">Loading…</div></div>`;

    document.getElementById("rt-pf-body").innerHTML = html;
  }

  window.rtProfitExport = function(){
    const from = document.getElementById("rt-pf-from").value;
    const to = document.getElementById("rt-pf-to").value;
    const q = new URLSearchParams();
    if (from) q.set("from_date", from);
    if (to) q.set("to_date", to);
    window.location.href = "/api/profit/export/csv?" + q.toString();
  };

  window.rtProfitSettings = async function(){
    try {
      const r = await fetch("/api/profit/settings");
      const s = await r.json();
      const info = [
        "Cost model settings",
        "",
        "Tech default rate (R/hr when tech not matched): " + s.tech_default_rate,
        "Parts cost ratio (0–1, e.g. 0.65 = 65%): " + s.parts_cost_ratio,
        "Overhead per hour (R/hr): " + s.overhead_per_hour,
        "",
        "Type a command:",
        "  rate 180         — tech default rate",
        "  parts 0.70       — parts cost ratio",
        "  overhead 50      — overhead per hour",
      ].join("\\n");
      const input = prompt(info);
      if (!input) return;
      const parts = input.trim().split(/\\s+/);
      let payload = {};
      if (parts[0] === "rate" && parts[1]) payload.tech_default_rate = parseFloat(parts[1]);
      else if (parts[0] === "parts" && parts[1]) payload.parts_cost_ratio = parseFloat(parts[1]);
      else if (parts[0] === "overhead" && parts[1]) payload.overhead_per_hour = parseFloat(parts[1]);
      else { alert("Unknown command"); return; }
      await fetch("/api/profit/settings", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      rtProfitLoad();
    } catch(e) { alert("Error: " + e.message); }
  };
})();
</script>
"""
