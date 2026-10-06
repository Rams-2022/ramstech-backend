AI_PANEL_HTML = r"""
<style>
#aiFab{position:fixed;bottom:170px;right:18px;width:60px;height:60px;border-radius:50%;
background:linear-gradient(135deg,#00a8e8,#0066a8);color:#fff;border:none;font-size:26px;
cursor:pointer;z-index:9997;box-shadow:0 6px 18px rgba(0,168,232,.45);
display:flex;align-items:center;justify-content:center;}
#aiFab:active{transform:scale(.92);}
#aiPanel{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;
padding:12px;overflow:auto;}
#aiInner{max-width:640px;margin:20px auto;background:#0f1520;color:#e6edf5;
border-radius:14px;padding:18px;border:1px solid #1e2938;}
.aiTabs{display:flex;gap:4px;margin-bottom:12px;background:#0a1018;padding:4px;border-radius:10px;}
.aiTab{flex:1;padding:10px 6px;background:transparent;color:#7b8da3;border:none;
border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;}
.aiTab.active{background:#00a8e8;color:#03121c;}
.aiIn{width:100%;padding:12px 14px;background:#0a1018;border:1px solid #1e2938;
border-radius:10px;color:#e6edf5;font-size:15px;box-sizing:border-box;
font-family:inherit;margin-bottom:10px;}
#aiBtn{width:100%;padding:14px;background:#00a8e8;color:#03121c;border:none;
border-radius:10px;font-weight:700;font-size:15px;cursor:pointer;}
#aiBtn:disabled{opacity:.55;}
#aiReply{display:none;white-space:pre-wrap;background:#0a1018;border:1px solid #1e2938;
border-radius:10px;padding:14px;margin-top:12px;font-size:14px;line-height:1.6;}
#aiChips{display:none;flex-wrap:wrap;gap:6px;margin-top:12px;}
.aiChip{background:#0a1018;color:#00a8e8;border:1px solid #00a8e8;border-radius:16px;
padding:6px 12px;font-size:13px;cursor:pointer;font-weight:600;}
#aiMedia{display:flex;gap:8px;margin-bottom:10px;}
#aiMedia button{flex:1;background:#0a1018;color:#00a8e8;border:1px dashed #00a8e8;
border-radius:10px;padding:10px;font-size:13px;cursor:pointer;font-weight:600;}
#aiPhotoPrev{display:none;margin-bottom:8px;position:relative;}
#aiPhotoPrev img{max-width:100%;border-radius:10px;border:1px solid #1e2938;}
#aiPhotoPrev button{position:absolute;top:6px;right:6px;background:#0a1018cc;color:#fff;
border:none;border-radius:50%;width:30px;height:30px;font-size:15px;cursor:pointer;}
</style>

<button id="aiFab" onclick="aiToggle()" style="display:none;">&#129302;</button>

<div id="aiPanel">
  <div id="aiInner">
    <div style="display:flex;justify-content:space-between;margin-bottom:14px;">
      <div>
        <div style="font-size:11px;color:#7b8da3;letter-spacing:.5px;">RAMSTECH AI</div>
        <div style="font-size:17px;font-weight:700;color:#00a8e8;">Diagnostic Assistant</div>
      </div>
      <button onclick="aiToggle()" style="background:#1e2938;color:#e6edf5;border:none;
        border-radius:8px;padding:8px 14px;font-size:16px;cursor:pointer;">&#10005;</button>
    </div>
    <div class="aiTabs">
      <button class="aiTab active" data-m="code" onclick="aiMode('code')">&#128292; Code</button>
      <button class="aiTab" data-m="symptom" onclick="aiMode('symptom')">&#129658; Symptom</button>
      <button class="aiTab" data-m="ask" onclick="aiMode('ask')">&#128172; Ask</button>
    </div>
    <div id="aiMedia">
      <input type="file" id="aiPic" accept="image/*" capture="environment"
        style="display:none;" onchange="aiPicLoad(event)">
      <button type="button" onclick="document.getElementById('aiPic').click()">&#128247; Photo</button>
      <button type="button" onclick="aiVoice()">&#127908; Speak</button>
    </div>
    <div id="aiPhotoPrev">
      <img id="aiPhotoImg">
      <button onclick="aiPicClear()">&#10005;</button>
    </div>
    <input id="aiVeh" class="aiIn" placeholder="Vehicle (optional) — e.g. Toyota Hilux 2015">
    <input id="aiCode" class="aiIn" placeholder="e.g. P0301" style="font-family:monospace;font-size:16px;">
    <textarea id="aiSym" class="aiIn" rows="3" placeholder="Describe the symptom" style="display:none;"></textarea>
    <textarea id="aiAsk" class="aiIn" rows="3" placeholder="Ask anything" style="display:none;"></textarea>
    <button id="aiBtn" onclick="aiSubmit()">&#129302; Get Answer</button>
    <div id="aiChips"></div>
    <div id="aiReply"></div>
  </div>
</div>

<script>
var _m='code', _pic=null, _rec=null;
var _DIAG_TABS=['chat','codes','problems','vin','paint','photo','wiring','obd','bulbs','batteries','tyres','fuses','service','inspect','boltcalc','torque'];
function aiToggle(){var p=document.getElementById('aiPanel');p.style.display=p.style.display==='block'?'none':'block';}
function aiMode(m){_m=m;document.querySelectorAll('.aiTab').forEach(function(t){t.classList.toggle('active',t.dataset.m===m);});
document.getElementById('aiCode').style.display=m==='code'?'block':'none';
document.getElementById('aiSym').style.display=m==='symptom'?'block':'none';
document.getElementById('aiAsk').style.display=m==='ask'?'block':'none';
document.getElementById('aiBtn').textContent={code:'Explain Code',symptom:'Find Codes',ask:'Ask AI'}[m];}
function aiPicLoad(e){var f=e.target.files[0];if(!f)return;if(f.size>5*1024*1024){alert('Max 5MB');return;}
var r=new FileReader();r.onload=function(ev){_pic=ev.target.result.split(',')[1];document.getElementById('aiPhotoImg').src=ev.target.result;document.getElementById('aiPhotoPrev').style.display='block';};r.readAsDataURL(f);}
function aiPicClear(){_pic=null;document.getElementById('aiPic').value='';document.getElementById('aiPhotoPrev').style.display='none';}
function aiVoice(){var SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert('Voice needs Chrome on Android');return;}
if(_rec){try{_rec.stop();}catch(_){}}
_rec=new SR();_rec.lang='en-ZA';_rec.interimResults=false;
_rec.onresult=function(e){var t=e.results[0][0].transcript;t=t.replace(/\bp\s*zero\s*/gi,'P0').replace(/\bb\s*one\s*/gi,'B1');
var f={code:'aiCode',symptom:'aiSym',ask:'aiAsk'}[_m];var el=document.getElementById(f);el.value=(el.value?el.value+' ':'')+t;};
_rec.onerror=function(e){alert('Voice: '+e.error);};_rec.start();}
async function aiSubmit(){
var v=document.getElementById('aiVeh').value.trim();
var b=document.getElementById('aiBtn'),r=document.getElementById('aiReply'),c=document.getElementById('aiChips');
var ep,body;
if(_m==='code'){var cd=document.getElementById('aiCode').value.trim().toUpperCase().replace(/[^A-Z0-9]/g,'');if(!cd){alert('Type a code');return;}ep='/api/fault-codes/ai';body={code:cd,vehicle:v};}
else if(_m==='symptom'){var q=document.getElementById('aiSym').value.trim();if(!q){alert('Describe symptom');return;}ep='/api/fault-codes/ai-search';body={query:q,vehicle:v};}
else{var q=document.getElementById('aiAsk').value.trim();if(!q&&!_pic){alert('Type a question or attach a photo');return;}ep='/api/ai-context';body={message:q||'Diagnose this photo',vehicle:v,active_tab:'',image_base64:_pic||null};}
b.disabled=true;b.textContent='Thinking...';r.style.display='none';c.style.display='none';
try{var res=await fetch(ep,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
var d=await res.json();
if(_m==='symptom'&&d.local_matches&&d.local_matches.length){c.innerHTML='';d.local_matches.forEach(function(m){var ch=document.createElement('button');ch.className='aiChip';ch.textContent=m.code;ch.onclick=function(){aiMode('code');document.getElementById('aiCode').value=m.code;aiSubmit();};c.appendChild(ch);});c.style.display='flex';}
r.textContent=(d.reply||d.answer||'No reply')+(d.provider?'\n\n— via '+d.provider:'');
r.style.display='block';}catch(e){r.textContent='Error: '+e.message;r.style.display='block';}
b.disabled=false;b.textContent='Get Answer';}
function aiUpdateFab(){
var fab=document.getElementById('aiFab');if(!fab)return;
var active=document.querySelector('.panel.active');var id=active?active.id:'';
fab.style.display=_DIAG_TABS.indexOf(id)>=0?'flex':'none';}
setTimeout(aiUpdateFab,200);
document.addEventListener('click',function(e){
if(e.target.closest('.bnav-item')||e.target.closest('.tile')||e.target.closest('.cat-card')||e.target.closest('.back-btn')){setTimeout(aiUpdateFab,60);}});
document.getElementById('aiPanel').addEventListener('click',function(e){if(e.target===this)aiToggle();});
</script>
"""
