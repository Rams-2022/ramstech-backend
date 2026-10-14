"""Central controller for all floating buttons.

Every floating element in the app is registered here with a list of
panel IDs where it is allowed to appear. A single loop then toggles
every element based on the current active panel.
"""
from fastapi import APIRouter

router = APIRouter()

FLOATING_MANAGER_HTML = r"""
<script>
(function(){
  // ═══════════════════════════════════════════════════════════
  // REGISTRY — every floating element and where it may appear
  // ═══════════════════════════════════════════════════════════
  var REGISTRY = [
    {
      selector: '#aiFab',
      showOn: [
        'chat','codes','problems','vin','paint','photo',
        'wiring','obd','bulbs','batteries','tyres','fuses',
        'service','inspect','boltcalc','torque'
      ]
    },
    {
      selector: '#rt-dock',
      showOn: ['home']
    },
    {
      selector: '#rt-role-badge',
      showOn: ['home']
    }
  ];

  // ─────────────────────────────────────────────────────────
  // STATE CACHE — remember the last state so we don't fight
  // ourselves by re-setting the same class/style repeatedly.
  // ─────────────────────────────────────────────────────────
  var _lastState = {};        // selector → "1" or "0"
  var _applying = false;      // re-entrancy guard for the observer
  var _lastPanelId = null;

  function activePanelId(){
    var active = document.querySelector('.panel.active');
    return active ? active.id : '';
  }

  function applyVisibility(force){
    // Re-entrancy guard: never let the observer fire while we're already applying
    if(_applying && !force) return;
    _applying = true;

    try{
      var currentId = activePanelId();

      // Fast-path: if nothing changed and not forced, skip DOM work entirely
      if(!force && currentId === _lastPanelId){
        _applying = false;
        return;
      }
      _lastPanelId = currentId;

      REGISTRY.forEach(function(entry){
        var shouldShow;
        if(entry.showOn.indexOf('*') >= 0){
          var exclude = entry.hideOn || [];
          shouldShow = exclude.indexOf(currentId) === -1;
        } else {
          shouldShow = entry.showOn.indexOf(currentId) >= 0;
        }

        // Compare to last state — if same, don't touch the DOM
        var want = shouldShow ? '1' : '0';
        if(_lastState[entry.selector] === want) return;
        _lastState[entry.selector] = want;

        var elements;
        try { elements = document.querySelectorAll(entry.selector); }
        catch(e){ return; }
        if(!elements.length) return;

        elements.forEach(function(el){
          if(shouldShow){
            el.classList.add('show');
            el.style.removeProperty('display');
            el.style.removeProperty('visibility');
          } else {
            el.classList.remove('show');
            el.style.setProperty('display', 'none', 'important');
          }
        });
      });
    } catch(e){
      console.error('[floating_manager]', e);
    }

    _applying = false;
  }

  // ── Initial run ──────────────────────────────────────────
  applyVisibility(true);

  // ── React to class changes (tab switches) ────────────────
  // We ONLY observe class changes, and the guard + state cache
  // prevent our own mutations from re-triggering us in a loop.
  try{
    var _mutTimer = null;
    new MutationObserver(function(){
      if(_mutTimer) return;
      _mutTimer = setTimeout(function(){
        _mutTimer = null;
        applyVisibility(false);
      }, 40);
    }).observe(document.body, {
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }catch(e){}

  // ── Light fallback poll (every 400ms — not 150!) ────────
  setInterval(function(){ applyVisibility(false); }, 400);

  // ── Hook into showTab so it fires instantly ──────────────
  function tryHookShowTab(){
    if(typeof window.showTab === 'function' && !window._fmHooked){
      window._fmHooked = true;
      var orig = window.showTab;
      window.showTab = function(name, el){
        var r = orig.apply(this, arguments);
        // Force re-evaluation because the panel id changed
        _lastPanelId = null;
        applyVisibility(true);
        setTimeout(function(){ _lastPanelId = null; applyVisibility(true); }, 0);
        setTimeout(function(){ _lastPanelId = null; applyVisibility(true); }, 80);
        return r;
      };
    }
  }
  tryHookShowTab();
  setTimeout(tryHookShowTab, 500);
  setTimeout(tryHookShowTab, 1500);

  window.refreshFloating = function(){ _lastPanelId = null; applyVisibility(true); };
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
