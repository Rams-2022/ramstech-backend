"""Central controller for all floating buttons.

Every floating element in the app is registered here with a list of
panel IDs where it is allowed to appear. A single loop then toggles
every element based on the current active panel — no more scattered
visibility logic in every module.

To change where a floating button appears, edit ONLY the REGISTRY
array below. That's it.
"""
from fastapi import APIRouter

router = APIRouter()

FLOATING_MANAGER_HTML = r"""
<script>
(function(){
  // ═══════════════════════════════════════════════════════════
  // REGISTRY — every floating element and where it may appear
  //
  //   selector : CSS selector for the floating element(s)
  //   showOn   : array of panel IDs where it may appear
  //              use ['*'] to allow on every panel
  //   hideOn   : only used when showOn is ['*'] — panels to skip
  // ═══════════════════════════════════════════════════════════
  var REGISTRY = [

    // ── AI Robot 🤖 — Diagnostics only ───────────────────────
    {
      selector: '#aiFab',
      showOn: [
        'chat',       // AI Chat
        'codes',      // Fault Codes
        'problems',   // Common Problems
        'vin',        // VIN Decoder
        'paint',      // Paint Match
        'photo',      // Photo Diagnosis
        'wiring',     // Wiring Library
        'obd',        // OBD-II PIDs
        'bulbs',      // Bulb Chart
        'batteries',  // Battery Sizes
        'tyres',      // Tyre Sizes
        'fuses',      // Fuse Box Diagrams
        'service',    // Service Calculator
        'inspect',    // Inspection Checklists
        'boltcalc',   // Bolt Torque Calculator
        'torque'      // Torque Specs
      ]
    },

    // ── Black + dock FAB — Home only ─────────────────────────
    {
      selector: '#rt-dock',
      showOn: ['home']
    },

    // ── Owner badge — Home only ──────────────────────────────
    {
      selector: '#rt-role-badge',
      showOn: ['home']
    }

    // ── To add more floating buttons later, add an entry: ────
    // { selector: '#someFab', showOn: ['jobs','invoices'] }
  ];

  // ═══════════════════════════════════════════════════════════
  // CORE — apply visibility based on the active panel
  // ═══════════════════════════════════════════════════════════
  function activePanelId(){
    var active = document.querySelector('.panel.active');
    return active ? active.id : '';
  }

  function applyVisibility(){
    var currentId = activePanelId();
    REGISTRY.forEach(function(entry){
      var elements;
      try { elements = document.querySelectorAll(entry.selector); }
      catch(e){ return; }
      if(!elements.length) return;

      var shouldShow;
      if(entry.showOn.indexOf('*') >= 0){
        var exclude = entry.hideOn || [];
        shouldShow = exclude.indexOf(currentId) === -1;
      } else {
        shouldShow = entry.showOn.indexOf(currentId) >= 0;
      }

      elements.forEach(function(el){
        if(shouldShow){
          el.classList.add('show');
          el.style.removeProperty('display');
          el.style.removeProperty('visibility');
          el.style.removeProperty('opacity');
          el.style.removeProperty('pointer-events');
        } else {
          el.classList.remove('show');
          el.style.setProperty('display', 'none', 'important');
          el.style.setProperty('visibility', 'hidden', 'important');
        }
      });
    });
  }

  // ── Initial run ────────────────────────────────────────────
  applyVisibility();

  // ── React to any DOM change (tab switches, class toggles) ──
  try{
    new MutationObserver(function(){
      applyVisibility();
    }).observe(document.body, {
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }catch(e){}

  // ── Fast fallback poll (belt-and-braces) ───────────────────
  setInterval(applyVisibility, 150);

  // ── Hook into showTab so it fires instantly ────────────────
  function tryHookShowTab(){
    if(typeof window.showTab === 'function' && !window._fmHooked){
      window._fmHooked = true;
      var orig = window.showTab;
      window.showTab = function(name, el){
        var r = orig.apply(this, arguments);
        applyVisibility();
        setTimeout(applyVisibility, 0);
        setTimeout(applyVisibility, 40);
        setTimeout(applyVisibility, 150);
        setTimeout(applyVisibility, 350);
        return r;
      };
    }
  }
  tryHookShowTab();
  setTimeout(tryHookShowTab, 500);
  setTimeout(tryHookShowTab, 1500);
  setTimeout(tryHookShowTab, 3000);

  // ── Expose for manual control ──────────────────────────────
  window.refreshFloating = applyVisibility;
  window.FLOATING_REGISTRY = REGISTRY;

  console.log('✓ Floating manager active — ' + REGISTRY.length + ' entries');
})();
</script>
"""


def floating_status():
    return {
        "enabled": True,
        "registered": 3,
        "centralized": True,
    }
