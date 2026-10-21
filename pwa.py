"""PWA — manifest, service worker, icons, install support."""
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# MANIFEST (Sci-Fi Theme Colors)
# ═══════════════════════════════════════════════════════════════
MANIFEST_JSON = """{
  "name": "RamsTech Workshop",
  "short_name": "RamsTech",
  "description": "AI-powered workshop assistant",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#050a14",
  "theme_color": "#00f2fe",
  "categories": ["productivity", "business"],
  "icons": [
    {
      "src": "/icon-192.svg",
      "sizes": "192x192",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512.svg",
      "sizes": "512x512",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}"""

# ═══════════════════════════════════════════════════════════════
# SERVICE WORKER (Smart Caching)
# ═══════════════════════════════════════════════════════════════
SW_JS = r"""
// Bump this version string to force the browser to drop old caches
const CACHE = 'ramstech-sci-fi-v1';

const STATIC = ['/manifest.json', '/icon-192.svg', '/icon-512.svg'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)).catch(()=>{}));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;

  // ── NEVER CACHE API CALLS OR HTML ──
  // This ensures you always get fresh data and the latest UI.
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname === '/' ||
    e.request.mode === 'navigate'
  ) {
    return; // Go straight to the network
  }

  // ── CACHE STATIC ASSETS (Icons, manifest) ──
  if (STATIC.some(p => url.pathname === p)) {
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
        if (resp && resp.ok) {
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});
        }
        return resp;
      }))
    );
    return;
  }
});
"""

# ═══════════════════════════════════════════════════════════════
# ICONS
# ═══════════════════════════════════════════════════════════════
ICON_192 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#00f2fe"/>
<stop offset="100%" stop-color="#4facfe"/>
</linearGradient></defs>
<rect width="192" height="192" rx="40" fill="#050a14"/>
<circle cx="96" cy="96" r="70" fill="none" stroke="url(#g)" stroke-width="4"/>
<text x="96" y="126" font-size="80" font-weight="900" text-anchor="middle"
fill="url(#g)" font-family="-apple-system,sans-serif">RT</text>
</svg>"""

ICON_512 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#00f2fe"/>
<stop offset="100%" stop-color="#4facfe"/>
</linearGradient></defs>
<rect width="512" height="512" rx="110" fill="#050a14"/>
<circle cx="256" cy="256" r="200" fill="none" stroke="url(#g)" stroke-width="10"/>
<text x="256" y="340" font-size="220" font-weight="900" text-anchor="middle"
fill="url(#g)" font-family="-apple-system,sans-serif">RT</text>
</svg>"""

# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════
@router.get("/manifest.json")
def manifest():
    return Response(content=MANIFEST_JSON, media_type="application/manifest+json")

@router.get("/sw.js")
def service_worker():
    return Response(
        content=SW_JS,
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )

@router.get("/icon-192.svg")
def icon192():
    return Response(content=ICON_192, media_type="image/svg+xml")

@router.get("/icon-512.svg")
def icon512():
    return Response(content=ICON_512, media_type="image/svg+xml")


# ═══════════════════════════════════════════════════════════════
# INJECTION (Head tags & SW Registration)
# ═══════════════════════════════════════════════════════════════
PWA_HTML = r"""
<script>
(function(){
  try {
    var head = document.head || document.getElementsByTagName('head')[0];
    
    // Add Manifest
    if(!document.querySelector('link[rel="manifest"]')){
      var m = document.createElement('link');
      m.rel = 'manifest';
      m.href = '/manifest.json';
      head.appendChild(m);
    }
    
    // Add Theme Color (Sci-Fi Cyan)
    if(!document.querySelector('meta[name="theme-color"]')){
      var t = document.createElement('meta');
      t.name = 'theme-color';
      t.content = '#00f2fe';
      head.appendChild(t);
    }
    
    // Add Apple Mobile Web App Tags
    if(!document.querySelector('meta[name="apple-mobile-web-app-capable"]')){
      var a = document.createElement('meta');
      a.name = 'apple-mobile-web-app-capable';
      a.content = 'yes';
      head.appendChild(a);

      var s = document.createElement('meta');
      s.name = 'apple-mobile-web-app-status-bar-style';
      s.content = 'black-translucent';
      head.appendChild(s);

      var n = document.createElement('meta');
      n.name = 'apple-mobile-web-app-title';
      n.content = 'RamsTech';
      head.appendChild(n);

      var ai = document.createElement('link');
      ai.rel = 'apple-touch-icon';
      ai.href = '/icon-192.svg';
      head.appendChild(ai);
    }

    // Register Service Worker
    if('serviceWorker' in navigator){
      window.addEventListener('load', function(){
        navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' })
          .then(function(reg){
            reg.update().catch(function(){});
            reg.addEventListener('updatefound', function(){
              var newSW = reg.installing;
              if (!newSW) return;
              newSW.addEventListener('statechange', function(){
                if (newSW.state === 'installed' && navigator.serviceWorker.controller) {
                  newSW.postMessage('SKIP_WAITING');
                }
              });
            });
          })
          .catch(function(e){ console.log('SW registration failed:', e); });

        // Reload if controller changes (ensures latest code is used)
        var refreshed = false;
        navigator.serviceWorker.addEventListener('controllerchange', function(){
          if (refreshed) return;
          refreshed = true;
          window.location.reload();
        });
      });
    }
  } catch(e) { console.log('PWA setup:', e); }
})();
</script>
"""
