"""
Multi-tenancy — one codebase, many workshops.

Design: OFF by default. Set MULTI_TENANT=1 on Render to enable.
When OFF: every row behaves as workshop_id="default" — zero behaviour change.
When ON:  every read/write is scoped to the requesting workshop.

How requests are resolved to a workshop (in priority order):
  1. Signed session cookie "rt_session" (from /login)
  2. Query param ?ws=<code> (for super-admin testing)
  3. Subdomain <code>.yourdomain.com (if you set it up later)
  4. Fallback: "default"
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
# WORKSHOP CODE NORMALIZATION
# ═══════════════════════════════════════════════════════════════
def _slugify(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:40] or "workshop"


# ═══════════════════════════════════════════════════════════════
# SESSION COOKIE — signed, stateless
# ═══════════════════════════════════════════════════════════════
def _sign(payload):
    """payload dict → signed string. base64(json).hmac."""
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
        # re-pad base64
        pad = "=" * (-len(raw) % 4)
        data = json.loads(base64.urlsafe_b64decode(raw + pad).decode())
    except Exception:
        return None
    # expiry check
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
    # 1. signed cookie
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    if session and session.get("ws"):
        return {
            "id": session["ws"],
            "user": session.get("user", "owner"),
            "role": session.get("role", "owner"),
            "source": "cookie",
        }

    # 2. query param (super-admin/testing only)
    qs = request.query_params.get("ws")
    if qs and SUPER_ADMIN_PIN and \
       request.query_params.get("admin_pin") == SUPER_ADMIN_PIN:
        return {"id": _slugify(qs), "user": "admin", "role": "super", "source": "query"}

    # 3. subdomain: <code>.ramstech.onrender.com
    host = (request.headers.get("host") or "").split(":")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[0] not in ("www", "api", "app"):
        return {"id": _slugify(parts[0]), "user": "owner", "role": "owner", "source": "subdomain"}

    # 4. fallback
    return {"id": "default", "user": "guest", "role": "guest", "source": "fallback"}


# ═══════════════════════════════════════════════════════════════
# WORKSHOPS STORE
# ═══════════════════════════════════════════════════════════════
def _list_workshops():
    """Uses main's store but bypasses tenant filter (super-admin view)."""
    from main import store_list as _store_list
    # temporarily force default context
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


# ═══════════════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════════════
def _check_pin(workshop_id, pin):
    """Return workshop record if PIN matches, else None."""
    w = _get_workshop(workshop_id)
    if not w:
        return None
    if not w.get("active", True):
        return None
    if str(w.get("owner_pin", "")) == str(pin):
        return w
    return None


# ═══════════════════════════════════════════════════════════════
# ROUTES
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


@router.get("/api/tenancy/workshops")
def list_workshops(request: Request):
    """Super-admin only."""
    pin = request.query_params.get("admin_pin") or \
          request.headers.get("x-admin-pin")
    if not SUPER_ADMIN_PIN or pin != SUPER_ADMIN_PIN:
        raise HTTPException(403, "Super-admin PIN required")
    items = _list_workshops()
    # scrub pins
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


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    return HTMLResponse(_login_html(next))


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
        httponly=True, samesite="lax", secure=False,
    )
    return resp


@router.get("/logout")
def do_logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp


# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE HTML
# ═══════════════════════════════════════════════════════════════
def _login_html(next_url):
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
           autocomplete="username" required autofocus>

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

// prefill workshop code from query string ?ws=xxx
const params = new URLSearchParams(window.location.search);
if (params.get("ws")) document.getElementById("ws").value = params.get("ws");
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE HOOK (called from main.py)
# ═══════════════════════════════════════════════════════════════
async def tenancy_middleware(request: Request, call_next):
    """Set context var for the duration of the request."""
    if not MULTI_TENANT:
        _current_workshop.set("default")
        return await call_next(request)

    info = resolve_workshop(request)
    token = _current_workshop.set(info["id"])
    try:
        response = await call_next(request)
    finally:
        _current_workshop.reset(token)
    return response
