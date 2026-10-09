"""Push notifications — Web Push via pywebpush + VAPID."""
import os
import json
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "").strip()
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "").strip()
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:info@ramstech.co.za").strip()


def _c():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    return db.get_client()


@router.get("/api/push/vapid-public-key")
def get_vapid_public():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(503, "Push not configured")
    return {"public_key": VAPID_PUBLIC_KEY}


@router.post("/api/push/subscribe")
async def subscribe(r: Request):
    d = await r.json()
    sub = d.get("subscription")
    if not sub or not sub.get("endpoint"):
        raise HTTPException(400, "subscription required")

    user = (d.get("user") or "unknown").strip()
    c = _c()

    existing = c.table("push_subscriptions").select("id").eq("endpoint", sub["endpoint"]).execute()
    if existing.data:
        return {"success": True, "message": "Already subscribed"}

    import uuid
    row = {
        "id": str(uuid.uuid4())[:12],
        "user": user,
        "endpoint": sub["endpoint"],
        "subscription": json.dumps(sub),
        "created": __import__("datetime").datetime.utcnow().isoformat(),
    }
    try:
        c.table("push_subscriptions").insert(row).execute()
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": True}


@router.post("/api/push/unsubscribe")
async def unsubscribe(r: Request):
    d = await r.json()
    endpoint = (d.get("endpoint") or "").strip()
    if not endpoint:
        raise HTTPException(400, "endpoint required")
    try:
        _c().table("push_subscriptions").delete().eq("endpoint", endpoint).execute()
    except Exception:
        pass
    return {"success": True}


def send_push_to_all(title, body, url="/"):
    """Broadcast a push notification to every subscribed device."""
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        print("[push] VAPID not configured")
        return 0

    try:
        from pywebpush import webpush, WebPushException
    except Exception as e:
        print(f"[push] pywebpush not installed: {e}")
        return 0

    try:
        c = _c()
        subs = c.table("push_subscriptions").select("*").execute().data or []
    except Exception:
        return 0

    sent = 0
    for s in subs:
        try:
            sub = json.loads(s["subscription"])
            webpush(
                subscription_info=sub,
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_SUBJECT},
            )
            sent += 1
        except Exception as e:
            # Invalid subscription — remove
            try:
                _c().table("push_subscriptions").delete().eq("id", s["id"]).execute()
            except Exception:
                pass
            print(f"[push] failed for {s.get('user')}: {e}")
    print(f"[push] sent {sent} notifications")
    return sent


PUSH_NOTIFY_HTML = r"""
<script>
(function(){
  // ═══════════════════════════════════════════════════
  // PUSH NOTIFICATIONS — subscribe + handle display
  // ═══════════════════════════════════════════════════
  var _vapidKey = null;
  var _subscribed = false;

  function _urlBase64ToUint8Array(base64){
    var padding = '='.repeat((4 - base64.length % 4) % 4);
    var base64Safe = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/');
    var raw = atob(base64Safe);
    var output = new Uint8Array(raw.length);
    for(var i=0; i<raw.length; i++) output[i] = raw.charCodeAt(i);
    return output;
  }

  async function loadVapid(){
    try{
      var r = await fetch('/api/push/vapid-public-key');
      var d = await r.json();
      _vapidKey = d.public_key;
      return !!_vapidKey;
    } catch(e){ return false; }
  }

  async function registerSW(){
    if(!('serviceWorker' in navigator)) return null;
    try{
      var reg = await navigator.serviceWorker.register('/push-sw.js', { scope: '/' });
      return reg;
    } catch(e){
      console.warn('[push] SW registration failed', e);
      return null;
    }
  }

  async function subscribe(){
    if(_subscribed) return true;
    if(!('Notification' in window) || !('serviceWorker' in navigator)) return false;

    var permission = await Notification.requestPermission();
    if(permission !== 'granted') return false;

    var ok = await loadVapid();
    if(!ok) return false;

    var reg = await registerSW();
    if(!reg) return false;

    try{
      var sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: _urlBase64ToUint8Array(_vapidKey)
      });
      await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          subscription: sub.toJSON(),
          user: localStorage.getItem('ramstech_user') || 'unknown'
        })
      });
      _subscribed = true;
      console.log('[push] Subscribed');
      return true;
    } catch(e){
      console.warn('[push] Subscribe failed', e);
      return false;
    }
  }

  // ═══════════════════════════════════════════════════
  // AUTO-PROMPT ON FIRST USER INTERACTION
  // ═══════════════════════════════════════════════════
  async function tryAutoSubscribe(){
    try{
      if(Notification.permission === 'granted'){
        await subscribe();
        return;
      }
      if(Notification.permission === 'denied') return;

      // Wait for first tap (browser requires user gesture)
      var handler = async function(){
        document.removeEventListener('click', handler);
        document.removeEventListener('touchstart', handler);
        setTimeout(subscribe, 800);
      };
      document.addEventListener('click', handler, { once: true });
      document.addEventListener('touchstart', handler, { once: true });
    } catch(e){}
  }

  // Manual trigger available for UI
  window.dpEnablePush = async function(){
    var ok = await subscribe();
    if(window.dpToast){
      dpToast(ok ? '🔔 Notifications enabled' : '❌ Could not enable notifications', ok ? 'success' : 'error');
    }
    return ok;
  };

  // Add a "Enable notifications" button to Settings
  setInterval(function(){
    var settingsTab = document.getElementById('settings');
    if(!settingsTab || document.getElementById('pushEnableBtn')) return;
    if(_subscribed) return;
    var card = settingsTab.querySelector('.card');
    if(!card) return;
    var b = document.createElement('button');
    b.id = 'pushEnableBtn';
    b.className = 'btn btn-dark';
    b.textContent = '🔔 Enable Push Notifications';
    b.style.cssText = 'margin-top:10px;';
    b.onclick = window.dpEnablePush;
    card.appendChild(b);
  }, 2000);

  // Start after page settles
  setTimeout(tryAutoSubscribe, 4000);

  console.log('✓ Push notify loaded');
})();
</script>
"""
