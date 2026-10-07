"""PWA — manifest, service worker, icons, install support."""
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

MANIFEST_JSON = """{
  "name": "RamsTech Workshop",
  "short_name": "RamsTech",
  "description": "AI-powered workshop assistant",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0f172a",
  "theme_color": "#E65100",
  "categories": ["productivity", "business"],
  "icons": [
    {
      "src": "/icon-192.svg",
      "sizes": "192x192",
      "type": "image/svg+xml",
      "purpose": "any"
    },
    {
      "src": "/icon-512.svg",
      "sizes": "512x512",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}"""

SW_JS = r"""
const CACHE = 'ramstech-v1';
const STATIC = ['/manifest.json', '/icon-192.svg', '/icon-512.svg'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC)).catch(()=>{})
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/')) return;

  if (e.request.mode === 'navigate' || url.pathname === '/') {
    e.respondWith(
      fetch(e.request).then(r => {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});
        return r;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
      const copy = resp.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});
      return resp;
    }))
  );
});
"""

ICON_192 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#E65100"/>
<stop offset="100%" stop-color="#FF9800"/>
</linearGradient></defs>
<rect width="192" height="192" rx="40" fill="url(#g)"/>
<text x="96" y="128" font-size="88" font-weight="900" text-anchor="middle"
fill="#fff" font-family="-apple-system,BlinkMacSystemFont,sans-serif">RT</text>
</svg>"""

ICON_512 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#E65100"/>
<stop offset="100%" stop-color="#FF9800"/>
</linearGradient></defs>
<rect width="512" height="512" rx="110" fill="url(#g)"/>
<text x="256" y="340" font-size="240" font-weight="900" text-anchor="middle"
fill="#fff" font-family="-apple-system,BlinkMacSystemFont,sans-serif">RT</text>
</svg>"""


@router.get("/manifest.json")
def manifest():
    return Response(content=MANIFEST_JSON, media_type="application/manifest+json")


@router.get("/sw.js")
def service_worker():
    return Response(content=SW_JS, media_type="application/javascript",
                    headers={"Service-Worker-Allowed": "/"})


@router.get("/icon-192.svg")
def icon192():
    return Response(content=ICON_192, media_type="image/svg+xml")


@router.get("/icon-512.svg")
def icon512():
    return Response(content=ICON_512, media_type="image/svg+xml")


PWA_HTML = r"""
<script>
(function(){
  try {
    var head = document.head || document.getElementsByTagName('head')[0];
    if(!document.querySelector('link[rel="manifest"]')){
      var m = document.createElement('link');
      m.rel = 'manifest';
      m.href = '/manifest.json';
      head.appendChild(m);
    }
    if(!document.querySelector('meta[name="theme-color"]')){
      var t = document.createElement('meta');
      t.name = 'theme-color';
      t.content = '#E65100';
      head.appendChild(t);
    }
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
    if('serviceWorker' in navigator){
      window.addEventListener('load', function(){
        navigator.serviceWorker.register('/sw.js').catch(function(e){
          console.log('SW registration failed:', e);
        });
      });
    }
  } catch(e) { console.log('PWA setup:', e); }
})();
</script>
"""
