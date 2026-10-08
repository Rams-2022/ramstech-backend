"""Simple PIN authentication — bypasses Supabase cache issues."""
import os
import json

# ── PIN MAP ──
# Change PINs here to match your team.
# Format: "PIN": {"name": "Full Name", "role": "Mechanic"}
PIN_MAP = {
    "1234": {"name": "Sipho",   "role": "Mechanic"},
    "2345": {"name": "Thabo",   "role": "Mechanic"},
    "1988": {"name": "Manager", "role": "Manager"},
}

# Optional: override with env variable STAFF_PINS (JSON string)
_env_pins = os.getenv("STAFF_PINS", "").strip()
if _env_pins:
    try:
        PIN_MAP = json.loads(_env_pins)
    except Exception:
        pass


def lookup_pin(pin):
    """Return the staff dict for a PIN, or None if invalid."""
    p = str(pin or "").strip()
    if len(p) != 4 or not p.isdigit():
        return None
    entry = PIN_MAP.get(p)
    if not entry:
        return None
    return {
        "id": p,
        "name": entry.get("name", "Unknown"),
        "role": entry.get("role", ""),
        "active": True,
    }
