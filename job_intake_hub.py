"""Job intake hub — single entry point that hides individual FABs and offers Photo or Voice."""
from fastapi import APIRouter

router = APIRouter()

JOB_INTAKE_HUB_HTML = r"""
<style>
/* Hide the individual floating buttons — they're now inside the hub */
#photoIntakeBtn,
#voiceIntakeBtn,
#piInlineBtn,
#viInlineBtn{
  display:none !important;
}

#jiHubModal{
  display:none;
  position:fixed;
  inset:0;
  background:rgba(5,7,10,.85);
  backdrop-filter:blur(10px);
  z-index:9998;
  padding:20px;
  overflow:auto;
}
#jiHubModal.open{
  display:block;
  animation:jiFade .25s ease;
}
@keyframes jiFade{from{opacity:0;}to{opacity:1;}}

#jiHubCard{
  max-width:420px;
  margin:60px auto;
  background:linear-gradient(180deg, #1a1f27 0%, #0a0c10 100%);
  border:1px solid #2a3141;
  border-radius:20px;
  padding:28px 22px;
  color:#e6edf5;
  box-shadow:0 24px 80px rgba(0,0,0,.8);
  animation:jiSlideUp .35s cubic-bezier(.16,1,.3,1);
}
@keyframes jiSlideUp{
  from{opacity:0;transform:translateY(20px) scale(.96);}
  to{opacity:1;transform:translateY(0) scale(1);}
}
#jiHubCard h2{
  font-size:20px;
  font-weight:800;
  color:#fff;
  margin:0 0 6px;
  text-align:center;
  letter-spacing:-.01em;
}
#jiHubCard .sub{
  font-size:13px;
  color:#7b8da3;
  text-align:center;
  margin-bottom:24px;
  line-height:1.5;
}
.jiOption{
  width:100%;
  display:flex;
  align-items:center;
  gap:16px;
  padding:18px 20px;
  background:linear-gradient(180deg, #2a3141 0%, #141820 100%);
  border:1px solid #3d4654;
  border-radius:14px;
  color:#fff;
  cursor:pointer;
  margin-bottom:12px;
  text-align:left;
  font-family:inherit;
  transition:all .15s ease;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.1),
    0 6px 16px rgba(0,0,0,.4);
}
.jiOption:active{
  transform:translateY(2px) scale(.98);
  box-shadow:
    inset 0 3px 8px rgba(0,0,0,.6),
    0 2px 6px rgba(0,0,0,.3);
}
.jiOption:hover{
  border-color:#4a5568;
}
.jiOptionIcon{
  width:52px;
  height:52px;
  border-radius:14px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:26px;
  flex-shrink:0;
  box-shadow:
    inset 0 2px 0 rgba(255,255,255,.2),
    0 4px 12px rgba(0,0,0,.4);
}
.jiOptionIcon.photo{
  background:linear-gradient(135deg,#8b5cf6,#6d28d9);
}
.jiOptionIcon.voice{
  background:linear-gradient(135deg,#ef4444,#b91c1c);
}
.jiOptionIcon.manual{
  background:linear-gradient(135deg,#f59e0b,#b45309);
}
.jiOptionBody{
  flex:1;
  min-width:0;
}
.jiOptionTitle{
  font-size:16px;
  font-weight:800;
  color:#fff;
  margin-bottom:2px;
}
.jiOptionSub{
  font-size:12px;
  color:#8b95a8;
  line-height:1.4;
}
.jiClose{
  width:100%;
  padding:14px;
  background:transparent;
  border:1px solid #2a3141;
  border-radius:12px;
  color:#7b8da3;
  font-size:14px;
  font-weight:700;
  cursor:pointer;
  font-family:inherit;
  margin-top:6px;
}
.jiClose:active{background:#141820;}
</style>

<div id="jiHubModal">
  <div id="jiHubCard">
    <h2>New Job Card</h2>
    <div class="sub">Choose how you'd like to capture the details</div>

    <button class="jiOption" onclick="jiPickPhoto()">
      <div class="jiOptionIcon photo">📸</div>
      <div class="jiOptionBody">
        <div class="jiOptionTitle">From Photo</div>
        <div class="jiOptionSub">Snap the VIN, plate, or dashboard — AI fills the rest</div>
      </div>
    </button>

    <button class="jiOption" onclick="jiPickVoice()">
      <div class="jiOptionIcon voice">🎤</div>
      <div class="jiOptionBody">
        <div class="jiOptionTitle">By Voice</div>
        <div class="jiOptionSub">Describe the job out loud — AI writes it up</div>
      </div>
    </button>

    <button class="jiOption" onclick="jiPickManual()">
      <div class="jiOptionIcon manual">✍️</div>
      <div class="jiOptionBody">
        <div class="jiOptionTitle">Manually</div>
        <div class="jiOptionSub">Type the details on a blank job card</div>
      </div>
    </button>

    <button class="jiClose" onclick="jiClose()">Cancel</button>
  </div>
</div>

<script>
function jiOpen(){
  document.getElementById('jiHubModal').classList.add('open');
}
function jiClose(){
  document.getElementById('jiHubModal').classList.remove('open');
}

function jiPickPhoto(){
  jiClose();
  if(typeof piOpen === 'function'){
    setTimeout(piOpen, 200);
  } else {
    if(window.dpToast) dpToast('Photo module not available', 'error');
  }
}

function jiPickVoice(){
  jiClose();
  if(typeof viOpen === 'function'){
    setTimeout(viOpen, 200);
  } else {
    if(window.dpToast) dpToast('Voice module not available', 'error');
  }
}

function jiPickManual(){
  jiClose();
  // Open the original manual job form if it exists
  if(typeof showJobForm === 'function'){
    setTimeout(showJobForm, 200);
  } else {
    // Fallback: show a toast
    if(window.dpToast) dpToast('Manual form coming up', 'info');
  }
}

function jiInjectHub(){
  var jobsTab = document.getElementById('jobs');
  if(!jobsTab || document.getElementById('jiHubBtn')) return;
  var title = jobsTab.querySelector('.panel-title');
  if(!title) return;

  // Remove the old inline buttons from photo_intake / voice_intake
  var pi = document.getElementById('piInlineBtn');
  if(pi) pi.remove();
  var vi = document.getElementById('viInlineBtn');
  if(vi) vi.remove();

  // Add the single unified button
  var btn = document.createElement('button');
  btn.id = 'jiHubBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#8b5cf6,#6d28d9);margin-bottom:10px;';
  btn.textContent = '➕ New Job Card (Photo · Voice · Manual)';
  btn.onclick = jiOpen;
  title.parentNode.insertBefore(btn, title.nextSibling);
}

// Run frequently to catch tab changes
setInterval(jiInjectHub, 900);
setTimeout(jiInjectHub, 600);

// Close on backdrop tap
document.getElementById('jiHubModal').addEventListener('click', function(e){
  if(e.target === this) jiClose();
});

console.log('✓ Job intake hub active');
</script>
"""
