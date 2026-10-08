"""Offline write queue — saves all POST/PUT/DELETE when offline, replays on reconnect."""
from fastapi import APIRouter

router = APIRouter()

OFFLINE_HTML = r"""
<style>
#queuePill{
  position:fixed;
  top:44px;
  left:50%;
  transform:translateX(-50%);
  padding:8px 16px;
  border-radius:20px;
  font-size:12px;
  font-weight:700;
  letter-spacing:.05em;
  font-family:'JetBrains Mono','Consolas',monospace;
  z-index:9988;
  display:flex;
  align-items:center;
  gap:8px;
  transition:all .3s ease;
  box-shadow:0 6px 20px rgba(0,0,0,.5);
  border:1px solid;
  cursor:pointer;
  opacity:0;
  pointer-events:none;
}
#queuePill.show{
  opacity:1;
  pointer-events:auto;
}
#queuePill.pending{
  background:linear-gradient(180deg, rgba(255,159,28,.2), rgba(255,159,28,.1));
  border-color:rgba(255,159,28,.5);
  color:#ff9f1c;
}
#queuePill.syncing{
  background:linear-gradient(180deg, rgba(58,169,255,.2), rgba(58,169,255,.1));
  border-color:rgba(58,169,255,.5);
  color:#3aa9ff;
}
#queuePill.error{
  background:linear-gradient(180deg, rgba(255,61,61,.2), rgba(255,61,61,.1));
  border-color:rgba(255,61,61,.5);
  color:#ff3d3d;
}
#queuePill .qdot{
  width:8px;height:8px;
  border-radius:50%;
  background:currentColor;
  box-shadow:0 0 10px currentColor;
  animation:qPulse 1.4s ease-in-out infinite;
}
#queuePill.syncing .qdot{
  animation:qSpin 1s linear infinite;
}
@keyframes qPulse{
  0%,100%{transform:scale(1);opacity:1;}
  50%{transform:scale(.7);opacity:.5;}
}
@keyframes qSpin{
  to{transform:rotate(360deg);}
}
#queuePill .qcount{
  font-weight:900;
  background:rgba(0,0,0,.3);
  padding:2px 8px;
  border-radius:10px;
  font-size:11px;
}

/* Offline banner */
#offlineBanner{
  position:fixed;
  bottom:80px;
  left:16px;
  right:16px;
  max-width:400px;
  margin:0 auto;
  background:linear-gradient(180deg, rgba(255,61,61,.25), rgba(255,61,61,.15));
  border:1px solid rgba(255,61,61,.5);
  border-radius:12px;
  padding:14px 18px;
  color:#ffcccc;
  font-size:13px;
  font-weight:600;
  z-index:9987;
  text-align:center;
  backdrop-filter:blur(8px);
  display:none;
  animation:offlineSlideIn .4s ease;
}
#offlineBanner.show{display:block;}
#offlineBanner strong{color:#fff;}
@keyframes offlineSlideIn{
  from{opacity:0;transform:translateY(20px);}
  to{opacity:1;transform:translateY(0);}
}

/* Manual sync button */
#syncNowBtn{
  display:inline-block;
  margin-left:8px;
  padding:4px 10px;
  background:rgba(255,255,255,.15);
  border:1px solid rgba(255,255,255,.25);
  border-radius:8px;
  color:#fff;
  font-size:11px;
  font-weight:700;
  cursor:pointer;
  text-decoration:none;
}
#syncNowBtn:active{transform:scale(.95);}
</style>

<div id="queuePill" class="pending" onclick="dpQueueStatus()">
  <span class="qdot"></span>
  <span id="qText">Pending</span>
  <span class="qcount" id="qCount">0</span>
</div>

<div id="offlineBanner">
  <div><strong>Offline mode</strong></div>
  <div style="font-size:12px;margin-top:4px;" id="offlineMsg">Changes are saved locally</div>
</div>

<script>
(function(){
  // ═══════════════════════════════════════════════════
  // OFFLINE QUEUE — intercepts writes, replays on online
  // ═══════════════════════════════════════════════════
  var QUEUE_KEY = 'dp_write_queue_v1';
  var _origFetch = window.fetch.bind(window);
  var _replaying = false;
  var _replayTimer = null;

  // ═══════════════════════════════════════════════════
  // QUEUE STORAGE
  // ═══════════════════════════════════════════════════
  function _readQueue(){
    try{
      var raw = localStorage.getItem(QUEUE_KEY);
      if(!raw) return [];
      return JSON.parse(raw) || [];
    }catch(e){ return []; }
  }

  function _writeQueue(q){
    try{
      localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
    }catch(e){
      console.error('Queue write failed', e);
    }
    _updateUI();
  }

  function _enqueue(item){
    var q = _readQueue();
    item.id = 'q_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    item.timestamp = Date.now();
    item.retries = 0;
    q.push(item);
    _writeQueue(q);
    return item.id;
  }

  function _dequeue(id){
    var q = _readQueue();
    q = q.filter(function(x){ return x.id !== id; });
    _writeQueue(q);
  }

  function _clearQueue(){
    _writeQueue([]);
  }

  // ═══════════════════════════════════════════════════
  // UI INDICATORS
  // ═══════════════════════════════════════════════════
  function _updateUI(){
    var q = _readQueue();
    var pill = document.getElementById('queuePill');
    var count = document.getElementById('qCount');
    var text = document.getElementById('qText');
    var banner = document.getElementById('offlineBanner');
    var bannerMsg = document.getElementById('offlineMsg');

    if(!pill || !count || !text) return;

    if(q.length === 0){
      pill.classList.remove('show','pending','syncing','error');
      banner.classList.remove('show');
      return;
    }

    pill.classList.add('show');
    pill.classList.remove('syncing','error');
    pill.classList.add('pending');
    count.textContent = q.length;
    text.textContent = q.length === 1 ? 'Change pending' : 'Changes pending';

    if(!navigator.onLine){
      banner.classList.add('show');
      bannerMsg.innerHTML = '<strong>' + q.length + '</strong> change(s) saved locally. Will sync when online.';
    } else {
      banner.classList.remove('show');
    }
  }

  window.dpQueueStatus = function(){
    var q = _readQueue();
    if(q.length === 0){
      _toast('No pending changes', 'success');
      return;
    }
    if(!navigator.onLine){
      _toast('Offline — ' + q.length + ' change(s) queued', 'warn');
      return;
    }
    _toast('Syncing ' + q.length + ' change(s)…', 'info');
    _replay();
  };

  function _toast(msg, type){
    if(window.dpToast){ window.dpToast(msg, type); return; }
    console.log('[queue]', msg);
  }

  // ═══════════════════════════════════════════════════
  // REPLAY QUEUE
  // ═══════════════════════════════════════════════════
  async function _replay(){
    if(_replaying) return;
    if(!navigator.onLine) return;

    var q = _readQueue();
    if(q.length === 0) return;

    _replaying = true;
    var pill = document.getElementById('queuePill');
    var text = document.getElementById('qText');
    if(pill){ pill.classList.remove('pending','error'); pill.classList.add('syncing'); }
    if(text) text.textContent = 'Syncing';

    // Sort by timestamp (oldest first)
    q.sort(function(a,b){ return a.timestamp - b.timestamp; });

    var succeeded = 0;
    var failed = 0;

    for(var i=0; i<q.length; i++){
      var item = q[i];
      try {
        var opts = {
          method: item.method,
          headers: item.headers || { 'Content-Type': 'application/json' }
        };
        if(item.body) opts.body = item.body;

        var resp = await _origFetch(item.url, opts);

        if(resp && resp.ok){
          _dequeue(item.id);
          succeeded++;
        } else if(resp && (resp.status >= 400 && resp.status < 500)){
          // 4xx = client error, don't retry — discard
          console.warn('[queue] discarding failed item', item.url, resp.status);
          _dequeue(item.id);
          failed++;
        } else {
          // 5xx = server error, keep for retry
          item.retries = (item.retries || 0) + 1;
          if(item.retries > 5){
            console.warn('[queue] too many retries, discarding', item.url);
            _dequeue(item.id);
            failed++;
          }
        }
      } catch(e){
        // Network error — stop replaying, try again later
        console.warn('[queue] replay error, stopping', e);
        break;
      }
    }

    _replaying = false;

    if(succeeded > 0){
      _toast('Synced ' + succeeded + ' change' + (succeeded === 1 ? '' : 's'), 'success');
      // Clear read caches so fresh data is fetched
      if(window.dpClearCaches) window.dpClearCaches();
    }

    if(failed > 0){
      _toast(failed + ' change(s) discarded (server rejected)', 'error');
    }

    _updateUI();

    // If queue still has items, schedule another retry
    var remaining = _readQueue();
    if(remaining.length > 0){
      clearTimeout(_replayTimer);
      _replayTimer = setTimeout(_replay, 30000); // retry in 30s
    }
  }

  // ═══════════════════════════════════════════════════
  // INTERCEPT FETCH FOR WRITES
  // ═══════════════════════════════════════════════════
  window.fetch = function(url, opts){
    var urlStr = typeof url === 'string' ? url : (url && url.url) || '';
    var method = (opts && opts.method || 'GET').toUpperCase();

    // Only intercept writes
    if(method !== 'POST' && method !== 'PUT' && method !== 'DELETE' && method !== 'PATCH'){
      return _origFetch(url, opts);
    }

    // Skip auth endpoints — these should fail if offline
    if(urlStr.indexOf('/api/auth/') !== -1 ||
       urlStr.indexOf('/api/tech/login') !== -1 ||
       urlStr.indexOf('/api/owner-pin') !== -1){
      return _origFetch(url, opts);
    }

    // Skip non-JSON writes (rare, but photos go through JSON so this is fine)
    // Also skip queue replay calls (avoid infinite loop)
    if(_replaying){
      return _origFetch(url, opts);
    }

    // If offline, queue immediately
    if(!navigator.onLine){
      _enqueue({
        url: urlStr,
        method: method,
        headers: (opts && opts.headers) || { 'Content-Type': 'application/json' },
        body: (opts && opts.body) || null
      });
      _toast('Saved offline — will sync when online', 'info');
      return Promise.resolve(new Response(
        JSON.stringify({ success: true, offline: true, queued: true }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));
    }

    // Online: try the request. If it fails with a network error, queue it.
    return _origFetch(url, opts).then(function(resp){
      return resp;
    }).catch(function(err){
      // Network error — queue and return fake success
      console.warn('[queue] write failed, queueing', urlStr, err);
      _enqueue({
        url: urlStr,
        method: method,
        headers: (opts && opts.headers) || { 'Content-Type': 'application/json' },
        body: (opts && opts.body) || null
      });
      _toast('Saved — will retry when network returns', 'warn');
      return new Response(
        JSON.stringify({ success: true, offline: true, queued: true }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    });
  };

  // ═══════════════════════════════════════════════════
  // NETWORK EVENTS
  // ═══════════════════════════════════════════════════
  window.addEventListener('online', function(){
    _updateUI();
    setTimeout(_replay, 1000);
  });

  window.addEventListener('offline', function(){
    _updateUI();
    if(window.dpToast) dpToast('Offline — changes will save locally', 'warn');
  });

  // ═══════════════════════════════════════════════════
  // AUTO-REPLAY ON APP LOAD
  // ═══════════════════════════════════════════════════
  setTimeout(function(){
    _updateUI();
    if(navigator.onLine && _readQueue().length > 0){
      _replay();
    }
  }, 3000);

  // Retry periodically when online
  setInterval(function(){
    if(navigator.onLine && _readQueue().length > 0 && !_replaying){
      _replay();
    }
  }, 60000);

  // ═══════════════════════════════════════════════════
  // EXPOSE FOR DEBUGGING
  // ═══════════════════════════════════════════════════
  window.dpQueueCount = function(){ return _readQueue().length; };
  window.dpQueueClear = _clearQueue;
  window.dpQueueReplay = _replay;

  console.log('✓ Offline queue active');
})();
</script>
"""
