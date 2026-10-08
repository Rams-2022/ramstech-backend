"""Instant mode — client-side caching, prefetch, optimistic UI, sync indicator."""
from fastapi import APIRouter

router = APIRouter()

INSTANT_HTML = r"""
<style>
#syncPill{
  position:fixed;
  top:14px;
  left:50%;
  transform:translateX(-50%);
  padding:6px 14px;
  border-radius:20px;
  font-size:11px;
  font-weight:700;
  letter-spacing:.08em;
  text-transform:uppercase;
  font-family:'JetBrains Mono','Consolas',monospace;
  z-index:9989;
  display:flex;
  align-items:center;
  gap:6px;
  transition:all .3s ease;
  box-shadow:0 4px 12px rgba(0,0,0,.4);
  pointer-events:none;
  opacity:0;
}
#syncPill.show{opacity:1;}
#syncPill.synced{
  background:linear-gradient(180deg, rgba(0,230,118,.15), rgba(0,230,118,.08));
  border:1px solid rgba(0,230,118,.4);
  color:#00e676;
}
#syncPill.syncing{
  background:linear-gradient(180deg, rgba(255,159,28,.15), rgba(255,159,28,.08));
  border:1px solid rgba(255,159,28,.4);
  color:#ff9f1c;
}
#syncPill.offline{
  background:linear-gradient(180deg, rgba(255,61,61,.15), rgba(255,61,61,.08));
  border:1px solid rgba(255,61,61,.4);
  color:#ff3d3d;
}
#syncPill .dot{
  width:6px;height:6px;
  border-radius:50%;
  background:currentColor;
  box-shadow:0 0 8px currentColor;
}
#syncPill.syncing .dot{animation:syncPulse 1s ease-in-out infinite;}
@keyframes syncPulse{
  0%,100%{opacity:1;transform:scale(1);}
  50%{opacity:.4;transform:scale(.7);}
}

/* Fast fade-in for cached data */
.panel.active{
  animation:instantFade .2s ease-out !important;
}
@keyframes instantFade{
  from{opacity:.6;}
  to{opacity:1;}
}

/* Instant pressed feedback */
.btn:active, .btn-sm:active, .tile:active, .cat-card:active, .bnav-item:active{
  transition:transform .05s ease !important;
}
</style>

<div id="syncPill" class="synced show">
  <span class="dot"></span>
  <span id="syncText">Ready</span>
</div>

<script>
(function(){
  // ═══════════════════════════════════════════════════
  // INSTANT MODE — transparent fetch caching layer
  // ═══════════════════════════════════════════════════
  var _origFetch = window.fetch.bind(window);
  var _cachePrefix = 'dp_cache_';
  var _activeFetches = 0;
  var _syncTimer = null;
  var _hasNetwork = true;

  function _updateSyncPill(state, text){
    var pill = document.getElementById('syncPill');
    var txt = document.getElementById('syncText');
    if(!pill || !txt) return;
    pill.classList.remove('synced','syncing','offline');
    pill.classList.add(state);
    txt.textContent = text;
    pill.classList.add('show');
    if(state === 'synced'){
      clearTimeout(_syncTimer);
      _syncTimer = setTimeout(function(){
        pill.classList.remove('show');
      }, 1400);
    }
  }

  function _setFetching(delta){
    _activeFetches = Math.max(0, _activeFetches + delta);
    if(_activeFetches > 0){
      _updateSyncPill('syncing', 'Syncing…');
    } else {
      _updateSyncPill('synced', 'Synced');
    }
  }

  function _cacheKey(url){
    return _cachePrefix + url;
  }

  function _readCache(url){
    try{
      var raw = localStorage.getItem(_cacheKey(url));
      if(!raw) return null;
      return raw;
    }catch(e){return null;}
  }

  function _writeCache(url, text){
    try{
      localStorage.setItem(_cacheKey(url), text);
    }catch(e){
      // storage full — clear old entries
      try{
        Object.keys(localStorage).forEach(function(k){
          if(k.indexOf(_cachePrefix) === 0) localStorage.removeItem(k);
        });
        localStorage.setItem(_cacheKey(url), text);
      }catch(e2){}
    }
  }

  function _clearAllCaches(){
    try{
      Object.keys(localStorage).forEach(function(k){
        if(k.indexOf(_cachePrefix) === 0) localStorage.removeItem(k);
      });
    }catch(e){}
  }

  // Wrap Response so it survives cloning
  function _makeResponse(text){
    return new Response(text, {
      status: 200,
      statusText: 'OK',
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // Only cache these endpoints
  var _cacheableEndpoints = [
    '/api/jobs',
    '/api/customers',
    '/api/inventory',
    '/api/invoices',
    '/api/appointments',
    '/api/quotes',
    '/api/staff',
    '/api/expenses',
    '/api/purchase-orders',
    '/api/parts-search',
    '/api/suppliers',
    '/api/fault-codes'
  ];

  function _isCacheable(url, method){
    if(method !== 'GET') return false;
    for(var i=0; i<_cacheableEndpoints.length; i++){
      if(url.indexOf(_cacheableEndpoints[i]) === 0 ||
         url.indexOf(_cacheableEndpoints[i] + '?') !== -1 ||
         url.indexOf(_cacheableEndpoints[i] + '/') !== -1) {
        return true;
      }
    }
    return false;
  }

  function _isWrite(method){
    return method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH';
  }

  // ═══════════════════════════════════════════════════
  // INTERCEPT FETCH
  // ═══════════════════════════════════════════════════
  window.fetch = function(url, opts){
    var urlStr = typeof url === 'string' ? url : (url && url.url) || '';
    var method = (opts && opts.method) || 'GET';
    method = method.toUpperCase();

    // Writes: invalidate cache so next read picks up fresh data
    if(_isWrite(method)){
      _setFetching(1);
      return _origFetch(url, opts).then(function(resp){
        _setFetching(-1);
        _hasNetwork = true;
        if(resp && resp.ok){
          _clearAllCaches();
        }
        return resp;
      }).catch(function(err){
        _setFetching(-1);
        _hasNetwork = false;
        _updateSyncPill('offline', 'Offline');
        throw err;
      });
    }

    // Only cache certain GETs
    if(!_isCacheable(urlStr, method)){
      return _origFetch(url, opts);
    }

    var cached = _readCache(urlStr);

    if(cached){
      // Return cached instantly, refresh in background
      _origFetch(url, opts).then(function(resp){
        if(!resp || !resp.ok) return;
        return resp.clone().text().then(function(text){
          _writeCache(urlStr, text);
          _hasNetwork = true;
        });
      }).catch(function(){
        _hasNetwork = false;
      });

      return Promise.resolve(_makeResponse(cached));
    }

    // No cache yet — fetch normally, then cache
    _setFetching(1);
    return _origFetch(url, opts).then(function(resp){
      _setFetching(-1);
      if(!resp || !resp.ok) return resp;
      return resp.clone().text().then(function(text){
        _writeCache(urlStr, text);
        _hasNetwork = true;
        return _makeResponse(text);
      });
    }).catch(function(err){
      _setFetching(-1);
      _hasNetwork = false;
      _updateSyncPill('offline', 'Offline');
      throw err;
    });
  };

  // ═══════════════════════════════════════════════════
  // PREFETCH ON APP LOAD
  // ═══════════════════════════════════════════════════
  setTimeout(function(){
    // Give the page 1.5s to settle before flooding the network
    _setFetching(1);
    var endpoints = ['/api/jobs', '/api/customers', '/api/inventory', '/api/invoices'];
    Promise.all(endpoints.map(function(u){
      return _origFetch(u).then(function(r){
        if(!r || !r.ok) return null;
        return r.text().then(function(t){ _writeCache(u, t); });
      }).catch(function(){ return null; });
    })).then(function(){
      _setFetching(-1);
    });
  }, 1500);

  // ═══════════════════════════════════════════════════
  // NETWORK STATUS
  // ═══════════════════════════════════════════════════
  window.addEventListener('online', function(){
    _hasNetwork = true;
    _updateSyncPill('synced', 'Back online');
  });
  window.addEventListener('offline', function(){
    _hasNetwork = false;
    _updateSyncPill('offline', 'Offline — changes will sync');
  });

  // ═══════════════════════════════════════════════════
  // EXPOSE CACHE TO OTHER MODULES
  // ═══════════════════════════════════════════════════
  window.dpReadCache = function(url){
    var raw = _readCache(url);
    if(!raw) return null;
    try{ return JSON.parse(raw); }catch(e){ return null; }
  };
  window.dpClearCaches = _clearAllCaches;

  console.log('✓ Instant mode active');
})();
</script>
"""
