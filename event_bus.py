"""Event bus — tabs communicate through named events."""
from fastapi import APIRouter

router = APIRouter()

EVENT_BUS_HTML = r"""
<script>
(function(){
  // ═══════════════════════════════════════════════════
  // SHARED EVENT BUS
  // ═══════════════════════════════════════════════════
  var _listeners = {};      // { eventName: [fn, fn, ...] }
  var _history = [];        // last 100 events for debugging
  var _context = {};        // current operational context
                             // e.g. { currentJob: '6e4c5c4b', currentCustomer: 'abc123' }

  // ─── Subscribe ───
  window.dpOn = function(eventName, handler){
    if(!_listeners[eventName]) _listeners[eventName] = [];
    _listeners[eventName].push(handler);
    return function off(){  // return an unsubscribe function
      _listeners[eventName] = _listeners[eventName].filter(function(h){ return h !== handler; });
    };
  };

  // ─── Publish ───
  window.dpEmit = function(eventName, payload){
    payload = payload || {};
    var evt = {
      name: eventName,
      payload: payload,
      ts: Date.now(),
      context: JSON.parse(JSON.stringify(_context))
    };
    _history.push(evt);
    if(_history.length > 100) _history.shift();

    // Notify all listeners
    (_listeners[eventName] || []).forEach(function(fn){
      try { fn(payload, evt); } catch(e){ console.warn('[event bus]', eventName, e); }
    });

    // Wildcard listeners (any event)
    (_listeners['*'] || []).forEach(function(fn){
      try { fn(payload, evt); } catch(e){}
    });

    // Cross-device broadcast via realtime_sync (if available)
    if(window.dpBroadcast){
      try { window.dpBroadcast(eventName, payload); } catch(e){}
    }

    console.log('📡', eventName, payload);
  };

  // ─── Context tracking ───
  // Tabs can set global context (e.g. current job) that any tab can read
  window.dpSetContext = function(key, value){
    _context[key] = value;
  };
  window.dpGetContext = function(key){
    return key ? _context[key] : _context;
  };

  // ─── History for debugging ───
  window.dpEventHistory = function(){
    return _history.slice();
  };

  // ═══════════════════════════════════════════════════
  // AUTO-INSTRUMENT: wrap fetch to detect writes and emit events
  // ═══════════════════════════════════════════════════
  var _origFetch = window.fetch.bind(window);
  var _endpointToEvent = [
    { match: /^\/api\/customers$/, method: 'POST', event: 'customer.created' },
    { match: /^\/api\/appointments$/, method: 'POST', event: 'appointment.created' },
    { match: /^\/api\/jobs$/, method: 'POST', event: 'job.created' },
    { match: /^\/api\/jobs\/[^\/]+\/cost$/, method: 'POST', event: 'job.cost_set' },
    { match: /^\/api\/quotes$/, method: 'POST', event: 'quote.created' },
    { match: /^\/api\/quotes\/[^\/]+\/accept$/, method: 'POST', event: 'quote.accepted' },
    { match: /^\/api\/invoices$/, method: 'POST', event: 'invoice.created' },
    { match: /^\/api\/invoices\/[^\/]+\/pay$/, method: 'POST', event: 'invoice.paid' },
    { match: /^\/api\/inventory$/, method: 'POST', event: 'stock.added' },
    { match: /^\/api\/inventory\/[^\/]+\/adjust$/, method: 'POST', event: 'stock.adjusted' },
    { match: /^\/api\/po\/create$/, method: 'POST', event: 'po.created' },
    { match: /^\/api\/po\/[^\/]+\/receive$/, method: 'POST', event: 'po.received' },
    { match: /^\/api\/clockins$/, method: 'POST', event: 'staff.clocked_in' },
    { match: /^\/api\/clockins\/[^\/]+\/out$/, method: 'POST', event: 'staff.clocked_out' },
    { match: /^\/api\/workflow\/start\//, method: 'POST', event: 'job.started' },
    { match: /^\/api\/workflow\/progress\//, method: 'POST', event: 'job.progress' },
    { match: /^\/api\/workflow\/complete\//, method: 'POST', event: 'job.completed' },
    { match: /^\/api\/workflow\/qc\//, method: 'POST', event: 'job.qc_passed' },
    { match: /^\/api\/workflow\/invoice\//, method: 'POST', event: 'invoice.created' },
    { match: /^\/api\/workflow\/assign\//, method: 'POST', event: 'job.assigned' },
    { match: /^\/api\/workflow\/quote-owner-sign\//, method: 'POST', event: 'job.created' }
  ];

  window.fetch = function(url, opts){
    var urlStr = typeof url === 'string' ? url : (url && url.url) || '';
    var method = ((opts && opts.method) || 'GET').toUpperCase();

    return _origFetch(url, opts).then(function(resp){
      if(resp && resp.ok){
        // Try to extract response body for the payload, without consuming it
        var clone = resp.clone();
        clone.json().then(function(body){
          _endpointToEvent.forEach(function(rule){
            if(rule.method === method && rule.match.test(urlStr)){
              dpEmit(rule.event, body || {});
            }
          });
        }).catch(function(){});
      }
      return resp;
    });
  };

  console.log('✓ Event bus ready — try dpEventHistory() in console');
})();
</script>
"""
