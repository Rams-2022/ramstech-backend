"""
Consolidated Function Dock — visibility handled by floating_manager.py.
"""
from fastapi import APIRouter

router = APIRouter()

DOCK_HTML = r"""
<style>
  #rt-debtors-btn, #rt-profit-btn, #rt-dmg-btn { display: none !important; }

  #rt-role-badge {
    top: auto !important;
    right: auto !important;
    bottom: 100px !important;
    left: 16px !important;
    transform: scale(0.85) !important;
    transform-origin: bottom left !important;
    opacity: 0.92;
  }

  #rt-dock {
    position: fixed;
    bottom: 96px;
    right: 16px;
    z-index: 9998;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
    transition: opacity .2s ease;
  }

  #rt-dock-fab {
    width: 56px; height: 56px; border-radius: 50%;
    background: #111; color: #fff; border: none; cursor: pointer;
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 300; line-height: 1;
    padding: 0 0 3px 0;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), background 0.2s ease;
  }
  #rt-dock-fab:hover { transform: scale(1.06); }
  #rt-dock.open #rt-dock-fab { transform: rotate(45deg); background: #dc2626; }

  #rt-dock-menu {
    display: flex; flex-direction: column; gap: 8px;
    align-items: flex-end; pointer-events: none;
  }
  #rt-dock.open #rt-dock-menu { pointer-events: auto; }

  .rt-dock-item {
    display: flex; align-items: center; gap: 10px;
    background: #fff; color: #111; border: 1px solid #e5e5e5;
    border-radius: 30px; padding: 10px 16px 10px 14px;
    cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    font-weight: 700; font-size: 13px; white-space: nowrap;
    opacity: 0; transform: translateY(10px) scale(0.9);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: inherit;
  }
  #rt-dock.open .rt-dock-item { opacity: 1; transform: translateY(0) scale(1); }
  #rt-dock.open .rt-dock-item:nth-child(1) { transition-delay: 0.04s; }
  #rt-dock.open .rt-dock-item:nth-child(2) { transition-delay: 0.08s; }
  #rt-dock.open .rt-dock-item:nth-child(3) { transition-delay: 0.12s; }
  #rt-dock.open .rt-dock-item:nth-child(4) { transition-delay: 0.16s; }
  #rt-dock.open .rt-dock-item:nth-child(5) { transition-delay: 0.20s; }

  .rt-dock-item:hover { background: #f5f5f5; transform: translateX(-4px); }
  .rt-dock-item .icon { font-size: 18px; width: 24px; text-align: center; }

  #rt-dock-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.15);
    z-index: 9997; opacity: 0; pointer-events: none;
    transition: opacity 0.2s ease;
  }
  #rt-dock.open ~ #rt-dock-backdrop { opacity: 1; pointer-events: auto; }

  @media (max-width: 640px) {
    #rt-dock { bottom: 90px; right: 14px; }
    #rt-dock-fab { width: 52px; height: 52px; font-size: 24px; }
    .rt-dock-item { padding: 9px 14px 9px 12px; font-size: 12px; }
    #rt-role-badge { bottom: 96px !important; left: 14px !important; }
  }

  @media print {
    #rt-dock, #rt-dock-backdrop, #rt-role-badge { display: none !important; }
  }
</style>

<div id="rt-dock">
  <div id="rt-dock-menu">
    <button class="rt-dock-item" data-owner-only="0" onclick="rtDockRun('rtDebtorsOpen')">
      <span class="icon">💰</span>Debtors
    </button>
    <button class="rt-dock-item" data-owner-only="1" onclick="rtDockRun('rtProfitOpen')">
      <span class="icon">📊</span>Profit
    </button>
    <button class="rt-dock-item" data-owner-only="0" onclick="rtDockRun('rtDmgOpen')">
      <span class="icon">📸</span>Vehicle Check-In
    </button>
    <button class="rt-dock-item" data-owner-only="1" onclick="rtDockRun('rtStaffOpen')">
      <span class="icon">👥</span>Staff
    </button>
    <button class="rt-dock-item" data-owner-only="1" onclick="rtDockRun('rtBkOpen')">
      <span class="icon">💾</span>Backup
    </button>
  </div>
  <button id="rt-dock-fab" onclick="rtDockToggle(event)" aria-label="Open tools menu">+</button>
</div>
<div id="rt-dock-backdrop" onclick="rtDockClose()"></div>

<script>
(function(){
  window.rtDockToggle = function(e){
    if (e) e.stopPropagation();
    var dock = document.getElementById("rt-dock");
    if (!dock) return;
    dock.classList.toggle("open");
  };

  window.rtDockClose = function(){
    var dock = document.getElementById("rt-dock");
    if (dock) dock.classList.remove("open");
    var bd = document.getElementById("rt-dock-backdrop");
    if (bd) bd.style.pointerEvents = "none";
  };

  window.rtDockRun = function(fnName){
    try { rtDockClose(); } catch(e) {}
    try {
      var bd = document.getElementById("rt-dock-backdrop");
      if (bd) { bd.style.pointerEvents = "none"; bd.style.opacity = "0"; }
    } catch(e) {}

    setTimeout(function(){
      try {
        if (typeof window[fnName] === "function") {
          window[fnName]();
        } else {
          console.warn("[dock] handler not found:", fnName);
        }
      } catch(e) { console.error("[dock] error running", fnName, e); }
    }, 150);
  };

  document.addEventListener("keydown", function(e){
    if (e.key === "Escape") rtDockClose();
  });

  fetch("/api/whoami")
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (!d || !d.authenticated) return;
      var role = d.role || "guest";
      var isPrivileged = (role === "owner" || role === "manager" || role === "super");
      if (!isPrivileged) {
        document.querySelectorAll('.rt-dock-item[data-owner-only="1"]')
          .forEach(function(el){ el.style.display = "none"; });
      }
    })
    .catch(function(){ /* silent */ });

  // NOTE: visibility (show/hide based on active tab) is handled by
  // floating_manager.py. This file only owns click behaviour.
})();
</script>
"""


def dock_status():
    return {"dock_enabled": True, "items": 5, "managed_by": "floating_manager"}
