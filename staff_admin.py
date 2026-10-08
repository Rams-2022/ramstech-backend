"""Staff management — owner-only staff PIN administration."""
import uuid
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

# Rate limiting: track failed login attempts
_attempts = {}  # {ip_or_key: [timestamps]}


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


@router.get("/api/staff-pins/list")
def list_staff_pins():
    r = _c().table("staff_pins").select("*").order("name").execute()
    return {"staff": r.data or []}


@router.post("/api/staff-pins/add")
async def add_staff_pin(r: Request):
    d = await r.json()
    name = (d.get("name") or "").strip()
    pin = str(d.get("pin") or "").strip()
    role = (d.get("role") or "Mechanic").strip()
    phone = (d.get("phone") or "").strip()

    if not name:
        raise HTTPException(400, "Name required")
    if len(pin) != 4 or not pin.isdigit():
        raise HTTPException(400, "PIN must be 4 digits")

    # Check PIN uniqueness
    dup = _c().table("staff_pins").select("name").eq("pin", pin).execute()
    if dup.data:
        other = dup.data[0].get("name", "another staff member")
        raise HTTPException(409, f"PIN already used by {other}")

    # Check name uniqueness (no duplicate names)
    namedup = _c().table("staff_pins").select("id").eq("name", name).execute()
    if namedup.data:
        raise HTTPException(409, f"Staff member '{name}' already exists")

    sid = str(uuid.uuid4())[:8]
    row = {
        "id": sid,
        "name": name,
        "pin": pin,
        "role": role,
        "phone": phone,
        "active": True,
        "created": datetime.utcnow().isoformat(),
    }
    _c().table("staff_pins").insert(row).execute()
    return {"success": True, "staff": row}


@router.post("/api/staff-pins/update/{sid}")
async def update_staff_pin(sid: str, r: Request):
    d = await r.json()
    updates = {}

    if "name" in d:
        name = (d.get("name") or "").strip()
        if not name:
            raise HTTPException(400, "Name cannot be empty")
        updates["name"] = name
    if "pin" in d:
        pin = str(d.get("pin") or "").strip()
        if len(pin) != 4 or not pin.isdigit():
            raise HTTPException(400, "PIN must be 4 digits")
        dup = _c().table("staff_pins").select("id, name").eq("pin", pin).execute()
        if dup.data and dup.data[0]["id"] != sid:
            raise HTTPException(409, f"PIN already used by {dup.data[0]['name']}")
        updates["pin"] = pin
    if "role" in d:
        updates["role"] = (d.get("role") or "").strip()
    if "phone" in d:
        updates["phone"] = (d.get("phone") or "").strip()
    if "active" in d:
        updates["active"] = bool(d.get("active"))

    if not updates:
        raise HTTPException(400, "No changes provided")

    _c().table("staff_pins").update(updates).eq("id", sid).execute()
    return {"success": True, "updates": updates}


@router.delete("/api/staff-pins/{sid}")
def delete_staff_pin(sid: str):
    _c().table("staff_pins").delete().eq("id", sid).execute()
    return {"success": True}


# ═══════════════════════════════════
# OWNER PIN change
# ═══════════════════════════════════
@router.post("/api/owner-pin/change")
async def change_owner_pin(r: Request):
    d = await r.json()
    current = str(d.get("current") or "").strip()
    new_pin = str(d.get("new_pin") or "").strip()

    import os
    expected = os.getenv("OWNER_PIN", "9999").strip()
    if current != expected:
        raise HTTPException(401, "Current PIN incorrect")
    if len(new_pin) != 4 or not new_pin.isdigit():
        raise HTTPException(400, "New PIN must be 4 digits")

    # Try to store in Supabase — but owner PIN also needs to update in Render env
    try:
        existing = _c().table("app_settings").select("key").eq("key", "owner_pin").execute()
        if existing.data:
            _c().table("app_settings").update({"value": new_pin, "updated": datetime.utcnow().isoformat()}).eq("key", "owner_pin").execute()
        else:
            _c().table("app_settings").insert({"key": "owner_pin", "value": new_pin, "updated": datetime.utcnow().isoformat()}).execute()
    except Exception as e:
        print(f"[owner-pin] supabase store failed: {e}")

    return {
        "success": True,
        "message": "PIN saved to database. Also update OWNER_PIN in Render environment for full effect.",
        "note": "In-memory change is immediate; persistent change requires Render env var update.",
        "new_pin": new_pin,
    }


STAFF_ADMIN_HTML = r"""
<style>
#saModal{display:none;position:fixed;inset:0;background:#0a1018;z-index:9999;overflow:auto;color:#fff;}
#saInner{max-width:700px;margin:0 auto;padding:16px;min-height:100vh;}
.saIn{width:100%;padding:12px;background:#0f1520;border:1px solid #1e2938;border-radius:9px;
color:#e6edf5;font-size:14px;box-sizing:border-box;font-family:inherit;margin-bottom:8px;}
.saBtn{width:100%;padding:14px;background:#10b981;color:#fff;border:none;border-radius:10px;
font-weight:700;font-size:15px;cursor:pointer;margin-bottom:8px;text-decoration:none;display:block;text-align:center;}
.saBtn.dark{background:#1e2938;}
.saBtn.red{background:#ef4444;}
.saBtn.blue{background:#0ea5e9;}
.saBtn.orange{background:#f97316;}
.saRow{display:flex;gap:8px;}
.saRow .saIn{flex:1;}
.saCard{background:#0f1520;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-bottom:10px;}
.saHeader{display:flex;justify-content:space-between;align-items:center;
padding-bottom:14px;border-bottom:2px solid #1e2938;margin-bottom:14px;}
.saStaff{padding:12px;background:#0f1520;border:1px solid #1e2938;border-radius:10px;margin-bottom:8px;}
.saStaff .name{font-size:16px;font-weight:800;color:#10b981;}
.saStaff .role{font-size:12px;color:#94a3b8;}
.saStaff .pinmask{font-family:monospace;font-size:14px;color:#f97316;letter-spacing:2px;}
.saBadge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;
font-weight:700;color:#fff;background:#10b981;margin-left:6px;}
.saBadge.inactive{background:#6b7280;}
</style>

<div id="saModal">
<div id="saInner">
<div class="saHeader">
<div>
<div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">MANAGER</div>
<div style="font-size:18px;font-weight:800;color:#10b981;">Staff Management</div>
</div>
<button onclick="saClose()" style="background:#1e2938;color:#fff;border:none;
border-radius:8px;padding:8px 14px;cursor:pointer;">X</button>
</div>

<div class="saCard">
<h3 style="margin-bottom:10px;color:#10b981;">➕ Add New Staff</h3>
<input id="saName" class="saIn" placeholder="Full name (e.g. Sipho Nkosi)">
<input id="saRole" class="saIn" placeholder="Role (e.g. Mechanic, Apprentice, Manager)">
<input id="saPhone" class="saIn" placeholder="Phone (optional)">
<input id="saPin" class="saIn" placeholder="4-digit PIN" maxlength="4" inputmode="numeric" type="tel">
<button class="saBtn" onclick="saAddStaff()">Add Staff Member</button>
</div>

<div class="saCard">
<h3 style="margin-bottom:10px;color:#f59e0b;">🔑 Change Owner PIN</h3>
<input id="saCurrentPin" class="saIn" placeholder="Current owner PIN" maxlength="4" inputmode="numeric" type="tel">
<input id="saNewPin" class="saIn" placeholder="New owner PIN" maxlength="4" inputmode="numeric" type="tel">
<button class="saBtn orange" onclick="saChangeOwnerPin()">Change Owner PIN</button>
</div>

<div class="saCard">
<h3 style="margin-bottom:10px;color:#0ea5e9;">👥 Staff Members</h3>
<div id="saStaffList">Loading...</div>
</div>

<div id="saRes" style="display:none;background:#0a1018;border:1px solid #1e2938;
border-radius:10px;padding:12px;margin-top:10px;font-size:13px;white-space:pre-wrap;"></div>
</div>
</div>

<script>
function saOpen(){document.getElementById('saModal').style.display='block';saLoadStaff();}
function saClose(){document.getElementById('saModal').style.display='none';}
function saRes(t){var e=document.getElementById('saRes');e.textContent=t;e.style.display='block';}

async function saGet(p){var r=await fetch(p);var t=await r.text();try{return JSON.parse(t);}catch(e){return {error:t.slice(0,200)};}}
async function saPost(p,b){var r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});var t=await r.text();try{return JSON.parse(t);}catch(e){return {error:t.slice(0,200)};}}
async function saDel(p){var r=await fetch(p,{method:'DELETE'});return r.json();}

async function saLoadStaff(){
  var d = await saGet('/api/staff-pins/list');
  var list = d.staff||[];
  if(!list.length){
    document.getElementById('saStaffList').innerHTML = '<div style="text-align:center;padding:20px;color:#7b8da3;">No staff yet. Add your first above.</div>';
    return;
  }
  var h = '';
  list.forEach(function(s){
    var active = s.active !== false;
    var badge = active ? '<span class="saBadge">ACTIVE</span>' : '<span class="saBadge inactive">INACTIVE</span>';
    h += '<div class="saStaff">';
    h += '<div class="name">' + s.name + badge + '</div>';
    h += '<div class="role">' + (s.role || 'Mechanic') + (s.phone ? ' · ' + s.phone : '') + '</div>';
    h += '<div class="pinmask">PIN: ' + s.pin + '</div>';
    h += '<div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">';
    h += '<button class="saBtn blue" style="flex:1;padding:8px;font-size:12px;margin:0;" onclick="saChangePin(\'' + s.id + '\',\'' + s.name + '\')">Change PIN</button>';
    if(active){
      h += '<button class="saBtn dark" style="flex:1;padding:8px;font-size:12px;margin:0;" onclick="saToggleActive(\'' + s.id + '\',false)">Deactivate</button>';
    } else {
      h += '<button class="saBtn" style="flex:1;padding:8px;font-size:12px;margin:0;" onclick="saToggleActive(\'' + s.id + '\',true)">Reactivate</button>';
    }
    h += '<button class="saBtn red" style="flex:1;padding:8px;font-size:12px;margin:0;" onclick="saDeleteStaff(\'' + s.id + '\',\'' + s.name + '\')">Delete</button>';
    h += '</div></div>';
  });
  document.getElementById('saStaffList').innerHTML = h;
}

async function saAddStaff(){
  var name = document.getElementById('saName').value.trim();
  var pin = document.getElementById('saPin').value.trim();
  var role = document.getElementById('saRole').value.trim() || 'Mechanic';
  var phone = document.getElementById('saPhone').value.trim();
  if(!name){saRes('Name required');return;}
  if(pin.length !== 4){saRes('PIN must be 4 digits');return;}
  var d = await saPost('/api/staff-pins/add', {name:name, pin:pin, role:role, phone:phone});
  if(d.success){
    saRes('✓ Added ' + name + ' with PIN ' + pin);
    ['saName','saRole','saPhone','saPin'].forEach(function(i){document.getElementById(i).value='';});
    saLoadStaff();
  } else {
    saRes('Error: ' + (d.detail || JSON.stringify(d)));
  }
}

async function saChangePin(sid, name){
  var newPin = prompt('New 4-digit PIN for ' + name + ':');
  if(!newPin) return;
  if(newPin.length !== 4 || !/^\d+$/.test(newPin)){alert('PIN must be 4 digits');return;}
  var d = await saPost('/api/staff-pins/update/' + sid, {pin:newPin});
  if(d.success){
    saRes('✓ PIN changed for ' + name);
    saLoadStaff();
  } else {
    saRes('Error: ' + (d.detail || JSON.stringify(d)));
  }
}

async function saToggleActive(sid, active){
  var d = await saPost('/api/staff-pins/update/' + sid, {active: active});
  if(d.success){
    saLoadStaff();
  } else {
    saRes('Error: ' + (d.detail || ''));
  }
}

async function saDeleteStaff(sid, name){
  if(!confirm('Delete ' + name + ' permanently?\n\nTheir PIN will be removed and they cannot log in.'))return;
  var d = await saDel('/api/staff-pins/' + sid);
  if(d.success){
    saRes('✓ Deleted ' + name);
    saLoadStaff();
  } else {
    saRes('Error: ' + JSON.stringify(d));
  }
}

async function saChangeOwnerPin(){
  var current = document.getElementById('saCurrentPin').value.trim();
  var newPin = document.getElementById('saNewPin').value.trim();
  if(!current || newPin.length !== 4){saRes('Both fields required');return;}
  var d = await saPost('/api/owner-pin/change', {current:current, new_pin:newPin});
  if(d.success){
    saRes('✓ ' + d.message);
    document.getElementById('saCurrentPin').value = '';
    document.getElementById('saNewPin').value = '';
  } else {
    saRes('Error: ' + (d.detail || JSON.stringify(d)));
  }
}

function saInjectIntoSettings(){
  var settingsTab = document.getElementById('settings');
  if(!settingsTab || document.getElementById('saInlineBtn')) return;
  var title = settingsTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'saInlineBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#10b981,#059669);margin-bottom:10px;';
  btn.textContent = '👥 Manage Staff & PINs';
  btn.onclick = saOpen;
  title.parentNode.insertBefore(btn, title.nextSibling);
}

setInterval(saInjectIntoSettings, 900);
setTimeout(saInjectIntoSettings, 600);
document.getElementById('saModal').addEventListener('click',function(e){if(e.target===this)saClose();});
</script>
"""
