WORKFLOW_HTML = r"""
<style>
#wfFab{position:fixed;bottom:170px;left:18px;width:60px;height:60px;border-radius:50%;
background:linear-gradient(135deg,#10b981,#047857);color:#fff;border:none;font-size:26px;
cursor:pointer;z-index:9997;box-shadow:0 6px 18px rgba(16,185,129,.5);
display:none;align-items:center;justify-content:center;}
#wfPanel{display:none;position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;
padding:12px;overflow:auto;}
#wfInner{max-width:680px;margin:16px auto;background:#0f1520;color:#e6edf5;
border-radius:14px;padding:18px;border:1px solid #1e2938;}
.wfTabs{display:flex;gap:4px;margin-bottom:12px;background:#0a1018;padding:4px;border-radius:10px;}
.wfTab{flex:1;padding:9px 4px;background:transparent;color:#7b8da3;border:none;
border-radius:7px;font-size:11px;font-weight:600;cursor:pointer;}
.wfTab.active{background:#10b981;color:#03121c;}
.wfIn{width:100%;padding:11px 12px;background:#0a1018;border:1px solid #1e2938;
border-radius:9px;color:#e6edf5;font-size:14px;box-sizing:border-box;
font-family:inherit;margin-bottom:8px;}
.wfBtn{width:100%;padding:13px;background:#10b981;color:#fff;border:none;
border-radius:9px;font-weight:700;font-size:14px;cursor:pointer;margin-bottom:8px;}
.wfBtn:disabled{opacity:.5;}
.wfBtn.dark{background:#1e2938;}
.wfBtn.red{background:#ef4444;}
.wfBtn.blue{background:#00a8e8;color:#03121c;}
.wfRow{display:flex;gap:8px;}
.wfRow .wfIn{flex:1;}
#wfResult{display:none;background:#0a1018;border:1px solid #1e2938;border-radius:10px;
padding:12px;margin-top:10px;font-size:13px;white-space:pre-wrap;line-height:1.5;}
#wfSigWrap{display:none;margin:10px 0;}
#wfSigPad{border:2px dashed #334155;border-radius:10px;width:100%;height:160px;
background:#fff;touch-action:none;}
.wfNote{font-size:11px;color:#7b8da3;margin-bottom:10px;}
#wfStage{font-size:12px;color:#10b981;font-weight:700;margin-bottom:6px;}
</style>

<button id="wfFab" onclick="wfToggle()">&#9881;</button>

<div id="wfPanel">
  <div id="wfInner">
    <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
      <div>
        <div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">WORKSHOP</div>
        <div style="font-size:17px;font-weight:700;color:#10b981;">Workflow</div>
      </div>
      <button onclick="wfToggle()" style="background:#1e2938;color:#e6edf5;border:none;
        border-radius:8px;padding:8px 14px;font-size:16px;cursor:pointer;">&#10005;</button>
    </div>

    <div class="wfTabs">
      <button class="wfTab active" data-t="quote" onclick="wfMode('quote')">New Quote</button>
      <button class="wfTab" data-t="vehicle" onclick="wfMode('vehicle')">Vehicle</button>
      <button class="wfTab" data-t="job" onclick="wfMode('job')">Job</button>
    </div>

    <!-- ═══ QUOTE TAB ═══ -->
    <div id="wfQuote">
      <div class="wfNote">Customer signs → job created automatically</div>
      <input id="wqCust" class="wfIn" placeholder="Customer name">
      <input id="wqPhone" class="wfIn" placeholder="Phone">
      <div class="wfRow">
        <input id="wqReg" class="wfIn" placeholder="Registration" autocapitalize="characters" style="text-transform:uppercase">
        <input id="wqKm" class="wfIn" type="number" placeholder="Odometer km">
      </div>
      <div class="wfRow">
        <input id="wqMake" class="wfIn" placeholder="Make (Toyota)">
        <input id="wqModel" class="wfIn" placeholder="Model (Hilux)">
      </div>
      <textarea id="wqDesc" class="wfIn" rows="2" placeholder="Work description"></textarea>
      <div class="wfRow">
        <input id="wqLabour" class="wfIn" type="number" placeholder="Labour R" value="0">
        <input id="wqParts" class="wfIn" type="number" placeholder="Parts R" value="0">
      </div>
      <button class="wfBtn dark" onclick="wfOpenSig()">&#9997; Customer Signature</button>
      <div id="wfSigWrap">
        <canvas id="wfSigPad" width="600" height="160"></canvas>
        <div class="wfRow" style="margin-top:8px;">
          <button class="wfBtn dark" onclick="wfSigClear()">Clear</button>
          <button class="wfBtn" onclick="wfSigSave()">Confirm</button>
        </div>
      </div>
      <div id="wfSigPreview" style="margin-bottom:8px;"></div>
      <button id="wfQuoteBtn" class="wfBtn" onclick="wfSubmitQuote()" disabled>Approve &amp; Create Job</button>
      <div id="wfResult"></div>
    </div>

    <!-- ═══ VEHICLE TAB ═══ -->
    <div id="wfVehicle" style="display:none;">
      <div class="wfNote">Look up a vehicle by registration</div>
      <div class="wfRow">
        <input id="wvReg" class="wfIn" placeholder="Registration" autocapitalize="characters" style="text-transform:uppercase">
        <button class="wfBtn" style="width:auto;padding:11px 16px;" onclick="wfLookupVehicle()">Search</button>
      </div>
      <div id="wvResult"></div>
    </div>

    <!-- ═══ JOB TAB ═══ -->
    <div id="wfJob" style="display:none;">
      <div class="wfNote">Manage an existing job (enter job id)</div>
      <input id="wjId" class="wfIn" placeholder="Job ID (e.g. a4f2c8d1)">
      <div class="wfRow">
        <button class="wfBtn blue" onclick="wfLoadJob()">Load</button>
        <button class="wfBtn dark" onclick="wfAssign()">Assign</button>
      </div>
      <div class="wfRow">
        <button class="wfBtn" onclick="wfPinAction('start')">Start (PIN)</button>
        <button class="wfBtn" onclick="wfPinAction('complete')">Complete (PIN)</button>
      </div>
      <div class="wfRow">
        <button class="wfBtn" onclick="wfPinAction('qc')">QC (PIN)</button>
        <button class="wfBtn blue" onclick="wfInvoice()">Invoice</button>
      </div>
      <div class="wfRow">
        <input id="wjPct" class="wfIn" type="number" placeholder="Progress %" min="0" max="100">
        <button class="wfBtn blue" onclick="wfSetProgress()">Update</button>
      </div>
      <div id="wjResult"></div>
    </div>
  </div>
</div>

<script>
var _wfMode='quote', _wfSigData='', _wfSigPad=null, _wfSigCtx=null, _wfDraw=false;

function wfToggle(){var p=document.getElementById('wfPanel');p.style.display=p.style.display==='block'?'none':'block';}
function wfMode(m){_wfMode=m;document.querySelectorAll('.wfTab').forEach(function(t){t.classList.toggle('active',t.dataset.t===m);});
document.getElementById('wfQuote').style.display=m==='quote'?'block':'none';
document.getElementById('wfVehicle').style.display=m==='vehicle'?'block':'none';
document.getElementById('wfJob').style.display=m==='job'?'block':'none';}

async function wfPost(path,body){var r=await fetch('/api/workflow'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json();}
async function wfGet(path){var r=await fetch('/api/workflow'+path);return r.json();}
function wfShow(id,html){var el=document.getElementById(id);el.innerHTML=html;el.style.display='block';}

// ─── SIGNATURE ───
function wfOpenSig(){
document.getElementById('wfSigWrap').style.display='block';
_wfSigPad=document.getElementById('wfSigPad');
_wfSigCtx=_wfSigPad.getContext('2d');
_wfSigCtx.strokeStyle='#000';_wfSigCtx.lineWidth=2.5;_wfSigCtx.lineCap='round';
var getP=function(e){var r=_wfSigPad.getBoundingClientRect();var x=(e.touches?e.touches[0].clientX:e.clientX)-r.left;var y=(e.touches?e.touches[0].clientY:e.clientY)-r.top;return{x:x*(_wfSigPad.width/r.width),y:y*(_wfSigPad.height/r.height)};};
_wfSigPad.onmousedown=_wfSigPad.ontouchstart=function(e){_wfDraw=true;var p=getP(e);_wfSigCtx.beginPath();_wfSigCtx.moveTo(p.x,p.y);e.preventDefault();};
_wfSigPad.onmousemove=_wfSigPad.ontouchmove=function(e){if(!_wfDraw)return;var p=getP(e);_wfSigCtx.lineTo(p.x,p.y);_wfSigCtx.stroke();e.preventDefault();};
_wfSigPad.onmouseup=_wfSigPad.ontouchend=function(){_wfDraw=false;};
}
function wfSigClear(){_wfSigCtx.clearRect(0,0,_wfSigPad.width,_wfSigPad.height);_wfSigData='';document.getElementById('wfQuoteBtn').disabled=true;}
function wfSigSave(){_wfSigData=_wfSigPad.toDataURL('image/png');document.getElementById('wfSigPreview').innerHTML='<img src="'+_wfSigData+'" style="width:100%;border:1px solid #334155;border-radius:10px;background:#fff">';document.getElementById('wfSigWrap').style.display='none';document.getElementById('wfQuoteBtn').disabled=false;}

// ─── QUOTE SUBMIT ───
async function wfSubmitQuote(){
var b=document.getElementById('wfQuoteBtn');b.disabled=true;b.textContent='Creating...';
try{
var d=await wfPost('/quote-sign',{
customer:document.getElementById('wqCust').value.trim(),
phone:document.getElementById('wqPhone').value.trim(),
registration:document.getElementById('wqReg').value.trim().toUpperCase(),
km:parseInt(document.getElementById('wqKm').value)||0,
make:document.getElementById('wqMake').value.trim(),
model:document.getElementById('wqModel').value.trim(),
description:document.getElementById('wqDesc').value.trim(),
labour:parseFloat(document.getElementById('wqLabour').value)||0,
parts:parseFloat(document.getElementById('wqParts').value)||0,
signature:_wfSigData
});
if(d.success){wfShow('wfResult','Job created: #'+d.job_id+'\nQuote: #'+d.quote_id);
['wqCust','wqPhone','wqReg','wqKm','wqMake','wqModel','wqDesc','wqLabour','wqParts'].forEach(function(i){document.getElementById(i).value='';});
_wfSigData='';document.getElementById('wfSigPreview').innerHTML='';}
else{wfShow('wfResult','Error: '+(d.detail||JSON.stringify(d)));}
}catch(e){wfShow('wfResult','Error: '+e.message);}
b.disabled=false;b.textContent='Approve & Create Job';
}

// ─── VEHICLE LOOKUP ───
async function wfLookupVehicle(){
var reg=document.getElementById('wvReg').value.trim().toUpperCase();
if(!reg){alert('Enter registration');return;}
var d=await wfGet('/vehicle/'+reg);
if(!d.vehicle){wfShow('wvResult','No record for '+reg);return;}
var v=d.vehicle;
var h='<div style="font-weight:700;margin-bottom:6px;">'+v.registration+'</div>'+
(v.make||v.model?'<div>'+v.make+' '+v.model+' '+(v.year||'')+'</div>':'')+
(v.last_km?'<div>Last km: '+v.last_km+'</div>':'');
if(d.history&&d.history.length){h+='<div style="margin-top:8px;font-weight:600;">History</div>';
d.history.forEach(function(j){h+='<div style="padding:6px 0;border-top:1px solid #1e2938;">#'+j.id+' — '+j.status+' — '+(j.complaint||'').slice(0,40)+'</div>';});}
wfShow('wvResult',h);
}

// ─── JOB ACTIONS ───
function wfLoadJob(){
var jid=document.getElementById('wjId').value.trim();
if(!jid){alert('Enter job id');return;}
wfGet('/job/'+jid).then(function(d){
if(d.detail){wfShow('wjResult','Not found');return;}
var j=d.job;
var h='<div style="font-weight:700;">#'+j.id+' — '+j.status+'</div>'+
'<div>Customer: '+(j.customer||'')+'</div>'+
'<div>Vehicle: '+(j.vehicle||'')+'</div>'+
'<div>Assigned: '+(j.assigned_to||'—')+'</div>'+
'<div>Progress: '+(j.progress||0)+'%</div>'+
'<div>Started by: '+(j.tech_started_by||'—')+'</div>'+
'<div>Completed by: '+(j.tech_completed_by||'—')+'</div>'+
'<div>QC by: '+(j.qc_by||'—')+'</div>';
wfShow('wjResult',h);
});}

async function wfAssign(){
var jid=document.getElementById('wjId').value.trim();
var tech=prompt('Technician name:');
if(!tech||!jid)return;
var d=await wfPost('/assign/'+jid,{tech:tech});
wfShow('wjResult',d.success?'Assigned to '+tech:'Error: '+(d.detail||''));}

async function wfPinAction(action){
var jid=document.getElementById('wjId').value.trim();
if(!jid){alert('Enter job id');return;}
var pin=prompt('Technician/Manager 4-digit PIN:');
if(!pin)return;
var d=await wfPost('/'+action+'/'+jid,{pin:pin});
if(d.success){wfShow('wjResult','OK — '+JSON.stringify(d));}else{wfShow('wjResult','Error: '+(d.detail||JSON.stringify(d)));}}

async function wfSetProgress(){
var jid=document.getElementById('wjId').value.trim();
var p=document.getElementById('wjPct').value;
if(!jid||!p){alert('Enter job id and %');return;}
var d=await wfPost('/progress/'+jid,{progress:p});
wfShow('wjResult',d.success?'Progress '+d.progress+'%':'Error');}

async function wfInvoice(){
var jid=document.getElementById('wjId').value.trim();
if(!jid){alert('Enter job id');return;}
var by=prompt('Invoiced by (name):')||'';
var d=await wfPost('/invoice/'+jid,{by:by});
if(d.success){wfShow('wjResult','Invoice #'+d.invoice_id+' created');}else{wfShow('wjResult','Error: '+(d.detail||''));}}

// ─── SHOW FAB ONLY ON JOBS TAB ───
function wfUpdateFab(){
var fab=document.getElementById('wfFab');if(!fab)return;
var a=document.querySelector('.panel.active');
fab.style.display=(a&&a.id==='jobs')?'flex':'none';}
setTimeout(wfUpdateFab,300);
document.addEventListener('click',function(e){
if(e.target.closest('.bnav-item')||e.target.closest('.tile'))setTimeout(wfUpdateFab,80);});
document.getElementById('wfPanel').addEventListener('click',function(e){if(e.target===this)wfToggle();});
</script>
"""
