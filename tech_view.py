"""Technician view — PIN login via auth.py, only their own jobs."""
from fastapi import APIRouter, HTTPException, Request
import auth

router = APIRouter()


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


@router.post("/api/tech/login")
async def tech_login(r: Request):
    d = await r.json()
    s = auth.lookup_pin(d.get("pin"))
    if not s:
        raise HTTPException(401, "Invalid PIN")
    try:
        r2 = _c().table("jobs").select("*").eq("assigned_to", s["name"]).execute()
        all_jobs = r2.data or []
    except Exception:
        all_jobs = []
    active = [j for j in all_jobs if j.get("status") not in ("Invoiced", "Completed")]
    done = [j for j in all_jobs if j.get("status") in ("Invoiced", "Completed")]
    active.sort(key=lambda x: x.get("created") or "", reverse=True)
    done.sort(key=lambda x: x.get("created") or "", reverse=True)
    return {
        "success": True,
        "name": s["name"],
        "role": s.get("role", ""),
        "active": active[:20],
        "done": done[:10],
    }


@router.get("/api/tech/jobs/{tech_name}")
def tech_jobs(tech_name: str):
    try:
        r = _c().table("jobs").select("*").eq("assigned_to", tech_name).execute()
        all_jobs = r.data or []
    except Exception:
        all_jobs = []
    active = [j for j in all_jobs if j.get("status") not in ("Invoiced", "Completed")]
    done = [j for j in all_jobs if j.get("status") in ("Invoiced", "Completed")]
    active.sort(key=lambda x: x.get("created") or "", reverse=True)
    done.sort(key=lambda x: x.get("created") or "", reverse=True)
    return {"active": active[:20], "done": done[:10]}


TECH_HTML = r"""
<style>
#tvBtn{position:fixed;bottom:170px;left:18px;width:60px;height:60px;border-radius:50%;
background:linear-gradient(135deg,#f59e0b,#b45309);color:#fff;border:none;font-size:26px;
cursor:pointer;z-index:9996;box-shadow:0 6px 18px rgba(245,158,11,.5);
display:flex;align-items:center;justify-content:center;}
#tvModal{display:none;position:fixed;inset:0;background:#0a1018;z-index:9999;overflow:auto;}
#tvInner{max-width:680px;margin:0 auto;padding:16px;color:#e6edf5;min-height:100vh;}
.tvIn{width:100%;padding:14px;background:#0f1520;border:1px solid #1e2938;border-radius:10px;
color:#e6edf5;font-size:18px;box-sizing:border-box;text-align:center;letter-spacing:8px;
font-family:monospace;margin-bottom:12px;}
.tvBtn{width:100%;padding:16px;background:#10b981;color:#fff;border:none;border-radius:10px;
font-weight:700;font-size:16px;cursor:pointer;margin-bottom:8px;}
.tvBtn:active{transform:scale(.98);}
.tvBtn.dark{background:#1e2938;}
.tvBtn.red{background:#ef4444;}
.tvBtn.blue{background:#00a8e8;color:#03121c;}
.tvCard{background:#0f1520;border-left:4px solid #f59e0b;border-radius:10px;
padding:14px;margin-bottom:10px;}
.tvCard.ready{border-left-color:#10b981;}
.tvCard.qc{border-left-color:#8b5cf6;}
.tvName{font-weight:800;font-size:16px;margin-bottom:4px;}
.tvMeta{font-size:12px;color:#94a3b8;margin-bottom:6px;}
.tvDesc{font-size:14px;color:#e6edf5;margin:8px 0;line-height:1.4;}
.tvBadge{display:inline-block;padding:3px 9px;border-radius:10px;font-size:11px;
font-weight:700;color:#fff;background:#f59e0b;margin-left:6px;}
.tvBadge.green{background:#10b981;}
.tvBadge.purple{background:#8b5cf6;}
.tvProg{height:8px;background:#1e2938;border-radius:4px;margin:10px 0;overflow:hidden;}
.tvProgBar{height:100%;background:linear-gradient(90deg,#10b981,#34d399);transition:width .3s;}
.tvHeader{display:flex;justify-content:space-between;align-items:center;
padding-bottom:14px;border-bottom:2px solid #1e2938;margin-bottom:16px;}
.tvLogout{background:#1e2938;color:#e6edf5;border:none;border-radius:8px;
padding:8px 14px;font-size:13px;cursor:pointer;font-weight:600;}
.tvEmpty{text-align:center;color:#7b8da3;padding:40px 20px;font-size:14px;}
.tvSection{font-size:12px;font-weight:700;color:#7b8da3;text-transform:uppercase;
letter-spacing:1.5px;margin:20px 0 10px;}
</style>

<button id="tvBtn" onclick="tvOpen()" title="Technician Mode">&#128119;</button>

<div id="tvModal">
  <div id="tvInner">
    <div id="tvLoginView">
      <div style="text-align:center;padding:60px 20px 20px;">
        <div style="font-size:56px;margin-bottom:8px;">&#128119;</div>
        <div style="font-size:22px;font-weight:800;color:#f59e0b;margin-bottom:6px;">Technician Mode</div>
        <div style="font-size:13px;color:#94a3b8;margin-bottom:28px;">Enter your 4-digit PIN</div>
      </div>
      <input id="tvPin" type="tel" maxlength="4" inputmode="numeric" class="tvIn" placeholder="....">
      <button class="tvBtn" onclick="tvLogin()">Login</button>
      <button class="tvBtn dark" onclick="tvClose()">Cancel</button>
      <div id="tvError" style="color:#ef4444;text-align:center;font-size:13px;margin-top:12px;"></div>
    </div>

    <div id="tvJobsView" style="display:none;">
      <div class="tvHeader">
        <div>
          <div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">TECHNICIAN</div>
          <div id="tvTechName" style="font-size:18px;font-weight:800;color:#f59e0b;"></div>
        </div>
        <div>
          <button class="tvLogout" onclick="tvRefresh()" style="margin-right:6px;">&#8635;</button>
          <button class="tvLogout" onclick="tvLogout()">Logout</button>
        </div>
      </div>
      <div id="tvJobList"></div>
    </div>

    <div id="tvJobDetail" style="display:none;">
      <div class="tvHeader">
        <button class="tvLogout" onclick="tvBack()">&#8592; Back</button>
        <div id="tvJobId" style="font-weight:700;color:#f59e0b;"></div>
        <button class="tvLogout" onclick="tvRefresh()">&#8635;</button>
      </div>
      <div id="tvJobContent"></div>
    </div>
  </div>
</div>

<script>
var _tvTech=null, _tvPin=null, _tvJobId=null;

function tvOpen(){document.getElementById('tvModal').style.display='block';tvCheckSession();}
function tvClose(){document.getElementById('tvModal').style.display='none';}

function tvCheckSession(){
  try{
    var saved=localStorage.getItem('tech_session');
    if(saved){
      var s=JSON.parse(saved);
      if(s.name&&s.pin){
        _tvTech=s.name;_tvPin=s.pin;
        tvShowJobs();
        return;
      }
    }
  }catch(e){}
  document.getElementById('tvLoginView').style.display='block';
  document.getElementById('tvJobsView').style.display='none';
  document.getElementById('tvJobDetail').style.display='none';
  document.getElementById('tvPin').value='';
  document.getElementById('tvError').textContent='';
}

async function tvLogin(){
  var pin=document.getElementById('tvPin').value.trim();
  if(pin.length!==4){document.getElementById('tvError').textContent='Enter 4 digits';return;}
  document.getElementById('tvError').textContent='Checking...';
  try{
    var r=await fetch('/api/tech/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin})});
    var d=await r.json();
    if(d.success){
      _tvTech=d.name;_tvPin=pin;
      localStorage.setItem('tech_session',JSON.stringify({name:d.name,pin:pin}));
      localStorage.setItem('app_role','tech');
      document.body.classList.add('tech-mode');
      tvShowJobs();
    } else {
      document.getElementById('tvError').textContent=d.detail||'Invalid PIN';
    }
  }catch(e){document.getElementById('tvError').textContent='Network error';}
}

function tvLogout(){
  localStorage.removeItem('tech_session');
  localStorage.removeItem('app_role');
  document.body.classList.remove('tech-mode');
  _tvTech=null;_tvPin=null;
  if(typeof appLogout === 'function'){
    tvClose();
    appLogout();
  } else {
    tvCheckSession();
  }
}

async function tvShowJobs(){
  document.getElementById('tvLoginView').style.display='none';
  document.getElementById('tvJobsView').style.display='block';
  document.getElementById('tvJobDetail').style.display='none';
  document.getElementById('tvTechName').textContent=_tvTech;
  document.getElementById('tvJobList').innerHTML='<div class="tvEmpty">Loading...</div>';
  try{
    var r=await fetch('/api/tech/jobs/'+encodeURIComponent(_tvTech));
    var d=await r.json();
    tvRenderJobs(d);
  }catch(e){
    document.getElementById('tvJobList').innerHTML='<div class="tvEmpty">Error loading jobs</div>';
  }
}

function tvRenderJobs(d){
  var h='';
  if(!d.active||d.active.length===0){
    h+='<div class="tvEmpty">No active jobs assigned to you</div>';
  } else {
    h+='<div class="tvSection">Active Jobs ('+d.active.length+')</div>';
    d.active.forEach(function(j){
      var badge='<span class="tvBadge">'+j.status+'</span>';
      if(j.status==='Ready for Pickup') badge='<span class="tvBadge green">Ready</span>';
      if(j.status==='Awaiting QC') badge='<span class="tvBadge purple">Awaiting QC</span>';
      var meta=(j.vehicle||'')+(j.registration?' · '+j.registration:'')+(j.km?' · '+j.km+' km':'');
      var prog=0;
      try{var m=JSON.parse(j.signature||'{}');prog=m.progress||0;}catch(e){}
      h+='<div class="tvCard" onclick="tvOpenJob(\''+j.id+'\')">'+
         '<div class="tvName">'+(j.customer||'')+badge+'</div>'+
         '<div class="tvMeta">'+meta+'</div>'+
         '<div class="tvDesc">'+(j.complaint||'')+'</div>'+
         '<div class="tvProg"><div class="tvProgBar" style="width:'+prog+'%"></div></div>'+
         '<div style="font-size:11px;color:#94a3b8;">Progress: '+prog+'%</div>'+
         '</div>';
    });
  }
  if(d.done&&d.done.length>0){
    h+='<div class="tvSection">Recently Completed</div>';
    d.done.forEach(function(j){
      h+='<div class="tvCard ready">'+
         '<div class="tvName">'+(j.customer||'')+' <span class="tvBadge green">'+j.status+'</span></div>'+
         '<div class="tvMeta">'+(j.vehicle||'')+' · '+(j.registration||'')+'</div>'+
         '<div class="tvDesc" style="color:#7b8da3;">'+(j.complaint||'')+'</div>'+
         '</div>';
    });
  }
  document.getElementById('tvJobList').innerHTML=h;
}

async function tvOpenJob(jid){
  _tvJobId=jid;
  document.getElementById('tvJobsView').style.display='none';
  document.getElementById('tvJobDetail').style.display='block';
  document.getElementById('tvJobId').textContent='Job #'+jid;
  document.getElementById('tvJobContent').innerHTML='<div class="tvEmpty">Loading...</div>';
  try{
    var r=await fetch('/api/workflow/job/'+jid);
    var d=await r.json();
    if(!d.job){document.getElementById('tvJobContent').innerHTML='<div class="tvEmpty">Not found</div>';return;}
    tvRenderJob(d.job,d.meta||{});
  }catch(e){
    document.getElementById('tvJobContent').innerHTML='<div class="tvEmpty">Error</div>';
  }
}

function tvRenderJob(j,meta){
  var prog=meta.progress||0;
  var h='<div class="tvCard">'+
    '<div class="tvName">'+(j.customer||'')+'</div>'+
    '<div class="tvMeta">'+(j.vehicle||'')+(j.registration?' · '+j.registration:'')+(j.km?' · '+j.km+' km':'')+'</div>'+
    '<div class="tvDesc">'+(j.complaint||'')+'</div>'+
    '<div class="tvProg"><div class="tvProgBar" style="width:'+prog+'%"></div></div>'+
    '<div style="font-size:12px;color:#94a3b8;margin-top:6px;">Progress: '+prog+'% | Status: '+j.status+'</div>'+
    '</div>';

  if(j.status==='In Progress'&&!meta.started_by){
    h+='<button class="tvBtn" onclick="tvAction(\'start\')">&#9654; Start Work</button>';
  }
  if(j.status==='In Progress'){
    h+='<div class="tvCard">'+
       '<div style="font-size:13px;color:#94a3b8;margin-bottom:8px;">Update progress:</div>'+
       '<div style="display:flex;gap:6px;margin-bottom:8px;">'+
       '<button class="tvBtn dark" style="margin:0;" onclick="tvQuickProgress(25)">25%</button>'+
       '<button class="tvBtn dark" style="margin:0;" onclick="tvQuickProgress(50)">50%</button>'+
       '<button class="tvBtn dark" style="margin:0;" onclick="tvQuickProgress(75)">75%</button>'+
       '<button class="tvBtn dark" style="margin:0;" onclick="tvQuickProgress(100)">100%</button>'+
       '</div></div>';
    h+='<button class="tvBtn blue" onclick="tvAction(\'complete\')">&#10003; Complete Work</button>';
  }
  if(j.status==='Awaiting QC'||j.status==='Ready for Pickup'){
    h+='<div class="tvEmpty" style="padding:20px;">Waiting for manager QC</div>';
  }
  if(j.status==='Invoiced'||j.status==='Completed'){
    h+='<div class="tvEmpty" style="padding:20px;color:#10b981;">&#10003; Job complete</div>';
  }

  document.getElementById('tvJobContent').innerHTML=h;
}

async function tvAction(act){
  var pin=prompt('Enter your PIN:');
  if(!pin)return;
  var ep=act==='start'?'/start/':'/complete/';
  var url='/api/workflow'+ep+_tvJobId;
  try{
    var r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin})});
    var d=await r.json();
    if(d.success){
      alert('Done: '+act);
      tvOpenJob(_tvJobId);
    } else {
      alert('Error: '+(d.detail||JSON.stringify(d)));
    }
  }catch(e){alert('Network error');}
}

async function tvQuickProgress(pct){
  try{
    var r=await fetch('/api/workflow/progress/'+_tvJobId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({progress:pct})});
    var d=await r.json();
    if(d.success){ tvOpenJob(_tvJobId); }
  }catch(e){}
}

function tvBack(){
  document.getElementById('tvJobDetail').style.display='none';
  tvShowJobs();
}

function tvRefresh(){
  if(_tvJobId&&document.getElementById('tvJobDetail').style.display==='block'){tvOpenJob(_tvJobId);}
  else{tvShowJobs();}
}
</script>
"""
