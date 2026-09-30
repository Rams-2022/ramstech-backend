# db.py — Supabase database layer with in-memory fallback

import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

_client = None
_db_ready = False

def init():
    """Initialize Supabase client. Called once at startup."""
    global _client, _db_ready
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[db] Supabase not configured — using in-memory storage")
        return
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection
        _client.table("workshop").select("id").limit(1).execute()
        _db_ready = True
        print("[db] ✓ Supabase connected")
    except Exception as e:
        print(f"[db] Supabase init failed: {e} — falling back to memory")
        _db_ready = False

def is_ready() -> bool:
    return _db_ready

# ═══════════════════════════════════
# GENERIC CRUD
# ═══════════════════════════════════
def get_all(table: str):
    if not _db_ready: return []
    try:
        return _client.table(table).select("*").execute().data or []
    except Exception as e:
        print(f"[db] get_all({table}) error: {e}")
        return []

def get_one(table: str, id_val):
    if not _db_ready: return None
    try:
        r = _client.table(table).select("*").eq("id", id_val).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        print(f"[db] get_one({table}) error: {e}")
        return None

def insert(table: str, row: dict):
    if not _db_ready: return row
    try:
        r = _client.table(table).insert(row).execute()
        return r.data[0] if r.data else row
    except Exception as e:
        print(f"[db] insert({table}) error: {e}")
        return row

def update(table: str, id_val, updates: dict):
    if not _db_ready: return None
    try:
        r = _client.table(table).update(updates).eq("id", id_val).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        print(f"[db] update({table}) error: {e}")
        return None

def delete(table: str, id_val):
    if not _db_ready: return False
    try:
        _client.table(table).delete().eq("id", id_val).execute()
        return True
    except Exception as e:
        print(f"[db] delete({table}) error: {e}")
        return False

# ═══════════════════════════════════
# WORKSHOP (single row)
# ═══════════════════════════════════
def get_workshop() -> dict:
    if not _db_ready: return None
    try:
        r = _client.table("workshop").select("*").eq("id", 1).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        print(f"[db] get_workshop error: {e}")
        return None

def save_workshop(data: dict) -> dict:
    if not _db_ready: return data
    try:
        _client.table("workshop").update(data).eq("id", 1).execute()
        return data
    except Exception as e:
        print(f"[db] save_workshop error: {e}")
        return data
