"""Real-time sync — live updates across all devices via Supabase Realtime (Broadcast)."""
from fastapi import APIRouter

router = APIRouter()

REALTIME_SYNC_HTML = r"""
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function(){
  // ═══════════════════════════════════════════════════
  // REAL-TIME SYNC — Broadcast channel for live updates
  // ═══════════════════════════════════════════════════
  var SUPABASE_URL = '';
  var SUPABASE_ANON = '';
  var _client = null;
  var _channel = null;
  var _connected = false;
  var _myDeviceId = 'dev_' + Math.random().toString(36).slice(2, 10);

  // ═══════════════════════════════════════════════════
  // CONFIG ENDPOINT — get public Supabase credentials
  // ═══════════════════════════════════════════════════
  async function loadConfig(){
    try{
      var r = await fetch('/api/realtime/config');
      var d = await r.json();
      if(d.success){
        SUPABASE_URL = d.url;
        SUPABASE_ANON = d.anon_key;
        return true;
      }
    } catch(e){}
    return false;
  }

  // ═══════════════════════════════════════════════════
  // CONNECT TO BROADCAST CHANNEL
  // ═══════════════════════════════════════════════════
  async function connect(){
    if(_connected) return;
    var ok = await loadConfig();
    if(!ok || !SUPABASE_URL || !SUPABASE_ANON){
      console.log('[sync] Realtime not configured');
      return;
    }
    try{
      _client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON);
      _channel = _client.channel('ramstech_workshop', {
        config: { broadcast: { self: false } }
      });

      // Listen for job/status updates from other devices
      _channel
        .on('broadcast', { event: 'job_created' }, function(payload){
          _handleRemote('job_created', payload);
        })
        .on('broadcast', { event: 'job_updated' }, function(payload){
          _handleRemote('job_updated', payload);
        })
        .on('broadcast', { event: 'job_deleted' }, function(payload){
          _handleRemote('job_deleted', payload);
        })
        .on('broadcast', { event: 'status_changed' }, function(payload){
          _handleRemote('status_changed', payload);
        })
        .on('broadcast', { event: 'customer_added' }, function(payload){
          _handleRemote('customer_added', payload);
        })
        .subscribe(function(status){
          if(status === 'SUBSCRIBED'){
            _connected = true;
            _setPill('connected');
          }
        });
    } catch(e){
      console.warn('[sync] Connection failed', e);
    }
  }

  // ═══════════════════════════════════════════════════
  // HANDLE REMOTE EVENTS
  // ═══════════════════════════════════════════════════
  function _handleRemote(event, payload){
    if(!payload || payload.device === _myDeviceId) return; // ignore own events

    // Show a subtle toast
    var label = {
      job_created: '📋 New job added',
      job_updated: '✏️ Job updated',
      job_deleted: '🗑️ Job deleted',
      status_changed: '🔄 Job status changed',
      customer_added: '👤 Customer added'
    }[event] || '📡 Update';
    if(window.dpToast) dpToast(label, 'info');

    // Clear caches so next load fetches fresh
    if(window.dpClearCaches) window.dpClearCaches();

    // Refresh current view if it's a relevant tab
    var active = document.querySelector('.panel.active');
    if(active){
      var id = active.id;
      try{
        if(id === 'jobs' && typeof loadJobs === 'function') loadJobs();
        else if(id === 'customers' && typeof loadCustomers === 'function') loadCustomers();
        else if(id === 'invoices' && typeof loadInvoices === 'function') loadInvoices();
        else if(id === 'inventory' && typeof loadInventory === 'function') loadInventory();
      } catch(e){}
    }

    // Pulse the sync pill
    _setPill('synced');
  }

  // ═══════════════════════════════════════════════════
  // BROADCAST LOCAL CHANGES
  // ═══════════════════════════════════════════════════
  function _broadcast(event, data){
    if(!_connected || !_channel) return;
    try{
      _channel.send({
        type: 'broadcast',
        event: event,
        payload: Object.assign({ device: _myDeviceId, ts: Date.now() }, data || {})
      });
    } catch(e){}
  }

  // ═══════════════════════════════════════════════════
  // WRAP FETCH TO AUTO-BROADCAST ON WRITES
  // ═══════════════════════════════════════════════════
  var _origFetch = window.fetch.bind(window);
  window.fetch = function(url, opts){
    var urlStr = typeof url === 'string' ? url : (url && url.url) || '';
    var method = ((opts && opts.method) || 'GET').toUpperCase();

    return _origFetch(url, opts).then(function(resp){
      if(resp && resp.ok && (method === 'POST' || method === 'PUT' || method === 'DELETE')){
        // Fire broadcast events based on endpoint
        if(urlStr.indexOf('/api/jobs') === 0){
          if(method === 'POST') _broadcast('job_created', {});
          else if(method === 'PUT') _broadcast('job_updated', {});
          else if(method === 'DELETE') _broadcast('job_deleted', {});
        } else if(urlStr.indexOf('/api/customers') === 0){
          if(method === 'POST') _broadcast('customer_added', {});
        }
      }
      return resp;
    });
  };

  // ═══════════════════════════════════════════════════
  // STATUS PILL
  // ═══════════════════════════════════════════════════
  function _setPill(state){
    var pill = document.getElementById('syncPill');
    if(!pill) return;
    if(state === 'connected'){
      pill.classList.add('show');
      setTimeout(function(){ pill.classList.remove('show'); }, 1200);
    } else if(state === 'synced'){
      pill.classList.add('show');
      var txt = document.getElementById('syncText');
      if(txt) txt.textContent = 'Live update';
      setTimeout(function(){ pill.classList.remove('show'); }, 1200);
    }
  }

  // ═══════════════════════════════════════════════════
  // HEARTBEAT — reconnect if disconnected
  // ═══════════════════════════════════════════════════
  setInterval(function(){
    if(!_connected){
      connect();
    }
  }, 30000);

  // Start after page settles
  setTimeout(connect, 2500);

  // Expose for debugging
  window.dpBroadcast = _broadcast;
  window.dpRealtimeStatus = function(){ return _connected ? 'connected' : 'offline'; };

  console.log('✓ Realtime sync loaded');
})();
</script>
"""
