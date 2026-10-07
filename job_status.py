"""Job Card Workflow — 9-stage kanban board."""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

STATUSES = [
    "New",
    "Diagnosing",
    "Awaiting Approval",
    "Awaiting Parts",
    "In Progress",
    "QC",
    "Ready for Pickup",
    "Completed",
    "Invoiced",
]


@router.get("/api/jobs/kanban")
def jobs_kanban():
    import db
    if not db.is_ready():
        return {"statuses": STATUSES, "columns": {}}
    jobs = db.get_all("jobs") or []
    columns = {s: [] for s in STATUSES}
    for j in jobs:
        s = j.get("status") or "New"
        if s not in columns:
            columns[s] = []
        columns[s].append({
            "id": j.get("id"),
            "customer": j.get("customer", ""),
            "vehicle": j.get("vehicle", ""),
            "registration": j.get("registration", ""),
            "complaint": (j.get("complaint") or "")[:60],
            "total": j.get("total", 0),
        })
    return {"statuses": STATUSES, "columns": columns}


@router.post("/api/jobs/{jid}/status")
async def set_job_status(jid: str, r: Request):
    import db
    from datetime import datetime
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    d = await r.json()
    new_status = (d.get("status") or "").strip()
    note = (d.get("note") or "").strip()
    if new_status not in STATUSES:
        raise HTTPException(400, f"Invalid status. Allowed: {STATUSES}")
    job = db.get_one("jobs", jid)
    if not job:
        raise HTTPException(404, "Job not found")
    old_status = job.get("status") or "New"
    job["status"] = new_status
    timeline = job.get("timeline") or []
    if isinstance(timeline, str):
        timeline = [timeline]
    entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} — {old_status} → {new_status}"
    if note:
        entry += f" | {note}"
    timeline.append(entry)
    job["timeline"] = timeline
    db.update("jobs", jid, {"status": new_status, "timeline": timeline})
    return {"success": True, "job": job, "old_status": old_status, "new_status": new_status}


JOB_STATUS_HTML = r"""
<style>
#jsFab{display:none;position;fixed;bottom:96px;right:18px;width:52px;height:52px;border-radius:50%;
background:linear-gradient(135deg,#7c3aed,#5b21b6);color:#fff;border:none;font-size:22px;
cursor:pointer;z-index:9996;box-shadow:0 6px 18px rgba(124,58,237,.45);}
#jsPanel{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9998;padding:10px;overflow:auto;}
#jsInner{background:#0f1520;color:#e6edf5;border-radius:14px;padding:14px;max-width:1000px;margin:20px auto;}
.jsCol{background:#0a1018;border:1px solid #1e2938;border-radius:10px;padding:8px;margin-bottom:8px;}
.jsColHeader{font-size:12px;font-weight:700;margin-bottom:6px;letter-spacing:.5px;}
.jsCard{background:#0f1520;border-left:3px solid;border-radius:6px;padding:8px;margin-bottom:6px;cursor:pointer;font-size:12px;}
.jsCard:hover{background:#1e2938;}
.jsCardId{color:#7b8da3;font-size:10px;}
.jsCardTitle{font-weight:700;margin:2px 0;}
.jsCardSub{color:#a5b4c7;font-size:11px;}
</style>
<button id="jsFab" onclick="jsToggle()" title="Job Board">📋</button>
<div id="jsPanel">
<div id="jsInner">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
<div>
<div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">WORKSHOP</div>
<div style="font-size:17px;font-weight:700;color:#7c3aed;">Job Board</div>
</div>
<div>
<button onclick="jsLoad()" style="background:#1e2938;color:#e6edf5;border:none;border-radius:6px;padding:8px 12px;font-size:12px;cursor:pointer;margin-right:6px;">↻ Refresh</button>
<button onclick="jsToggle()" style="background:#1e2938;color:#e6edf5;border:none;border-radius:6px;padding:8px 12px;font-size:14px;cursor:pointer;">✕</button>
</div>
</div>
<div id="jsBoard" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">
<div style="color:#7b8da3;font-size:13px;">Loading…</div>
</div>
</div>
</div>
<div id="jsMove" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;padding:16px;">
<div style="max-width:400px;margin:60px auto;background:#0f1520;color:#e6edf5;border-radius:12px;padding:18px;">
<div style="font-size:12px;color:#7b8da3;margin-bottom:6px;">MOVE JOB</div>
<div id="jsMoveJob" style="font-weight:700;margin-bottom:12px;"></div>
<select id="jsMoveStatus" style="width:100%;padding:10px;background:#0a1018;color:#e6edf5;border:1px solid #1e2938;border-radius:8px;font-size:14px;margin-bottom:10px;"></select>
<input id="jsMoveNote" placeholder="Note (optional)" style="width:100%;padding:10px;background:#0a1018;color:#e6edf5;border:1px solid #1e2938;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:10px;">
<div style="display:flex;gap:6px;">
<button onclick="jsSubmitMove()" style="flex:1;background:#7c3aed;color:#fff;border:none;border-radius:8px;padding:12px;font-weight:700;cursor:pointer;">Move</button>
<button onclick="document.getElementById('jsMove').style.display='none'" style="flex:1;background:#1e2938;color:#e6edf5;border:none;border-radius:8px;padding:12px;cursor:pointer;">Cancel</button>
</div>
</div>
</div>
<script>
var _jsStatuses=[];
var _jsSelected=null;
function jsToggle(){var p=document.getElementById('jsPanel');var v=p.style.display==='block';p.style.display=v?'none':'block';if(!v)jsLoad();}
function jsLoad(){
var b=document.getElementById('jsBoard');
b.innerHTML='<div style="color:#7b8da3;font-size:13px;">Loading…</div>';
fetch('/api/jobs/kanban').then(function(r){return r.json();}).then(function(d){
_jsStatuses=d.statuses||[];
var cols=d.columns||{};
var html='';
_jsStatuses.forEach(function(s){
var items=cols[s]||[];
html+='<div class="jsCol"><div class="jsColHeader" style="color:'+_jsColor(s)+'">'+s+' ('+items.length+')</div>';
items.forEach(function(j){
html+='<div class="jsCard" style="border-color:'+_jsColor(s)+'" onclick="jsOpenMove(\''+j.id+'\',\''+_jsEscape(j.customer)+'\',\''+_jsEscape(j.vehicle)+'\')">';
html+='<div class="jsCardId">#'+j.id+'</div>';
html+='<div class="jsCardTitle">'+_jsEscape(j.customer||'(no customer)')+'</div>';
html+='<div class="jsCardSub">'+_jsEscape(j.vehicle||'')+(j.registration?' · '+_jsEscape(j.registration):'')+'</div>';
if(j.complaint)html+='<div class="jsCardSub" style="font-style:italic;">'+_jsEscape(j.complaint)+'</div>';
html+='</div>';
});
html+='</div>';
});
b.innerHTML=html;
}).catch(function(e){b.innerHTML='<div style="color:#ef4444;">Error: '+e.message+'</div>';});
}
function _jsColor(s){
var m={'New':'#00a8e8','Diagnosing':'#7c3aed','Awaiting Approval':'#f59e0b','Awaiting Parts':'#ef4444','In Progress':'#06b6d4','QC':'#8b5cf6','Ready for Pickup':'#10b981','Completed':'#16a34a','Invoiced':'#64748b'};
return m[s]||'#64748b';
}
function _jsEscape(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;');}
function jsOpenMove(jid,cust,veh){
_jsSelected=jid;
document.getElementById('jsMoveJob').textContent='#'+jid+' — '+cust+' ('+veh+')';
var sel=document.getElementById('jsMoveStatus');
sel.innerHTML='';
_jsStatuses.forEach(function(s){
var o=document.createElement('option');o.value=s;o.textContent=s;sel.appendChild(o);
});
document.getElementById('jsMoveNote').value='';
document.getElementById('jsMove').style.display='block';
}
function jsSubmitMove(){
if(!_jsSelected)return;
var s=document.getElementById('jsMoveStatus').value;
var n=document.getElementById('jsMoveNote').value;
fetch('/api/jobs/'+_jsSelected+'/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:s,note:n})})
.then(function(r){return r.json();})
.then(function(d){
if(d.success){document.getElementById('jsMove').style.display='none';jsLoad();}
else{alert('Failed: '+(d.detail||d.reply||'unknown'));}
})
.catch(function(e){alert('Error: '+e.message);});
}
document.getElementById('jsMove').addEventListener('click',function(e){if(e.target===this)this.style.display='none';});
setInterval(function(){
var jp=document.getElementById('jobs');
if(!jp||document.getElementById('jsInlineBtn'))return;
var t=jp.querySelector('.panel-title');
if(!t)return;
var b=document.createElement('button');
b.id='jsInlineBtn';
b.className='btn';
b.style.cssText='background:linear-gradient(135deg,#7c3aed,#5b21b6);';
b.textContent='Kanban View';
b.onclick=function(){jsToggle();};
t.parentNode.insertBefore(b,t.nextSibling);
},900);
</script>
"""


def get_html():
    return JOB_STATUS_HTML
