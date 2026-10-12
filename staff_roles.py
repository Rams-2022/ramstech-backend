"""
Staff PINs & Roles — role-based access for workshops.

Extends the existing staff system with:
  • Per-staff PINs for individual logins
  • Role-based UI filtering (owner sees everything, tech sees own jobs)
  • Owner-facing staff management panel
  • /api/whoami so the app knows who's using it
"""
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(tags=["staff-roles"])


# ═══════════════════════════════════════════════════════════════
# ROLE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
ROLES = {
    "owner": {
        "label": "Owner",
        "description": "Full access to everything",
        "capabilities": ["*"],
        "color": "#111111",
    },
    "manager": {
        "label": "Manager",
        "description": "Runs day-to-day. No system settings.",
        "capabilities": [
            "view_dashboard", "view_jobs", "edit_jobs", "assign_jobs",
            "view_customers", "edit_customers",
            "view_invoices", "edit_invoices",
            "view_quotes", "edit_quotes",
            "view_appointments", "edit_appointments",
            "view_inventory", "edit_inventory",
            "view_staff", "view_reports",
            "view_profit", "view_debtors", "send_reminders",
            "clock_in",
        ],
        "color": "#1e40af",
    },
    "supervisor": {
        "label": "Supervisor",
        "description": "Manages technicians and jobs. No financials.",
        "capabilities": [
            "view_dashboard", "view_jobs", "edit_jobs", "assign_jobs",
            "view_customers", "edit_customers",
            "view_appointments", "edit_appointments",
            "view_inventory", "edit_inventory",
            "view_staff",
            "clock_in",
        ],
        "color": "#7c3aed",
    },
    "hr": {
        "label": "HR / Admin",
        "description": "Staff records and attendance only.",
        "capabilities": [
            "view_staff", "edit_staff",
            "view_clockins", "edit_clockins",
            "clock_in",
        ],
        "color": "#0891b2",
    },
    "receptionist": {
        "label": "Receptionist",
        "description": "Front desk. Customers, jobs, invoices.",
        "capabilities": [
            "view_dashboard", "view_jobs", "edit_jobs",
            "view_customers", "edit_customers",
            "view_invoices", "edit_invoices",
            "view_quotes", "edit_quotes",
            "view_appointments", "edit_appointments",
            "view_debtors", "send_reminders",
            "clock_in",
        ],
        "color": "#ea580c",
    },
    "technician": {
        "label": "Technician",
        "description": "Own jobs only. Updates progress.",
        "capabilities": [
            "view_own_jobs", "edit_own_jobs",
            "view_inventory",
            "clock_in",
        ],
        "color": "#16a34a",
    },
    "driver": {
        "label": "Driver",
        "description": "Pickup and delivery assignments.",
        "capabilities": [
            "view_deliveries",
            "clock_in",
        ],
        "color": "#78716c",
    },
}


def has_capability(role, capability):
    if role not in ROLES:
        return False
    caps = ROLES[role]["capabilities"]
    return "*" in caps or capability in caps


def check_staff_pin(workshop_id, pin):
    """Look up a staff member by PIN within a specific workshop."""
    if not pin:
        return None
    pin = str(pin).strip()
    try:
        from main import store_list
        from tenancy import _current_workshop
    except Exception:
        return None

    tok = _current_workshop.set(workshop_id)
    try:
        staff = store_list("staff")
    finally:
        _current_workshop.reset(tok)

    for s in staff:
        if s.get("active", True) is False:
            continue
        if str(s.get("pin", "")).strip() == pin:
            return s
    return None


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/api/whoami")
def whoami(request: Request):
    from tenancy import _verify, COOKIE_NAME
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    if not session:
        return {"authenticated": False}

    role = session.get("role", "owner")
    role_def = ROLES.get(role, ROLES["owner"])
    return {
        "authenticated": True,
        "workshop": session.get("ws", "default"),
        "user": session.get("user", "owner"),
        "role": role,
        "role_label": role_def["label"],
        "role_color": role_def["color"],
        "staff_id": session.get("staff_id"),
        "capabilities": role_def["capabilities"],
        "is_owner": role == "owner",
    }


@router.get("/api/roles")
def list_roles():
    return {
        "roles": [
            {"id": k, "label": v["label"], "description": v["description"],
             "color": v["color"]}
            for k, v in ROLES.items()
        ]
    }


@router.post("/api/staff/{sid}/pin")
async def set_staff_pin(sid: str, request: Request):
    _require_owner(request)
    d = await request.json()
    pin = str(d.get("pin") or "").strip()
    if not pin or len(pin) < 4 or len(pin) > 6 or not pin.isdigit():
        raise HTTPException(400, "PIN must be 4-6 digits")

    from main import store_get, store_save
    staff = store_get("staff", sid)
    if not staff:
        raise HTTPException(404, "Staff not found")
    staff["pin"] = pin
    store_save("staff", sid, staff)
    return {"success": True}


@router.post("/api/staff/{sid}/role")
async def set_staff_role(sid: str, request: Request):
    _require_owner(request)
    d = await request.json()
    role = str(d.get("role") or "").strip()
    if role not in ROLES or role == "owner":
        raise HTTPException(400, "Invalid role")

    from main import store_get, store_save
    staff = store_get("staff", sid)
    if not staff:
        raise HTTPException(404, "Staff not found")
    staff["role"] = role
    store_save("staff", sid, staff)
    return {"success": True}


@router.post("/api/staff/{sid}/deactivate")
def deactivate_staff(sid: str, request: Request):
    _require_owner(request)
    from main import store_get, store_save
    staff = store_get("staff", sid)
    if not staff:
        raise HTTPException(404)
    staff["active"] = False
    store_save("staff", sid, staff)
    return {"success": True}


@router.post("/api/staff/{sid}/activate")
def activate_staff(sid: str, request: Request):
    _require_owner(request)
    from main import store_get, store_save
    staff = store_get("staff", sid)
    if not staff:
        raise HTTPException(404)
    staff["active"] = True
    store_save("staff", sid, staff)
    return {"success": True}


def _require_owner(request: Request):
    from tenancy import _verify, COOKIE_NAME
    token = request.cookies.get(COOKIE_NAME)
    session = _verify(token)
    if not session:
        raise HTTPException(401, "Not authenticated")
    if session.get("role", "owner") != "owner":
        raise HTTPException(403, "Owner access required")


# ═══════════════════════════════════════════════════════════════
# UI injection — role badge + UI filtering + staff manager
# ═══════════════════════════════════════════════════════════════
STAFF_ROLES_HTML = """
<style>
  #rt-role-badge {
    position: fixed; top: 12px; right: 12px; z-index: 9997;
    background: #111; color: #fff; padding: 6px 12px;
    border-radius: 20px; font-size: 11px; font-weight: 800;
    letter-spacing: 0.5px; cursor: pointer;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    display: none; align-items: center; gap: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  #rt-role-badge .dot {
    width: 6px; height: 6px; border-radius: 50%; background: #16a34a;
  }
  #rt-role-badge .role {
    background: rgba(255,255,255,0.15);
    padding: 2px 8px; border-radius: 10px; font-size: 10px;
  }
  #rt-staff-panel {
    display: none; position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,0.55); padding: 24px; overflow-y: auto;
  }
  #rt-staff-panel.open { display: block; }
  .rt-staff-modal {
    max-width: 640px; margin: 0 auto; background: #fff;
    border-radius: 14px; padding: 28px 28px;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    color: #1a1a1a; position: relative;
  }
  .rt-staff-modal h2 { margin: 0 0 6px; font-size: 22px; letter-spacing: -0.5px; }
  .rt-staff-modal .sub { color: #777; font-size: 13px; margin: 0 0 22px; }
  .rt-staff-close {
    position: absolute; top: 18px; right: 22px; background: none;
    border: none; font-size: 24px; cursor: pointer; color: #999;
  }
  .rt-staff-add {
    background: #fafafa; padding: 16px; border-radius: 10px;
    margin-bottom: 20px;
  }
  .rt-staff-add label {
    display: block; font-size: 10px; font-weight: 800;
    text-transform: uppercase; letter-spacing: 1px;
    color: #666; margin-bottom: 4px;
  }
  .rt-staff-add input, .rt-staff-add select {
    width: 100%; padding: 9px 11px; border: 1px solid #ddd;
    border-radius: 8px; font-size: 14px; font-family: inherit;
    margin-bottom: 10px;
  }
  .rt-staff-add .grid2 {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  }
  .rt-staff-add button {
    width: 100%; padding: 12px; background: #111; color: #fff;
    border: none; border-radius: 8px; font-weight: 800;
    font-size: 13px; cursor: pointer; letter-spacing: 0.3px;
  }
  .rt-staff-list { display: flex; flex-direction: column; gap: 8px; }
  .rt-staff-item {
    background: #fff; border: 1px solid #e5e5e5; border-radius: 10px;
    padding: 12px 14px; display: flex; align-items: center;
    justify-content: space-between; gap: 10px;
  }
  .rt-staff-item.inactive { opacity: 0.55; }
  .rt-staff-item .name {
    font-weight: 800; font-size: 14px; margin-bottom: 2px;
  }
  .rt-staff-item .meta {
    font-size: 11px; color: #888;
  }
  .rt-staff-item .role-tag {
    display: inline-block; padding: 2px 8px;
    border-radius: 10px; font-size: 9px; font-weight: 800;
    color: #fff; text-transform: uppercase;
    letter-spacing: 0.5px; margin-left: 6px;
  }
  .rt-staff-item .actions { display: flex; gap: 6px; }
  .rt-staff-item .actions button {
    padding: 6px 10px; background: #f5f5f5; border: none;
    border-radius: 6px; font-size: 11px; font-weight: 700;
    cursor: pointer; color: #333;
  }
  .rt-staff-item .actions button:hover { background: #e5e5e5; }
  .rt-staff-item .actions button.danger { color: #dc2626; }
  .rt-staff-item .actions button.ok { color: #16a34a; }
  @media print { #rt-role-badge, #rt-staff-panel { display: none !important; } }
</style>

<div id="rt-role-badge" onclick="rtStaffOpen()">
  <span class="dot"></span>
  <span class="name" id="rt-user-name">…</span>
  <span class="role" id="rt-user-role">…</span>
</div>

<div id="rt-staff-panel" onclick="if(event.target===this)rtStaffClose()">
  <div class="rt-staff-modal">
    <button class="rt-staff-close" onclick="rtStaffClose()">×</button>
    <h2>Staff & Roles</h2>
    <p class="sub">Give each staff member their own PIN. They log in at the same URL with that PIN.</p>

    <div class="rt-staff-add" id="rt-staff-add-wrap">
      <div class="grid2">
        <div>
          <label>Full name</label>
          <input id="rt-s-name" placeholder="e.g. Sipho Mkhize">
        </div>
        <div>
          <label>Role</label>
          <select id="rt-s-role">
            <option value="manager">Manager</option>
            <option value="supervisor">Supervisor</option>
            <option value="hr">HR / Admin</option>
            <option value="receptionist">Receptionist</option>
            <option value="technician" selected>Technician</option>
            <option value="driver">Driver</option>
          </select>
        </div>
      </div>
      <div class="grid2">
        <div>
          <label>Phone</label>
          <input id="rt-s-phone" placeholder="072 123 4567">
        </div>
        <div>
          <label>PIN (4-6 digits)</label>
          <input id="rt-s-pin" placeholder="4821" maxlength="6"
                 inputmode="numeric">
        </div>
      </div>
      <div class="grid2">
        <div>
          <label>Hourly rate</label>
          <input id="rt-s-rate" placeholder="180" inputmode="numeric">
        </div>
        <div>
          <label>&nbsp;</label>
          <button onclick="rtStaffCreate()">+ Add staff member</button>
        </div>
      </div>
    </div>

    <div class="rt-staff-list" id="rt-staff-list">
      <div style="color:#888;text-align:center;padding:20px">Loading…</div>
    </div>
  </div>
</div>

<script>
(function(){
  let ME = null;

  async function loadMe(){
    try {
      const r = await fetch("/api/whoami");
      ME = await r.json();
      if (ME.authenticated) renderBadge();
      applyFilters();
    } catch(e) { console.error("whoami failed", e); }
  }

  function renderBadge(){
    const badge = document.getElementById("rt-role-badge");
    const nameEl = document.getElementById("rt-user-name");
    const roleEl = document.getElementById("rt-user-role");
    if (!badge || !ME) return;
    nameEl.textContent = ME.user || "User";
    roleEl.textContent = ME.role_label || "Owner";
    roleEl.style.background = ME.role_color || "#111";
    badge.style.display = "flex";
  }

  function can(cap){
    if (!ME || !ME.authenticated) return false;
    if (ME.capabilities && ME.capabilities.includes("*")) return true;
    return ME.capabilities && ME.capabilities.includes(cap);
  }

  function applyFilters(){
    if (!ME) return;
    const debtors = document.getElementById("rt-debtors-btn");
    if (debtors && !can("view_debtors")) debtors.style.display = "none";
    const profit = document.getElementById("rt-profit-btn");
    if (profit && !can("view_profit")) profit.style.display = "none";
    const arToggle = document.getElementById("rt-ar-toggle");
    if (arToggle && !can("view_debtors")) arToggle.style.display = "none";
    const shareBtn = document.getElementById("rt-portal-share");
    if (shareBtn && !can("view_debtors")) shareBtn.style.display = "none";
  }

  window.rtStaffOpen = async function(){
    if (!ME || ME.role !== "owner") return;
    document.getElementById("rt-staff-panel").classList.add("open");
    await rtStaffLoad();
  };
  window.rtStaffClose = function(){
    document.getElementById("rt-staff-panel").classList.remove("open");
  };

  window.rtStaffLoad = async function(){
    const list = document.getElementById("rt-staff-list");
    try {
      const r = await fetch("/api/staff");
      const d = await r.json();
      const staff = (d.staff || []).filter(s => (s.role || "") !== "");
      if (!staff.length){
        list.innerHTML = '<div style="text-align:center;padding:30px;color:#888;font-size:13px">No staff yet. Add one above.</div>';
        return;
      }
      const rr = await fetch("/api/roles");
      const roles = (await rr.json()).roles;
      const colors = {};
      roles.forEach(x => colors[x.id] = x.color);

      list.innerHTML = staff.map(s => {
        const role = s.role || "technician";
        const color = colors[role] || "#666";
        const inactive = s.active === false;
        return `
          <div class="rt-staff-item ${inactive ? 'inactive' : ''}">
            <div>
              <div class="name">
                ${esc(s.name)}
                <span class="role-tag" style="background:${color}">${esc(role)}</span>
              </div>
              <div class="meta">
                ${esc(s.phone || '')} ${s.pin ? '· PIN set' : '· no PIN'}
                ${inactive ? ' · inactive' : ''}
              </div>
            </div>
            <div class="actions">
              <button onclick="rtStaffResetPin('${esc(s.id)}')">Reset PIN</button>
              ${inactive
                ? `<button class="ok" onclick="rtStaffActivate('${esc(s.id)}')">Reactivate</button>`
                : `<button class="danger" onclick="rtStaffDeactivate('${esc(s.id)}')">Deactivate</button>`}
            </div>
          </div>`;
      }).join("");
    } catch(e) {
      list.innerHTML = '<div style="color:#c00;padding:20px">Error: ' + esc(e.message) + '</div>';
    }
  };

  window.rtStaffCreate = async function(){
    const name = document.getElementById("rt-s-name").value.trim();
    const role = document.getElementById("rt-s-role").value;
    const phone = document.getElementById("rt-s-phone").value.trim();
    const pin = document.getElementById("rt-s-pin").value.trim();
    const rate = document.getElementById("rt-s-rate").value.trim();
    if (!name || !pin) { alert("Name and PIN required"); return; }
    if (pin.length < 4 || !/^[0-9]+$/.test(pin)) {
      alert("PIN must be 4-6 digits"); return;
    }
    try {
      const r = await fetch("/api/staff", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          name, role, phone, pin,
          hourly_rate: rate ? parseFloat(rate) : 150,
        }),
      });
      const d = await r.json();
      if (!d.success) throw new Error(d.detail || "Create failed");
      document.getElementById("rt-s-name").value = "";
      document.getElementById("rt-s-phone").value = "";
      document.getElementById("rt-s-pin").value = "";
      document.getElementById("rt-s-rate").value = "";
      await rtStaffLoad();
    } catch(e) { alert("Error: " + e.message); }
  };

  window.rtStaffResetPin = async function(id){
    const pin = prompt("New PIN (4-6 digits):");
    if (!pin) return;
    if (pin.length < 4 || !/^[0-9]+$/.test(pin)) {
      alert("PIN must be 4-6 digits"); return;
    }
    try {
      await fetch("/api/staff/" + id + "/pin", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({pin}),
      });
      alert("PIN updated");
      await rtStaffLoad();
    } catch(e) { alert("Error: " + e.message); }
  };

  window.rtStaffDeactivate = async function(id){
    if (!confirm("Deactivate this staff member? They will lose access immediately.")) return;
    try {
      await fetch("/api/staff/" + id + "/deactivate", {method: "POST"});
      await rtStaffLoad();
    } catch(e) { alert("Error: " + e.message); }
  };

  window.rtStaffActivate = async function(id){
    try {
      await fetch("/api/staff/" + id + "/activate", {method: "POST"});
      await rtStaffLoad();
    } catch(e) { alert("Error: " + e.message); }
  };

  function esc(s){
    return String(s||"").replace(/[&<>"']/g, m => (
      {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  }

  const obs = new MutationObserver(() => applyFilters());
  obs.observe(document.body, {childList: true, subtree: true});

  setTimeout(loadMe, 500);
})();
</script>
"""
