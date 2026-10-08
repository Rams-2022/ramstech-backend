"""Smart global search — instant cross-data search."""
from fastapi import APIRouter

router = APIRouter()

SMART_SEARCH_HTML = r"""
<style>
#searchFab{
  position:fixed;
  top:80px;
  left:14px;
  width:42px;
  height:42px;
  border-radius:50%;
  background:linear-gradient(180deg, #2a3141 0%, #080a0e 100%);
  border:1px solid #4a5568;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.15),
    0 4px 12px rgba(0,0,0,.6);
  color:#ff9f1c;
  cursor:pointer;
  z-index:9990;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:0;
  transition:transform .2s ease;
}
#searchFab svg{
  width:20px;height:20px;
  stroke:currentColor;
  fill:none;
  stroke-width:2.2;
  stroke-linecap:round;
  stroke-linejoin:round;
}
#searchFab:active{transform:scale(.9);}

#searchOverlay{
  position:fixed;
  inset:0;
  background:rgba(5,7,10,.96);
  backdrop-filter:blur(12px);
  z-index:99997;
  display:none;
  flex-direction:column;
  padding:16px;
}
#searchOverlay.open{
  display:flex;
  animation:searchIn .25s ease-out;
}
@keyframes searchIn{
  from{opacity:0;transform:translateY(-12px);}
  to{opacity:1;transform:translateY(0);}
}
#searchInner{
  max-width:720px;
  width:100%;
  margin:0 auto;
  display:flex;
  flex-direction:column;
  height:100%;
}
#searchHeader{
  display:flex;
  align-items:center;
  gap:10px;
  margin-bottom:16px;
  padding-top:8px;
}
#searchInput{
  flex:1;
  padding:16px 20px;
  background:linear-gradient(180deg, #080a0e 0%, #1e242f 100%);
  border:1px solid #4a5568;
  border-radius:12px;
  color:#e8ecf2;
  font-size:16px;
  font-family:'JetBrains Mono','Consolas',monospace;
  box-shadow:inset 0 3px 6px rgba(0,0,0,.7);
  outline:none;
}
#searchInput:focus{
  border-color:#ff6b1a;
  box-shadow:
    inset 0 3px 6px rgba(0,0,0,.7),
    0 0 0 2px rgba(255,107,26,.25);
}
#searchClose{
  width:44px;
  height:44px;
  border-radius:10px;
  background:linear-gradient(180deg, #2a3141, #080a0e);
  border:1px solid #4a5568;
  color:#c8d0dc;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:0;
}
#searchClose svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:2.5;}
#searchClose:active{transform:scale(.94);}

#searchResults{
  flex:1;
  overflow-y:auto;
  padding-bottom:20px;
}

.searchGroup{
  margin-bottom:20px;
}
.searchGroupTitle{
  font-size:10px;
  font-weight:800;
  color:#ff9f1c;
  text-transform:uppercase;
  letter-spacing:.15em;
  padding:6px 4px 8px;
  font-family:'JetBrains Mono','Consolas',monospace;
  border-bottom:1px dashed rgba(255,159,28,.25);
  margin-bottom:8px;
  display:flex;
  justify-content:space-between;
  align-items:center;
}
.searchGroupTitle .count{
  color:#7a8494;
  font-weight:600;
}

.searchItem{
  padding:12px 14px;
  background:linear-gradient(180deg, rgba(42,49,65,.4), rgba(20,24,32,.6));
  border:1px solid rgba(74,85,104,.5);
  border-radius:8px;
  margin-bottom:6px;
  cursor:pointer;
  transition:all .15s ease;
  display:flex;
  align-items:center;
  gap:12px;
}
.searchItem:active{
  transform:scale(.985);
  background:linear-gradient(180deg, rgba(255,107,26,.15), rgba(255,107,26,.05));
  border-color:#ff6b1a;
}
.searchItemIcon{
  width:36px;
  height:36px;
  border-radius:8px;
  display:flex;
  align-items:center;
  justify-content:center;
  flex-shrink:0;
  font-size:18px;
}
.searchItemIcon.job{background:rgba(255,107,26,.15);color:#ff9f1c;}
.searchItemIcon.customer{background:rgba(58,169,255,.15);color:#3aa9ff;}
.searchItemIcon.inventory{background:rgba(255,204,0,.15);color:#ffcc00;}
.searchItemIcon.invoice{background:rgba(0,230,118,.15);color:#00e676;}
.searchItemIcon.vin{background:rgba(139,92,246,.15);color:#8b5cf6;}
.searchItemIcon.procedure{background:rgba(236,72,153,.15);color:#ec4899;}
.searchItemBody{
  flex:1;
  min-width:0;
}
.searchItemTitle{
  font-size:14px;
  font-weight:700;
  color:#e8ecf2;
  margin-bottom:2px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.searchItemSub{
  font-size:11px;
  color:#7a8494;
  font-family:'JetBrains Mono','Consolas',monospace;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.searchItemArrow{
  color:#4a5568;
  font-size:16px;
  flex-shrink:0;
}
.searchEmpty{
  text-align:center;
  padding:60px 20px;
  color:#7a8494;
}
.searchEmpty svg{
  width:56px;
  height:56px;
  stroke:#2a3141;
  fill:none;
  stroke-width:1.5;
  margin-bottom:14px;
}
.searchEmptyTitle{
  font-size:15px;
  font-weight:700;
  color:#c8d0dc;
  margin-bottom:6px;
}
.searchEmptyText{
  font-size:12px;
  line-height:1.5;
}
.searchRecentTitle{
  font-size:10px;
  color:#7a8494;
  text-transform:uppercase;
  letter-spacing:.15em;
  margin-bottom:10px;
  font-family:'JetBrains Mono','Consolas',monospace;
}
.searchRecentChip{
  display:inline-block;
  padding:8px 14px;
  background:rgba(42,49,65,.5);
  border:1px solid #4a5568;
  border-radius:16px;
  color:#c8d0dc;
  font-size:12px;
  margin:0 6px 6px 0;
  cursor:pointer;
  font-family:'JetBrains Mono','Consolas',monospace;
}
.searchRecentChip:active{
  background:rgba(255,107,26,.15);
  border-color:#ff6b1a;
}
</style>

<button id="searchFab" onclick="dpOpenSearch()" title="Search everything">
  <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
</button>

<div id="searchOverlay">
  <div id="searchInner">
    <div id="searchHeader">
      <input id="searchInput" type="text" placeholder="Search jobs, customers, parts, invoices…" autocomplete="off" autocorrect="off" spellcheck="false">
      <button id="searchClose" onclick="dpCloseSearch()">
        <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div id="searchResults"></div>
  </div>
</div>

<script>
(function(){
  var _recent = [];
  try{
    var r = localStorage.getItem('dp_recent_searches');
    if(r) _recent = JSON.parse(r);
  }catch(e){}

  function _saveRecent(q){
    q = q.trim();
    if(!q || q.length < 2) return;
    _recent = [q].concat(_recent.filter(function(x){return x !== q;})).slice(0, 6);
    try{ localStorage.setItem('dp_recent_searches', JSON.stringify(_recent)); }catch(e){}
  }

  function _getData(){
    var jobs = (window.dpReadCache && window.dpReadCache('/api/jobs')) || {};
    var customers = (window.dpReadCache && window.dpReadCache('/api/customers')) || {};
    var inventory = (window.dpReadCache && window.dpReadCache('/api/inventory')) || {};
    var invoices = (window.dpReadCache && window.dpReadCache('/api/invoices')) || {};
    return {
      jobs: jobs.jobs || [],
      customers: customers.customers || [],
      inventory: inventory.items || [],
      invoices: invoices.invoices || []
    };
  }

  function _match(text, q){
    if(!text) return false;
    return String(text).toLowerCase().indexOf(q) !== -1;
  }

  function _highlight(str, q){
    if(!str) return '';
    var esc = String(str).replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
    if(!q) return esc;
    var idx = esc.toLowerCase().indexOf(q.toLowerCase());
    if(idx === -1) return esc;
    return esc.slice(0, idx) +
      '<span style="color:#ff9f1c;font-weight:900;">' +
      esc.slice(idx, idx + q.length) +
      '</span>' +
      esc.slice(idx + q.length);
  }

  function _goToTab(tab){
    var navs = document.querySelectorAll('.bnav-item');
    var map = {jobs:0, dashboard:1, chat:2, customers:3, invoices:3, inventory:3};
    var idx = map[tab] || 0;
    if(navs[idx]) navs[idx].click();
    else if(typeof showTab === 'function') showTab(tab);
  }

  function _search(q){
    var results = document.getElementById('searchResults');
    if(!q || q.length < 2){
      _renderRecent();
      return;
    }
    q = q.toLowerCase();
    var data = _getData();
    var groups = [];

    // JOBS
    var jobMatches = data.jobs.filter(function(j){
      return _match(j.customer, q) || _match(j.vehicle, q) ||
             _match(j.registration, q) || _match(j.complaint, q) ||
             _match(j.id, q) || _match(j.phone, q);
    }).slice(0, 8);
    if(jobMatches.length) groups.push({
      title: 'Jobs', key: 'jobs', icon: '🔧', items: jobMatches.map(function(j){
        return {
          id: j.id,
          title: j.customer || '(no customer)',
          sub: [j.vehicle, j.registration, j.status].filter(Boolean).join(' · '),
          onClick: function(){ dpCloseSearch(); _goToTab('jobs'); }
        };
      })
    });

    // CUSTOMERS
    var custMatches = data.customers.filter(function(c){
      return _match(c.name, q) || _match(c.phone, q) || _match(c.email, q);
    }).slice(0, 6);
    if(custMatches.length) groups.push({
      title: 'Customers', key: 'customers', icon: '👤', items: custMatches.map(function(c){
        return {
          id: c.id,
          title: c.name || '(no name)',
          sub: [c.phone, c.email].filter(Boolean).join(' · '),
          onClick: function(){ dpCloseSearch(); _goToTab('customers'); }
        };
      })
    });

    // INVENTORY / PARTS
    var partMatches = data.inventory.filter(function(p){
      return _match(p.part_number, q) || _match(p.name, q) ||
             _match(p.category, q) || _match(p.supplier, q);
    }).slice(0, 8);
    if(partMatches.length) groups.push({
      title: 'Parts', key: 'inventory', icon: '🔩', items: partMatches.map(function(p){
        return {
          id: p.id,
          title: p.name || p.part_number || '(unnamed)',
          sub: [p.part_number, (p.qty !== undefined ? p.qty + ' in stock' : '')].filter(Boolean).join(' · '),
          onClick: function(){ dpCloseSearch(); _goToTab('inventory'); }
        };
      })
    });

    // INVOICES
    var invMatches = data.invoices.filter(function(i){
      return _match(i.customer, q) || _match(i.description, q) || _match(i.id, q);
    }).slice(0, 6);
    if(invMatches.length) groups.push({
      title: 'Invoices', key: 'invoices', icon: '💰', items: invMatches.map(function(i){
        return {
          id: i.id,
          title: i.customer || '(no customer)',
          sub: [i.description, i.total ? 'R' + parseFloat(i.total).toFixed(2) : ''].filter(Boolean).join(' · '),
          onClick: function(){ dpCloseSearch(); _goToTab('invoices'); }
        };
      })
    });

    // VIN or plate detection
    var trimmed = q.toUpperCase().replace(/\s/g, '');
    if(trimmed.length === 17 && /^[A-HJ-NPR-Z0-9]+$/.test(trimmed)){
      groups.unshift({
        title: 'Vehicle Lookup', key: 'vin', icon: '🚗', items: [{
          id: trimmed,
          title: 'Look up VIN ' + trimmed,
          sub: 'Decode vehicle and show workshop history',
          onClick: function(){
            dpCloseSearch();
            fetch('/api/vin/' + trimmed).then(function(r){return r.json();}).then(function(d){
              alert('VIN: ' + d.vin + '\nManufacturer: ' + d.manufacturer + '\nCountry: ' + d.country + '\nYear: ' + d.year);
            });
          }
        }]
      });
    }

    _saveRecent(document.getElementById('searchInput').value.trim());
    _renderResults(groups, q);
  }

  function _renderResults(groups, q){
    var el = document.getElementById('searchResults');
    if(!groups.length){
      el.innerHTML = '<div class="searchEmpty">' +
        '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
        '<div class="searchEmptyTitle">No matches</div>' +
        '<div class="searchEmptyText">Nothing found for "' + _esc(q) + '".<br>Try a customer name, plate, or part number.</div>' +
        '</div>';
      return;
    }
    var html = '';
    groups.forEach(function(g, gIdx){
      html += '<div class="searchGroup">';
      html += '<div class="searchGroupTitle">';
      html += '<span>' + g.icon + ' ' + g.title + '</span>';
      html += '<span class="count">' + g.items.length + '</span>';
      html += '</div>';
      g.items.forEach(function(item, iIdx){
        var onClickId = 'dp_search_click_' + gIdx + '_' + iIdx;
        _clickHandlers[onClickId] = item.onClick;
        html += '<div class="searchItem" onclick="dpSearchClick(\'' + onClickId + '\')">';
        html += '<div class="searchItemIcon ' + g.key + '">' + g.icon + '</div>';
        html += '<div class="searchItemBody">';
        html += '<div class="searchItemTitle">' + _highlight(item.title, q) + '</div>';
        if(item.sub) html += '<div class="searchItemSub">' + _highlight(item.sub, q) + '</div>';
        html += '</div>';
        html += '<div class="searchItemArrow">›</div>';
        html += '</div>';
      });
      html += '</div>';
    });
    el.innerHTML = html;
  }

  function _renderRecent(){
    var el = document.getElementById('searchResults');
    if(!_recent.length){
      el.innerHTML = '<div class="searchEmpty">' +
        '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
        '<div class="searchEmptyTitle">Search everything</div>' +
        '<div class="searchEmptyText">Find jobs, customers, parts, invoices, and VINs.<br>Just start typing.</div>' +
        '</div>';
      return;
    }
    var html = '<div class="searchRecentTitle">Recent searches</div>';
    _recent.forEach(function(r){
      html += '<span class="searchRecentChip" onclick="dpSearchRecent(\'' + _esc(r).replace(/'/g, "\\'") + '\')">' + _esc(r) + '</span>';
    });
    el.innerHTML = html;
  }

  function _esc(s){
    return String(s || '').replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }

  var _clickHandlers = {};
  window.dpSearchClick = function(id){
    var fn = _clickHandlers[id];
    if(typeof fn === 'function') fn();
  };
  window.dpSearchRecent = function(q){
    document.getElementById('searchInput').value = q;
    _search(q);
  };

  var _debounceTimer = null;
  function _onInput(){
    clearTimeout(_debounceTimer);
    var q = document.getElementById('searchInput').value;
    _debounceTimer = setTimeout(function(){ _search(q); }, 120);
  }

  window.dpOpenSearch = function(){
    document.getElementById('searchOverlay').classList.add('open');
    setTimeout(function(){
      document.getElementById('searchInput').focus();
      _renderRecent();
    }, 120);
  };
  window.dpCloseSearch = function(){
    document.getElementById('searchOverlay').classList.remove('open');
    document.getElementById('searchInput').blur();
  };

  document.getElementById('searchInput').addEventListener('input', _onInput);
  document.getElementById('searchInput').addEventListener('keydown', function(e){
    if(e.key === 'Escape'){ dpCloseSearch(); }
  });

  // Keyboard shortcut: Ctrl/Cmd+K
  document.addEventListener('keydown', function(e){
    if((e.ctrlKey || e.metaKey) && e.key === 'k'){
      e.preventDefault();
      dpOpenSearch();
    }
  });

  console.log('✓ Smart search active');
})();
</script>
"""
