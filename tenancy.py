"""
Multi-tenancy — one codebase, many workshops.

Design: OFF by default. Set MULTI_TENANT=1 on Render to enable.
When OFF: every row behaves as workshop_id="default" — zero behaviour change.
When ON:  every read/write is scoped to the requesting workshop.

Auth gate: when MULTI_TENANT=1, unauthenticated requests to non-public
paths are blocked. API paths always get JSON 401; browser paths get
redirected to /login.
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

router = APIRouter(tags=["tenancy"])


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


# ═══════════════════════════════════════════════════════════════
# SLUGIFY
# ═══════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════
# REQUEST → WORKSHOP RESOLUTION
# ═══════════════════════════════════════════════════════════════
def resolve_workshop(request):
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    if session and session.get("ws"):
        return {
            "id": session["ws"],
            "user": session.get("user", "owner"),
            "role": session.get("role", "owner"),
            "source": "cookie",
        }

    qs = request.query_params.get("ws")
    if qs and SUPER_ADMIN_PIN and \
       request.query_params.get("admin_pin") == SUPER_ADMIN_PIN:
        return {"id": _slugify(qs), "user": "admin", "role": "super", "source": "query"}

    host = (request.headers.get("host") or "").split(":")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[0] not in ("www", "api", "app"):
        return {"id": _slugify(parts[0]), "user": "owner", "role": "owner",
                "source": "subdomain"}

    return {"id": "default", "user": "guest", "role": "guest", "source": "fallback"}


# ═══════════════════════════════════════════════════════════════
# WORKSHOPS STORE
# ═══════════════════════════════════════════════════════════════
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
    if not w:
        return None
    if not w.get("active", True):
        return None
    if str(w.get("owner_pin", "")) == str(pin):
        return w
    return None


# ═══════════════════════════════════════════════════════════════
# ROUTES — API
# ═══════════════════════════════════════════════════════════════
@router.get("/api/tenancy/status")
def tenancy_status():
    return {
        "multi_tenant": MULTI_TENANT,
        "session_secret_set": SESSION_SECRET != "change-me-please",
        "super_admin_configured": bool(SUPER_ADMIN_PIN),
        "current": get_current_workshop(),
    }


@router.get("/api/tenancy/current")
def tenancy_current(request: Request):
    info = resolve_workshop(request)
    return {
        "workshop_id": info["id"],
        "user": info["user"],
        "role": info["role"],
        "source": info["source"],
    }


@router.get("/api/tenancy/debug/gate")
def debug_gate(request: Request):
    """Diagnostic — shows exactly what the middleware sees for this request."""
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    return {
        "multi_tenant": MULTI_TENANT,
        "cookie_name": COOKIE_NAME,
        "cookie_present": bool(token),
        "cookie_length": len(token) if token else 0,
        "session_valid": bool(session),
        "session_ws": session.get("ws") if session else None,
        "path": str(request.url.path),
        "is_public": _is_public(str(request.url.path)),
        "is_api": str(request.url.path).startswith("/api/"),
    }


@router.get("/api/tenancy/workshops")
def list_workshops(request: Request):
    pin = request.query_params.get("admin_pin") or \
          request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Super-admin PIN required")
    items = _list_workshops()
    safe = []
    for w in items:
        safe.append({k: v for k, v in w.items() if k != "owner_pin"})
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

    rec = {
        "id": wid,
        "name": name,
        "owner_email": (d.get("owner_email") or "").strip(),
        "owner_phone": (d.get("owner_phone") or "").strip(),
        "owner_pin": str(d.get("owner_pin") or "1234"),
        "plan": d.get("plan") or "pro",
        "active": True,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "notes": (d.get("notes") or "").strip(),
    }
    _save_workshop(rec)
    return {"success": True, "workshop": {k: v for k, v in rec.items()
                                          if k != "owner_pin"}}


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
# ROUTES — Auth
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
    resp.set_cookie(
        COOKIE_NAME, token,
        max_age=SESSION_DAYS * 24 * 3600,
        httponly=True, samesite="lax", secure=False, path="/",
    )
    return resp


@router.get("/logout")
def do_logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE HTML
# ═══════════════════════════════════════════════════════════════
def _login_html(next_url, ws=""):
    return """<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in — RamsTech</title>
<style>
  *{box-sizing:border-box}
  body{
    font-family:-apple-system,"Segoe UI",Roboto,sans-serif;
    margin:0;padding:0;background:#111;color:#fff;min-height:100vh;
    display:flex;align-items:center;justify-content:center;
  }
  .card{
    width:100%;max-width:380px;padding:40px 32px;
    background:#1a1a1a;border-radius:20px;
    box-shadow:0 20px 60px rgba(0,0,0,0.5);
  }
  .logo{
    width:56px;height:56px;border-radius:14px;background:#fff;color:#111;
    display:flex;align-items:center;justify-content:center;
    font-weight:900;font-size:22px;letter-spacing:-1px;
    margin-bottom:20px;
  }
  h1{margin:0 0 6px;font-size:22px;letter-spacing:-0.5px;font-weight:800}
  .sub{color:#888;font-size:13px;margin:0 0 28px}
  label{
    display:block;font-size:11px;text-transform:uppercase;
    letter-spacing:1px;color:#888;font-weight:700;margin:16px 0 6px;
  }
  input{
    width:100%;padding:14px;border:1px solid #333;border-radius:10px;
    font-size:16px;background:#0d0d0d;color:#fff;font-family:inherit;
    transition:border-color 0.15s;
  }
  input:focus{outline:none;border-color:#fff}
  button{
    width:100%;padding:14px;margin-top:24px;background:#fff;color:#111;
    border:none;border-radius:10px;font-weight:800;font-size:14px;
    cursor:pointer;letter-spacing:0.3px;
  }
  button:hover{background:#e5e5e5}
  button:disabled{background:#444;color:#888;cursor:not-allowed}
  .err{
    background:#3b0a0a;color:#fca5a5;padding:12px;border-radius:10px;
    font-size:13px;margin-top:16px;display:none;
  }
  .err.on{display:block}
  .hint{
    text-align:center;margin-top:24px;font-size:12px;color:#555;
  }
  .hint a{color:#888;text-decoration:none}
  .hint a:hover{color:#fff}
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

  <div class="hint">
    <a href="/">← Back to home</a>
  </div>
</div>

<script>
const NEXT = """ + json.dumps(next_url) + """;

async function doLogin(e){
  e.preventDefault();
  const btn = document.getElementById("btn");
  const err = document.getElementById("err");
  err.classList.remove("on");
  btn.disabled = true; btn.textContent = "Signing in…";
  try {
    const r = await fetch("/api/login", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        workshop: document.getElementById("ws").value,
        pin: document.getElementById("pin").value,
      }),
    });
    const d = await r.json();
    if (!r.ok || !d.success) {
      err.textContent = d.detail || d.error || "Sign in failed";
      err.classList.add("on");
      btn.disabled = false; btn.textContent = "Sign in";
      return false;
    }
    window.location.href = NEXT || "/";
  } catch(ex) {
    err.textContent = "Network error: " + ex.message;
    err.classList.add("on");
    btn.disabled = false; btn.textContent = "Sign in";
  }
  return false;
}

const params = new URLSearchParams(window.location.search);
if (params.get("ws") && !document.getElementById("ws").value) {
  document.getElementById("ws").value = params.get("ws");
}
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# ADMIN UI
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
  body{
    font-family:-apple-system,"Segoe UI",Roboto,sans-serif;
    margin:0;padding:20px 16px 60px;background:#0f0f0f;color:#fff;
  }
  .wrap{max-width:640px;margin:0 auto}
  h1{font-size:22px;margin:0 0 6px;letter-spacing:-0.4px}
  .sub{color:#888;font-size:13px;margin:0 0 24px}
  .card{
    background:#1a1a1a;border-radius:14px;padding:20px;
    margin-bottom:16px;border:1px solid #2a2a2a;
  }
  label{
    display:block;font-size:11px;text-transform:uppercase;
    letter-spacing:1px;color:#888;font-weight:700;margin-bottom:6px;
  }
  input,select{
    width:100%;padding:12px;border:1px solid #333;border-radius:10px;
    font-size:15px;background:#0d0d0d;color:#fff;font-family:inherit;
    margin-bottom:14px;
  }
  input:focus,select:focus{outline:none;border-color:#fff}
  button{
    padding:13px 20px;background:#16a34a;color:#fff;border:none;
    border-radius:10px;font-weight:800;font-size:14px;cursor:pointer;
    letter-spacing:0.3px;width:100%;
  }
  button:active{transform:scale(0.99)}
  button.secondary{background:#333}
  .err,.ok{
    padding:12px;border-radius:10px;font-size:13px;
    margin-bottom:14px;display:none;
  }
  .err{background:#3b0a0a;color:#fca5a5}
  .ok{background:#0a3b1a;color:#86efac}
  .err.on,.ok.on{display:block}
  .hdr{
    display:flex;align-items:center;justify-content:space-between;
    margin-bottom:16px;
  }
  .ws-list{display:flex;flex-direction:column;gap:10px}
  .ws-item{
    background:#222;padding:14px;border-radius:10px;
    display:flex;align-items:center;justify-content:space-between;
    gap:12px;
  }
  .ws-item .name{font-weight:700;font-size:15px;margin-bottom:3px}
  .ws-item .code{
    font-family:ui-monospace,Menlo,monospace;
    font-size:12px;color:#888;
  }
  .ws-item .plan{
    display:inline-block;padding:2px 8px;border-radius:12px;
    font-size:10px;font-weight:800;text-transform:uppercase;
    letter-spacing:0.5px;background:#2a2a2a;color:#aaa;
    margin-left:6px;
  }
  .ws-item .plan.pro{background:#1e40af;color:#93c5fd}
  .ws-item .plan.starter{background:#4c1d95;color:#c4b5fd}
  .ws-item .plan.workshop{background:#166534;color:#86efac}
  .ws-item .active-dot{
    width:8px;height:8px;border-radius:50%;background:#16a34a;
    display:inline-block;margin-right:6px;
  }
  .ws-item.inactive .active-dot{background:#666}
  .ws-actions{display:flex;gap:6px}
  .ws-actions button{
    width:auto;padding:8px 12px;font-size:12px;background:#333;
  }
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
      <div class="hdr">
        <strong style="font-size:15px">Create workshop</strong>
      </div>

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
        <button class="secondary" style="width:auto;padding:6px 12px;font-size:12px"
                onclick="loadList()">↻</button>
      </div>
      <div class="ws-list" id="ws_list">
        <div style="color:#888;font-size:13px">Loading…</div>
      </div>
    </div>

  </div>
</div>

<script>
let PIN = sessionStorage.getItem("rt_admin_pin") || "";

function showMsg(kind, text){
  const el = document.getElementById(kind === "err" ? "err" : "ok");
  el.textContent = text;
  el.classList.add("on");
  setTimeout(() => el.classList.remove("on"), 5000);
}

function savePin(){
  const v = document.getElementById("pin").value.trim();
  if (!v) return;
  PIN = v;
  sessionStorage.setItem("rt_admin_pin", v);
  unlock();
}

function unlock(){
  if (!PIN) return;
  document.getElementById("workspace").style.display = "block";
  loadList();
}

async function loadList(){
  const el = document.getElementById("ws_list");
  el.innerHTML = "<div style='color:#888;font-size:13px'>Loading…</div>";
  try {
    const r = await fetch("/api/tenancy/workshops?admin_pin=" +
                          encodeURIComponent(PIN));
    if (r.status === 403) {
      el.innerHTML = "<div style='color:#fca5a5;font-size:13px'>Invalid admin PIN.</div>";
      return;
    }
    const d = await r.json();
    if (!d.workshops || !d.workshops.length) {
      el.innerHTML = "<div style='color:#888;font-size:13px'>No workshops yet. Create one above.</div>";
      return;
    }
    el.innerHTML = d.workshops.map(w => `
      <div class="ws-item ${w.active === false ? 'inactive' : ''}">
        <div>
          <div class="name">
            <span class="active-dot"></span>${esc(w.name)}
            <span class="plan ${w.plan||''}">${w.plan||'—'}</span>
          </div>
          <div class="code">${esc(w.id)}${w.owner_email ? ' · ' + esc(w.owner_email) : ''}</div>
        </div>
        <div class="ws-actions">
          <button onclick="copyLogin('${esc(w.id)}')">Share</button>
        </div>
      </div>
    `).join("");
  } catch(e) {
    el.innerHTML = "<div style='color:#fca5a5;font-size:13px'>Error: " + e.message + "</div>";
  }
}

function copyLogin(id){
  const url = window.location.origin + "/login?ws=" + id;
  const msg = "Your RamsTech login:\\n" + url + "\\n\\nUse your owner PIN to sign in.";
  if (navigator.clipboard) {
    navigator.clipboard.writeText(msg)
      .then(() => showMsg("ok", "Login link copied to clipboard"))
      .catch(() => prompt("Copy this link:", url));
  } else {
    prompt("Copy this link:", url);
  }
}

async function createWorkshop(){
  const name = document.getElementById("w_name").value.trim();
  const id = document.getElementById("w_id").value.trim();
  const pin = document.getElementById("w_pin").value.trim();
  const email = document.getElementById("w_email").value.trim();
  const plan = document.getElementById("w_plan").value;

  if (!name || !pin) { showMsg("err", "Name and PIN are required"); return; }

  try {
    const r = await fetch("/api/tenancy/workshops?admin_pin=" +
                          encodeURIComponent(PIN), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        name, id: id || undefined,
        owner_pin: pin, owner_email: email, plan,
      }),
    });
    const d = await r.json();
    if (!r.ok) {
      showMsg("err", d.detail || d.error || "Failed to create");
      return;
    }
    showMsg("ok", "Created workshop: " + d.workshop.id);
    document.getElementById("w_name").value = "";
    document.getElementById("w_id").value = "";
    document.getElementById("w_pin").value = "";
    document.getElementById("w_email").value = "";
    loadList();
  } catch(e) {
    showMsg("err", "Error: " + e.message);
  }
}

function esc(s){
  return String(s||"").replace(/[&<>"']/g, m => (
    {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
}

if (PIN) { document.getElementById("pin").value = PIN; unlock(); }
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE — tenancy context + auth gate
# ═══════════════════════════════════════════════════════════════

_PUBLIC_PREFIXES = (
    "/login",
    "/logout",
    "/api/login",
    "/admin",
    "/api/tenancy/",
    "/health",
    "/push-sw.js",
    "/api/realtime/config",
    "/pay/",
    "/portal/",
    "/api/portal/",
    "/api/payments/webhook/",
    "/api/auto-remind/run",
    "/api/auto-remind/status",
    "/favicon.ico",
    "/robots.txt",
    "/manifest.json",
    "/service-worker.js",
    "/sw.js",
)


def _is_public(path):
    for p in _PUBLIC_PREFIXES:
        if path == p or path.startswith(p):
            return True
    return False


async def tenancy_middleware(request: Request, call_next):
    """
    When MULTI_TENANT=1:
      • Blocks unauthenticated requests to non-public paths
      • API paths (starting with /api/) always get JSON 401
      • Browser paths get redirected to /login
      • Authenticated requests are scoped to the workshop in the cookie
    When MULTI_TENANT=0:
      • Everything falls through unchanged, current workshop = "default"
    """
    if not MULTI_TENANT:
        _current_workshop.set("default")
        return await call_next(request)

    path = request.url.path

    # ── Auth gate ────────────────────────────────────────────
    if not _is_public(path):
        token = request.cookies.get(COOKIE_NAME)
        session = _verify(token)
        if not session:
            # API paths → JSON 401, no exceptions
            if path.startswith("/api/"):
                return JSONResponse(
                    {"detail": "Not authenticated", "login": "/login"},
                    status_code=401,
                )
            # Browser paths → redirect to login
            nxt = path if path.startswith("/") else "/"
            return RedirectResponse(
                f"/login?next={nxt}", status_code=302)

    # ── Workshop context for the duration of the request ────
    info = resolve_workshop(request)
    ctx_token = _current_workshop.set(info["id"])
    try:
        response = await call_next(request)
    finally:
        _current_workshop.reset(ctx_token)
    return response
