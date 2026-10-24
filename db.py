# db.py — Supabase database layer with in-memory fallback
import os
import logging

logger = logging.getLogger("ramstech.db")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

_client = None
_db_ready = False

def init():
    global _client, _db_ready
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("[db] Supabase not configured — using in-memory storage")
        return
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _client.table("workshop").select("id").limit(1).execute()
        _db_ready = True
        logger.info("[db] ✓ Supabase connected")
    except Exception as e:
        logger.error(f"[db] Supabase init failed: {e} — falling back to memory")
        _db_ready = False

def is_ready() -> bool:
    return _db_ready

def get_all(table: str):
    if not _db_ready: return []
    try:
        return _client.table(table).select("*").execute().data or []
    except Exception as e:
        logger.error(f"[db] get_all({table}) error: {e}")
        return []

def get_one(table: str, id_val):
    if not _db_ready: return None
    try:
        r = _client.table(table).select("*").eq("id", id_val).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"[db] get_one({table}) error: {e}")
        return None

def upsert(table: str, row: dict):
    """Combines insert and update into a single database call."""
    if not _db_ready: return row
    try:
        r = _client.table(table).upsert(row).execute()
        return r.data[0] if r.data else row
    except Exception as e:
        logger.error(f"[db] upsert({table}) error: {e}")
        return row

def delete(table: str, id_val):
    if not _db_ready: return False
    try:
        _client.table(table).delete().eq("id", id_val).execute()
        return True
    except Exception as e:
        logger.error(f"[db] delete({table}) error: {e}")
        return False

def get_workshop() -> dict:
    if not _db_ready: return None
    try:
        r = _client.table("workshop").select("*").eq("id", 1).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"[db] get_workshop error: {e}")
        return None

def save_workshop(data: dict) -> dict:
    if not _db_ready: return data
    try:
        data["id"] = 1
        _client.table("workshop").upsert(data).execute()
        return data
    except Exception as e:
        logger.error(f"[db] save_workshop error: {e}")
        return data

def get_client():
    return _client
