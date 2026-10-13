"""
Consolidated Function Dock — with screen-aware visibility.

Behaviour:
  • All floating UI (dock FAB, role badge, search button) only visible
    when on the HOME screen with no modal open
  • Auto-hides when the user navigates into a category
  • Auto-hides when any modal opens (Debtors, Profit, Check-In, Staff, Backup)
  • Auto-hides stray floating avatar buttons everywhere
  • Owner-only dock items hidden for non-owner roles

Home detection: the app's home screen shows the "CHOOSE A CATEGORY"
heading and no "Back to Categories" button. When either signal flips,
we hide/show accordingly.
"""

DOCK_HTML = """
<style>
  /* ── Hide all legacy floating buttons ──────────────────── */
  #rt-debtors-btn,
  #rt-profit-btn,
  #rt-dmg-btn {
    display: none !important;
  }

  /* ── Reposition the role badge above the bottom nav ──── */
  #rt-role-badge {
    top: auto !important;
    right: auto !important;
    bottom: 100px !important;
    left: 16px !important;
    transform: scale(0.85) !important;
    transform-origin: bottom left !important;
    opacity: 0.92;
  }

  /* ═══════════════════════════════════════════════════════════
     HOME-ONLY RULE — hides all floating UI when not on home
     ═══════════════════════════════════════════════════════════ */
  body.rt-not-home #rt-dock,
  body.rt-not-home #rt-role-badge,
  body.rt-not-home .rt-floating-detected {
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
  }

  /* Smooth transitions */
  #rt-dock,
  #rt-role-badge {
    transition: opacity 0.25s ease, transform 0.25s ease,
                visibility 0.25s ease;
  }

  /* ═══════════════════════════════════════════════════════════
     MODAL RULE — hides all floating UI when a modal is open
     ═══════════════════════════════════════════════════════════ */
  body.rt-modal-open #rt-dock,
  body.rt-modal-open #rt-role-badge,
  body.rt-modal-open .rt-floating-detected {
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
  }

  /* ── The dock ──────────────────────────────────────────── */
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
  }

  #rt-dock-fab {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: #111;
    color: #fff;
    border: none;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    font-weight: 300;
    line-height: 1;
    padding: 0 0 3px 0;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
                background 0.2s ease;
  }
  #rt-dock-fab:hover { transform: scale(1.06); }
  #rt-dock.open #rt-dock-fab {
    transform: rotate(45deg);
    background: #dc2626;
  }

  #rt-dock-menu {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: flex-end;
    pointer-events: none;
  }
  #rt-dock.open #rt-dock-menu { pointer-events: auto; }

  .rt-dock-item {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #fff;
    color: #111;
    border: 1px solid #e5e5e5;
    border-radius: 30px;
    padding: 10px 16px 10px 14px;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    font-weight: 700;
    font-size: 13px;
    white-space: nowrap;
    opacity: 0;
    transform: translateY(10px) scale(0.9);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: inherit;
  }
  #rt-dock.open .rt-dock-item {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  #rt-dock.open .rt-dock-item:nth-child(1) { transition-delay: 0.04s; }
  #rt-dock.open .rt-dock-item:nth-child(2) { transition-delay: 0.08s; }
  #rt-dock.open .rt-dock-item:nth-child(3) { transition-delay: 0.12s; }
  #rt-dock.open .rt-dock-item:nth-child(4) { transition-delay: 0.16s; }
  #rt-dock.open .rt-dock-item:nth-child(5) { transition-delay: 0.20s; }

  .rt-dock-item:hover {
    background: #f5f5f5;
    transform: translateX(-4px);
  }
  .rt-dock-item .icon {
    font-size: 18px;
    width: 24px;
    text-align: center;
  }

  #rt-dock-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.15);
    z-index: 9997;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
  }
  #rt-dock.open ~ #rt-dock-backdrop {
    opacity: 1;
    pointer-events: auto;
  }

  @media (max-width: 640px) {
    #rt-dock { bottom: 90px; right: 14px; }
    #rt-dock-fab { width: 52px; height: 52px; font-size: 24px; }
    .rt-dock-item { padding: 9px 14px 9px 12px; font-size: 12px; }
    #rt-role-badge { bottom: 96px !important; left: 14px !important; }
  }

  @media print {
    #rt-dock, #rt-dock-backdrop, #rt-role-badge,
    .rt-floating-detected { display: none !important; }
  }
</style>

<div id="rt-dock">
  <div id="rt-dock-menu">
    <button class="rt-dock-item" data-owner-only="0"
            onclick="rtDockRun('rtDebtorsOpen')">
      <span class="icon">💰</span>Debtors
    </button>
    <button class="rt-dock-item" data-owner-only="1"
            onclick="rtDockRun('rtProfitOpen')">
      <span class="icon">📊</span>Profit
    </button>
    <button class="rt-dock-item" data-owner-only="0"
            onclick="rtDockRun('rtDmgOpen')">
      <span class="icon">📸</span>Vehicle Check-In
    </button>
    <button class="rt-dock-item" data-owner-only="1"
            onclick="rtDockRun('rtStaffOpen')">
      <span class="icon">👥</span>Staff
    </button>
    <button class="rt-dock-item" data-owner-only="1"
            onclick="rtDockRun('rtBkOpen')">
      <span class="icon">💾</span>Backup
    </button>
  </div>
  <button id="rt-dock-fab" onclick="rtDockToggle(event)"
          aria-label="Open tools menu">+</button>
</div>
<div id="rt-dock-backdrop" onclick="rtDockClose()"></div>

<script>
(function(){

  // ═══════════════════════════════════════════════════════════
  // DOCK BEHAVIOUR
  // ═══════════════════════════════════════════════════════════
  window.rtDockToggle = function(e){
    if (e) e.stopPropagation();
    document.getElementById("rt-dock").classList.toggle("open");
  };
  window.rtDockClose = function(){
    document.getElementById("rt-dock").classList.remove("open");
  };
  window.rtDockRun = function(fnName){
    rtDockClose();
    setTimeout(function(){
      try {
        if (typeof window[fnName] === "function") {
          window[fnName]();
        } else {
          console.warn("[dock] handler not found:", fnName);
        }
      } catch(e) {
        console.error("[dock] error running", fnName, e);
      }
    }, 150);
  };

  document.addEventListener("keydown", function(e){
    if (e.key === "Escape") rtDockClose();
  });

  // ═══════════════════════════════════════════════════════════
  // HOME DETECTION
  // ═══════════════════════════════════════════════════════════
  function isOnHomeScreen(){
    try {
      var text = (document.body.innerText || "").toUpperCase();
      if (text.indexOf("BACK TO CATEGORIES") !== -1) return false;
      if (text.indexOf("CHOOSE A CATEGORY") !== -1) return true;
      var grids = document.querySelectorAll('[class*="categor"], [id*="categor"]');
      if (grids.length > 0) return true;
      return true;
    } catch(e) {
      return true;
    }
  }

  // ═══════════════════════════════════════════════════════════
  // MODAL DETECTION
  // ═══════════════════════════════════════════════════════════
  var MODAL_SELECTORS = [
    "#rt-debtors-overlay",
    "#rt-profit-overlay",
    "#rt-dmg-overlay",
    "#rt-staff-panel",
    "#rt-backup-panel"
  ];

  function anyModalOpen(){
    for (var i = 0; i < MODAL_SELECTORS.length; i++){
      var el = document.querySelector(MODAL_SELECTORS[i]);
      if (el && el.classList.contains("open")) return true;
    }
    return false;
  }

  // ═══════════════════════════════════════════════════════════
  // FLOATING ELEMENT DETECTION
  // ═══════════════════════════════════════════════════════════
  var KEEP_IDS = [
    "rt-dock", "rt-dock-fab", "rt-dock-menu", "rt-dock-backdrop",
    "rt-role-badge",
    "rt-debtors-overlay", "rt-profit-overlay", "rt-dmg-overlay",
    "rt-staff-panel", "rt-backup-panel",
    "rt-debtors-btn", "rt-profit-btn", "rt-dmg-btn"
  ];

  // Text patterns that identify the stray avatar button
var STRAY_CONTENT_PATTERNS = [
  "avatar", "profile", "user-btn", "userBtn", "help-btn",
  "chat-btn", "chatbot", "support", "assistant", "floating-user"
];

  function detectFloatingButtons(){
    try {
      var nodes = document.body.querySelectorAll("button, div, a, img, span");
      for (var i = 0; i < nodes.length; i++){
        var el = nodes[i];
        if (el.id && KEEP_IDS.indexOf(el.id) !== -1) continue;
        if (el.classList && el.classList.contains("rt-floating-detected")) continue;
        if (el.closest("#rt-dock, #rt-dock-backdrop")) continue;
        if (el.closest("#rt-debtors-overlay, #rt-profit-overlay")) continue;
        if (el.closest("#rt-dmg-overlay, #rt-staff-panel, #rt-backup-panel")) continue;

        var cs = window.getComputedStyle(el);
        if (cs.position !== "fixed") continue;
        if (cs.display === "none" || cs.visibility === "hidden") continue;

        var r = el.getBoundingClientRect();
        if (r.width < 20 || r.width > 130) continue;
        if (r.height < 20 || r.height > 130) continue;

        var isTopLeft = (r.left < 120 && r.top < 220);
        var isBottomLeft = (r.left < 260 && r.top > window.innerHeight - 400);
        var isBottomRight = (r.left > window.innerWidth - 220 &&
                             r.top > window.innerHeight - 400);

        var shouldHide = isTopLeft || isBottomLeft || isBottomRight;

        // Content-based detection (catches emoji avatar even if position is odd)
        if (!shouldHide) {
          var content = (el.textContent || "") + " " +
                        (el.className || "") + " " +
                        (el.id || "") + " " +
                        ((el.getAttribute && el.getAttribute("aria-label")) || "") + " " +
                        ((el.getAttribute && el.getAttribute("title")) || "");
          for (var p = 0; p < STRAY_CONTENT_PATTERNS.length; p++){
            if (content.indexOf(STRAY_CONTENT_PATTERNS[p]) !== -1){
              if (r.left < 320 || r.top > window.innerHeight - 400){
                shouldHide = true;
              }
              break;
            }
          }
        }

        if (shouldHide){
          el.classList.add("rt-floating-detected");
          el.dataset.rtFloating = "1";
          console.log("[dock] hiding stray FAB:",
                      el.tagName, el.id || el.className || "(no id)");
        }
      }
    } catch(e) {}
  }

  // ═══════════════════════════════════════════════════════════
  // MASTER UPDATE
  // ═══════════════════════════════════════════════════════════
  function updateVisibility(){
    detectFloatingButtons();
    var isHome = isOnHomeScreen();
    var modalOpen = anyModalOpen();
    document.body.classList.toggle("rt-not-home", !isHome);
    document.body.classList.toggle("rt-modal-open", modalOpen);

    if (!isHome || modalOpen) {
      var dock = document.getElementById("rt-dock");
      if (dock) dock.classList.remove("open");
    }
  }

  function watchModals(){
    MODAL_SELECTORS.forEach(function(sel){
      var el = document.querySelector(sel);
      if (!el || el.__rtDockWatched) return;
      el.__rtDockWatched = true;
      new MutationObserver(updateVisibility).observe(el, {
        attributes: true, attributeFilter: ["class", "style"]
      });
    });
  }

  // ═══════════════════════════════════════════════════════════
  // RUN + OBSERVE
  // ═══════════════════════════════════════════════════════════
  function runAll(){
    watchModals();
    updateVisibility();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runAll);
  } else {
    runAll();
  }
  setTimeout(runAll, 500);
  setTimeout(runAll, 1500);
  setTimeout(runAll, 3000);
  setTimeout(runAll, 6000);

  try {
    new MutationObserver(function(){
      watchModals();
      updateVisibility();
    }).observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "style", "hidden"]
    });
  } catch(e) {}

  window.addEventListener("hashchange", updateVisibility);
  window.addEventListener("popstate", updateVisibility);

  // ═══════════════════════════════════════════════════════════
  // Hide owner-only items for non-owner roles
  // ═══════════════════════════════════════════════════════════
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
})();
</script>
"""


def dock_status():
    return {
        "dock_enabled": True,
        "items": 5,
        "auto_hide_on_modal": True,
        "home_only": True,
    }
