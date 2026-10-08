"""Design polish — modern typography, animations, loading states, onboarding."""
from fastapi import APIRouter

router = APIRouter()

DESIGN_HTML = r"""
<!-- ═══════════════════════════════════════════ -->
<!-- DESIGN POLISH — typography, motion, states  -->
<!-- ═══════════════════════════════════════════ -->

<!-- Load Inter font + Lucide icons -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>

<style>
/* ═══════════════════════════════════════════ */
/* TYPOGRAPHY — Inter, tighter hierarchy       */
/* ═══════════════════════════════════════════ */
:root{
  --brand-900:#0a1018;
  --brand-800:#0f1520;
  --brand-700:#1e2938;
  --brand-600:#2a3a4f;
  --brand-primary:#E65100;
  --brand-primary-light:#FF8A3D;
  --brand-blue:#0ea5e9;
  --brand-green:#10b981;
  --brand-amber:#f59e0b;
  --brand-purple:#8b5cf6;
  --brand-pink:#ec4899;
  --brand-text:#e6edf5;
  --brand-muted:#7b8da3;
  --brand-subtle:#94a3b8;
  --radius-sm:8px;
  --radius-md:12px;
  --radius-lg:16px;
  --radius-xl:20px;
  --shadow-sm:0 1px 3px rgba(0,0,0,.15);
  --shadow-md:0 4px 14px rgba(0,0,0,.25);
  --shadow-lg:0 12px 40px rgba(0,0,0,.35);
  --shadow-glow:0 8px 32px rgba(230,81,0,.35);
}

body, button, input, textarea, select, .btn, .btn-sm, .panel-title, .card, h1, h2, h3{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  font-feature-settings: 'cv02','cv03','cv04','cv11';
}

h1, .panel-title{
  letter-spacing: -0.02em !important;
  font-weight: 800 !important;
}
h2, h3, .card h3{
  letter-spacing: -0.01em !important;
  font-weight: 700 !important;
}
button, .btn, .btn-sm{
  letter-spacing: -0.005em !important;
  font-weight: 700 !important;
}

/* ═══════════════════════════════════════════ */
/* MOTION — smooth, subtle, purposeful         */
/* ═══════════════════════════════════════════ */
*{
  transition: background-color .18s ease,
              color .18s ease,
              border-color .18s ease,
              transform .12s ease,
              box-shadow .18s ease,
              opacity .18s ease;
}

.panel.active{
  animation: panelIn .32s cubic-bezier(.16,1,.3,1) !important;
}
@keyframes panelIn{
  from{opacity:0;transform:translateY(10px);}
  to{opacity:1;transform:translateY(0);}
}

.tile:active, .cat-card:active, .bnav-item:active, .btn:active, .btn-sm:active{
  transform:scale(.96);
}

.tile, .cat-card, .btn, .btn-sm, .card{
  will-change:transform;
}

/* Ripple effect on buttons */
.btn, .btn-sm, button:not(.bnav-item){
  position:relative;
  overflow:hidden;
}
.btn::after, .btn-sm::after{
  content:'';
  position:absolute;
  inset:0;
  background:radial-gradient(circle, rgba(255,255,255,.3) 0%, transparent 70%);
  opacity:0;
  pointer-events:none;
  transition:opacity .35s ease;
}
.btn:active::after, .btn-sm:active::after{
  opacity:1;
  transition:opacity 0s;
}

/* ═══════════════════════════════════════════ */
/* SKELETON LOADERS                             */
/* ═══════════════════════════════════════════ */
.skeleton{
  background:linear-gradient(90deg, var(--brand-800) 0%, var(--brand-700) 50%, var(--brand-800) 100%);
  background-size:200% 100%;
  border-radius:var(--radius-sm);
  animation:skeleton 1.4s ease-in-out infinite;
}
@keyframes skeleton{
  0%{background-position:200% 0;}
  100%{background-position:-200% 0;}
}
.skel-line{height:14px;margin:8px 0;}
.skel-line.w60{width:60%;}
.skel-line.w80{width:80%;}
.skel-line.w40{width:40%;}
.skel-card{
  background:var(--brand-800);
  border:1px solid var(--brand-700);
  border-radius:var(--radius-md);
  padding:16px;
  margin-bottom:10px;
}

/* ═══════════════════════════════════════════ */
/* EMPTY STATES                                 */
/* ═══════════════════════════════════════════ */
.empty-state{
  text-align:center;
  padding:48px 24px;
  color:var(--brand-muted);
}
.empty-state svg{
  width:64px;
  height:64px;
  stroke:var(--brand-700);
  stroke-width:1.5;
  margin-bottom:16px;
  opacity:.8;
}
.empty-state h3{
  font-size:16px;
  font-weight:700;
  color:var(--brand-text);
  margin-bottom:6px;
}
.empty-state p{
  font-size:13px;
  color:var(--brand-muted);
  max-width:280px;
  margin:0 auto 16px;
  line-height:1.5;
}
.empty-state .btn{
  max-width:240px;
  margin:0 auto;
}

/* ═══════════════════════════════════════════ */
/* CARD POLISH                                  */
/* ═══════════════════════════════════════════ */
.card{
  border-radius:var(--radius-lg) !important;
  transition:transform .15s ease, box-shadow .2s ease !important;
}
.card:hover{
  box-shadow:0 8px 24px rgba(0,0,0,.25) !important;
}
.card:active{
  transform:scale(.995);
}

/* ═══════════════════════════════════════════ */
/* BUTTON POLISH                                */
/* ═══════════════════════════════════════════ */
.btn{
  border-radius:var(--radius-md) !important;
  transition:all .15s cubic-bezier(.16,1,.3,1) !important;
}
.btn:not(:disabled):hover{
  filter:brightness(1.08);
  box-shadow:0 8px 24px rgba(0,0,0,.3) !important;
}
.btn:disabled{
  opacity:.55;
  cursor:not-allowed;
  filter:grayscale(.3);
}

.btn.loading{
  color:transparent !important;
  position:relative;
  pointer-events:none;
}
.btn.loading::before{
  content:'';
  position:absolute;
  top:50%;left:50%;
  width:20px;height:20px;
  margin:-10px 0 0 -10px;
  border:2px solid rgba(255,255,255,.3);
  border-top-color:#fff;
  border-radius:50%;
  animation:spin .7s linear infinite;
}
@keyframes spin{to{transform:rotate(360deg);}}

/* ═══════════════════════════════════════════ */
/* ICON REFINEMENT                              */
/* ═══════════════════════════════════════════ */
.icon-inline{
  display:inline-block;
  width:18px;height:18px;
  vertical-align:middle;
  margin-right:6px;
  stroke:currentColor;
  fill:none;
  stroke-width:2;
  stroke-linecap:round;
  stroke-linejoin:round;
}
.bnav-icon svg, .cat-icon svg, .tile-icon svg{
  width:1em;height:1em;
  stroke:currentColor;
  fill:none;
  stroke-width:1.8;
  stroke-linecap:round;
  stroke-linejoin:round;
  display:block;
  margin:0 auto;
}

/* ═══════════════════════════════════════════ */
/* ONBOARDING TOUR                              */
/* ═══════════════════════════════════════════ */
#onboardOverlay{
  position:fixed;inset:0;
  background:rgba(0,0,0,.85);
  backdrop-filter:blur(8px);
  z-index:99998;
  display:none;
  align-items:center;
  justify-content:center;
  padding:20px;
}
#onboardOverlay.show{
  display:flex;
  animation:fadeIn .35s ease;
}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
#onboardCard{
  max-width:400px;
  background:linear-gradient(160deg, #0f1520 0%, #0a1018 100%);
  border:1px solid var(--brand-700);
  border-radius:24px;
  padding:32px 24px 24px;
  text-align:center;
  color:var(--brand-text);
  box-shadow:0 24px 80px rgba(0,0,0,.6);
  animation:onboardIn .5s cubic-bezier(.16,1,.3,1);
}
@keyframes onboardIn{
  from{opacity:0;transform:translateY(20px) scale(.95);}
  to{opacity:1;transform:translateY(0) scale(1);}
}
#onboardCard .ob-icon{
  width:80px;height:80px;
  margin:0 auto 20px;
  background:linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
  border-radius:24px;
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow:0 12px 40px rgba(230,81,0,.4);
}
#onboardCard .ob-icon svg{
  width:44px;height:44px;
  stroke:#fff;
  fill:none;
  stroke-width:1.8;
  stroke-linecap:round;
  stroke-linejoin:round;
}
#onboardCard h2{
  font-size:22px;
  font-weight:800;
  letter-spacing:-.02em;
  margin-bottom:8px;
}
#onboardCard p{
  font-size:14px;
  color:var(--brand-muted);
  line-height:1.6;
  margin-bottom:24px;
}
#onboardDots{
  display:flex;
  justify-content:center;
  gap:6px;
  margin-bottom:20px;
}
#onboardDots .dot{
  width:6px;height:6px;
  border-radius:50%;
  background:var(--brand-700);
  transition:all .3s ease;
}
#onboardDots .dot.active{
  background:var(--brand-primary);
  width:24px;
  border-radius:3px;
}
#onboardCard .ob-actions{
  display:flex;
  gap:8px;
}
#onboardCard .ob-actions button{
  flex:1;
  padding:14px;
  border:none;
  border-radius:12px;
  font-weight:700;
  font-size:14px;
  cursor:pointer;
  font-family:inherit;
}
#onboardCard .ob-skip{
  background:transparent;
  color:var(--brand-muted);
}
#onboardCard .ob-next{
  background:linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
  color:#fff;
  box-shadow:0 8px 24px rgba(230,81,0,.35);
}

/* ═══════════════════════════════════════════ */
/* TOAST NOTIFICATIONS                          */
/* ═══════════════════════════════════════════ */
#toastWrap{
  position:fixed;
  top:80px;
  left:50%;
  transform:translateX(-50%);
  z-index:99999;
  display:flex;
  flex-direction:column;
  gap:8px;
  pointer-events:none;
}
.toast{
  background:var(--brand-800);
  color:var(--brand-text);
  padding:12px 20px;
  border-radius:12px;
  border:1px solid var(--brand-700);
  font-size:14px;
  font-weight:600;
  box-shadow:0 12px 32px rgba(0,0,0,.4);
  animation:toastIn .35s cubic-bezier(.16,1,.3,1);
  max-width:340px;
  text-align:center;
}
.toast.success{border-color:var(--brand-green);}
.toast.error{border-color:#ef4444;}
.toast.info{border-color:var(--brand-blue);}
@keyframes toastIn{
  from{opacity:0;transform:translateY(-12px) scale(.95);}
  to{opacity:1;transform:translateY(0) scale(1);}
}
.toast.out{
  animation:toastOut .3s ease forwards;
}
@keyframes toastOut{
  to{opacity:0;transform:translateY(-12px) scale(.95);}
}

/* ═══════════════════════════════════════════ */
/* INPUT REFINEMENT                             */
/* ═══════════════════════════════════════════ */
input:focus, textarea:focus, select:focus{
  outline:none;
  border-color:var(--brand-primary) !important;
  box-shadow:0 0 0 3px rgba(230,81,0,.15) !important;
}

/* Reduce visual clutter in nav */
.bottom-nav{
  backdrop-filter:blur(12px);
  background:rgba(15,21,32,.92) !important;
}

/* ═══════════════════════════════════════════ */
/* HIDE EMOJI IN FAVOUR OF SVG ICONS            */
/* ═══════════════════════════════════════════ */
.bnav-icon:not(:has(svg)),
.cat-icon:not(:has(svg)),
.tile-icon:not(:has(svg)){
  font-size:0;
}
</style>

<!-- Onboarding overlay -->
<div id="onboardOverlay">
  <div id="onboardCard">
    <div class="ob-icon" id="obIcon"></div>
    <h2 id="obTitle"></h2>
    <p id="obText"></p>
    <div id="onboardDots"></div>
    <div class="ob-actions">
      <button class="ob-skip" onclick="obSkip()">Skip</button>
      <button class="ob-next" id="obNextBtn" onclick="obNext()">Next</button>
    </div>
  </div>
</div>

<!-- Toast container -->
<div id="toastWrap"></div>

<script>
// ═══════════════════════════════════════════
// LUCIDE ICON HELPER
// ═══════════════════════════════════════════
function dpIcon(name){
  return '<i data-lucide="' + name + '"></i>';
}
function dpRefreshIcons(){
  try{
    if(window.lucide && window.lucide.createIcons){
      window.lucide.createIcons();
    }
  }catch(e){}
}

// ═══════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════
window.dpToast = function(msg, type){
  type = type || 'info';
  var wrap = document.getElementById('toastWrap');
  if(!wrap) return;
  var t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  wrap.appendChild(t);
  setTimeout(function(){
    t.classList.add('out');
    setTimeout(function(){ t.remove(); }, 300);
  }, 2400);
};

// ═══════════════════════════════════════════
// BUTTON LOADING STATE
// ═══════════════════════════════════════════
window.dpLoad = function(btn, on){
  if(!btn) return;
  if(on){
    btn.classList.add('loading');
    btn.disabled = true;
  } else {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
};

// ═══════════════════════════════════════════
// SKELETON HELPER
// ═══════════════════════════════════════════
window.dpSkeleton = function(lines){
  lines = lines || 3;
  var h = '<div class="skel-card">';
  for(var i=0;i<lines;i++){
    h += '<div class="skeleton skel-line ' + (i === 0 ? 'w60' : i === 1 ? 'w80' : 'w40') + '"></div>';
  }
  h += '</div>';
  return h;
};

// ═══════════════════════════════════════════
// EMPTY STATE HELPER
// ═══════════════════════════════════════════
window.dpEmpty = function(icon, title, text, btnText, btnFn){
  var h = '<div class="empty-state">';
  h += '<i data-lucide="' + icon + '" style="width:64px;height:64px;stroke:#1e2938;fill:none;stroke-width:1.5;margin-bottom:16px;display:inline-block;"></i>';
  h += '<h3>' + title + '</h3>';
  h += '<p>' + text + '</p>';
  if(btnText && btnFn){
    h += '<button class="btn" onclick="' + btnFn + '">' + btnText + '</button>';
  }
  h += '</div>';
  return h;
};

// ═══════════════════════════════════════════
// REPLACE EMOJI WITH SVG ICONS AUTOMATICALLY
// ═══════════════════════════════════════════
var _emojiMap = {
  '🏠':'home', '📊':'bar-chart-3', '🤖':'bot', '📋':'clipboard-list', '⚙️':'settings',
  '🔧':'wrench', '📟':'activity', '📖':'book-open', '🔍':'search', '🎨':'palette',
  '📸':'camera', '👥':'users', '📅':'calendar', '💬':'message-circle', '💰':'dollar-sign',
  '📦':'package', '🛒':'shopping-cart', '👷':'hard-hat', '🕐':'clock', '💸':'trending-down',
  '⛽':'fuel', '🎁':'gift', '🗓️':'calendar-check', '🔌':'plug', '⚡':'zap',
  '💡':'lightbulb', '🔋':'battery', '🛞':'circle-dot', '✅':'check-circle', '⏰':'alarm-clock',
  '🔩':'bolt', '📈':'line-chart', '🧾':'receipt', '🚗':'car', '📱':'smartphone',
  '📞':'phone', '📧':'mail', '📍':'map-pin', '⚠️':'alert-triangle', '❌':'x',
  '➕':'plus', '✓':'check', '✕':'x', '←':'arrow-left', '→':'arrow-right', '↻':'refresh-cw',
  '⏹':'square', '🎤':'mic', '📥':'download', '🖨':'printer', '🗑️':'trash-2'
};

function dpReplaceEmoji(){
  try{
    // Nav icons
    document.querySelectorAll('.bnav-icon').forEach(function(el){
      var t = el.textContent.trim();
      var icon = _emojiMap[t];
      if(icon && !el.querySelector('svg') && !el.querySelector('i')){
        el.innerHTML = '<i data-lucide="' + icon + '"></i>';
      }
    });
    // Category icons
    document.querySelectorAll('.cat-icon').forEach(function(el){
      var t = el.textContent.trim();
      var icon = _emojiMap[t];
      if(icon && !el.querySelector('svg')){
        el.innerHTML = '<i data-lucide="' + icon + '" style="width:38px;height:38px;stroke:currentColor;fill:none;stroke-width:1.8;"></i>';
      }
    });
    // Tile icons
    document.querySelectorAll('.tile-icon').forEach(function(el){
      var t = el.textContent.trim();
      var icon = _emojiMap[t];
      if(icon && !el.querySelector('svg') && !el.querySelector('i')){
        el.innerHTML = '<i data-lucide="' + icon + '" style="width:32px;height:32px;stroke:currentColor;fill:none;stroke-width:1.8;display:block;margin:0 auto;"></i>';
      }
    });
    dpRefreshIcons();
  }catch(e){}
}

// Run emoji replacement periodically
setInterval(dpReplaceEmoji, 800);

// ═══════════════════════════════════════════
// ONBOARDING TOUR
// ═══════════════════════════════════════════
var _obSteps = [
  {
    icon: 'sparkles',
    title: 'Welcome to RamsTech',
    text: 'Your complete workshop manager. Quotes, jobs, invoices, and AI diagnostics — all from your phone.'
  },
  {
    icon: 'clipboard-list',
    title: 'Jobs Tab is Home Base',
    text: 'Create quotes, assign technicians, track progress, and generate invoices. Everything flows through here.'
  },
  {
    icon: 'bot',
    title: 'AI Assistant',
    text: 'Tap the blue robot on any diagnostic tab. Look up fault codes, diagnose from photos, or ask anything.'
  },
  {
    icon: 'camera',
    title: 'Scan Anything',
    text: 'Scan part barcodes or type a VIN. Get instant part availability, prices, and vehicle history.'
  },
  {
    icon: 'hard-hat',
    title: 'Technician Mode',
    text: 'Your team logs in with their own PIN. They see only their jobs. You see everything.'
  }
];
var _obIdx = 0;

function obRender(){
  var step = _obSteps[_obIdx];
  document.getElementById('obIcon').innerHTML = '<i data-lucide="' + step.icon + '"></i>';
  document.getElementById('obTitle').textContent = step.title;
  document.getElementById('obText').textContent = step.text;
  var dots = '';
  for(var i=0;i<_obSteps.length;i++){
    dots += '<div class="dot ' + (i === _obIdx ? 'active' : '') + '"></div>';
  }
  document.getElementById('onboardDots').innerHTML = dots;
  document.getElementById('obNextBtn').textContent = _obIdx === _obSteps.length - 1 ? 'Get Started' : 'Next';
  dpRefreshIcons();
}

function obNext(){
  if(_obIdx < _obSteps.length - 1){
    _obIdx++;
    obRender();
  } else {
    obSkip();
  }
}

function obSkip(){
  document.getElementById('onboardOverlay').classList.remove('show');
  try{ localStorage.setItem('dp_onboarded', '1'); }catch(e){}
}

function obShow(){
  _obIdx = 0;
  obRender();
  document.getElementById('onboardOverlay').classList.add('show');
}

// Show on first visit
setTimeout(function(){
  try{
    if(!localStorage.getItem('dp_onboarded')){
      // Wait until lock screen is dismissed (if applicable)
      var waitForApp = setInterval(function(){
        var lock = document.getElementById('lockScreen');
        if(lock && lock.style.display !== 'flex' && lock.style.display !== 'block'){
          clearInterval(waitForApp);
          obShow();
        } else if(!lock){
          clearInterval(waitForApp);
          obShow();
        }
      }, 500);
      // Safety: show after 5 seconds regardless
      setTimeout(function(){ clearInterval(waitForApp); obShow(); }, 5000);
    }
  }catch(e){}
}, 1200);

// ═══════════════════════════════════════════
// BUTTON LOADING AUTO-HOOK
// ═══════════════════════════════════════════
document.addEventListener('click', function(e){
  var btn = e.target.closest('button');
  if(!btn || btn.classList.contains('bnav-item') || btn.classList.contains('ob-skip') || btn.classList.contains('ob-next')) return;
  if(btn.classList.contains('loading')){ e.preventDefault(); return; }
  // Auto-add loading state on async buttons (heuristic: data attribute or form submit)
  if(btn.dataset && btn.dataset.dpLoad === 'true'){
    dpLoad(btn, true);
  }
}, true);

// ═══════════════════════════════════════════
// AUTO-WRAP LOADING STATES
// ═══════════════════════════════════════════
// Watch for "Loading..." text in common containers
setInterval(function(){
  document.querySelectorAll('.loading').forEach(function(el){
    if(el.dataset.dpUpgraded) return;
    el.dataset.dpUpgraded = '1';
    var t = el.textContent.trim().toLowerCase();
    if(t === 'loading...' || t === 'loading…'){
      el.outerHTML = dpSkeleton(3);
    }
  });
}, 400);

console.log('✓ Design polish loaded');
</script>
"""
