"""Merge Clock In/Out into the Staff tab — one tile, two views."""
from fastapi import APIRouter

router = APIRouter()

STAFF_MERGE_HTML = r"""
<style>
/* Hide the Clock In/Out tile in Operations */
body .tile[onclick*="'clockin'"]{
  display:none !important;
}
/* Also hide it if the onclick uses different quoting */
body .tile[onclick*='"clockin"']{
  display:none !important;
}

/* Sub-toggle inside Staff tab */
#staffSubTabs{
  display:flex;
  gap:4px;
  margin-bottom:16px;
  background:rgba(0,0,0,.25);
  padding:4px;
  border-radius:10px;
  border:1px solid rgba(255,255,255,.08);
}
.staffSubTab{
  flex:1;
  padding:11px 8px;
  background:transparent;
  color:#8b95a8;
  border:none;
  border-radius:8px;
  font-size:13px;
  font-weight:700;
  cursor:pointer;
  transition:all .15s ease;
  font-family:inherit;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:6px;
}
.staffSubTab.active{
  background:linear-gradient(135deg,#10b981,#059669);
  color:#fff;
  box-shadow:0 4px 12px rgba(16,185,129,.4);
}
.staffSubTab .icon{
  font-size:15px;
}
</style>

<script>
(function(){
  // ═══════════════════════════════════════════════════════
  // Redirect clock-in tile → staff tab
  // ═══════════════════════════════════════════════════════
  function patchClockInTile(){
    document.querySelectorAll('.tile').forEach(function(tile){
      var oc = tile.getAttribute('onclick') || '';
      if(oc.indexOf('clockin') !== -1 && !tile.dataset.staffMerged){
        tile.dataset.staffMerged = '1';
        tile.style.display = 'none';
      }
    });
  }

  // ═══════════════════════════════════════════════════════
  // Inject sub-tabs into Staff panel
  // ═══════════════════════════════════════════════════════
  function injectStaffSubTabs(){
    var staffPanel = document.getElementById('staff');
    if(!staffPanel) return;
    if(document.getElementById('staffSubTabs')) return;

    var title = staffPanel.querySelector('.panel-title');
    if(!title) return;

    // Wrap existing staff content in a container so we can toggle it
    var wrapper = document.createElement('div');
    wrapper.id = 'staffOriginalContent';

    // Move everything after the title into the wrapper (except our subtabs)
    var siblings = [];
    var next = title.nextSibling;
    while(next){
      siblings.push(next);
      next = next.nextSibling;
    }
    siblings.forEach(function(node){
      wrapper.appendChild(node);
    });

    // Create the toggle
    var toggle = document.createElement('div');
    toggle.id = 'staffSubTabs';
    toggle.innerHTML =
      '<button class="staffSubTab active" data-view="staff" onclick="staffSubView(\'staff\')">' +
        '<span class="icon">👷</span> Staff Members' +
      '</button>' +
      '<button class="staffSubTab" data-view="clockin" onclick="staffSubView(\'clockin\')">' +
        '<span class="icon">🕐</span> Clock In/Out' +
      '</button>';

    // Create a placeholder panel for clock-in content
    var clockPanel = document.createElement('div');
    clockPanel.id = 'staffClockInView';
    clockPanel.style.display = 'none';
    clockPanel.innerHTML = '<div class="loading">Loading clock-in data…</div>';

    // Assemble: title, toggle, staff wrapper, clock wrapper
    title.parentNode.insertBefore(toggle, title.nextSibling);
    title.parentNode.insertBefore(wrapper, toggle.nextSibling);
    title.parentNode.insertBefore(clockPanel, wrapper.nextSibling);
  }

  // ═══════════════════════════════════════════════════════
  // Sub-view switcher
  // ═══════════════════════════════════════════════════════
  window.staffSubView = function(view){
    document.querySelectorAll('.staffSubTab').forEach(function(t){
      t.classList.toggle('active', t.dataset.view === view);
    });

    var staffView = document.getElementById('staffOriginalContent');
    var clockView = document.getElementById('staffClockInView');

    if(view === 'staff'){
      if(staffView) staffView.style.display = 'block';
      if(clockView) clockView.style.display = 'none';
    } else {
      if(staffView) staffView.style.display = 'none';
      if(clockView) clockView.style.display = 'block';
      loadClockInContent();
    }
  };

  // ═══════════════════════════════════════════════════════
  // Clock-in content loader — reuses existing endpoints
  // ═══════════════════════════════════════════════════════
  async function loadClockInContent(){
    var el = document.getElementById('staffClockInView');
    if(!el) return;
    el.innerHTML = '<div class="loading">Loading…</div>';

    try{
      var staffResp = await fetch('/api/staff');
      var clockResp = await fetch('/api/clockins');
      var sd = await staffResp.json();
      var cd = await clockResp.json();
      var staff = sd.staff || [];
      var clockins = cd.clockins || [];

      if(!staff.length){
        el.innerHTML =
          '<div class="card" style="text-align:center;padding:30px;">' +
            '<p style="color:var(--text2)">Add staff first to enable clock in/out.</p>' +
          '</div>';
        return;
      }

      var html = '';
      staff.forEach(function(s){
        var active = clockins.find(function(c){
          return c.staff_id === s.id && !c.clock_out;
        });
        html += '<div class="card">';
        html += '<h3>👷 ' + esc(s.name) + '</h3>';
        if(active){
          html += '<p style="color:#10b981;font-weight:700;">🕐 Clocked in at ' + esc(active.clock_in) + '</p>';
          html += '<button class="btn-sm red" onclick="staffClockOut(\'' + s.id + '\')">Clock Out</button>';
        } else {
          var last = clockins.filter(function(c){ return c.staff_id === s.id; }).pop();
          if(last && last.clock_out){
            html += '<p style="color:var(--text2);font-size:12px;">Last out: ' + esc(last.clock_out) + '</p>';
          }
          html += '<button class="btn-sm green" onclick="staffClockIn(\'' + s.id + '\')">Clock In</button>';
        }
        html += '</div>';
      });

      el.innerHTML = html;
    } catch(e){
      el.innerHTML = '<div class="card"><p style="color:#ef4444;">Error loading clock-in data</p></div>';
    }
  }

  function esc(t){
    var d = document.createElement('div');
    d.textContent = t || '';
    return d.innerHTML;
  }

  window.staffClockIn = async function(id){
    try{
      await fetch('/api/clockins', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ staff_id: id })
      });
      loadClockInContent();
      if(window.dpToast) dpToast('Clocked in', 'success');
    } catch(e){
      if(window.dpToast) dpToast('Failed to clock in', 'error');
    }
  };

  window.staffClockOut = async function(id){
    try{
      await fetch('/api/clockins/' + id + '/out', { method: 'POST' });
      loadClockInContent();
      if(window.dpToast) dpToast('Clocked out', 'success');
    } catch(e){
      if(window.dpToast) dpToast('Failed to clock out', 'error');
    }
  };

  // ═══════════════════════════════════════════════════════
  // Hook into tab changes to ensure sub-tabs get injected
  // ═══════════════════════════════════════════════════════
  document.addEventListener('click', function(e){
    var el = e.target.closest('.tile, .bnav-item, .back-btn, .cat-card');
    if(el){
      setTimeout(function(){
        patchClockInTile();
        injectStaffSubTabs();
      }, 100);
    }
  });

  // Also run periodically to catch programmatic navigation
  setInterval(function(){
    patchClockInTile();
    injectStaffSubTabs();
  }, 800);

  // Initial run
  setTimeout(function(){
    patchClockInTile();
    injectStaffSubTabs();
  }, 600);

  console.log('✓ Staff merge active');
})();
</script>
"""
