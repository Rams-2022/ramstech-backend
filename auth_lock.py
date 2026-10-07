"""Owner/Technician login lock for the app."""
import os
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

# Owner PIN — change this in Render Environment (default: 9999)
OWNER_PIN = os.getenv("OWNER_PIN", "9999").strip()


@router.post("/api/auth/owner-login")
async def owner_login(r: Request):
    d = await r.json()
    pin = str(d.get("pin") or "").strip()
    if not pin:
        raise HTTPException(400, "PIN required")
    if pin == OWNER_PIN:
        return {"success": True, "role": "owner"}
    raise HTTPException(401, "Invalid owner PIN")


@router.get("/api/auth/owner-pin-default")
def owner_pin_default():
    return {"is_default": OWNER_PIN == "9999"}


AUTH_LOCK_HTML = r"""
<style>
#lockScreen{position:fixed;inset:0;background:linear-gradient(135deg,#0a1018,#0f1520);
z-index:99999;display:none;align-items:center;justify-content:center;padding:20px;}
#lockInner{max-width:380px;width:100%;text-align:center;color:#e6edf5;}
#lockLogo{font-size:44px;background:linear-gradient(135deg,#E65100,#FF9800);
width:100px;height:100px;border-radius:24px;margin:0 auto 24px;
display:flex;align-items:center;justify-content:center;font-weight:900;color:#fff;
box-shadow:0 12px 32px rgba(230,81,0,.4);}
#lockInner h1{font-size:22px;font-weight:800;margin-bottom:6px;color:#fff;}
#lockInner .sub{font-size:13px;color:#94a3b8;margin-bottom:28px;}
.lockBtn{width:100%;padding:18px;border:none;border-radius:14px;font-size:16px;
font-weight:700;cursor:pointer;margin-bottom:12px;color:#fff;}
.lockBtn:active{transform:scale(.98);}
.lockBtn.owner{background:linear-gradient(135deg,#E65100,#FF9800);}
.lockBtn.tech{background:linear-gradient(135deg,#f59e0b,#b45309);}
.lockBtn.cancel{background:#1e2938;}
#lockPinView{display:none;}
#lockPinView h2{font-size:17px;font-weight:700;margin-bottom:6px;color:#fff;}
#lockPinInput{width:100%;padding:18px;background:#0f1520;border:2px solid #1e2938;
border-radius:14px;color:#e6edf5;font-size:24px;text-align:center;letter-spacing:12px;
font-family:monospace;margin:20px 0;box-sizing:border-box;}
#lockPinInput:focus{outline:none;border-color:#E65100;}
#lockError{color:#ef4444;font-size:13px;margin-top:12px;min-height:18px;}
body.tech-mode .bottom-nav{display:none!important;}
body.tech-mode .wfBtn,
body.tech-mode #wfNewQuoteBtn,
body.tech-mode #jsInlineBtn,
body.tech-mode #aiFab,
body.tech-mode #aiPanel,
body.tech-mode #wfModal,
body.tech-mode #jsPanel,
body.tech-mode #jsMove{display:none!important;}
</style>

<div id="lockScreen">
  <div id="lockInner">
    <div id="lockLogo">RT</div>
    <h1>RamsTech Workshop</h1>
    <div class="sub">Sign in to continue</div>

    <div id="lockChoiceView">
      <button class="lockBtn owner" onclick="lockPick('owner')">&#128188; Owner / Manager</button>
      <button class="lockBtn tech" onclick="lockPick('tech')">&#128119; Technician</button>
    </div>

    <div id="lockPinView">
      <h2 id="lockPinTitle">Enter PIN</h2>
      <input type="tel" maxlength="4" inputmode="numeric" id="lockPinInput" placeholder="...." autocomplete="off">
      <button class="lockBtn owner" onclick="lockSubmit()">Sign In</button>
      <button class="lockBtn cancel" onclick="lockBack()">Back</button>
    </div>

    <div id="lockError"></div>
  </div>
</div>

<script>
var _lockRole = null;

function lockShow(){
  var s = document.getElementById('lockScreen');
  if(s) s.style.display='flex';
  document.getElementById('lockChoiceView').style.display='block';
  document.getElementById('lockPinView').style.display='none';
  document.getElementById('lockError').textContent='';
  _lockRole = null;
}
function lockHide(){
  var s = document.getElementById('lockScreen');
  if(s) s.style.display='none';
}
function lockPick(role){
  _lockRole = role;
  document.getElementById('lockChoiceView').style.display='none';
  document.getElementById('lockPinView').style.display='block';
  document.getElementById('lockPinTitle').textContent =
    role==='owner'?'Owner PIN':'Technician PIN';
  document.getElementById('lockPinInput').value='';
  document.getElementById('lockError').textContent='';
  setTimeout(function(){document.getElementById('lockPinInput').focus();},150);
}
function lockBack(){
  document.getElementById('lockChoiceView').style.display='block';
  document.getElementById('lockPinView').style.display='none';
  _lockRole = null;
  document.getElementById('lockError').textContent='';
}

async function lockSubmit(){
  var pin = document.getElementById('lockPinInput').value.trim();
  if(pin.length !== 4){
    document.getElementById('lockError').textContent = 'Enter 4 digits';
    return;
  }
  document.getElementById('lockError').textContent = 'Checking...';

  if(_lockRole === 'owner'){
    try {
      var r = await fetch('/api/auth/owner-login', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({pin:pin})
      });
      var d = await r.json();
      if(d.success){
        localStorage.setItem('app_role','owner');
        localStorage.removeItem('tech_session');
        document.body.classList.remove('tech-mode');
        lockHide();
        return;
      }
    } catch(e){}
    document.getElementById('lockError').textContent = 'Invalid owner PIN';
    document.getElementById('lockPinInput').value = '';
    return;
  }

  try {
    var r = await fetch('/api/tech/login', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pin:pin})
    });
    var d = await r.json();
    if(d.success){
      localStorage.setItem('app_role','tech');
      localStorage.setItem('tech_session', JSON.stringify({name:d.name,pin:pin}));
      document.body.classList.add('tech-mode');
      lockHide();
      setTimeout(function(){
        if(typeof tvOpen === 'function') tvOpen();
      }, 400);
      return;
    }
  } catch(e){}
  document.getElementById('lockError').textContent = 'Invalid technician PIN';
  document.getElementById('lockPinInput').value = '';
}

// Logout — call from anywhere
window.appLogout = function(){
  localStorage.removeItem('app_role');
  localStorage.removeItem('tech_session');
  document.body.classList.remove('tech-mode');
  if(typeof tvClose === 'function') tvClose();
  lockShow();
};

// Auto-show lock on first load
(function(){
  var role = localStorage.getItem('app_role');
  if(!role){
    setTimeout(lockShow, 150);
  } else if(role === 'tech'){
    document.body.classList.add('tech-mode');
    setTimeout(function(){
      if(typeof tvOpen === 'function') tvOpen();
    }, 900);
  }
})();

// Keep techs inside tech mode: if they close the modal, reopen it
setInterval(function(){
  if(localStorage.getItem('app_role') === 'tech'){
    var m = document.getElementById('tvModal');
    if(m && m.style.display !== 'block'){
      if(typeof tvOpen === 'function') tvOpen();
    }
  }
}, 1500);

// Inject Logout button into Settings panel
setInterval(function(){
  var s = document.getElementById('settings');
  if(!s || document.getElementById('appLogoutBtn')) return;
  if(localStorage.getItem('app_role') !== 'owner') return;
  var card = s.querySelector('.card');
  if(!card) return;
  var b = document.createElement('button');
  b.id = 'appLogoutBtn';
  b.className = 'btn btn-dark';
  b.textContent = 'Logout';
  b.style.cssText = 'background:linear-gradient(135deg,#ef4444,#dc2626);margin-top:10px;';
  b.onclick = function(){
    if(confirm('Log out of RamsTech?')) window.appLogout();
  };
  card.appendChild(b);
}, 1200);
</script>
"""
