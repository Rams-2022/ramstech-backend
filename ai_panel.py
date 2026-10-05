AI_PANEL_HTML = r"""
<style>
#aiFab{position:fixed;bottom:24px;right:18px;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#00a8e8,#0066a8);color:#fff;border:none;font-size:26px;cursor:pointer;z-index:9997;box-shadow:0 6px 18px rgba(0,168,232,.45);}
#aiPanel{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;padding:12px;overflow:auto;}
#aiInner{max-width:640px;margin:20px auto;background:#0f1520;color:#e6edf5;border-radius:14px;padding:18px;border:1px solid #1e2938;}
.aiTabs{display:flex;gap:4px;background:#0a1018;padding:4px;border-radius:10px;margin-bottom:12px;}
.aiTab{flex:1;padding:9px 4px;background:transparent;color:#7b8da3;border:none;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;}
.aiTab.active{background:#00a8e8;color:#03121c;}
.aiIn{width:100%;padding:11px 12px;background:#0a1018;border:1px solid #1e2938;border-radius:9px;color:#e6edf5;font-size:15px;box-sizing:border-box;margin-bottom:8px;font-family:inherit;}
#aiBtn{width:100%;padding:13px;background:#00a8e8;color:#03121c;border:none;border-radius:9px;font-weight:700;font-size:15px;cursor:pointer;}
#aiReply{display:none;white-space:pre-wrap;background:#0a1018;border:1px solid #1e2938;border-radius:10px;padding:12px;margin-top:12px;font-size:14px;line-height:1.6;}
#aiChips{display:none;flex-wrap:wrap;gap:6px;margin-top:10px;}
.chip{background:#0a1018;color:#00a8e8;border:1px solid #00a8e8;border-radius:14px;padding:5px 10px;font-size:12px;cursor:pointer;font-weight:600;}
</style>
<button id="aiFab" onclick="aiToggle()">🤖</button>
<div id="aiPanel">
<div id="aiInner">
<div style="display:flex;justify-content:space-between;margin-bottom:12px;">
<div style="font-size:16px;font-weight:700;color:#00a8e8;">🤖 RamsTech AI</div>
<button onclick="aiToggle()" style="background:#1e2938;color:#fff;border:none;border-radius:7px;padding:6px 12px;cursor:pointer;">✕</button>
</div>
<div class="aiTabs">
<button class="aiTab active" data-m="code" onclick="aiMode('code')">🔤 Code</button>
<button class="aiTab" data-m="symptom" onclick="aiMode('symptom')">🩺 Symptom</button>
<button class="aiTab" data-m="ask" onclick="aiMode('ask')">💬 Ask</button>
</div>
<div style="display:flex;gap:8px;margin-bottom:8px;">
<input type="file" id="aiPic" accept="image/*" capture="environment" style="display:none;" onchange="aiPicLoad(event)">
<button type="button" onclick="document.getElementById('aiPic').click()" style="flex:1;background:#0a1018;color:#00a8e8;border:1px dashed #00a8e8;border-radius:9px;padding:9px;font-size:12px;font-weight:600;cursor:pointer;">📷 Photo</button>
<button type="button" onclick="aiVoice()" style="flex:1;background:#0a1018;color:#00a8e8;border:1px dashed #00a8e8;border-radius:9px;padding:9px;font-size:12px;font-weight:600;cursor:pointer;">🎤 Speak</button>
</div>
<div id="aiPicPrev" style="display:none;position:relative;margin-bottom:8px;">
<img id="aiPicImg" style="max-width:100%;border-radius:9px;">
<button onclick="aiPicClear()" style="position:absolute;top:5px;right:5px;background:#0a1018cc;color:#fff;border:none;border-radius:50%;width:26px;height:26px;font-size:14px;cursor:pointer;">✕</button>
</div>
<input id="aiVeh" class="aiIn" placeholder="Vehicle (optional)">
<input id="aiCode" class="aiIn" placeholder="e.g. P0301" style="font-family:monospace;">
<textarea id="aiSym" class="aiIn" rows="3" placeholder="Describe the symptom" style="display:none;"></textarea>
<textarea id="aiAsk" class="aiIn" rows="3" placeholder="Ask anything" style="display:none;"></textarea>
<button id="aiBtn" onclick="aiSubmit()">🤖 Get Answer</button>
<div id="aiChips"></div>
<div id="aiReply"></div>
</div>
</div>
<script>
var _m='code';
var _pic=null;
var _rec=null;
function aiPicLoad(e){var f=e.target.files[0];if(!f)return;if(f.size>5*1024*1024){alert('Max 5MB');return;}
var r=new FileReader();r.onload=function(ev){_pic=ev.target.result.split(',')[1];document.getElementById('aiPicImg').src=ev.target.result;document.getElementById('aiPicPrev').style.display='block';};r.readAsDataURL(f);}
function aiPicClear(){_pic=null;document.getElementById('aiPic').value='';document.getElementById('aiPicPrev').style.display='none';}
function aiVoice(){var SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert('Voice needs Chrome on Android');return;}
if(_rec){try{_rec.stop();}catch(_){}}
_rec=new SR();_rec.lang='en-ZA';_rec.interimResults=false;_rec.maxAlternatives=1;
_rec.onresult=function(e){var t=e.results[0][0].transcript;
t=t.replace(/\bp\s*zero\s*/gi,'P0').replace(/\bb\s*one\s*/gi,'B1').replace(/\bc\s*zero\s*/gi,'C0').replace(/\bu\s*zero\s*/gi,'U0');
var f={code:'aiCode',symptom:'aiSym',ask:'aiAsk'}[_m];var el=document.getElementById(f);el.value=(el.value?el.value+' ':'')+t;};
_rec.onerror=function(e){alert('Voice: '+e.error);};_rec.start();}
function aiToggle(){var p=document.getElementById('aiPanel');p.style.display=p.style.display==='block'?'none':'block';}
function aiMode(m){_m=m;document.querySelectorAll('.aiTab').forEach(function(t){t.classList.toggle('active',t.dataset.m===m);});
document.getElementById('aiCode').style.display=m==='code'?'block':'none';
document.getElementById('aiSym').style.display=m==='symptom'?'block':'none';
document.getElementById('aiAsk').style.display=m==='ask'?'block':'none';
document.getElementById('aiBtn').textContent={code:'🤖 Explain Code',symptom:'🩺 Find Codes',ask:'💬 Ask AI'}[m];}
function aiSubmit(){
var v=document.getElementById('aiVeh').value.trim();
var b=document.getElementById('aiBtn'),r=document.getElementById('aiReply'),c=document.getElementById('aiChips');
var ep,body;
if(_m==='code'){var cd=document.getElementById('aiCode').value.trim().toUpperCase().replace(/[^A-Z0-9]/g,'');if(!cd){alert('Type a code');return;}ep='/api/fault-codes/ai';body={code:cd,vehicle:v};}
else if(_m==='symptom'){var q=document.getElementById('aiSym').value.trim();if(!q){alert('Describe symptom');return;}ep='/api/fault-codes/ai-search';body={query:q,vehicle:v};}
else{var q=document.getElementById('aiAsk').value.trim();if(!q){alert('Type a question');return;}ep='/api/ai-context';body={message:q,vehicle:v,active_tab:''};}
b.disabled=true;b.textContent='⏳ Thinking…';r.style.display='none';c.style.display='none';
fetch(ep,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
.then(function(res){return res.json();})
.then(function(d){
if(_m==='symptom'&&d.local_matches&&d.local_matches.length){c.innerHTML='';d.local_matches.forEach(function(m){var ch=document.createElement('button');ch.className='chip';ch.textContent=m.code;ch.onclick=function(){aiMode('code');document.getElementById('aiCode').value=m.code;aiSubmit();};c.appendChild(ch);});c.style.display='flex';}
r.textContent=(d.reply||d.answer||'No reply')+(d.provider?'\n\n— via '+d.provider:'');
r.style.display='block';b.disabled=false;b.textContent='🤖 Get Answer';})
.catch(function(e){r.textContent='Error: '+e.message;r.style.display='block';b.disabled=false;b.textContent='🤖 Get Answer';});}
document.getElementById('aiPanel').addEventListener('click',function(e){if(e.target===this)aiToggle();});
</script>
"""
