"""Workshop workflow: draft quote -> customer sign -> owner sign -> job -> invoice."""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


def _get(t, i):
    r = _c().table(t).select("*").eq("id", i).execute()
    return r.data[0] if r.data else None


def _upd(t, i, d):
    r = _c().table(t).update(d).eq("id", i).execute()
    return r.data[0] if r.data else None


def _ins(t, d):
    r = _c().table(t).insert(d).execute()
    return r.data[0] if r.data else None


def _pin(pin):
    p = str(pin or "").strip()
    if len(p) != 4 or not p.isdigit():
        raise HTTPException(400, "PIN must be 4 digits")
    r = _c().table("staff").select("*").eq("pin", p).execute()
    if not r.data:
        raise HTTPException(401, "Invalid PIN")
    s = r.data[0]
    if s.get("active") is False:
        raise HTTPException(401, "Staff inactive")
    return s


def _tl(job, text):
    tl = list(job.get("timeline") or [])
    tl.append(f"{_now()} — {text}")
    return tl


@router.post("/set-pin")
async def set_pin(r: Request):
    d = await r.json()
    sid = (d.get("staff_id") or "").strip()
    pin = str(d.get("pin") or "").strip()
    if not sid or len(pin) != 4 or not pin.isdigit():
        raise HTTPException(400, "staff_id and 4-digit pin required")
    dup = _c().table("staff").select("id").eq("pin", pin).execute()
    if dup.data and dup.data[0]["id"] != sid:
        raise HTTPException(409, "PIN in use")
    _upd("staff", sid, {"pin": pin})
    return {"success": True}


# ═══════════════════════════════════
# QUOTES — pending list for jobs tab
# ═══════════════════════════════════
@router.get("/quotes-pending")
def quotes_pending():
    r = _c().table("quotes").select("*").in_(
        "status", ["draft", "customer_signed"]).order("created", desc=True).execute()
    return {"quotes": r.data or []}


@router.post("/quote-create")
async def quote_create(r: Request):
    d = await r.json()
    qid = str(uuid.uuid4())[:8]
    labour = float(d.get("labour", 0) or 0)
    parts = float(d.get("parts", 0) or 0)
    sub = round(labour + parts, 2)
    vat = round(sub * 0.15, 2)
    row = {
        "id": qid, "customer": d.get("customer", ""),
        "phone": d.get("phone", ""),
        "vehicle": (d.get("make", "") + " " + d.get("model", "")).strip(),
        "registration": (d.get("registration") or "").upper(),
        "make": d.get("make", ""), "model": d.get("model", ""),
        "km": int(d.get("km") or 0),
        "description": d.get("description", ""),
        "labour": labour, "parts": parts,
        "subtotal": sub, "vat": vat, "total": round(sub + vat, 2),
        "status": "draft", "created": _now(),
    }
    _ins("quotes", row)
    return {"success": True, "quote_id": qid, "quote": row}


@router.post("/quote-customer-sign/{qid}")
async def quote_customer_sign(qid: str, r: Request):
    d = await r.json()
    sig = d.get("signature") or ""
    if not sig:
        raise HTTPException(400, "signature required")
    q = _get("quotes", qid)
    if not q:
        raise HTTPException(404, "Quote not found")
    _upd("quotes", qid, {
        "signature_customer": sig,
        "customer_signed_at": datetime.utcnow().isoformat(),
        "status": "customer_signed",
    })
    return {"success": True}


@router.post("/quote-owner-sign/{qid}")
async def quote_owner_sign(qid: str, r: Request):
    d = await r.json()
    sig = d.get("signature") or ""
    if not sig:
        raise HTTPException(400, "signature required")
    q = _get("quotes", qid)
    if not q:
        raise HTTPException(404, "Quote not found")
    _upd("quotes", qid, {
        "signature_owner": sig,
        "owner_signed_at": datetime.utcnow().isoformat(),
        "status": "approved",
    })

    reg = (q.get("registration") or "").upper()
    v = _c().table("vehicles").select("id").eq("registration", reg).execute()
    vid = v.data[0]["id"] if v.data else None

    jid = str(uuid.uuid4())[:8]
    job = {
        "id": jid, "customer": q.get("customer", ""),
        "phone": q.get("phone", ""),
        "vehicle": q.get("vehicle", "") or reg,
        "registration": reg,
        "km": int(q.get("km") or 0),
        "complaint": q.get("description", ""),
        "assigned_to": "", "photos": [],
        "signature": q.get("signature_customer", ""),
        "warranty_months": 6,
        "status": "In Progress", "stage": "Approved",
        "timeline": [f"{_now()} — Quote #{qid} approved (customer + owner signed)"],
        "labour_hours": 0, "labour_rate": 450,
        "parts_cost": float(q.get("parts") or 0),
        "labour_cost": float(q.get("labour") or 0),
        "subtotal": float(q.get("subtotal") or 0),
        "vat": float(q.get("vat") or 0),
        "total": float(q.get("total") or 0),
        "created": _now(),
        "vehicle_id": vid, "quote_id": qid, "progress": 0,
    }
    _ins("jobs", job)
    _upd("quotes", qid, {"job_id": jid})
    return {"success": True, "job_id": jid}


@router.get("/quote/{qid}")
def quote_get(qid: str):
    q = _get("quotes", qid)
    if not q:
        raise HTTPException(404, "Quote not found")
    return {"quote": q}


# ═══════════════════════════════════
# VEHICLE lookup
# ═══════════════════════════════════
@router.get("/vehicle/{reg}")
def get_vehicle(reg: str):
    reg = reg.upper().strip()
    r = _c().table("vehicles").select("*").eq("registration", reg).execute()
    v = r.data[0] if r.data else None
    if not v:
        return {"vehicle": None}
    h = _c().table("jobs").select("id,created,complaint,status,total")\
        .eq("registration", reg).order("created", desc=True).limit(20).execute()
    return {"vehicle": v, "history": h.data or []}


# ═══════════════════════════════════
# JOB workflow actions
# ═══════════════════════════════════
@router.post("/assign/{jid}")
async def assign(jid: str, r: Request):
    d = await r.json()
    tech = (d.get("tech") or "").strip()
    if not tech:
        raise HTTPException(400, "tech required")
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    _upd("jobs", jid, {
        "assigned_to": tech,
        "assigned_at": datetime.utcnow().isoformat(),
        "stage": "Assigned",
        "timeline": _tl(job, f"Assigned to {tech}"),
    })
    return {"success": True}


@router.post("/start/{jid}")
async def start(jid: str, r: Request):
    d = await r.json()
    s = _pin(d.get("pin"))
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    _upd("jobs", jid, {
        "tech_started_by": s["name"],
        "started_at": datetime.utcnow().isoformat(),
        "status": "In Progress", "stage": "In Progress",
        "timeline": _tl(job, f"{s['name']} started work"),
    })
    return {"success": True, "tech": s["name"]}


@router.post("/progress/{jid}")
async def progress(jid: str, r: Request):
    d = await r.json()
    pct = max(0, min(100, int(d.get("progress") or 0)))
    note = (d.get("note") or "").strip()
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    txt = f"Progress {pct}%" + (f" | {note}" if note else "")
    _upd("jobs", jid, {"progress": pct, "timeline": _tl(job, txt)})
    return {"success": True, "progress": pct}


@router.post("/complete/{jid}")
async def complete(jid: str, r: Request):
    d = await r.json()
    s = _pin(d.get("pin"))
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    _upd("jobs", jid, {
        "tech_completed_by": s["name"],
        "completed_at": datetime.utcnow().isoformat(),
        "progress": 100, "status": "Awaiting QC", "stage": "QC",
        "timeline": _tl(job, f"{s['name']} marked complete"),
    })
    return {"success": True, "tech": s["name"]}


@router.post("/qc/{jid}")
async def qc(jid: str, r: Request):
    d = await r.json()
    s = _pin(d.get("pin"))
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    _upd("jobs", jid, {
        "qc_by": s["name"], "qc_at": datetime.utcnow().isoformat(),
        "status": "Ready for Pickup", "stage": "Ready",
        "timeline": _tl(job, f"QC passed by {s['name']}"),
    })
    return {"success": True, "manager": s["name"]}


@router.post("/invoice/{jid}")
async def make_invoice(jid: str, r: Request):
    d = await r.json()
    by = (d.get("by") or "").strip()
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    iid = str(uuid.uuid4())[:8]
    inv = {
        "id": iid, "customer": job.get("customer", ""),
        "vehicle": job.get("vehicle", ""),
        "description": job.get("complaint", ""),
        "labour": float(job.get("labour_cost") or 0),
        "parts": float(job.get("parts_cost") or 0),
        "subtotal": float(job.get("subtotal") or 0),
        "vat": float(job.get("vat") or 0),
        "total": float(job.get("total") or 0),
        "amount_paid": 0, "paid": False,
        "job_id": jid, "created": _now(),
    }
    _ins("invoices", inv)
    _upd("jobs", jid, {
        "invoiced_by": by, "invoiced_at": datetime.utcnow().isoformat(),
        "status": "Invoiced", "stage": "Invoiced", "invoice_id": iid,
        "timeline": _tl(job, f"Invoice #{iid} generated" + (f" by {by}" if by else "")),
    })
    return {"success": True, "invoice_id": iid, "invoice": inv}


@router.get("/job/{jid}")
def full_job(jid: str):
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"job": job}
