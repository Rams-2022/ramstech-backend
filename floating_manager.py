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
      ],
      forceInlineDisplay: true
    },
    {
      selector: '#rt-dock',
      showOn: ['home'],
      hideWhenVisible: ['#subView'],
      forceInlineDisplay: true
    },
    {
      selector: '#rt-role-badge',
      showOn: ['home'],
      hideWhenVisible: ['#subView'],
      forceInlineDisplay: true
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

        // Hide if any of hideWhenVisible selectors are currently shown
        if(shouldShow && entry.hideWhenVisible){
          for(var i = 0; i < entry.hideWhenVisible.length; i++){
            var hw = document.querySelector(entry.hideWhenVisible[i]);
            if(hw){
              var cs = window.getComputedStyle(hw);
              if(cs.display !== 'none' && cs.visibility !== 'hidden'){
                shouldShow = false;
                break;
              }
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
          if(shouldShow){
            el.classList.add('show');
            if(entry.forceInlineDisplay){
              el.style.setProperty('display', 'flex', 'important');
              el.style.setProperty('opacity', '1', 'important');
              el.style.setProperty('visibility', 'visible', 'important');
              el.style.setProperty('pointer-events', 'auto', 'important');
            }
          } else {
            el.classList.remove('show');
            if(entry.forceInlineDisplay){
              el.style.setProperty('display', 'none', 'important');
              el.style.setProperty('opacity', '0', 'important');
              el.style.setProperty('visibility', 'hidden', 'important');
              el.style.setProperty('pointer-events', 'none', 'important');
            }
          }
        });
      });
    } catch(e){
      console.error('[floating_manager]', e);
    }

    _applying = false;
  }

  applyVisibility(true);

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

  setInterval(function(){ applyVisibility(false); }, 400);

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

  window.refreshFloating = function(){
    _lastPanelId = null;
    applyVisibility(true);
  };
  window.FLOATING_REGISTRY = REGISTRY;

  console.log('✓ Floating manager active — ' + REGISTRY.length + ' entries');
})();
</script>
"""


def floating_status():
    return {"enabled": True, "registered": 3, "centralized": True}
