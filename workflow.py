"""Workshop workflow using ONLY original jobs columns (bypasses Supabase cache bug)."""
import uuid, json
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


def _meta(job):
    sig = job.get("signature") or ""
    if sig.startswith("{"):
        try:
            return json.loads(sig)
        except Exception:
            pass
    return {"customer_sig": sig, "owner_sig": "", "stage": job.get("status", "New"),
            "progress": 0, "tech": "", "started_by": "", "completed_by": "", "qc_by": ""}


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


@router.post("/tech-pin")
async def tech_pin(r: Request):
    d = await r.json()
    s = _pin(d.get("pin"))
    return {"staff_id": s["id"], "name": s["name"], "role": s.get("role", "")}


@router.get("/quotes-pending")
def quotes_pending():
    r = _c().table("jobs").select("*").in_(
        "status", ["Draft Quote", "Awaiting Owner"]).order("created", desc=True).execute()
    return {"quotes": r.data or []}


@router.post("/quote-create")
async def quote_create(r: Request):
    try:
        d = await r.json()
        jid = str(uuid.uuid4())[:8]
        labour = float(d.get("labour", 0) or 0)
        parts = float(d.get("parts", 0) or 0)
        sub = round(labour + parts, 2)
        vat = round(sub * 0.15, 2)
        vtxt = ((d.get("make", "") or "") + " " + (d.get("model", "") or "")).strip()
        meta = {"customer_sig": "", "owner_sig": "", "stage": "Draft",
                "progress": 0, "tech": "", "started_by": "", "completed_by": "", "qc_by": ""}
        row = {
            "id": jid,
            "customer": d.get("customer", "") or "",
            "phone": d.get("phone", "") or "",
            "vehicle": vtxt or (d.get("registration", "") or ""),
            "registration": (d.get("registration") or "").upper(),
            "km": int(d.get("km") or 0),
            "complaint": d.get("description", "") or "",
            "assigned_to": "",
            "photos": [],
            "signature": json.dumps(meta),
            "warranty_months": 6,
            "status": "Draft Quote",
            "timeline": [f"{_now()} — Quote drafted"],
            "labour_hours": 0,
            "labour_rate": 450,
            "parts_cost": parts,
            "labour_cost": labour,
            "subtotal": sub,
            "vat": vat,
            "total": round(sub + vat, 2),
            "created": _now(),
        }
        _ins("jobs", row)
        return {"success": True, "quote_id": jid, "quote": row}
    except Exception as e:
        import traceback
        print(f"[quote-create ERROR]\n{traceback.format_exc()}")
        return {"success": False, "detail": f"{type(e).__name__}: {str(e)}"}


@router.get("/quote/{qid}")
def quote_get(qid: str):
    q = _get("jobs", qid)
    if not q:
        raise HTTPException(404, "Quote not found")
    meta = _meta(q)
    return {"quote": q, "meta": meta}


@router.post("/quote-customer-sign/{qid}")
async def quote_customer_sign(qid: str, r: Request):
    d = await r.json()
    sig = d.get("signature") or ""
    if not sig:
        raise HTTPException(400, "signature required")
    q = _get("jobs", qid)
    if not q:
        raise HTTPException(404, "Quote not found")
    meta = _meta(q)
    meta["customer_sig"] = sig
    meta["stage"] = "Awaiting Owner"
    _upd("jobs", qid, {
        "signature": json.dumps(meta),
        "status": "Awaiting Owner",
        "timeline": _tl(q, "Customer signature captured"),
    })
    return {"success": True}


@router.post("/quote-owner-sign/{qid}")
async def quote_owner_sign(qid: str, r: Request):
    d = await r.json()
    sig = d.get("signature") or ""
    if not sig:
        raise HTTPException(400, "signature required")
    q = _get("jobs", qid)
    if not q:
        raise HTTPException(404, "Quote not found")
    meta = _meta(q)
    meta["owner_sig"] = sig
    meta["stage"] = "Approved"
    _upd("jobs", qid, {
        "signature": json.dumps(meta),
        "status": "In Progress",
        "timeline": _tl(q, "Owner approved — job active"),
    })
    return {"success": True, "job_id": qid}


@router.get("/vehicle/{reg}")
def get_vehicle(reg: str):
    reg = reg.upper().strip()
    r = _c().table("jobs").select("id,created,complaint,status,total")\
        .eq("registration", reg).order("created", desc=True).limit(20).execute()
    return {"vehicle": {"registration": reg}, "history": r.data or []}


@router.post("/assign/{jid}")
async def assign(jid: str, r: Request):
    d = await r.json()
    tech = (d.get("tech") or "").strip()
    if not tech:
        raise HTTPException(400, "tech required")
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    meta = _meta(job)
    meta["tech"] = tech
    meta["stage"] = "Assigned"
    _upd("jobs", jid, {
        "assigned_to": tech,
        "signature": json.dumps(meta),
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
    meta = _meta(job)
    meta["stage"] = "In Progress"
    meta["started_by"] = s["name"]
    _upd("jobs", jid, {
        "signature": json.dumps(meta),
        "status": "In Progress",
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
    meta = _meta(job)
    meta["progress"] = pct
    txt = f"Progress {pct}%" + (f" | {note}" if note else "")
    _upd("jobs", jid, {"signature": json.dumps(meta), "timeline": _tl(job, txt)})
    return {"success": True, "progress": pct}


@router.post("/complete/{jid}")
async def complete(jid: str, r: Request):
    d = await r.json()
    s = _pin(d.get("pin"))
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    meta = _meta(job)
    meta["completed_by"] = s["name"]
    meta["progress"] = 100
    meta["stage"] = "QC"
    _upd("jobs", jid, {
        "signature": json.dumps(meta),
        "status": "Awaiting QC",
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
    meta = _meta(job)
    meta["qc_by"] = s["name"]
    meta["stage"] = "Ready"
    _upd("jobs", jid, {
        "signature": json.dumps(meta),
        "status": "Ready for Pickup",
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
    meta = _meta(job)
    meta["stage"] = "Invoiced"
    _upd("jobs", jid, {
        "signature": json.dumps(meta),
        "status": "Invoiced",
        "timeline": _tl(job, f"Invoice #{iid} generated"),
    })
    return {"success": True, "invoice_id": iid, "invoice": inv}


@router.get("/job/{jid}")
def full_job(jid: str):
    job = _get("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    meta = _meta(job)
    return {"job": job, "meta": meta}
