"""PIN authentication — reads from Supabase staff_pins, falls back to hardcoded."""
import os
import time

# Rate limiting state
_attempts = {}  # {key: [timestamps]}
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


def _check_rate_limit(key):
    """Returns None if OK, or seconds to wait if rate-limited."""
    now = time.time()
    if key not in _attempts:
        _attempts[key] = []
    # prune old attempts
    _attempts[key] = [t for t in _attempts[key] if now - t < WINDOW_SECONDS]
    if len(_attempts[key]) >= MAX_ATTEMPTS:
        oldest = min(_attempts[key])
        wait = int(WINDOW_SECONDS - (now - oldest)) + 1
        return wait
    return None


def _record_attempt(key):
    if key not in _attempts:
        _attempts[key] = []
    _attempts[key].append(time.time())


def _clear_attempts(key):
    _attempts.pop(key, None)


# Fallback if Supabase unavailable
_FALLBACK_PINS = {
    "1234": {"name": "Sipho", "role": "Mechanic"},
    "2345": {"name": "Thabo", "role": "Mechanic"},
    "1988": {"name": "Manager", "role": "Manager"},
}


def lookup_pin(pin):
    """Look up a staff member by PIN. Returns None if invalid or rate-limited."""
    p = str(pin or "").strip()
    if len(p) != 4 or not p.isdigit():
        return None

    rate = _check_rate_limit(p)
    if rate is not None:
        return None  # too many attempts

    result = None

    # Try Supabase first
    try:
        import db
        if db.is_ready():
            c = db.get_client()
            r = c.table("staff_pins").select("*").eq("pin", p).execute()
            if r.data:
                s = r.data[0]
                if s.get("active") is False:
                    _record_attempt(p)
                    return None
                result = {
                    "id": s.get("id"),
                    "name": s.get("name", "Unknown"),
                    "role": s.get("role", ""),
                    "active": True,
                }
    except Exception as e:
        print(f"[auth] supabase lookup failed: {e}")

    # Fallback to hardcoded
    if not result:
        entry = _FALLBACK_PINS.get(p)
        if entry:
            result = {
                "id": p,
                "name": entry.get("name", "Unknown"),
                "role": entry.get("role", ""),
                "active": True,
            }

    if result:
        _clear_attempts(p)
        return result

    _record_attempt(p)
    return None
