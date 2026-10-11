"""
Multi-tenancy — one codebase, many workshops.

Also hosts the sales kit routes (/kit/leave-behind, /kit/case-study,
/kit/onboarding) so no extra module wiring is required.

Design: OFF by default. Set MULTI_TENANT=1 on Render to enable.
When OFF: every row behaves as workshop_id="default" — zero behaviour change.
When ON:  every read/write is scoped to the requesting workshop.
"""
import os
import hmac
import hashlib
import base64
import json
import re
from datetime import datetime, timedelta
from contextvars import ContextVar

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

router = APIRouter(tags=["tenancy", "sales-kit"])


# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
MULTI_TENANT = os.getenv("MULTI_TENANT", "").strip() == "1"
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip() or "change-me-please"
SESSION_DAYS = 30
COOKIE_NAME = "rt_session"
SUPER_ADMIN_PIN = os.getenv("SUPER_ADMIN_PIN", "").strip()


_current_workshop: ContextVar = ContextVar("current_workshop", default="default")


def is_multi_tenant():
    return MULTI_TENANT


def get_current_workshop():
    return _current_workshop.get() or "default"


def set_current_workshop(wid):
    _current_workshop.set(wid or "default")


def _slugify(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:40] or "workshop"


# ═══════════════════════════════════════════════════════════════
# SESSION COOKIE
# ═══════════════════════════════════════════════════════════════
def _sign(payload):
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    sig = hmac.new(SESSION_SECRET.encode(), raw.encode(),
                   hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{sig}"


def _verify(token):
    if not token or "." not in token:
        return None
    raw, sig = token.rsplit(".", 1)
    expected = hmac.new(SESSION_SECRET.encode(), raw.encode(),
                        hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        data = json.loads(base64.urlsafe_b64decode(raw + pad).decode())
    except Exception:
        return None
    exp = data.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        return None
    return data


def _make_session(workshop_id, user="owner", role="owner"):
    return _sign({
        "ws": workshop_id,
        "user": user,
        "role": role,
        "exp": (datetime.utcnow() + timedelta(days=SESSION_DAYS)).timestamp(),
    })


def resolve_workshop(request):
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    if session and session.get("ws"):
        return {"id": session["ws"], "user": session.get("user", "owner"),
                "role": session.get("role", "owner"), "source": "cookie"}
    qs = request.query_params.get("ws")
    if qs and SUPER_ADMIN_PIN and \
       request.query_params.get("admin_pin") == SUPER_ADMIN_PIN:
        return {"id": _slugify(qs), "user": "admin", "role": "super",
                "source": "query"}
    host = (request.headers.get("host") or "").split(":")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[0] not in ("www", "api", "app"):
        return {"id": _slugify(parts[0]), "user": "owner", "role": "owner",
                "source": "subdomain"}
    return {"id": "default", "user": "guest", "role": "guest",
            "source": "fallback"}


def _list_workshops():
    from main import store_list as _store_list
    tok = _current_workshop.set("default")
    try:
        return _store_list("workshops")
    except KeyError:
        return []
    finally:
        _current_workshop.reset(tok)


def _get_workshop(wid):
    for w in _list_workshops():
        if w.get("id") == wid:
            return w
    return None


def _save_workshop(rec):
    from main import store_save
    tok = _current_workshop.set("default")
    try:
        return store_save("workshops", rec["id"], rec)
    finally:
        _current_workshop.reset(tok)


def _check_pin(workshop_id, pin):
    w = _get_workshop(workshop_id)
    if not w or not w.get("active", True):
        return None
    if str(w.get("owner_pin", "")) == str(pin):
        return w
    return None


# ═══════════════════════════════════════════════════════════════
# API — tenancy
# ═══════════════════════════════════════════════════════════════
@router.get("/api/tenancy/status")
def tenancy_status():
    return {"multi_tenant": MULTI_TENANT,
            "session_secret_set": SESSION_SECRET != "change-me-please",
            "super_admin_configured": bool(SUPER_ADMIN_PIN),
            "current": get_current_workshop()}


@router.get("/api/tenancy/current")
def tenancy_current(request: Request):
    info = resolve_workshop(request)
    return {"workshop_id": info["id"], "user": info["user"],
            "role": info["role"], "source": info["source"]}


@router.get("/api/tenancy/debug/gate")
def debug_gate(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    return {"multi_tenant": MULTI_TENANT, "cookie_present": bool(token),
            "session_valid": bool(session),
            "session_ws": session.get("ws") if session else None,
            "path": str(request.url.path),
            "is_public": _is_public(str(request.url.path)),
            "is_api": str(request.url.path).startswith("/api/")}


@router.get("/api/tenancy/workshops")
def list_workshops(request: Request):
    pin = request.query_params.get("admin_pin") or \
          request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Super-admin PIN required")
    items = _list_workshops()
    safe = [{k: v for k, v in w.items() if k != "owner_pin"} for w in items]
    return {"count": len(safe), "workshops": safe}


@router.post("/api/tenancy/workshops")
async def create_workshop(request: Request):
    pin = request.query_params.get("admin_pin") or \
          request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Super-admin PIN required")
    d = await request.json()
    name = (d.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "name required")
    wid = _slugify(d.get("id") or name)
    if _get_workshop(wid):
        raise HTTPException(409, f"Workshop '{wid}' already exists")
    rec = {"id": wid, "name": name,
           "owner_email": (d.get("owner_email") or "").strip(),
           "owner_phone": (d.get("owner_phone") or "").strip(),
           "owner_pin": str(d.get("owner_pin") or "1234"),
           "plan": d.get("plan") or "pro", "active": True,
           "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "notes": (d.get("notes") or "").strip()}
    _save_workshop(rec)
    return {"success": True,
            "workshop": {k: v for k, v in rec.items() if k != "owner_pin"}}


@router.delete("/api/tenancy/workshops/{wid}")
def deactivate_workshop(wid: str, request: Request):
    pin = request.query_params.get("admin_pin") or \
          request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Super-admin PIN required")
    w = _get_workshop(wid)
    if not w:
        raise HTTPException(404)
    w["active"] = False
    _save_workshop(w)
    return {"success": True}


# ═══════════════════════════════════════════════════════════════
# Auth routes
# ═══════════════════════════════════════════════════════════════
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/", ws: str = ""):
    return HTMLResponse(_login_html(next, ws))


@router.post("/api/login")
async def do_login(request: Request):
    d = await request.json()
    code = _slugify(d.get("workshop") or "default")
    pin = str(d.get("pin") or "")
    if not pin:
        raise HTTPException(400, "PIN required")
    w = _check_pin(code, pin)
    if not w:
        raise HTTPException(401, "Invalid workshop or PIN")
    token = _make_session(code, user="owner", role="owner")
    resp = JSONResponse({"success": True, "workshop": code,
                         "name": w.get("name")})
    resp.set_cookie(COOKIE_NAME, token, max_age=SESSION_DAYS * 24 * 3600,
                    httponly=True, samesite="lax", secure=False, path="/")
    return resp


@router.get("/logout")
def do_logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


def _login_html(next_url, ws=""):
    return """<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in — RamsTech</title>
<style>
  *{box-sizing:border-box}
  body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;
    padding:0;background:#111;color:#fff;min-height:100vh;display:flex;
    align-items:center;justify-content:center}
  .card{width:100%;max-width:380px;padding:40px 32px;background:#1a1a1a;
    border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.5)}
  .logo{width:56px;height:56px;border-radius:14px;background:#fff;color:#111;
    display:flex;align-items:center;justify-content:center;font-weight:900;
    font-size:22px;letter-spacing:-1px;margin-bottom:20px}
  h1{margin:0 0 6px;font-size:22px;letter-spacing:-0.5px;font-weight:800}
  .sub{color:#888;font-size:13px;margin:0 0 28px}
  label{display:block;font-size:11px;text-transform:uppercase;
    letter-spacing:1px;color:#888;font-weight:700;margin:16px 0 6px}
  input{width:100%;padding:14px;border:1px solid #333;border-radius:10px;
    font-size:16px;background:#0d0d0d;color:#fff;font-family:inherit}
  input:focus{outline:none;border-color:#fff}
  button{width:100%;padding:14px;margin-top:24px;background:#fff;color:#111;
    border:none;border-radius:10px;font-weight:800;font-size:14px;
    cursor:pointer;letter-spacing:0.3px}
  button:hover{background:#e5e5e5}
  button:disabled{background:#444;color:#888;cursor:not-allowed}
  .err{background:#3b0a0a;color:#fca5a5;padding:12px;border-radius:10px;
    font-size:13px;margin-top:16px;display:none}
  .err.on{display:block}
  .hint{text-align:center;margin-top:24px;font-size:12px;color:#555}
  .hint a{color:#888;text-decoration:none}
</style></head>
<body>
<div class="card">
  <div class="logo">RT</div>
  <h1>Welcome back</h1>
  <p class="sub">Sign in to your workshop</p>
  <form onsubmit="return doLogin(event)">
    <label>Workshop code</label>
    <input name="workshop" id="ws" placeholder="e.g. rams-auto"
           autocomplete="username" required autofocus value=""" + json.dumps(ws or "") + """>
    <label>Owner PIN</label>
    <input name="pin" id="pin" type="password" inputmode="numeric"
           placeholder="••••" autocomplete="current-password" required>
    <button type="submit" id="btn">Sign in</button>
    <div class="err" id="err"></div>
  </form>
  <div class="hint"><a href="/">← Back to home</a></div>
</div>
<script>
const NEXT = """ + json.dumps(next_url) + """;
async function doLogin(e){
  e.preventDefault();
  const btn=document.getElementById("btn");
  const err=document.getElementById("err");
  err.classList.remove("on");
  btn.disabled=true; btn.textContent="Signing in…";
  try{
    const r=await fetch("/api/login",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({workshop:document.getElementById("ws").value,
        pin:document.getElementById("pin").value})});
    const d=await r.json();
    if(!r.ok||!d.success){
      err.textContent=d.detail||d.error||"Sign in failed";
      err.classList.add("on");btn.disabled=false;btn.textContent="Sign in";
      return false;
    }
    window.location.href=NEXT||"/";
  }catch(ex){
    err.textContent="Network error: "+ex.message;
    err.classList.add("on");btn.disabled=false;btn.textContent="Sign in";
  }
  return false;
}
const params=new URLSearchParams(window.location.search);
if(params.get("ws")&&!document.getElementById("ws").value){
  document.getElementById("ws").value=params.get("ws");
}
</script></body></html>"""


# ═══════════════════════════════════════════════════════════════
# Admin UI
# ═══════════════════════════════════════════════════════════════
@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(_admin_html())


def _admin_html():
    return """<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Super Admin — RamsTech</title>
<style>
  *{box-sizing:border-box}
  body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;
    padding:20px 16px 60px;background:#0f0f0f;color:#fff}
  .wrap{max-width:640px;margin:0 auto}
  h1{font-size:22px;margin:0 0 6px;letter-spacing:-0.4px}
  .sub{color:#888;font-size:13px;margin:0 0 24px}
  .card{background:#1a1a1a;border-radius:14px;padding:20px;
    margin-bottom:16px;border:1px solid #2a2a2a}
  label{display:block;font-size:11px;text-transform:uppercase;
    letter-spacing:1px;color:#888;font-weight:700;margin-bottom:6px}
  input,select{width:100%;padding:12px;border:1px solid #333;border-radius:10px;
    font-size:15px;background:#0d0d0d;color:#fff;font-family:inherit;
    margin-bottom:14px}
  input:focus,select:focus{outline:none;border-color:#fff}
  button{padding:13px 20px;background:#16a34a;color:#fff;border:none;
    border-radius:10px;font-weight:800;font-size:14px;cursor:pointer;
    letter-spacing:0.3px;width:100%}
  button.secondary{background:#333}
  .err,.ok{padding:12px;border-radius:10px;font-size:13px;margin-bottom:14px;
    display:none}
  .err{background:#3b0a0a;color:#fca5a5}
  .ok{background:#0a3b1a;color:#86efac}
  .err.on,.ok.on{display:block}
  .hdr{display:flex;align-items:center;justify-content:space-between;
    margin-bottom:16px}
  .ws-list{display:flex;flex-direction:column;gap:10px}
  .ws-item{background:#222;padding:14px;border-radius:10px;display:flex;
    align-items:center;justify-content:space-between;gap:12px}
  .ws-item .name{font-weight:700;font-size:15px;margin-bottom:3px}
  .ws-item .code{font-family:ui-monospace,Menlo,monospace;font-size:12px;
    color:#888}
  .ws-item .plan{display:inline-block;padding:2px 8px;border-radius:12px;
    font-size:10px;font-weight:800;text-transform:uppercase;
    letter-spacing:0.5px;background:#2a2a2a;color:#aaa;margin-left:6px}
  .ws-item .plan.pro{background:#1e40af;color:#93c5fd}
  .ws-item .plan.starter{background:#4c1d95;color:#c4b5fd}
  .ws-item .plan.workshop{background:#166534;color:#86efac}
  .ws-item .active-dot{width:8px;height:8px;border-radius:50%;
    background:#16a34a;display:inline-block;margin-right:6px}
  .ws-item.inactive .active-dot{background:#666}
  .ws-actions{display:flex;gap:6px}
  .ws-actions button{width:auto;padding:8px 12px;font-size:12px;background:#333}
  .pin-row{display:flex;gap:10px;align-items:flex-end}
  .pin-row input{margin-bottom:0;flex:1}
  .pin-row button{width:auto;padding:12px 20px}
</style></head>
<body>
<div class="wrap">
  <h1>Super Admin</h1>
  <p class="sub">Manage workshops · create · list · share login links</p>
  <div class="card">
    <div class="err" id="err"></div>
    <div class="ok" id="ok"></div>
    <label>Super-admin PIN</label>
    <div class="pin-row">
      <input id="pin" type="password" inputmode="numeric"
             placeholder="Enter admin PIN" autocomplete="off">
      <button onclick="savePin()">Unlock</button>
    </div>
  </div>
  <div id="workspace" style="display:none">
    <div class="card">
      <div class="hdr"><strong style="font-size:15px">Create workshop</strong></div>
      <label>Workshop name</label>
      <input id="w_name" placeholder="e.g. Rams Auto Repairs">
      <label>Workshop code (URL-safe, lowercase)</label>
      <input id="w_id" placeholder="e.g. rams-auto">
      <label>Owner PIN (4–6 digits)</label>
      <input id="w_pin" type="text" inputmode="numeric" placeholder="e.g. 4821">
      <label>Owner email (optional)</label>
      <input id="w_email" type="email" placeholder="owner@example.com">
      <label>Plan</label>
      <select id="w_plan">
        <option value="starter">Starter</option>
        <option value="pro" selected>Pro</option>
        <option value="workshop">Workshop</option>
      </select>
      <button onclick="createWorkshop()">Create workshop</button>
    </div>
    <div class="card">
      <div class="hdr">
        <strong style="font-size:15px">Existing workshops</strong>
        <button class="secondary" style="width:auto;padding:6px 12px;
                font-size:12px" onclick="loadList()">↻</button>
      </div>
      <div class="ws-list" id="ws_list">
        <div style="color:#888;font-size:13px">Loading…</div>
      </div>
    </div>
  </div>
</div>
<script>
let PIN=sessionStorage.getItem("rt_admin_pin")||"";
function showMsg(kind,text){
  const el=document.getElementById(kind==="err"?"err":"ok");
  el.textContent=text;el.classList.add("on");
  setTimeout(()=>el.classList.remove("on"),5000);
}
function savePin(){
  const v=document.getElementById("pin").value.trim();
  if(!v)return;PIN=v;sessionStorage.setItem("rt_admin_pin",v);unlock();
}
function unlock(){
  if(!PIN)return;
  document.getElementById("workspace").style.display="block";loadList();
}
async function loadList(){
  const el=document.getElementById("ws_list");
  el.innerHTML="<div style='color:#888;font-size:13px'>Loading…</div>";
  try{
    const r=await fetch("/api/tenancy/workshops?admin_pin="+encodeURIComponent(PIN));
    if(r.status===403){
      el.innerHTML="<div style='color:#fca5a5;font-size:13px'>Invalid admin PIN.</div>";
      return;
    }
    const d=await r.json();
    if(!d.workshops||!d.workshops.length){
      el.innerHTML="<div style='color:#888;font-size:13px'>No workshops yet. Create one above.</div>";
      return;
    }
    el.innerHTML=d.workshops.map(w=>`
      <div class="ws-item ${w.active===false?'inactive':''}">
        <div>
          <div class="name">
            <span class="active-dot"></span>${esc(w.name)}
            <span class="plan ${w.plan||''}">${w.plan||'—'}</span>
          </div>
          <div class="code">${esc(w.id)}${w.owner_email?' · '+esc(w.owner_email):''}</div>
        </div>
        <div class="ws-actions">
          <button onclick="copyLogin('${esc(w.id)}')">Share</button>
        </div>
      </div>
    `).join("");
  }catch(e){
    el.innerHTML="<div style='color:#fca5a5;font-size:13px'>Error: "+e.message+"</div>";
  }
}
function copyLogin(id){
  const url=window.location.origin+"/login?ws="+id;
  const msg="Your RamsTech login:\\n"+url+"\\n\\nUse your owner PIN to sign in.";
  if(navigator.clipboard){
    navigator.clipboard.writeText(msg)
      .then(()=>showMsg("ok","Login link copied to clipboard"))
      .catch(()=>prompt("Copy this link:",url));
  }else{prompt("Copy this link:",url);}
}
async function createWorkshop(){
  const name=document.getElementById("w_name").value.trim();
  const id=document.getElementById("w_id").value.trim();
  const pin=document.getElementById("w_pin").value.trim();
  const email=document.getElementById("w_email").value.trim();
  const plan=document.getElementById("w_plan").value;
  if(!name||!pin){showMsg("err","Name and PIN are required");return;}
  try{
    const r=await fetch("/api/tenancy/workshops?admin_pin="+encodeURIComponent(PIN),{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({name,id:id||undefined,owner_pin:pin,
        owner_email:email,plan})});
    const d=await r.json();
    if(!r.ok){showMsg("err",d.detail||d.error||"Failed to create");return;}
    showMsg("ok","Created workshop: "+d.workshop.id);
    document.getElementById("w_name").value="";
    document.getElementById("w_id").value="";
    document.getElementById("w_pin").value="";
    document.getElementById("w_email").value="";
    loadList();
  }catch(e){showMsg("err","Error: "+e.message);}
}
function esc(s){
  return String(s||"").replace(/[&<>"']/g,m=>(
    {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
}
if(PIN){document.getElementById("pin").value=PIN;unlock();}
</script></body></html>"""


# ═══════════════════════════════════════════════════════════════
# SALES KIT — merged in so no extra module is needed
# ═══════════════════════════════════════════════════════════════
_PRINT_CSS = """
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;color:#111;
    background:#f5f5f5;line-height:1.5;-webkit-font-smoothing:antialiased}
  .page{width:210mm;min-height:297mm;margin:20px auto;background:#fff;
    padding:16mm 14mm;box-shadow:0 4px 20px rgba(0,0,0,0.08)}
  @media print{
    @page{size:A4;margin:0}
    body{background:#fff}
    .page{margin:0;box-shadow:none;width:auto;min-height:auto;padding:14mm 12mm}
    .no-print{display:none!important}
  }
  .no-print{max-width:210mm;margin:20px auto 0;padding:12px 14mm;background:#111;
    color:#fff;border-radius:8px;font-size:13px;text-align:center}
  .no-print a{color:#fff;font-weight:700}
"""


def _esc(s):
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


@router.get("/kit", response_class=HTMLResponse)
def kit_index():
    return HTMLResponse("""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sales Kit — RamsTech</title>
<style>
body{font-family:-apple-system,sans-serif;background:#111;color:#fff;
  padding:40px 20px;max-width:500px;margin:0 auto}
h1{font-size:22px;margin:0 0 6px;letter-spacing:-0.5px}
p{color:#888;font-size:13px;margin:0 0 30px}
a{display:block;padding:16px 20px;background:#1a1a1a;border:1px solid #2a2a2a;
  border-radius:12px;text-decoration:none;color:#fff;margin-bottom:10px;
  font-weight:600;font-size:14px}
a:hover{background:#222;border-color:#444}
a .sub{display:block;color:#888;font-size:12px;font-weight:400;margin-top:3px}
</style></head><body>
<h1>Sales Kit</h1>
<p>Print these to PDF from any phone browser.</p>
<a href="/kit/leave-behind">
  📄 Leave-Behind Brochure
  <span class="sub">Customer-facing one-pager. Share after a demo.</span>
</a>
<a href="/kit/case-study?pin=YOUR_PIN">
  📈 Case Study Template
  <span class="sub">Replace YOUR_PIN with your admin PIN. Fill via URL.</span>
</a>
<a href="/kit/onboarding?pin=YOUR_PIN">
  ✅ Onboarding Checklist
  <span class="sub">Replace YOUR_PIN. Print before every setup.</span>
</a>
</body></html>""")


@router.get("/kit/leave-behind", response_class=HTMLResponse)
def kit_leave_behind():
    return HTMLResponse("""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RamsTech — Workshop Software</title>
<style>""" + _PRINT_CSS + """
.brand{display:flex;align-items:center;gap:12px;margin-bottom:6mm}
.logo{width:44px;height:44px;background:#111;color:#fff;border-radius:10px;
  display:flex;align-items:center;justify-content:center;font-weight:900;
  font-size:18px;letter-spacing:-1px}
.brand h1{font-size:22px;letter-spacing:-0.5px;font-weight:800}
.brand .tag{font-size:11px;color:#666;text-transform:uppercase;
  letter-spacing:1px;font-weight:700}
.hero{font-size:26px;font-weight:900;letter-spacing:-1px;line-height:1.15;
  margin:6mm 0 4mm}
.hero .accent{color:#16a34a}
.problem{background:#fafafa;border-left:4px solid #dc2626;padding:5mm 6mm;
  border-radius:6px;margin-bottom:6mm;font-size:13px;line-height:1.6}
.problem strong{color:#dc2626}
h2{font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#666;
  font-weight:800;margin:6mm 0 3mm;padding-bottom:2mm;border-bottom:1px solid #eee}
.features{display:grid;gap:3mm}
.feature{display:flex;gap:4mm;align-items:flex-start}
.feature .icon{flex-shrink:0;width:24px;height:24px;background:#f0fdf4;
  border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-size:14px}
.feature .text{font-size:12.5px;line-height:1.55}
.feature .text strong{font-weight:700;display:block;margin-bottom:1px}
.feature .text span{color:#555}
.roi{background:#111;color:#fff;padding:5mm 6mm;border-radius:8px;margin:6mm 0}
.roi h3{font-size:14px;font-weight:800;margin-bottom:2mm}
.roi p{font-size:12px;line-height:1.6;color:#ddd}
.roi strong{color:#4ade80;font-weight:700}
.pricing{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3mm}
.tier{border:1px solid #e5e5e5;border-radius:8px;padding:4mm;text-align:center}
.tier.featured{border:2px solid #111;position:relative}
.tier.featured::before{content:"MOST POPULAR";position:absolute;top:-8px;
  left:50%;transform:translateX(-50%);background:#111;color:#fff;
  font-size:8px;font-weight:800;letter-spacing:1px;padding:2px 8px;
  border-radius:10px;white-space:nowrap}
.tier .name{font-size:11px;text-transform:uppercase;letter-spacing:1px;
  color:#666;font-weight:800;margin-bottom:3mm}
.tier .price{font-size:22px;font-weight:900;letter-spacing:-1px;line-height:1}
.tier .price small{font-size:11px;font-weight:500;color:#666}
.tier .target{font-size:10px;color:#666;margin-top:2mm;line-height:1.4}
.offer{background:#f0fdf4;border:1px dashed #16a34a;border-radius:8px;
  padding:4mm 6mm;margin:6mm 0;text-align:center}
.offer strong{color:#166534;font-size:14px;display:block;margin-bottom:2mm}
.offer span{font-size:12px;color:#333}
.guarantee{display:flex;gap:3mm;align-items:center;background:#fafafa;
  padding:3mm 5mm;border-radius:6px;font-size:11.5px;margin-top:6mm}
.guarantee .g-icon{font-size:20px;color:#16a34a}
.contact{margin-top:8mm;padding-top:5mm;border-top:1px solid #eee;display:flex;
  justify-content:space-between;align-items:center;font-size:12px}
.contact .cta{font-weight:800;font-size:13px}
.contact .info{color:#555}
</style></head><body>
<div class="no-print">📄 <a href="#" onclick="window.print();return false;">Tap here to print to PDF</a></div>
<div class="page">
  <div class="brand">
    <div class="logo">RT</div>
    <div>
      <div class="tag">RamsTech</div>
      <h1>Workshop Management, Done Right</h1>
    </div>
  </div>
  <div class="hero">Stop chasing money.<br><span class="accent">Start collecting it.</span></div>
  <div class="problem">Independent workshops lose <strong>R15,000 – R50,000 every month</strong> in late payments. You spend hours phoning customers who "forgot." RamsTech chases them for you — automatically.</div>
  <h2>What it does</h2>
  <div class="features">
    <div class="feature"><div class="icon">💰</div><div class="text"><strong>Aged Debtors Report</strong><span>See exactly who owes you what, colour-coded by how overdue.</span></div></div>
    <div class="feature"><div class="icon">💬</div><div class="text"><strong>WhatsApp Reminders</strong><span>Auto-tone by how overdue — friendly, firm, or urgent.</span></div></div>
    <div class="feature"><div class="icon">💳</div><div class="text"><strong>Pay-Now Links</strong><span>Customer taps, pays by card, invoice marks itself paid.</span></div></div>
    <div class="feature"><div class="icon">⚙</div><div class="text"><strong>Auto-Reminder Scheduler</strong><span>Chases everyone 30+ days overdue while you sleep.</span></div></div>
    <div class="feature"><div class="icon">📊</div><div class="text"><strong>Profit Dashboard</strong><span>See which jobs, technicians, and services actually make money.</span></div></div>
  </div>
  <div class="roi">
    <h3>The math is simple.</h3>
    <p>A workshop billing <strong>R450/hour</strong> only needs to recover <strong>4 extra billable hours per month</strong> to cover the Pro plan. Most workshops recover that in the first week — from invoices they'd have written off.</p>
  </div>
  <h2>Pricing</h2>
  <div class="pricing">
    <div class="tier"><div class="name">Starter</div><div class="price">R499<small>/mo</small></div><div class="target">Solo mechanics<br>& 1–2 bay shops</div></div>
    <div class="tier featured"><div class="name">Pro</div><div class="price">R1,499<small>/mo</small></div><div class="target">Established workshops<br>3–6 bays</div></div>
    <div class="tier"><div class="name">Workshop</div><div class="price">R2,999<small>/mo</small></div><div class="target">Multi-bay groups<br>& locations</div></div>
  </div>
  <div class="offer">
    <strong>Founding Member Offer — First 5 Workshops Only</strong>
    <span>R749/month (50% off) for the first 6 months. Free setup (normally R5,000).</span>
  </div>
  <div class="guarantee">
    <div class="g-icon">✓</div>
    <div><strong>30-day money-back guarantee.</strong> If it doesn't save you time or make you money in your first month, we refund every cent. No forms. No arguments.</div>
  </div>
  <div class="contact">
    <div class="cta">Book a 15-minute demo →</div>
    <div class="info">WhatsApp: <strong>[YOUR NUMBER]</strong><br>Email: [YOUR EMAIL]</div>
  </div>
</div>
</body></html>""")


@router.get("/kit/case-study", response_class=HTMLResponse)
def kit_case_study(request: Request):
    pin = request.query_params.get("pin") or request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Admin PIN required (?pin=...)")
    q = request.query_params
    name = _esc(q.get("name", "Rams Auto Repairs"))
    owner = _esc(q.get("owner", "Owner Name"))
    collected = _esc(q.get("collected", "47,500"))
    invoices = _esc(q.get("invoices", "23"))
    hours_saved = _esc(q.get("hours", "12"))
    months = _esc(q.get("months", "1"))
    quote = _esc(q.get("quote",
        "I used to spend Sunday nights chasing payments. Now it happens "
        "by itself — I just check the dashboard Monday morning."))
    return HTMLResponse("""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Case Study — """ + name + """</title>
<style>""" + _PRINT_CSS + """
.kicker{font-size:11px;text-transform:uppercase;letter-spacing:2px;
  color:#16a34a;font-weight:800;margin-bottom:3mm}
h1{font-size:30px;font-weight:900;letter-spacing:-1.2px;line-height:1.15;
  margin-bottom:4mm}
.sub{font-size:14px;color:#555;line-height:1.6;margin-bottom:8mm;
  max-width:155mm}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:4mm;
  margin-bottom:8mm}
.metric{background:#111;color:#fff;padding:5mm 4mm;border-radius:10px;
  text-align:center}
.metric .num{font-size:24px;font-weight:900;letter-spacing:-1px;
  color:#4ade80;line-height:1}
.metric .lbl{font-size:10px;text-transform:uppercase;letter-spacing:1px;
  color:#999;font-weight:700;margin-top:2mm}
h2{font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#666;
  font-weight:800;margin:7mm 0 3mm;padding-bottom:2mm;border-bottom:1px solid #eee}
.body-text{font-size:13px;line-height:1.7;color:#333;margin-bottom:4mm}
.body-text strong{color:#111}
.quote{border-left:4px solid #16a34a;padding:4mm 6mm;background:#f0fdf4;
  border-radius:0 8px 8px 0;font-size:14px;font-style:italic;line-height:1.6;
  color:#166534;margin:6mm 0}
.quote .attr{display:block;margin-top:3mm;font-style:normal;font-size:12px;
  font-weight:700;color:#111}
.cta-block{margin-top:8mm;padding:5mm 6mm;background:#111;color:#fff;
  border-radius:10px;display:flex;justify-content:space-between;
  align-items:center}
.cta-block .cta-text{font-size:14px;font-weight:700}
.cta-block .cta-sub{font-size:11px;color:#999;margin-top:1mm}
.cta-block .cta-btn{background:#16a34a;color:#fff;padding:3mm 5mm;
  border-radius:6px;font-weight:800;font-size:12px;text-decoration:none}
</style></head><body>
<div class="no-print">📄 <a href="#" onclick="window.print();return false;">Print to PDF</a></div>
<div class="page">
  <div class="kicker">Case Study · RamsTech</div>
  <h1>How """ + name + """ collected<br>R""" + collected + """ in overdue invoices<br>in """ + months + """ month</h1>
  <p class="sub">""" + owner + """ used to spend evenings chasing unpaid invoices by phone. Here's what changed when they switched to RamsTech.</p>
  <div class="metrics">
    <div class="metric"><div class="num">R""" + collected + """</div><div class="lbl">Collected</div></div>
    <div class="metric"><div class="num">""" + invoices + """</div><div class="lbl">Invoices Chased</div></div>
    <div class="metric"><div class="num">""" + hours_saved + """h</div><div class="lbl">Admin Saved / Mo</div></div>
  </div>
  <h2>The Problem</h2>
  <p class="body-text">Like most independent workshops, <strong>""" + name + """</strong> relied on a mix of paper job cards, WhatsApp messages, and memory. Late payments were the norm. Following up meant stopping work, pulling a customer's file, and having an awkward conversation — so it kept sliding.</p>
  <h2>What Changed</h2>
  <p class="body-text">Within a week of switching to RamsTech, every overdue invoice had a live pay-now link in a WhatsApp message — sent automatically, with the tone tuned to how overdue it was. The owner stopped chasing. <strong>RamsTech chased for them.</strong></p>
  <p class="body-text">A month in, the numbers spoke for themselves: <strong>R""" + collected + """</strong> collected from customers who had been sitting on invoices for 30, 60, and even 90+ days. Work that used to take hours of admin every week now happens on autopilot.</p>
  <div class="quote">""" + quote + """<span class="attr">— """ + owner + """, """ + name + """</span></div>
  <div class="cta-block">
    <div>
      <div class="cta-text">See it work on your own invoices.</div>
      <div class="cta-sub">15-minute demo. No obligation. On-site or remote.</div>
    </div>
    <a class="cta-btn" href="#">Book a Demo →</a>
  </div>
</div>
</body></html>""")


@router.get("/kit/onboarding", response_class=HTMLResponse)
def kit_onboarding(request: Request):
    pin = request.query_params.get("pin") or request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Admin PIN required (?pin=...)")
    return HTMLResponse("""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Client Onboarding — RamsTech</title>
<style>""" + _PRINT_CSS + """
h1{font-size:26px;font-weight:900;letter-spacing:-1px;margin-bottom:3mm}
.sub{font-size:13px;color:#555;margin-bottom:8mm}
.client-info{background:#fafafa;padding:4mm 5mm;border-radius:8px;
  margin-bottom:8mm;font-size:12.5px;line-height:2}
.client-info .lbl{color:#666;font-weight:700;display:inline-block;width:32mm}
.client-info .line{display:inline-block;min-width:100mm;
  border-bottom:1px solid #ccc}
h2{font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#111;
  font-weight:800;margin:7mm 0 3mm;padding-bottom:2mm;border-bottom:2px solid #111}
.task{display:flex;gap:3mm;align-items:flex-start;padding:2.5mm 0;
  font-size:12.5px;line-height:1.5;border-bottom:1px solid #f0f0f0}
.task:last-child{border-bottom:none}
.task .box{flex-shrink:0;width:5mm;height:5mm;border:1.5px solid #111;
  border-radius:2px;margin-top:1px}
.task .body{flex:1}
.task .title{font-weight:700}
.task .note{color:#666;font-size:11.5px;margin-top:1px}
.footer{margin-top:10mm;padding-top:5mm;border-top:1px solid #eee;display:flex;
  justify-content:space-between;font-size:11px;color:#888}
</style></head><body>
<div class="no-print">🖨 <a href="#" onclick="window.print();return false;">Print to PDF</a></div>
<div class="page">
  <h1>Client Onboarding Checklist</h1>
  <p class="sub">Complete every step on Day 1. Walk the client through each button that matters.</p>
  <div class="client-info">
    <div><span class="lbl">Workshop name:</span><span class="line"></span></div>
    <div><span class="lbl">Owner name:</span><span class="line"></span></div>
    <div><span class="lbl">Owner cell:</span><span class="line"></span></div>
    <div><span class="lbl">Workshop code:</span><span class="line"></span></div>
    <div><span class="lbl">Owner PIN set:</span><span class="line"></span></div>
    <div><span class="lbl">Plan:</span><span class="line"></span></div>
    <div><span class="lbl">Setup fee paid:</span><span class="line"></span></div>
    <div><span class="lbl">Onboarded by:</span><span class="line"></span></div>
    <div><span class="lbl">Date:</span><span class="line"></span></div>
  </div>
  <h2>1. Workshop Setup</h2>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Create workshop in /admin</div><div class="note">Name, code (lowercase), owner PIN.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Log in as the client on their phone</div><div class="note">Use /login?ws=CODE. Add to home screen.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Configure workshop profile</div><div class="note">Logo, labour rate, VAT, bank details.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Set profit-model defaults</div><div class="note">Tech rate, parts ratio, overhead.</div></div></div>
  <h2>2. Import Existing Data</h2>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Top 20 customers</div><div class="note">Name, phone, email.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Top 10 overdue invoices</div><div class="note">Customer, description, amount, due date.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Existing staff</div><div class="note">Name, role, hourly rate.</div></div></div>
  <h2>3. Live Demo — The 4 Buttons</h2>
  <div class="task"><div class="box"></div><div class="body"><div class="title">💰 Debtors</div><div class="note">Point at a red row. Explain ageing buckets.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">💬 Remind &amp; Pay</div><div class="note">Send to the owner's own phone. Watch it arrive.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">🔗 Share portal</div><div class="note">Open /portal/PHONE. Let them tap around.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">⚙ Auto-remind</div><div class="note">Min 30 days, cooldown 7. Confirm enabled.</div></div></div>
  <h2>4. Confirm Handover</h2>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Client can log in unassisted</div><div class="note">Have them log out and back in without help.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Client has your WhatsApp number</div><div class="note">Needed for first-week check-ins.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Follow-ups scheduled</div><div class="note">Day 2, 7 WhatsApp. Day 14 call. Day 30 case study.</div></div></div>
  <div class="task"><div class="box"></div><div class="body"><div class="title">Setup fee received or invoiced</div><div class="note">Do not leave without payment or signed invoice.</div></div></div>
  <div class="footer">
    <span>RamsTech Onboarding — internal use</span>
    <span>Signature: _____________________</span>
  </div>
</div>
</body></html>""")


# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE — tenancy context + auth gate
# ═══════════════════════════════════════════════════════════════
_PUBLIC_PREFIXES = (
    "/login", "/logout", "/api/login",
    "/admin", "/api/tenancy/",
    "/health", "/push-sw.js", "/api/realtime/config",
    "/pay/", "/portal/", "/api/portal/",
    "/api/payments/webhook/",
    "/api/auto-remind/run", "/api/auto-remind/status",
    "/favicon.ico", "/robots.txt",
    "/manifest.json", "/service-worker.js", "/sw.js",
    "/kit",
)


def _is_public(path):
    for p in _PUBLIC_PREFIXES:
        if path == p or path.startswith(p):
            return True
    return False


async def tenancy_middleware(request: Request, call_next):
    if not MULTI_TENANT:
        _current_workshop.set("default")
        return await call_next(request)

    path = request.url.path
    if not _is_public(path):
        token = request.cookies.get(COOKIE_NAME)
        session = _verify(token)
        if not session:
            if path.startswith("/api/"):
                return JSONResponse(
                    {"detail": "Not authenticated", "login": "/login"},
                    status_code=401)
            nxt = path if path.startswith("/") else "/"
            return RedirectResponse(f"/login?next={nxt}", status_code=302)

    info = resolve_workshop(request)
    ctx_token = _current_workshop.set(info["id"])
    try:
        response = await call_next(request)
    finally:
        _current_workshop.reset(ctx_token)
    return response
