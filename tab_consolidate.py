"""Consolidate related tabs into hub tabs with sub-views."""
from fastapi import APIRouter

router = APIRouter()

TAB_CONSOLIDATE_HTML = r"""
<style>
/* Hide tiles we're consolidating */
body .tile[onclick*="'quotes'"],
body .tile[onclick*="'warranty'"],
body .tile[onclick*="'reminders'"],
body .tile[onclick*="'bulbs'"],
body .tile[onclick*="'batteries'"],
body .tile[onclick*="'tyres'"],
body .tile[onclick*="'fuses'"],
body .tile[onclick*="'obd'"],
body .tile[onclick*="'wiring'"]{
  display:none !important;
}

/* Sub-tab bar styling */
.consSubTabs{
  display:flex;
  gap:4px;
  margin-bottom:16px;
  background:rgba(0,0,0,.25);
  padding:4px;
  border-radius:10px;
  border:1px solid rgba(255,255,255,.08);
  overflow-x:auto;
  scrollbar-width:none;
}
.consSubTabs::-webkit-scrollbar{display:none;}
.consSubTab{
  flex:1;
  min-width:80px;
  padding:10px 8px;
  background:transparent;
  color:#8b95a8;
  border:none;
  border-radius:8px;
  font-size:12px;
  font-weight:700;
  cursor:pointer;
  transition:all .15s ease;
  font-family:inherit;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:3px;
  white-space:nowrap;
}
.consSubTab .icon{font-size:16px;}
.consSubTab.active{
  background:linear-gradient(135deg,#E65100,#FF8A3D);
  color:#fff;
  box-shadow:0 4px 12px rgba(230,81,0,.4);
}
.consSubView{display:none;}
.consSubView.active{display:block;}
</style>

<script>
(function(){
  // ═══════════════════════════════════════════════════════
  // TAB CONSOLIDATION DEFINITIONS
  // ═══════════════════════════════════════════════════════
  var merges = [
    {
      id: 'money',
      title: '💰 Money',
      color: 'linear-gradient(135deg,#10b981,#047857)',
      icon: '💰',
      views: [
        { key: 'invoices', label: 'Invoices', icon: '🧾' },
        { key: 'quotes', label: 'Quotes', icon: '💬' }
      ]
    },
    {
      id: 'followups',
      title: '🎁 Follow-ups',
      color: 'linear-gradient(135deg,#ec4899,#be185d)',
      icon: '🎁',
      views: [
        { key: 'warranty', label: 'Warranty', icon: '🎁' },
        { key: 'reminders', label: 'Reminders', icon: '🗓️' }
      ]
    },
    {
      id: 'specs',
      title: '🛞 Vehicle Specs',
      color: 'linear-gradient(135deg,#f59e0b,#b45309)',
      icon: '🛞',
      views: [
        { key: 'bulbs', label: 'Bulbs', icon: '💡' },
        { key: 'batteries', label: 'Batteries', icon: '🔋' },
        { key: 'tyres', label: 'Tyres', icon: '🛞' },
        { key: 'fuses', label: 'Fuses', icon: '🔌' }
      ]
    },
    {
      id: 'electrical',
      title: '⚡ Electrical',
      color: 'linear-gradient(135deg,#eab308,#a16207)',
      icon: '⚡',
      views: [
        { key: 'obd', label: 'OBD-II PIDs', icon: '⚡' },
        { key: 'wiring', label: 'Wiring', icon: '🔌' }
      ]
    }
  ];

  // ═══════════════════════════════════════════════════════
  // INJECT NEW TILES INTO REFERENCE / WORKSHOP CATEGORIES
  // ═══════════════════════════════════════════════════════
  function injectTiles(){
    // Look for the operations grid (where warranty/reminders/expenses live)
    // and reference grid (bulbs/batteries/tyres/fuses/obd/wiring)
    // We'll inject hub tiles into whichever grid has our hidden tiles as parents

    merges.forEach(function(m){
      // Find the parent grid that contains at least one of our target keys
      var targetTiles = m.views.map(function(v){
        return document.querySelector('.tile[onclick*="\'' + v.key + '\'"]');
      }).filter(Boolean);

      if(!targetTiles.length) return;
      if(document.getElementById('hub_' + m.id)) return;

      var parentGrid = targetTiles[0].parentNode;
      if(!parentGrid) return;

      // Create the hub tile
      var tile = document.createElement('div');
      tile.id = 'hub_' + m.id;
      tile.className = 'tile';
      tile.setAttribute('onclick', 'consHubOpen(\'' + m.id + '\')');
      tile.innerHTML =
        '<div class="tile-accent" style="background:' + m.color + '"></div>' +
        '<div class="tile-icon" style="color:' + m.color.split(',')[1].split(')')[0] + '">' + m.icon + '</div>' +
        '<div class="tile-label">' + m.title.split(' ').slice(1).join(' ') + '</div>' +
        '<div class="tile-sub">' + m.views.length + ' in 1</div>';

      // Insert at the end of the grid
      parentGrid.appendChild(tile);
    });
  }

  // ═══════════════════════════════════════════════════════
  // HUB OPEN — switches to a merged panel
  // ═══════════════════════════════════════════════════════
  window.consHubOpen = function(id){
    var merge = merges.find(function(m){ return m.id === id; });
    if(!merge) return;

    // Find any existing hub panel
    var hub = document.getElementById('consHub_' + id);

    if(!hub){
      // Build the hub panel: it wraps existing panels
      hub = document.createElement('div');
      hub.id = 'consHub_' + id;
      hub.className = 'panel';
      hub.dataset.consolidated = '1';

      // Sub-tabs
      var tabs = '<div class="consSubTabs">';
      merge.views.forEach(function(v, i){
        var active = i === 0 ? 'active' : '';
        tabs += '<button class="consSubTab ' + active + '" data-view="' + v.key + '" ' +
                'onclick="consSubView(\'' + id + '\',\'' + v.key + '\')">' +
                '<span class="icon">' + v.icon + '</span>' +
                '<span>' + v.label + '</span>' +
                '</button>';
      });
      tabs += '</div>';

      // Views container
      var viewsHtml = '';
      merge.views.forEach(function(v, i){
        var active = i === 0 ? 'active' : '';
        viewsHtml += '<div class="consSubView ' + active + '" data-view="' + v.key + '" id="consView_' + id + '_' + v.key + '"></div>';
      });

      hub.innerHTML =
        '<div class="panel-title">' + merge.title + '</div>' +
        tabs +
        viewsHtml;

      // Append to body (before bottom nav)
      var nav = document.querySelector('.bottom-nav');
      if(nav && nav.parentNode){
        nav.parentNode.insertBefore(hub, nav);
      } else {
        document.body.appendChild(hub);
      }
    }

    // Hide all other panels
    document.querySelectorAll('.panel').forEach(function(p){
      if(!p.dataset.consolidated) p.classList.remove('active');
    });
    document.querySelectorAll('.consSubView').forEach(function(v){
      if(!v.closest('#consHub_' + id)) v.classList.remove('active');
    });

    // Show the hub
    hub.classList.add('active');

    // Move the original panels' content into the hub views
    merge.views.forEach(function(v){
      var originalPanel = document.getElementById(v.key);
      var viewBox = document.getElementById('consView_' + id + '_' + v.key);
      if(originalPanel && viewBox){
        if(!viewBox.dataset.populated){
          // Clone the original panel's children into the view
          Array.from(originalPanel.children).forEach(function(child){
            viewBox.appendChild(child);
          });
          viewBox.dataset.populated = '1';
          // Hide the original panel
          originalPanel.style.display = 'none';
          originalPanel.classList.remove('active');
        }
      }
    });

    // Trigger loader for the first view
    var firstKey = merge.views[0].key;
    triggerLoader(firstKey);

    window.scrollTo(0, 0);
  };

  // ═══════════════════════════════════════════════════════
  // SUB-VIEW SWITCH
  // ═══════════════════════════════════════════════════════
  window.consSubView = function(hubId, key){
    // Update tab styles
    var hub = document.getElementById('consHub_' + hubId);
    if(!hub) return;
    hub.querySelectorAll('.consSubTab').forEach(function(t){
      t.classList.toggle('active', t.dataset.view === key);
    });
    hub.querySelectorAll('.consSubView').forEach(function(v){
      v.classList.toggle('active', v.dataset.view === key);
    });
    triggerLoader(key);
  };

  // ═══════════════════════════════════════════════════════
  // TRIGGER LOADERS FOR MERGED TABS
  // ═══════════════════════════════════════════════════════
  function triggerLoader(key){
    try{
      var loaders = {
        invoices: function(){ if(typeof loadInvoices === 'function') loadInvoices(); },
        quotes: function(){ if(typeof loadQuotes === 'function') loadQuotes(); },
        warranty: function(){ if(typeof loadWarranty === 'function') loadWarranty(); },
        reminders: function(){ if(typeof loadReminders === 'function') loadReminders(); },
        bulbs: function(){ if(typeof loadBulbs === 'function') loadBulbs(); },
        batteries: function(){ if(typeof loadBatt === 'function') loadBatt(); },
        tyres: function(){ if(typeof loadTyre === 'function') loadTyre(); },
        fuses: function(){ if(typeof loadFuses === 'function') loadFuses(); },
        obd: function(){ if(typeof loadOBD === 'function') loadOBD(); },
        wiring: function(){ if(typeof loadWiring === 'function') loadWiring(); }
      };
      if(loaders[key]) loaders[key]();
    } catch(e){ console.warn('Loader failed for', key, e); }
  }

  // ═══════════════════════════════════════════════════════
  // PATCH showTab SO IT ROUTES MERGED KEYS TO HUB
  // ═══════════════════════════════════════════════════════
  function patchShowTab(){
    if(window._consShowTabPatched) return;
    if(typeof window.showTab !== 'function') return;
    var origShowTab = window.showTab;
    window.showTab = function(name, el){
      // Check if this tab is part of a merge
      var merge = null;
      var subKey = null;
      merges.forEach(function(m){
        m.views.forEach(function(v){
          if(v.key === name){ merge = m; subKey = v.key; }
        });
      });
      if(merge){
        consHubOpen(merge.id);
        if(subKey) setTimeout(function(){ consSubView(merge.id, subKey); }, 100);
        return;
      }
      return origShowTab.apply(this, arguments);
    };
    window._consShowTabPatched = true;
  }

  // ═══════════════════════════════════════════════════════
  // RUN
  // ═══════════════════════════════════════════════════════
  setInterval(function(){
    injectTiles();
    patchShowTab();
  }, 900);

  setTimeout(function(){
    injectTiles();
    patchShowTab();
  }, 700);

  console.log('✓ Tab consolidation active');
})();
</script>
"""
