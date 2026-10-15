"""Central controller for all floating buttons."""
from fastapi import APIRouter

router = APIRouter()

FLOATING_MANAGER_HTML = r"""
<script>
(function(){
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
  showOn: ['home'],
  // Also hide when the sub-category grid is showing inside Home
  hideWhenVisible: ['#subView']
}, 
    {
      selector: '#rt-role-badge',
      showOn: ['home']
    }
  ];

  var _lastState = {};
  var _lastPanelId = null;
  var _applying = false;

  function activePanelId(){
    var active = document.querySelector('.panel.active');
    return active ? active.id : '';
  }

  function applyVisibility(force){
    if(_applying && !force) return;
    _applying = true;

    try{
      var currentId = activePanelId();

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

// Additional check: if any element in hideWhenVisible is showing,
// force-hide this floating element.
if(shouldShow && entry.hideWhenVisible){
  for(var i = 0; i < entry.hideWhenVisible.length; i++){
    var hw = document.querySelector(entry.hideWhenVisible[i]);
    if(hw && hw.style.display !== 'none' && window.getComputedStyle(hw).display !== 'none'){
      shouldShow = false;
      break;
    }
  }
}

        var want = shouldShow ? '1' : '0';
        if(_lastState[entry.selector] === want) return;
        _lastState[entry.selector] = want;

        var elements;
        try { elements = document.querySelectorAll(entry.selector); }
        catch(e){ return; }
        if(!elements.length) return;

        elements.forEach(function(el){
          // ONLY toggle the class — never touch inline style
          if(shouldShow){
            el.classList.add('show');
          } else {
            el.classList.remove('show');
          }
        });
      });
    } catch(e){
      console.error('[floating_manager]', e);
    }

    _applying = false;
  }

  applyVisibility(true);

  // React to class changes — debounced
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

  // Fallback poll
  setInterval(function(){ applyVisibility(false); }, 400);

  // Hook showTab for instant reaction
  function tryHookShowTab(){
    if(typeof window.showTab === 'function' && !window._fmHooked){
      window._fmHooked = true;
      var orig = window.showTab;
      window.showTab = function(name, el){
        var r = orig.apply(this, arguments);
        _lastPanelId = null;
        applyVisibility(true);
        setTimeout(function(){ _lastPanelId = null; applyVisibility(true); }, 0);
        setTimeout(function(){ _lastPanelId = null; applyVisibility(true); }, 80);
        setTimeout(function(){ _lastPanelId = null; applyVisibility(true); }, 250);
        return r;
      };
    }
  }
  tryHookShowTab();
  setTimeout(tryHookShowTab, 500);
  setTimeout(tryHookShowTab, 1500);
  setTimeout(tryHookShowTab, 3000);

  window.refreshFloating = function(){ _lastPanelId = null; applyVisibility(true); };

  console.log('✓ Floating manager active — ' + REGISTRY.length + ' entries');
})();
</script>
"""


def floating_status():
    return {"enabled": True, "registered": 3, "centralized": True}
