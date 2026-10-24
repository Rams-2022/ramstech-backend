"""PIN authentication — IP rate-limited with JWT generation."""
import os
import time
import asyncio
import jwt
from datetime import datetime, timedelta, timezone

# Use an environment variable in production!
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-ramstech-key-change-me")
ALGORITHM = "HS256"

_attempts = {}  
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60

def _check_rate_limit(ip):
    now = time.time()
    if ip not in _attempts: _attempts[ip] = []
    _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW_SECONDS]
    if len(_attempts[ip]) >= MAX_ATTEMPTS:
        oldest = min(_attempts[ip])
        return int(WINDOW_SECONDS - (now - oldest)) + 1
    return None

def _record_attempt(ip):
    if ip not in _attempts: _attempts[ip] = []
    _attempts[ip].append(time.time())

def _clear_attempts(ip):
    _attempts.pop(ip, None)

def create_token(user_data: dict):
    """Generates a JWT valid for 12 hours."""
    payload = {
        "sub": user_data.get("id"),
        "name": user_data.get("name"),
        "role": user_data.get("role"),
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def _sync_db_lookup(p):
    try:
        import db
        if db.is_ready():
            c = db.get_client()
            r = c.table("staff_pins").select("*").eq("pin", p).execute()
            if r.data:
                s = r.data[0]
                if s.get("active") is False: return None
                return {"id": s.get("id"), "name": s.get("name", "Unknown"), "role": s.get("role", "")}
    except Exception as e:
        print(f"[auth] supabase lookup failed: {e}")
    return None

async def lookup_pin(pin, client_ip="unknown"):
    p = str(pin or "").strip()
    if len(p) != 4 or not p.isdigit(): return None

    rate = _check_rate_limit(client_ip)
    if rate is not None: return {"error": f"Too many attempts. Try again in {rate} seconds."}

    result = await asyncio.to_thread(_sync_db_lookup, p)

    if result:
        _clear_attempts(client_ip)
        result["token"] = create_token(result)
        return result

    _record_attempt(client_ip)
    return None
