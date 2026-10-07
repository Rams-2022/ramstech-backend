"""Print-ready invoice generator — returns standalone HTML page."""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


def _meta(job):
    sig = job.get("signature") or ""
    if sig.startswith("{"):
        try:
            return json.loads(sig)
        except Exception:
            pass
    return {"customer_sig": sig, "owner_sig": "", "stage": "", "progress": 0,
            "tech": "", "started_by": "", "completed_by": "", "qc_by": ""}


def _workshop():
    try:
        r = _c().table("workshop").select("*").eq("id", 1).execute()
        return r.data[0] if r.data else {}
    except Exception:
        return {}


@router.get("/api/workflow/invoice-html/{jid}", response_class=HTMLResponse)
def invoice_html(jid: str):
    r = _c().table("jobs").select("*").eq("id", jid).execute()
    if not r.data:
        raise HTTPException(404, "Job not found")
    job = r.data[0]
    meta = _meta(job)
    w = _workshop()

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

    timeline_rows = ""
    for entry in (job.get("timeline") or []):
        timeline_rows += f"<tr><td>{entry}</td></tr>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{inv_no} — {job.get('customer','')}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:#f0f2f5;color:#1a1a2e;padding:16px;}}
.page{{max-width:800px;margin:0 auto;background:#fff;padding:32px;
box-shadow:0 4px 24px rgba(0,0,0,.08);border-radius:12px;}}
.header{{display:flex;justify-content:space-between;align-items:flex-start;
padding-bottom:20px;border-bottom:3px solid #E65100;margin-bottom:24px;}}
.brand{{display:flex;gap:14px;align-items:center;}}
.logo{{font-size:48px;}}
.brand h1{{font-size:22px;color:#E65100;font-weight:800;letter-spacing:.5px;}}
.brand .sub{{font-size:12px;color:#666;margin-top:2px;}}
.inv-meta{{text-align:right;}}
.inv-meta h2{{font-size:22px;color:#1a1a2e;font-weight:800;}}
.inv-meta p{{font-size:12px;color:#666;margin-top:4px;}}
.section{{margin-bottom:20px;}}
.section h3{{font-size:12px;color:#E65100;text-transform:uppercase;
letter-spacing:1px;font-weight:700;margin-bottom:10px;
padding-bottom:6px;border-bottom:1px solid #e5e7eb;}}
.row{{display:flex;gap:20px;}}
.col{{flex:1;}}
.field{{font-size:13px;margin-bottom:6px;}}
.field b{{color:#666;font-weight:600;display:inline-block;min-width:90px;}}
table.items{{width:100%;border-collapse:collapse;margin-top:8px;}}
table.items th{{background:#E65100;color:#fff;text-align:left;
padding:10px;font-size:12px;font-weight:700;text-transform:uppercase;}}
table.items td{{padding:10px;border-bottom:1px solid #eee;font-size:13px;}}
table.items td.amt{{text-align:right;font-weight:600;}}
table.totals{{width:100%;margin-top:16px;}}
table.totals td{{padding:8px 10px;font-size:13px;}}
table.totals td:last-child{{text-align:right;font-weight:600;}}
table.totals tr.grand{{background:#fff5ec;}}
table.totals tr.grand td{{font-size:16px;font-weight:800;color:#E65100;
padding:12px 10px;border-top:2px solid #E65100;}}
.sigs{{display:flex;gap:16px;margin-top:14px;}}
.sigbox{{flex:1;border:1px solid #ddd;border-radius:8px;padding:10px;
text-align:center;min-height:100px;display:flex;flex-direction:column;
justify-content:flex-end;}}
.sigbox.empty{{background:#fafafa;}}
.sigbox img{{max-width:100%;max-height:80px;margin-bottom:6px;}}
.siglabel{{font-size:11px;color:#666;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}}
.tech-table{{width:100%;border-collapse:collapse;font-size:13px;}}
.tech-table td{{padding:8px 10px;border-bottom:1px solid #eee;}}
.tech-table td:first-child{{color:#666;font-weight:600;width:180px;}}
.timeline{{background:#f9fafb;border-left:3px solid #E65100;
padding:12px 14px;font-size:12px;color:#444;border-radius:4px;}}
.timeline td{{padding:3px 0;font-family:monospace;font-size:11px;}}
.status{{display:inline-block;padding:4px 12px;border-radius:12px;
font-size:11px;font-weight:700;color:#fff;background:#10b981;}}
.print-bar{{position:fixed;top:12px;right:12px;display:flex;gap:8px;z-index:100;}}
.print-bar button{{padding:10px 18px;background:#E65100;color:#fff;
border:none;border-radius:8px;font-weight:700;font-size:14px;
cursor:pointer;box-shadow:0 4px 12px rgba(230,81,0,.3);}}
.print-bar button.alt{{background:#4b5563;}}
.footer{{margin-top:32px;padding-top:16px;border-top:1px solid #eee;
font-size:11px;color:#888;text-align:center;}}
@media print{{
body{{background:#fff;padding:0;}}
.page{{box-shadow:none;border-radius:0;padding:16mm;max-width:100%;}}
.print-bar{{display:none;}}
}}
</style>
</head>
<body>
<div class="print-bar">
<button onclick="window.print()">🖨 Print / Save PDF</button>
<button class="alt" onclick="window.close()">Close</button>
</div>

<div class="page">
<div class="header">
<div class="brand">
<div class="logo">{logo}</div>
<div>
<h1>{name}</h1>
<div class="sub">{phone}<br>{address}<br>{email}</div>
</div>
</div>
<div class="inv-meta">
<h2>{inv_no}</h2>
<p>Date: {created}</p>
<p>Job: #{jid}</p>
<p><span class="status">{job.get('status','')}</span></p>
</div>
</div>

<div class="section">
<h3>Customer &amp; Vehicle</h3>
<div class="row">
<div class="col">
<div class="field"><b>Customer:</b> {job.get('customer','')}</div>
<div class="field"><b>Phone:</b> {job.get('phone','')}</div>
</div>
<div class="col">
<div class="field"><b>Vehicle:</b> {job.get('vehicle','')}</div>
<div class="field"><b>Registration:</b> {job.get('registration','')}</div>
<div class="field"><b>Odometer:</b> {job.get('km',0)} km</div>
</div>
</div>
</div>

<div class="section">
<h3>Work Performed</h3>
<div class="field" style="font-size:14px;">{job.get('complaint','')}</div>
<table class="items">
<thead>
<tr><th>Description</th><th style="text-align:right;">Amount</th></tr>
</thead>
<tbody>
<tr><td>Labour</td><td class="amt">R {labour:,.2f}</td></tr>
<tr><td>Parts &amp; Materials</td><td class="amt">R {parts:,.2f}</td></tr>
</tbody>
</table>
<table class="totals">
<tr><td>Subtotal</td><td>R {subtotal:,.2f}</td></tr>
<tr><td>VAT (15%)</td><td>R {vat:,.2f}</td></tr>
<tr class="grand"><td>TOTAL DUE</td><td>R {total:,.2f}</td></tr>
</table>
</div>

<div class="section">
<h3>Technician Accountability</h3>
<table class="tech-table">
<tr><td>Assigned to</td><td>{job.get('assigned_to') or meta.get('tech') or '—'}</td></tr>
<tr><td>Started by</td><td>{meta.get('started_by') or '—'}</td></tr>
<tr><td>Completed by</td><td>{meta.get('completed_by') or '—'}</td></tr>
<tr><td>QC signed off by</td><td>{meta.get('qc_by') or '—'}</td></tr>
</table>
</div>

<div class="section">
<h3>Signatures</h3>
<div class="sigs">
{sig_block("Customer Approval", cust_sig)}
{sig_block("Owner Approval", owner_sig)}
</div>
</div>

<div class="section">
<h3>Service Timeline</h3>
<div class="timeline">
<table>{timeline_rows}</table>
</div>
</div>

<div class="footer">
{name} — Thank you for your business.<br>
This invoice was generated electronically and is valid without a physical signature.
</div>
</div>
</body>
</html>"""
    return HTMLResponse(content=html)
