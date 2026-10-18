from fastapi import APIRouter

router = APIRouter()

DOCK_HTML = r"""
<style>
  #rt-debtors-btn, #rt-profit-btn, #rt-dmg-btn { display: none !important; }

  #rt-role-badge {
    top: auto !important;
    right: 16px !important;
    bottom: 100px !important;
    left: auto !important;
    transform: scale(0.85) !important;
    transform-origin: bottom right !important;
    opacity: 0.92;
  }

  /* MOVED TO BOTTOM LEFT */
  #rt-dock {
    position: fixed;
    bottom: 96px;
    left: 16px; 
    z-index: 9998;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  #rt-dock-fab {
    width: 56px; height: 56px; border-radius: 50%;
    background: #111; color: #fff; border: none; cursor: pointer;
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 300; line-height: 1;
    padding: 0 0 3px 0;
    transition: transform 0.25s, background 0.2s;
  }
  #rt-dock.open #rt-dock-fab { transform: rotate(45deg); background: #dc2626; }

  #rt-dock-menu {
    display: flex; flex-direction: column; gap: 8px;
    align-items: flex-start; pointer-events: none;
  }
  #rt-dock.open #rt-dock-menu { pointer-events: auto; }

  .rt-dock-item {
    display: flex; align-items: center; gap: 10px;
    background: #fff; color: #111; border: 1px solid #e5e5e5;
    border-radius: 30px; padding: 10px 16px;
    cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    font-weight: 700; font-size: 13px; white-space: nowrap;
    opacity: 0; transform: translateY(10px) scale(0.9);
    transition: all 0.2s;
  }
  #rt-dock.open .rt-dock-item { opacity: 1; transform: translateY(0) scale(1); }

  /* BACKDROP IS COMPLETELY REMOVED */
</style>

<div id="rt-dock">
  <div id="rt-dock-menu">
    <button class="rt-dock-item" onclick="rtDockRun('rtDebtorsOpen')">💰 Debtors</button>
    <button class="rt-dock-item" onclick="rtDockRun('rtProfitOpen')">📊 Profit</button>
    <button class="rt-dock-item" onclick="rtDockRun('rtDmgOpen')">📸 Vehicle Check-In</button>
    <button class="rt-dock-item" onclick="rtDockRun('rtStaffOpen')">👥 Staff</button>
    <button class="rt-dock-item" onclick="rtDockRun('rtBkOpen')">💾 Backup</button>
  </div>
  <button id="rt-dock-fab" onclick="rtDockToggle(event)">+</button>
</div>

<script>
(function(){
  window.rtDockToggle = function(e){
    if (e) e.stopPropagation();
    var dock = document.getElementById("rt-dock");
    if (dock) dock.classList.toggle("open");
  };
  
  window.rtDockClose = function(){
    var dock = document.getElementById("rt-dock");
    if (dock) dock.classList.remove("open");
  };
  
  window.rtDockRun = function(fnName){
    rtDockClose();
    setTimeout(function(){
      if (typeof window[fnName] === "function") window[fnName]();
    }, 150);
  };
})();
</script>
"""
