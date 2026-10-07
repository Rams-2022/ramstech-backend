WORKFLOW_HTML = r"""
<style>
#wfModal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;padding:12px;overflow:auto;}
#wfBox{max-width:640px;margin:16px auto;background:#0f1520;color:#e6edf5;border-radius:14px;padding:18px;border:1px solid #1e2938;}
.wfIn{width:100%;padding:11px;background:#0a1018;border:1px solid #1e2938;border-radius:9px;color:#e6edf5;font-size:14px;box-sizing:border-box;font-family:inherit;margin-bottom:8px;}
.wfBtn{width:100%;padding:12px;background:#10b981;color:#fff;border:none;border-radius:9px;font-weight:700;font-size:14px;cursor:pointer;margin-bottom:6px;}
.wfBtn:disabled{opacity:.5;}
.wfBtn.dark{background:#1e2938;}
.wfBtn.blue{background:#00a8e8;color:#03121c;}
.wfBtn.purple{background:#8b5cf6;}
.wfBtn.red{background:#ef4444;}
.wfRow{display:flex;gap:8px;}
.wfRow .wfIn{flex:1;}
.wfSig{border:2px dashed #334155;border-radius:10px;width:100%;height:150px;background:#fff;touch-action:none;}
#wfRes{display:none;background:#0a1018;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-top:10px;font-size:13px;white-space:pre-wrap;}
#wfBadge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;color:#fff;margin-left:6px;}
.badge-draft{background:#6b7280;}
.badge-csigned{background:#f59e0b;}
.badge-approved{background:#10b981;}
#wfQuoteList{margin-bottom:16px;}
.wfQuoteCard{background:#0a1018;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-bottom:8px;cursor:pointer;}
.wfQuoteCard:active{background:#1e2938;}
</style>

<div id="wfModal">
  <div id="wfBox">
    <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
      <div id="wfTitle" style="font-size:17px;font-weight:700;color:#10b981;">New Quote</div>
      <button onclick="wfClose()" style="background:#1e2938;color:#e6edf5;border:none;border-radius:8px;padding:8px 14px;cursor:pointer;">X</button>
    </div>

    <div id="wfQuoteCreate">
      <input id="wqCust" class="wfIn" placeholder="Customer name">
      <input id="wqPhone" class="wfIn" placeholder="Phone">
      <div class="wfRow">
        <input id="wqReg" class="wfIn" placeholder="Registration" style="text-transform:uppercase">
        <input id="wqKm" class="wfIn" type="number" placeholder="km">
      </div>
      <div class="wfRow">
        <input id="wqMake" class="wfIn" placeholder="Make">
        <input id="wqModel" class="wfIn" placeholder="Model">
      </div>
      <textarea id="wqDesc" class="wfIn" rows="2" placeholder="Work description"></textarea>
      <div class="wfRow">
        <input id="wqLabour" class="wfIn" type="number" placeholder="Labour R" value="0">
        <input id="wqParts" class="wfIn" type="number" placeholder="Parts R" value="0">
      </div>
      <button class="wfBtn" onclick="wfCreateQuote()">Save Quote (Draft)</button>
    </div>

    <div id="wfQuoteView" style="display:none;">
      <div id="wfQuoteInfo" style="font-size:13px;color:#94a3b8;margin-bottom:12px;"></div>
      <div id="wfQuoteActions"></div>
      <div id="wfSigArea"></div>
    </div>

    <div id="wfJobView" style="display:none;">
      <div id="wfJobInfo" style="font-size:13px;color:#94a3b8;margin-bottom:12px;"></div>
      <div id="wfJobActions"></div>
      <div class="wfRow" style="margin-top:10px;">
        <input id="wfProgIn" class="wfIn" type="number" placeholder="Progress %" min="0" max="100">
        <button class="wfBtn blue" onclick="wfSetProgress()" style="width:auto;padding:11px 16px;">Update %</button>
      </div>
    </div>

    <div id="wfRes"></div>
  </div>
</div>

<script>
var _wfJob=null, _wfQuote=null, _wfSigData='', _wfSigPad=null, _wfSigCtx=null, _wfDraw=false, _wfSigTarget=null;

async function wfPost(p,b){ var r=await fetch('/api/workflow'+p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}); var t=await r.text(); try{return JSON.parse(t);}catch(e){return {detail:'Server error: '+t.slice(0,200)};} }
async function wfGet(p){ var r=await fetch('/api/workflow'+p); var t=await r.text(); try{return JSON.parse(t);}catch(e){return {detail:'Server error: '+t.slice(0,200)};} }
function wfOpen(){ document.getElementById('wfModal').style.display='block'; }
function wfClose(){ document.getElementById('wfModal').style.display='none'; }
function wfRes(txt){ var e=document.getElementById('wfRes'); e.textContent=txt; e.style.display='block'; }

// ═══ NEW QUOTE ═══
function wfOpenNewQuote(){
  _wfJob=null; _wfQuote=null;
  document.getElementById('wfTitle').textContent='New Quote';
  document.getElementById('wfQuoteCreate').style.display='block';
  document.getElementById('wfQuoteView').style.display='none';
  document.getElementById('wfJobView').style.display='none';
  document.getElementById('wfRes').style.display='none';
  wfOpen();
}

async function wfCreateQuote(){
  var b=event.target; b.disabled=true; b.textContent='Saving...';
  var d=await wfPost('/quote-create',{
    customer:document.getElementById('wqCust').value.trim(),
    phone:document.getElementById('wqPhone').value.trim(),
    registration:document.getElementById('wqReg').value.trim().toUpperCase(),
    km:parseInt(document.getElementById('wqKm').value)||0,
    make:document.getElementById('wqMake').value.trim(),
    model:document.getElementById('wqModel').value.trim(),
    description:document.getElementById('wqDesc').value.trim(),
    labour:parseFloat(document.getElementById('wqLabour').value)||0,
    parts:parseFloat(document.getElementById('wqParts').value)||0
  });
  if(d.success){
    wfRes('Quote #'+d.quote_id+' saved as draft');
    ['wqCust','wqPhone','wqReg','wqKm','wqMake','wqModel','wqDesc','wqLabour','wqParts'].forEach(function(i){document.getElementById(i).value='';});
    if(typeof wfRefresh==='function') setTimeout(wfRefresh,600);
    setTimeout(function(){ wfOpenQuote(d.quote_id); },800);
  } else { wfRes('Error: '+(d.detail||JSON.stringify(d))); }
  b.disabled=false; b.textContent='Save Quote (Draft)';
}

// ═══ OPEN EXISTING QUOTE ═══
async function wfOpenQuote(qid){
  _wfQuote=qid; _wfJob=null;
  document.getElementById('wfTitle').textContent='Quote #'+qid;
  document.getElementById('wfQuoteCreate').style.display='none';
  document.getElementById('wfQuoteView').style.display='block';
  document.getElementById('wfJobView').style.display='none';
  document.getElementById('wfRes').style.display='none';
  document.getElementById('wfQuoteActions').innerHTML='Loading...';
  document.getElementById('wfSigArea').innerHTML='';
  wfOpen();
  var d=await wfGet('/quote/'+qid);
  if(!d.quote){ document.getElementById('wfQuoteActions').innerHTML='Quote not found'; return; }
  wfRenderQuote(d.quote);
}

function wfRenderQuote(q){
  var st=q.status||'draft';
  var badge={draft:'Draft',customer_signed:'Awaiting Owner',approved:'Approved'}[st]||st;
  var cls={draft:'badge-draft',customer_signed:'badge-csigned',approved:'badge-approved'}[st]||'badge-draft';
  document.getElementById('wfQuoteInfo').innerHTML=
    '<div><b>'+q.customer+'</b> — '+q.vehicle+' '+q.registration+'</div>'+
    '<div>'+q.description+'</div>'+
    '<div>Total: <b>R'+(q.total||0).toFixed(2)+'</b> <span id="wfBadge" class="'+cls+'">'+badge+'</span></div>';

  var h='';
  if(st==='draft'){
    h+='<div style="font-size:12px;color:#7b8da3;margin-bottom:8px;">Hand the phone to the customer to sign</div>';
    h+='<button class="wfBtn" onclick="wfOpenSig(\'customer\')">Customer Signature</button>';
  } else if(st==='customer_signed'){
    h+='<div style="font-size:12px;color:#7b8da3;margin-bottom:8px;">Customer signed ✓ — now hand to owner/manager</div>';
    h+='<button class="wfBtn blue" onclick="wfOpenSig(\'owner\')">Owner Approval Signature</button>';
  } else if(st==='approved'){
    h+='<div style="text-align:center;color:#10b981;font-weight:700;padding:12px;">Approved — job created</div>';
    if(q.job_id) h+='<button class="wfBtn dark" onclick="wfOpenJob(\''+q.job_id+'\')">Open Job #'+q.job_id+'</button>';
  }
  document.getElementById('wfQuoteActions').innerHTML=h;
}

// ═══ SIGNATURE PAD ═══
function wfOpenSig(target){
  _wfSigTarget=target;
  document.getElementById('wfSigArea').innerHTML=
    '<div style="margin-top:12px;"><canvas id="wfSigPad" class="wfSig" width="600" height="150"></canvas>'+
    '<div class="wfRow" style="margin-top:8px;">'+
    '<button class="wfBtn dark" onclick="wfSigClear()">Clear</button>'+
    '<button class="wfBtn" onclick="wfSigSave()">Confirm Signature</button>'+
    '</div></div>';
  _wfSigPad=document.getElementById('wfSigPad');
  _wfSigCtx=_wfSigPad.getContext('2d');
  _wfSigCtx.strokeStyle='#000'; _wfSigCtx.lineWidth=2.5; _wfSigCtx.lineCap='round';
  var getP=function(e){ var r=_wfSigPad.getBoundingClientRect(); var x=(e.touches?e.touches[0].clientX:e.clientX)-r.left; var y=(e.touches?e.touches[0].clientY:e.clientY)-r.top; return {x:x*(_wfSigPad.width/r.width),y:y*(_wfSigPad.height/r.height)}; };
  _wfSigPad.onmousedown=_wfSigPad.ontouchstart=function(e){ _wfDraw=true; var p=getP(e); _wfSigCtx.beginPath(); _wfSigCtx.moveTo(p.x,p.y); e.preventDefault(); };
  _wfSigPad.onmousemove=_wfSigPad.ontouchmove=function(e){ if(!_wfDraw)return; var p=getP(e); _wfSigCtx.lineTo(p.x,p.y); _wfSigCtx.stroke(); e.preventDefault(); };
  _wfSigPad.onmouseup=_wfSigPad.ontouchend=function(){ _wfDraw=false; };
}
function wfSigClear(){ _wfSigCtx.clearRect(0,0,_wfSigPad.width,_wfSigPad.height); }
async function wfSigSave(){
  var sig=_wfSigPad.toDataURL('image/png');
  var endpoint=_wfSigTarget==='customer'?'/quote-customer-sign/':'/quote-owner-sign/';
  var d=await wfPost(endpoint+_wfQuote,{signature:sig});
  if(d.success){
    if(_wfSigTarget==='customer'){ wfRes('Customer signature captured'); }
    else { wfRes('Owner approved — job #'+d.job_id+' created and appears in your Jobs list'); }
    if(typeof wfRefresh==='function') setTimeout(wfRefresh,600);
    setTimeout(function(){ wfOpenQuote(_wfQuote); },700);
  } else { wfRes('Error: '+(d.detail||JSON.stringify(d))); }
}

// ═══ JOB ACTIONS ═══
async function wfOpenJob(jid){
  _wfJob=jid; _wfQuote=null;
  document.getElementById('wfTitle').textContent='Job #'+jid;
  document.getElementById('wfQuoteCreate').style.display='none';
  document.getElementById('wfQuoteView').style.display='none';
  document.getElementById('wfJobView').style.display='block';
  document.getElementById('wfRes').style.display='none';
  document.getElementById('wfJobActions').innerHTML='Loading...';
  wfOpen();
  var d=await wfGet('/job/'+jid);
  if(!d.job){ document.getElementById('wfJobActions').innerHTML='Job not found'; return; }
  wfRenderJob(d.job);
}

function wfRenderJob(j){
  var s=j.stage||'Approved';
  document.getElementById('wfJobInfo').innerHTML=
    '<div><b>'+(j.customer||'')+'</b> — '+(j.vehicle||'')+' '+(j.registration||'')+'</div>'+
    '<div>Stage: <b style="color:#10b981">'+s+'</b> | Progress: '+(j.progress||0)+'%</div>'+
    '<div>Assigned: '+(j.assigned_to||'—')+' | Started: '+(j.tech_started_by||'—')+'</div>'+
    '<div>Completed: '+(j.tech_completed_by||'—')+' | QC: '+(j.qc_by||'—')+'</div>'+
    '<div>Invoice: '+(j.invoice_id||'—')+'</div>';

  var next={
    'Approved':{label:'Assign Technician',act:'assign'},
    'Assigned':{label:'Start Work (PIN)',act:'start'},
    'In Progress':{label:'Complete Work (PIN)',act:'complete'},
    'QC':{label:'QC Pass (PIN)',act:'qc'},
    'Awaiting QC':{label:'QC Pass (PIN)',act:'qc'},
    'Ready':{label:'Generate Invoice',act:'invoice'},
    'Invoiced':{label:'Done',act:'done'}
  };
  var n=next[s]||next['Approved'];
  var h='';
  if(n.act!=='done') h+='<button class="wfBtn" onclick="wfAction(\''+n.act+'\')">'+n.label+'</button>';
  else h+='<div style="text-align:center;color:#10b981;font-weight:700;padding:12px;">Job complete</div>';
  h+='<button class="wfBtn dark" onclick="wfAction(\'assign\')">Reassign</button>';
  h+='<button class="wfBtn purple" onclick="wfAction(\'timeline\')">View Timeline</button>';
  document.getElementById('wfJobActions').innerHTML=h;
}

async function wfAction(act){
  var jid=_wfJob; if(!jid)return;
  if(act==='assign'){ var t=prompt('Technician name:'); if(!t)return; var d=await wfPost('/assign/'+jid,{tech:t}); wfRes(d.success?'OK — assigned to '+t:'Error: '+(d.detail||'')); }
  else if(act==='start'||act==='complete'||act==='qc'){ var p=prompt('4-digit PIN:'); if(!p)return; var d=await wfPost('/'+act+'/'+jid,{pin:p}); wfRes(d.success?'OK — '+(d.tech||d.manager||''):'Error: '+(d.detail||JSON.stringify(d))); }
  else if(act==='invoice'){ var by=prompt('Invoiced by:')||''; var d=await wfPost('/invoice/'+jid,{by:by}); wfRes(d.success?'Invoice #'+d.invoice_id+' created':'Error: '+(d.detail||'')); }
  else if(act==='timeline'){ var d=await wfGet('/job/'+jid); var tl=(d.job&&d.job.timeline)||[]; wfRes(tl.join('\n')||'No timeline yet'); return; }
  if(typeof wfRefresh==='function') setTimeout(wfRefresh,500);
  setTimeout(function(){ wfOpenJob(jid); },900);
}

async function wfSetProgress(){
  var jid=_wfJob; if(!jid)return;
  var p=document.getElementById('wfProgIn').value;
  if(!p){ alert('Enter a %'); return; }
  var d=await wfPost('/progress/'+jid,{progress:p});
  wfRes(d.success?'Progress '+d.progress+'%':'Error');
  if(typeof wfRefresh==='function') setTimeout(wfRefresh,500);
}

// ═══ INJECT INTO JOBS TAB ═══
function wfInject(){
  var jobs=document.getElementById('jobs');
  if(!jobs) return;
  var title=jobs.querySelector('.panel-title');
  if(!title) return;

  // Add "New Quote" + refresh button
  if(!document.getElementById('wfNewQuoteBtn')){
    var b=document.createElement('button');
    b.id='wfNewQuoteBtn';
    b.className='btn';
    b.style.cssText='background:linear-gradient(135deg,#10b981,#047857);';
    b.textContent='+ New Quote (with Signatures)';
    b.onclick=wfOpenNewQuote;
    title.parentNode.insertBefore(b,title.nextSibling);
  }

  // Pending quotes section
  if(!document.getElementById('wfPendingWrap')){
    var wrap=document.createElement('div');
    wrap.id='wfPendingWrap';
    wrap.style.cssText='margin:16px 0;';
    title.parentNode.insertBefore(wrap,title.nextSibling.nextSibling);
    wfRefresh();
  }

  // Hook job cards to add "⚙ Workflow" button
  document.querySelectorAll('.card[id^="job-"]').forEach(function(card){
    if(card.dataset.wfHooked) return;
    card.dataset.wfHooked='1';
    var jid=card.id.replace('job-','');
    var actions=card.querySelector('.no-print');
    if(!actions) return;
    var b=document.createElement('button');
    b.className='btn-sm purple';
    b.textContent='⚙ Workflow';
    b.onclick=function(){ wfOpenJob(jid); };
    actions.appendChild(b);
  });
}

async function wfRefresh(){
  var wrap=document.getElementById('wfPendingWrap');
  if(!wrap) return;
  var d=await wfGet('/quotes-pending');
  var qs=d.quotes||[];
  if(qs.length===0){ wrap.innerHTML=''; return; }
  var h='<div style="font-size:12px;color:#7b8da3;font-weight:700;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px;">Pending Quotes ('+qs.length+')</div>';
  qs.forEach(function(q){
    var st=q.status||'draft';
    var label={draft:'Awaiting Customer Signature',customer_signed:'Awaiting Owner Approval'}[st]||st;
    var color={draft:'#6b7280',customer_signed:'#f59e0b'}[st]||'#6b7280';
    h+='<div class="wfQuoteCard" onclick="wfOpenQuote(\''+q.id+'\')">'+
       '<div style="font-weight:700;color:#00a8e8;">Quote #'+q.id+'</div>'+
       '<div style="color:#a5b4c7;font-size:12px;">'+q.customer+' — '+q.vehicle+' '+q.registration+'</div>'+
       '<div style="color:#e6edf5;font-size:13px;margin-top:4px;">'+q.description+'</div>'+
       '<div style="font-size:13px;margin-top:6px;">Total: <b>R'+(q.total||0).toFixed(2)+'</b> <span style="color:'+color+';font-weight:700;font-size:11px;"> ● '+label+'</span></div>'+
       '</div>';
  });
  wrap.innerHTML=h;
}

setInterval(wfInject, 900);
setTimeout(wfInject, 500);
document.getElementById('wfModal').addEventListener('click', function(e){ if(e.target===this) wfClose(); });
</script>
"""
