"""Complete job audit report — printable evidence of every action."""
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
    return {}


def _sig_img(sig):
    if sig and sig.startswith("data:image"):
        return '<img src="' + sig + '">'
    return ""


@router.get("/api/audit/{jid}/report", response_class=HTMLResponse)
def audit_report(jid: str):
    r = _c().table("jobs").select("*").eq("id", jid).execute()
    if not r.data:
        raise HTTPException(404, "Job not found")
    job = r.data[0]
    meta = _meta(job)

    try:
        wr = _c().table("workshop").select("*").eq("id", 1).execute()
        w = wr.data[0] if wr.data else {}
    except Exception:
        w = {}

    logo = w.get("logo") or "RT"
    name = w.get("name") or "RAMSTECH"
    phone = w.get("phone") or ""
    address = w.get("address") or ""

    cust_sig = meta.get("customer_sig") or ""
    if not cust_sig.startswith("data:"):
        cust_sig = ""
    owner_sig = meta.get("owner_sig") or ""
    if not owner_sig.startswith("data:"):
        owner_sig = ""

    tl = job.get("timeline") or []
    if isinstance(tl, str):
        try:
            tl = json.loads(tl)
        except Exception:
            tl = [tl]

    tl_rows = ""
    for i, entry in enumerate(tl, 1):
        tl_rows += '<tr><td style="width:40px;color:#999;">' + str(i) + '</td><td>' + str(entry) + '</td></tr>'

    photos = job.get("photos") or []
    if isinstance(photos, str):
        try:
            photos = json.loads(photos)
        except Exception:
            photos = []

    photo_html = ""
    for p in photos[:12]:
        if p and p.startswith("data:image"):
            photo_html += '<img src="' + p + '" style="width:120px;height:120px;object-fit:cover;border-radius:8px;border:1px solid #ddd;margin:4px;">'

    assigned = job.get("assigned_to") or meta.get("tech") or "—"
    started = meta.get("started_by") or "—"
    completed = meta.get("completed_by") or "—"
    qc_by = meta.get("qc_by") or "—"
    progress = meta.get("progress") or 0

    labour = float(job.get("labour_cost") or 0)
    parts = float(job.get("parts_cost") or 0)
    subtotal = float(job.get("subtotal") or 0)
    vat = float(job.get("vat") or 0)
    total = float(job.get("total") or 0)

    photos_section = ""
    if photos:
        photos_section = '<div class="section"><h3>Photos (' + str(len(photos)) + ')</h3><div class="photos">' + photo_html + '</div></div>'

    html = "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
    html += "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
    html += "<title>Job Report #" + jid + "</title>"
    html += "<style>"
    html += "*{box-sizing:border-box;margin:0;padding:0;}"
    html += "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;color:#1a1a2e;padding:16px;}"
    html += ".page{max-width:800px;margin:0 auto;background:#fff;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,.08);border-radius:12px;}"
    html += ".header{display:flex;justify-content:space-between;padding-bottom:20px;border-bottom:3px solid #E65100;margin-bottom:24px;}"
    html += ".logo{font-size:36px;background:#E65100;color:#fff;width:64px;height:64px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:900;}"
    html += "h1{font-size:20px;color:#E65100;font-weight:800;}"
    html += ".sub{font-size:12px;color:#666;margin-top:2px;line-height:1.5;}"
    html += ".meta{text-align:right;font-size:12px;color:#666;}"
    html += ".meta h2{font-size:18px;color:#1a1a2e;font-weight:800;}"
    html += ".section{margin-bottom:20px;}"
    html += ".section h3{font-size:12px;color:#E65100;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #e5e7eb;}"
    html += "table{width:100%;border-collapse:collapse;font-size:13px;}"
    html += "td{padding:8px 10px;border-bottom:1px solid #f0f0f0;vertical-align:top;}"
    html += "td:first-child{color:#666;font-weight:600;width:180px;}"
    html += ".timeline td:first-child{width:40px;color:#999;}"
    html += ".sig-box{display:flex;gap:16px;margin-top:10px;}"
    html += ".sig{flex:1;border:1px solid #ddd;border-radius:8px;padding:10px;text-align:center;min-height:100px;display:flex;flex-direction:column;justify-content:flex-end;background:#fafafa;}"
    html += ".sig img{max-width:100%;max-height:80px;margin-bottom:6px;}"
    html += ".sig-label{font-size:10px;color:#666;font-weight:600;text-transform:uppercase;}"
    html += ".photos{display:flex;flex-wrap:wrap;gap:6px;}"
    html += ".print-bar{position:fixed;top:12px;right:12px;display:flex;gap:8px;z-index:100;}"
    html += ".print-bar button{padding:10px 18px;background:#E65100;color:#fff;border:none;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer;}"
    html += ".print-bar button.alt{background:#4b5563;}"
    html += ".badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;color:#fff;background:#10b981;}"
    html += "@media print{body{background:#fff;padding:0;}.page{box-shadow:none;border-radius:0;padding:16mm;}.print-bar{display:none;}}"
    html += "</style></head><body>"

    html += "<div class='print-bar'>"
    html += "<button onclick='window.print()'>Print / Save PDF</button>"
    html += "<button class='alt' onclick='window.close()'>Close</button>"
    html += "</div>"

    html += "<div class='page'>"
    html += "<div class='header'>"
    html += "<div style='display:flex;gap:14px;align-items:center;'>"
    html += "<div class='logo'>" + logo + "</div>"
    html += "<div><h1>" + name + "</h1>"
    html += "<div class='sub'>" + phone + "<br>" + address + "</div>"
    html += "</div></div>"
    html += "<div class='meta'>"
    html += "<h2>JOB REPORT</h2>"
    html += "<div>#" + jid + "</div>"
    html += "<div>" + str(job.get('created','')) + "</div>"
    html += "<div><span class='badge'>" + str(job.get('status','')) + "</span></div>"
    html += "</div></div>"

    html += "<div class='section'><h3>Customer &amp; Vehicle</h3><table>"
    html += "<tr><td>Customer</td><td>" + str(job.get('customer','')) + "</td></tr>"
    html += "<tr><td>Phone</td><td>" + str(job.get('phone','')) + "</td></tr>"
    html += "<tr><td>Vehicle</td><td>" + str(job.get('vehicle','')) + "</td></tr>"
    html += "<tr><td>Registration</td><td>" + str(job.get('registration','')) + "</td></tr>"
    html += "<tr><td>Odometer</td><td>" + str(job.get('km',0)) + " km</td></tr>"
    html += "</table></div>"

    html += "<div class='section'><h3>Work Description</h3>"
    html += "<div style='font-size:14px;line-height:1.5;'>" + str(job.get('complaint','')) + "</div>"
    html += "</div>"

    html += "<div class='section'><h3>Technician Accountability</h3><table>"
    html += "<tr><td>Assigned to</td><td>" + assigned + "</td></tr>"
    html += "<tr><td>Started by</td><td>" + started + "</td></tr>"
    html += "<tr><td>Completed by</td><td>" + completed + "</td></tr>"
    html += "<tr><td>QC signed off by</td><td>" + qc_by + "</td></tr>"
    html += "<tr><td>Progress</td><td>" + str(progress) + "%</td></tr>"
    html += "<tr><td>Warranty</td><td>" + str(job.get('warranty_months',0)) + " months</td></tr>"
    html += "</table></div>"

    html += "<div class='section'><h3>Complete Action Timeline (" + str(len(tl)) + " entries)</h3>"
    html += "<table class='timeline'>" + tl_rows + "</table></div>"

    html += "<div class='section'><h3>Cost Breakdown</h3><table>"
    html += "<tr><td>Labour</td><td>R " + "{:,.2f}".format(labour) + "</td></tr>"
    html += "<tr><td>Parts</td><td>R " + "{:,.2f}".format(parts) + "</td></tr>"
    html += "<tr><td>Subtotal</td><td>R " + "{:,.2f}".format(subtotal) + "</td></tr>"
    html += "<tr><td>VAT (15%)</td><td>R " + "{:,.2f}".format(vat) + "</td></tr>"
    html += "<tr style='background:#fff5ec;'><td style='font-weight:800;color:#E65100;'>TOTAL</td>"
    html += "<td style='font-weight:800;color:#E65100;'>R " + "{:,.2f}".format(total) + "</td></tr>"
    html += "</table></div>"

    html += "<div class='section'><h3>Signatures</h3>"
    html += "<div class='sig-box'>"
    html += "<div class='sig'>" + _sig_img(cust_sig) + "<div class='sig-label'>Customer Approval</div></div>"
    html += "<div class='sig'>" + _sig_img(owner_sig) + "<div class='sig-label'>Owner Approval</div></div>"
    html += "</div></div>"

    html += photos_section

    html += "<div style='margin-top:32px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#888;text-align:center;'>"
    html += name + " — Job #" + jid + " — Complete accountability record<br>"
    html += "Generated " + str(job.get('created',''))
    html += "</div>"

    html += "</div></body></html>"

    return HTMLResponse(content=html)


AUDIT_HTML = r"""
<script>
function auditInject(){
  document.querySelectorAll('.card[id^="job-"]').forEach(function(card){
    if(card.dataset.auditHooked) return;
    card.dataset.auditHooked = '1';
    var jid = card.id.replace('job-','');
    var actions = card.querySelector('.no-print');
    if(!actions) return;
    var b = document.createElement('button');
    b.className = 'btn-sm';
    b.style.cssText = 'background:#dc2626;color:#fff;';
    b.textContent = '📋 Audit Report';
    b.onclick = function(){ window.open('/api/audit/'+jid+'/report','_blank'); };
    actions.appendChild(b);
  });
}
setInterval(auditInject, 1000);
setTimeout(auditInject, 600);
</script>
"""
