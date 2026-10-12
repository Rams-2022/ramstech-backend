"""
Pre-Existing Damage Report — vehicle condition at intake.

Captures photos + signature at drop-off so workshops are protected
from "you scratched my car" disputes. Every report is timestamped
and linked to a job. Customer signs on the phone screen.

Routes:
  /api/damage/report           POST — create new report
  /api/damage/report/{id}      GET  — retrieve report
  /api/damage/reports          GET  — list all reports
  /api/damage/job/{job_id}     GET  — reports for a job
  /damage/report/{id}          GET  — printable evidence page

UI: floating 📸 button + guided walkthrough modal.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["damage-report"])


def _list(table):
    from main import store_list
    return store_list(table)


def _get(table, i):
    from main import store_get
    return store_get(table, i)


def _save(table, i, row):
    from main import store_save
    return store_save(table, i, row)


# The 8 standard angles for a vehicle walkaround
VIEWS = [
    {"id": "front",      "label": "Front",           "hint": "Whole front, headlights, bumper"},
    {"id": "rear",       "label": "Rear",            "hint": "Whole rear, bumper, lights"},
    {"id": "left",       "label": "Left side",       "hint": "Full driver side"},
    {"id": "right",      "label": "Right side",      "hint": "Full passenger side"},
    {"id": "windscreen", "label": "Windscreen",      "hint": "Glass, wipers, roof"},
    {"id": "interior",   "label": "Interior",        "hint": "Seats, dash, mileage"},
    {"id": "tyres",      "label": "Tyres & wheels",  "hint": "All 4, tread depth"},
    {"id": "odometer",   "label": "Odometer",        "hint": "Clear shot of the mileage"},
]


# ═══════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════
@router.get("/api/damage/views")
def get_views():
    return {"views": VIEWS}


@router.post("/api/damage/report")
async def create_report(request: Request):
    d = await request.json()

    required = ["customer", "vehicle", "signature"]
    for r in required:
        if not (d.get(r) or "").strip():
            raise HTTPException(400, f"{r} is required")

    rid = str(uuid.uuid4())[:8]
    photos = d.get("photos") or {}
    # trim oversized base64 blobs to keep DB reasonable
    trimmed = {}
    for k, v in photos.items():
        if isinstance(v, str) and v.startswith("data:"):
            v = v.split(",", 1)[1] if "," in v else v
        trimmed[k] = (v or "")[:300000]

    report = {
        "id": rid,
        "job_id": d.get("job_id", ""),
        "customer": d.get("customer", ""),
        "phone": d.get("phone", ""),
        "vehicle": d.get("vehicle", ""),
        "registration": d.get("registration", ""),
        "km": int(d.get("km", 0)),
        "photos": trimmed,
        "photo_notes": d.get("photo_notes") or {},
        "general_notes": (d.get("general_notes") or "").strip(),
        "fuel_level": d.get("fuel_level", ""),
        "signature": d.get("signature", ""),
        "signed_by": d.get("signed_by", ""),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "created_by": d.get("created_by", ""),
    }
    _save("damage_reports", rid, report)
    return {"success": True, "report": report}


@router.get("/api/damage/reports")
def list_reports():
    rows = _list("damage_reports")
    rows.sort(key=lambda x: x.get("created", ""), reverse=True)
    summary = [{
        "id": r["id"],
        "job_id": r.get("job_id", ""),
        "customer": r.get("customer", ""),
        "vehicle": r.get("vehicle", ""),
        "registration": r.get("registration", ""),
        "created": r.get("created", ""),
        "photo_count": len([v for v in (r.get("photos") or {}).values() if v]),
    } for r in rows]
    return {"count": len(summary), "reports": summary}


@router.get("/api/damage/report/{rid}")
def get_report(rid: str):
    r = _get("damage_reports", rid)
    if not r:
        raise HTTPException(404, "Report not found")
    return r


@router.get("/api/damage/job/{job_id}")
def get_reports_for_job(job_id: str):
    rows = [r for r in _list("damage_reports") if r.get("job_id") == job_id]
    rows.sort(key=lambda x: x.get("created", ""), reverse=True)
    return {"count": len(rows), "reports": rows}


@router.delete("/api/damage/report/{rid}")
def delete_report(rid: str):
    from main import store_delete
    store_delete("damage_reports", rid)
    return {"success": True}


# ═══════════════════════════════════════════════════════════════
# PRINTABLE EVIDENCE PAGE
# ═══════════════════════════════════════════════════════════════
@router.get("/damage/report/{rid}", response_class=HTMLResponse)
def view_report(rid: str):
    r = _get("damage_reports", rid)
    if not r:
        raise HTTPException(404, "Report not found")
    return HTMLResponse(_report_html(r))


def _esc(s):
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def _report_html(r):
    photo_blocks = ""
    for v in VIEWS:
        img = (r.get("photos") or {}).get(v["id"], "")
        note = (r.get("photo_notes") or {}).get(v["id"], "")
        if img:
            src = img if img.startswith("data:") else f"data:image/jpeg;base64,{img}"
            photo_blocks += f"""
            <div class="photo">
              <div class="photo-label">{_esc(v['label'])}</div>
              <img src="{src}" alt="{_esc(v['label'])}">
              {f'<div class="photo-note">{_esc(note)}</div>' if note else ''}
            </div>
            """
        else:
            photo_blocks += f"""
            <div class="photo empty">
              <div class="photo-label">{_esc(v['label'])}</div>
              <div class="no-photo">No photo</div>
            </div>
            """

    sig = r.get("signature", "")
    if sig and not sig.startswith("data:"):
        sig = f"data:image/png;base64,{sig}"

    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Damage Report — {_esc(r.get('id',''))}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    font-family:-apple-system,"Segoe UI",Roboto,sans-serif;
    background:#f5f5f5;color:#111;padding:20px 16px;
  }}
  .wrap{{max-width:800px;margin:0 auto;background:#fff;
    border-radius:14px;padding:28px 28px 40px;
    box-shadow:0 4px 20px rgba(0,0,0,0.06)}}
  .hdr{{display:flex;justify-content:space-between;
    align-items:flex-start;border-bottom:2px solid #111;
    padding-bottom:16px;margin-bottom:20px}}
  .hdr h1{{font-size:22px;letter-spacing:-0.5px;font-weight:900;
    margin-bottom:4px}}
  .hdr .sub{{font-size:12px;color:#666}}
  .hdr .stamp{{font-size:11px;color:#666;text-align:right;
    font-family:ui-monospace,Menlo,monospace}}
  .meta{{display:grid;grid-template-columns:1fr 1fr;
    gap:10px 24px;margin-bottom:20px;font-size:13px}}
  .meta .row{{display:flex;justify-content:space-between;
    border-bottom:1px dashed #eee;padding-bottom:6px}}
  .meta .lbl{{color:#888;font-weight:700;
    text-transform:uppercase;letter-spacing:0.5px;font-size:10px}}
  .meta .val{{font-weight:700;color:#111}}
  h2{{font-size:11px;font-weight:800;letter-spacing:2px;
    text-transform:uppercase;color:#666;
    margin:24px 0 12px;padding-bottom:6px;
    border-bottom:1px solid #eee}}
  .photos{{display:grid;grid-template-columns:1fr 1fr;
    gap:14px}}
  .photo{{border:1px solid #e5e5e5;border-radius:10px;
    overflow:hidden;background:#fafafa}}
  .photo.empty{{opacity:0.55}}
  .photo-label{{padding:8px 12px;font-size:11px;
    font-weight:800;text-transform:uppercase;
    letter-spacing:1px;color:#666;background:#f0f0f0;
    border-bottom:1px solid #e5e5e5}}
  .photo img{{width:100%;display:block}}
  .no-photo{{padding:40px 12px;text-align:center;
    color:#bbb;font-size:12px;font-style:italic}}
  .photo-note{{padding:8px 12px;font-size:12px;
    color:#555;background:#fff;border-top:1px solid #eee;
    line-height:1.4}}
  .notes-box{{background:#fafafa;border-left:4px solid #111;
    padding:14px 16px;border-radius:6px;font-size:13px;
    line-height:1.6;color:#333}}
  .sig-wrap{{display:flex;justify-content:space-between;
    align-items:flex-end;gap:20px;
    padding:16px 0 0;border-top:1px solid #eee;
    margin-top:20px}}
  .sig-info{{font-size:12px;color:#666;line-height:1.8}}
  .sig-info .name{{font-weight:800;color:#111;font-size:14px;
    font-style:italic;border-bottom:1px solid #111;
    padding-bottom:2px;display:inline-block;min-width:200px}}
  .sig-img{{max-width:200px;height:auto;
    border:1px solid #e5e5e5;border-radius:6px;
    background:#fff;padding:4px}}
  .footer{{margin-top:28px;padding-top:16px;
    border-top:1px solid #eee;font-size:11px;
    color:#888;text-align:center;line-height:1.6}}
  .btn{{display:inline-block;background:#111;color:#fff;
    padding:10px 20px;border-radius:8px;text-decoration:none;
    font-weight:800;font-size:13px;margin-top:16px}}
  @media print{{
    body{{background:#fff;padding:0}}
    .wrap{{box-shadow:none;padding:0;max-width:100%}}
    .btn{{display:none}}
    .photo img{{max-height:180px;object-fit:cover}}
  }}
  @media (max-width:560px){{
    .meta,.photos{{grid-template-columns:1fr}}
    .sig-wrap{{flex-direction:column;align-items:stretch}}
    .sig-img{{max-width:100%}}
  }}
</style></head>
<body>
<div class="wrap">

  <div class="hdr">
    <div>
      <h1>Vehicle Condition Report</h1>
      <div class="sub">Pre-existing damage record · Report ID {_esc(r.get('id',''))}</div>
    </div>
    <div class="stamp">
      {_esc(r.get('created',''))}<br>
      {_esc(r.get('created_by','')) if r.get('created_by') else ''}
    </div>
  </div>

  <div class="meta">
    <div class="row">
      <span class="lbl">Customer</span>
      <span class="val">{_esc(r.get('customer',''))}</span>
    </div>
    <div class="row">
      <span class="lbl">Phone</span>
      <span class="val">{_esc(r.get('phone',''))}</span>
    </div>
    <div class="row">
      <span class="lbl">Vehicle</span>
      <span class="val">{_esc(r.get('vehicle',''))}</span>
    </div>
    <div class="row">
      <span class="lbl">Registration</span>
      <span class="val">{_esc(r.get('registration',''))}</span>
    </div>
    <div class="row">
      <span class="lbl">Kilometres</span>
      <span class="val">{r.get('km',0):,}</span>
    </div>
    <div class="row">
      <span class="lbl">Fuel level</span>
      <span class="val">{_esc(r.get('fuel_level',''))}</span>
    </div>
  </div>

  <h2>Vehicle Walkaround</h2>
  <div class="photos">
    {photo_blocks}
  </div>

  {f'<h2>Notes</h2><div class="notes-box">{_esc(r.get("general_notes",""))}</div>' if r.get("general_notes") else ''}

  <h2>Customer Acknowledgement</h2>
  <div class="sig-wrap">
    <div class="sig-info">
      I confirm the photos above accurately represent the condition of
      this vehicle at drop-off. Any damage not shown here is my
      responsibility to prove, or the workshop's to repair at no charge.<br><br>
      Signed by: <span class="name">{_esc(r.get('signed_by','') or r.get('customer',''))}</span><br>
      Date: {_esc(r.get('created','')[:10])}
    </div>
    {f'<img class="sig-img" src="{sig}" alt="Signature">' if sig else ''}
  </div>

  <div class="footer">
    This report was generated by RamsTech and is a legal record of vehicle
    condition at intake. Keep a copy for your files.<br>
    <a class="btn" href="#" onclick="window.print();return false;">🖨 Print this report</a>
  </div>

</div>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# INJECTED UI — floating button + walkthrough modal
# ═══════════════════════════════════════════════════════════════
DAMAGE_REPORT_HTML = """
<style>
  #rt-dmg-btn {
    position: fixed; bottom: 24px; left: 380px; z-index: 9998;
    background: #111; color: #fff; border: none; border-radius: 40px;
    padding: 12px 20px; font-weight: 700; font-size: 13px;
    cursor: pointer; box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  #rt-dmg-btn:hover { transform: translateY(-2px); }
  #rt-dmg-overlay {
    display: none; position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,0.6); padding: 20px; overflow-y: auto;
  }
  #rt-dmg-overlay.open { display: block; }
  .rt-dmg-modal {
    max-width: 640px; margin: 0 auto; background: #fff;
    border-radius: 14px; padding: 24px 24px 32px;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    color: #1a1a1a; position: relative;
  }
  .rt-dmg-modal h2 { margin: 0 0 4px; font-size: 22px; letter-spacing: -0.5px; }
  .rt-dmg-modal .sub { color: #777; font-size: 13px; margin: 0 0 18px; }
  .rt-dmg-close {
    position: absolute; top: 16px; right: 20px; background: none;
    border: none; font-size: 24px; cursor: pointer; color: #999;
  }
  .rt-dmg-steps {
    display: flex; gap: 6px; margin-bottom: 20px;
    font-size: 10px; font-weight: 800; letter-spacing: 0.5px;
    text-transform: uppercase; color: #888;
  }
  .rt-dmg-steps span {
    padding: 5px 10px; background: #f5f5f5; border-radius: 20px;
  }
  .rt-dmg-steps span.on { background: #111; color: #fff; }
  .rt-dmg-section { display: none; }
  .rt-dmg-section.on { display: block; }
  .rt-dmg-field { margin-bottom: 12px; }
  .rt-dmg-field label {
    display: block; font-size: 10px; font-weight: 800;
    text-transform: uppercase; letter-spacing: 1px;
    color: #666; margin-bottom: 5px;
  }
  .rt-dmg-field input, .rt-dmg-field textarea, .rt-dmg-field select {
    width: 100%; padding: 11px 12px; border: 1px solid #ddd;
    border-radius: 8px; font-size: 14px; font-family: inherit;
    background: #fafafa;
  }
  .rt-dmg-field input:focus, .rt-dmg-field textarea:focus {
    outline: none; border-color: #111; background: #fff;
  }
  .rt-dmg-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .rt-dmg-photos {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  }
  .rt-dmg-photo {
    border: 2px dashed #ddd; border-radius: 10px;
    padding: 12px; text-align: center; cursor: pointer;
    background: #fafafa; position: relative; overflow: hidden;
    min-height: 110px; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    transition: border-color 0.15s;
  }
  .rt-dmg-photo:hover { border-color: #111; }
  .rt-dmg-photo.has-photo {
    border-style: solid; border-color: #16a34a;
    background: #f0fdf4; padding: 0;
  }
  .rt-dmg-photo .label {
    font-weight: 800; font-size: 12px; margin-bottom: 3px;
  }
  .rt-dmg-photo .hint {
    font-size: 10px; color: #888; line-height: 1.3;
  }
  .rt-dmg-photo .icon { font-size: 22px; margin-bottom: 4px; }
  .rt-dmg-photo img {
    width: 100%; height: 130px; object-fit: cover;
    display: block; border-radius: 8px;
  }
  .rt-dmg-photo .overlay {
    position: absolute; top: 6px; right: 6px;
    background: #16a34a; color: #fff;
    width: 22px; height: 22px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 12px;
  }
  .rt-dmg-photo input[type=file] { display: none; }
  .rt-dmg-sig-canvas {
    width: 100%; height: 140px; background: #fafafa;
    border: 2px dashed #ddd; border-radius: 10px;
    cursor: crosshair; touch-action: none;
  }
  .rt-dmg-sig-wrap { position: relative; }
  .rt-dmg-sig-clear {
    position: absolute; top: 6px; right: 8px;
    background: #f5f5f5; border: none; padding: 4px 10px;
    border-radius: 6px; font-size: 11px; font-weight: 700;
    cursor: pointer; color: #666;
  }
  .rt-dmg-actions {
    display: flex; gap: 8px; margin-top: 20px;
  }
  .rt-dmg-actions button {
    flex: 1; padding: 13px; border-radius: 10px;
    font-weight: 800; font-size: 14px; cursor: pointer;
    border: none;
  }
  .rt-dmg-actions button.primary { background: #111; color: #fff; }
  .rt-dmg-actions button.secondary {
    background: #fff; color: #111; border: 2px solid #111;
  }
  .rt-dmg-actions button:disabled { opacity: 0.5; cursor: not-allowed; }
  .rt-dmg-msg {
    padding: 12px; border-radius: 10px; font-size: 13px;
    margin-top: 12px; display: none;
  }
  .rt-dmg-msg.on { display: block; }
  .rt-dmg-msg.err { background: #fef2f2; color: #991b1b; }
  .rt-dmg-msg.ok { background: #f0fdf4; color: #166534; }
  @media (max-width: 640px) {
    .rt-dmg-grid, .rt-dmg-photos { grid-template-columns: 1fr; }
    #rt-dmg-btn { left: 24px; bottom: 78px; }
  }
  @media print {
    #rt-dmg-btn, #rt-dmg-overlay { display: none !important; }
  }
</style>

<button id="rt-dmg-btn" onclick="rtDmgOpen()">📸 Vehicle Check-In</button>

<div id="rt-dmg-overlay" onclick="if(event.target===this)rtDmgClose()">
  <div class="rt-dmg-modal">
    <button class="rt-dmg-close" onclick="rtDmgClose()">×</button>
    <h2>Vehicle Condition Report</h2>
    <p class="sub">8 photos + signature. Protects you from "you scratched my car."</p>

    <div class="rt-dmg-steps">
      <span class="on" data-step="1">1. Details</span>
      <span data-step="2">2. Photos</span>
      <span data-step="3">3. Sign</span>
    </div>

    <!-- STEP 1 -->
    <div class="rt-dmg-section on" data-section="1">
      <div class="rt-dmg-grid">
        <div class="rt-dmg-field">
          <label>Customer name</label>
          <input id="rt-dmg-cust" placeholder="e.g. Thabo Mokoena">
        </div>
        <div class="rt-dmg-field">
          <label>Phone</label>
          <input id="rt-dmg-phone" placeholder="072 123 4567">
        </div>
        <div class="rt-dmg-field">
          <label>Vehicle</label>
          <input id="rt-dmg-veh" placeholder="e.g. Toyota Hilux 2.8">
        </div>
        <div class="rt-dmg-field">
          <label>Registration</label>
          <input id="rt-dmg-reg" placeholder="e.g. GP 123-456">
        </div>
        <div class="rt-dmg-field">
          <label>Kilometres</label>
          <input id="rt-dmg-km" inputmode="numeric" placeholder="58600">
        </div>
        <div class="rt-dmg-field">
          <label>Fuel level</label>
          <select id="rt-dmg-fuel">
            <option value="">—</option>
            <option>Empty</option>
            <option>1/4</option>
            <option>1/2</option>
            <option>3/4</option>
            <option>Full</option>
          </select>
        </div>
      </div>
    </div>

    <!-- STEP 2 -->
    <div class="rt-dmg-section" data-section="2">
      <div class="rt-dmg-photos" id="rt-dmg-photos"></div>
      <div class="rt-dmg-field" style="margin-top:14px">
        <label>General notes (optional)</label>
        <textarea id="rt-dmg-notes" rows="3"
          placeholder="Any existing damage, missing items, other observations…"></textarea>
      </div>
    </div>

    <!-- STEP 3 -->
    <div class="rt-dmg-section" data-section="3">
      <div class="rt-dmg-field">
        <label>Signed by (customer name)</label>
        <input id="rt-dmg-signed-by" placeholder="Full name">
      </div>
      <div class="rt-dmg-field">
        <label>Signature (draw with finger)</label>
        <div class="rt-dmg-sig-wrap">
          <canvas id="rt-dmg-sig" class="rt-dmg-sig-canvas"></canvas>
          <button class="rt-dmg-sig-clear" onclick="rtDmgClearSig()">Clear</button>
        </div>
      </div>
    </div>

    <div class="rt-dmg-msg" id="rt-dmg-msg"></div>

    <div class="rt-dmg-actions">
      <button class="secondary" id="rt-dmg-back" onclick="rtDmgBack()" style="display:none">← Back</button>
      <button class="primary" id="rt-dmg-next" onclick="rtDmgNext()">Next →</button>
      <button class="primary" id="rt-dmg-save" onclick="rtDmgSave()" style="display:none">Save report</button>
    </div>
  </div>
</div>

<script>
(function(){
  const VIEWS = [
    {id:"front",      label:"Front",          hint:"Whole front + bumper"},
    {id:"rear",       label:"Rear",           hint:"Whole rear + bumper"},
    {id:"left",       label:"Left side",      hint:"Driver side"},
    {id:"right",      label:"Right side",     hint:"Passenger side"},
    {id:"windscreen", label:"Windscreen",     hint:"Glass + wipers"},
    {id:"interior",   label:"Interior",       hint:"Seats + dash"},
    {id:"tyres",      label:"Tyres",          hint:"All 4 wheels"},
    {id:"odometer",   label:"Odometer",       hint:"Clear mileage shot"}
  ];

  let STEP = 1;
  let PHOTOS = {};
  let SIG_DATA = "";

  window.rtDmgOpen = function(){
    resetState();
    renderPhotos();
    renderSteps();
    document.getElementById("rt-dmg-overlay").classList.add("open");
    setTimeout(initSignature, 200);
  };

  window.rtDmgClose = function(){
    document.getElementById("rt-dmg-overlay").classList.remove("open");
  };

  function resetState(){
    STEP = 1;
    PHOTOS = {};
    SIG_DATA = "";
    ["cust","phone","veh","reg","km","notes","signed-by"].forEach(id => {
      const el = document.getElementById("rt-dmg-" + id);
      if (el) el.value = "";
    });
    document.getElementById("rt-dmg-fuel").value = "";
    const msg = document.getElementById("rt-dmg-msg");
    msg.classList.remove("on","err","ok");
    msg.textContent = "";
  }

  function renderSteps(){
    document.querySelectorAll(".rt-dmg-steps span").forEach(s => {
      s.classList.toggle("on", parseInt(s.dataset.step) === STEP);
    });
    document.querySelectorAll(".rt-dmg-section").forEach(s => {
      s.classList.toggle("on", parseInt(s.dataset.section) === STEP);
    });
    document.getElementById("rt-dmg-back").style.display = STEP > 1 ? "block" : "none";
    document.getElementById("rt-dmg-next").style.display = STEP < 3 ? "block" : "none";
    document.getElementById("rt-dmg-save").style.display = STEP === 3 ? "block" : "none";
  }

  function renderPhotos(){
    const wrap = document.getElementById("rt-dmg-photos");
    wrap.innerHTML = VIEWS.map(v => `
      <label class="rt-dmg-photo ${PHOTOS[v.id] ? 'has-photo' : ''}"
             for="rt-dmg-file-${v.id}">
        ${PHOTOS[v.id]
          ? `<img src="${PHOTOS[v.id]}" alt="${v.label}">
             <div class="overlay">✓</div>`
          : `<div class="icon">📷</div>
             <div class="label">${v.label}</div>
             <div class="hint">${v.hint}</div>`}
        <input type="file" accept="image/*" capture="environment"
               id="rt-dmg-file-${v.id}"
               onchange="rtDmgPhoto('${v.id}', this)">
      </label>
    `).join("");
  }

  window.rtDmgPhoto = function(id, input){
    const f = input.files && input.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = e => {
      const img = new Image();
      img.onload = () => {
        // downscale to max 900px wide, quality 0.75
        const canvas = document.createElement("canvas");
        const max = 900;
        let w = img.width, h = img.height;
        if (w > max) { h = h * max / w; w = max; }
        canvas.width = w; canvas.height = h;
        canvas.getContext("2d").drawImage(img, 0, 0, w, h);
        PHOTOS[id] = canvas.toDataURL("image/jpeg", 0.75);
        renderPhotos();
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(f);
  };

  function step1Valid(){
    const cust = document.getElementById("rt-dmg-cust").value.trim();
    const veh = document.getElementById("rt-dmg-veh").value.trim();
    if (!cust) { showMsg("err","Customer name is required"); return false; }
    if (!veh) { showMsg("err","Vehicle is required"); return false; }
    return true;
  }

  window.rtDmgNext = function(){
    if (STEP === 1 && !step1Valid()) return;
    if (STEP < 3) { STEP++; renderSteps(); if (STEP === 3) initSignature(); }
  };

  window.rtDmgBack = function(){
    if (STEP > 1) { STEP--; renderSteps(); }
  };

  window.rtDmgSave = async function(){
    const signedBy = document.getElementById("rt-dmg-signed-by").value.trim();
    const custName = document.getElementById("rt-dmg-cust").value.trim();
    if (!SIG_DATA) { showMsg("err","Please capture the customer's signature"); return; }
    if (!signedBy) { showMsg("err","Signed by is required"); return; }

    const body = {
      customer: custName,
      phone: document.getElementById("rt-dmg-phone").value.trim(),
      vehicle: document.getElementById("rt-dmg-veh").value.trim(),
      registration: document.getElementById("rt-dmg-reg").value.trim(),
      km: parseInt(document.getElementById("rt-dmg-km").value) || 0,
      fuel_level: document.getElementById("rt-dmg-fuel").value,
      general_notes: document.getElementById("rt-dmg-notes").value.trim(),
      photos: PHOTOS,
      photo_notes: {},
      signed_by: signedBy,
      signature: SIG_DATA,
      job_id: "",
    };

    const btn = document.getElementById("rt-dmg-save");
    btn.disabled = true; btn.textContent = "Saving…";
    try {
      const r = await fetch("/api/damage/report", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
      });
      const d = await r.json();
      if (!d.success) throw new Error(d.detail || "Failed");
      showMsg("ok","✓ Saved. Opening printable report…");
      const rid = d.report.id;
      setTimeout(() => {
        window.open("/damage/report/" + rid, "_blank");
        rtDmgClose();
      }, 800);
    } catch(e) {
      showMsg("err","Error: " + e.message);
      btn.disabled = false; btn.textContent = "Save report";
    }
  };

  function showMsg(kind, text){
    const m = document.getElementById("rt-dmg-msg");
    m.className = "rt-dmg-msg on " + kind;
    m.textContent = text;
  }

  // ── Signature pad ────────────────────────────────────────
  let SIG_CTX = null, SIG_DRAWING = false;

  function initSignature(){
    const canvas = document.getElementById("rt-dmg-sig");
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    SIG_CTX = canvas.getContext("2d");
    SIG_CTX.scale(2, 2);
    SIG_CTX.strokeStyle = "#111";
    SIG_CTX.lineWidth = 2.5;
    SIG_CTX.lineCap = "round";
    SIG_CTX.lineJoin = "round";

    const getPos = (e) => {
      const r = canvas.getBoundingClientRect();
      const t = e.touches ? e.touches[0] : e;
      return { x: t.clientX - r.left, y: t.clientY - r.top };
    };
    const start = (e) => {
      e.preventDefault();
      SIG_DRAWING = true;
      const p = getPos(e);
      SIG_CTX.beginPath();
      SIG_CTX.moveTo(p.x, p.y);
    };
    const move = (e) => {
      if (!SIG_DRAWING) return;
      e.preventDefault();
      const p = getPos(e);
      SIG_CTX.lineTo(p.x, p.y);
      SIG_CTX.stroke();
    };
    const end = (e) => {
      if (!SIG_DRAWING) return;
      e.preventDefault();
      SIG_DRAWING = false;
      SIG_DATA = canvas.toDataURL("image/png");
    };
    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    canvas.addEventListener("mouseup", end);
    canvas.addEventListener("mouseleave", end);
    canvas.addEventListener("touchstart", start, {passive:false});
    canvas.addEventListener("touchmove", move, {passive:false});
    canvas.addEventListener("touchend", end, {passive:false});
  }

  window.rtDmgClearSig = function(){
    const canvas = document.getElementById("rt-dmg-sig");
    if (!canvas || !SIG_CTX) return;
    SIG_CTX.clearRect(0, 0, canvas.width, canvas.height);
    SIG_DATA = "";
  };
})();
</script>
"""
