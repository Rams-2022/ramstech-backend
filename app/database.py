# app/database.py — Supabase wrapper with memory fallback
from app.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

_db = None
DB_READY = False

MEM = {
    "jobs":{}, "customers":{}, "invoices":{}, "quotes":{},
    "appointments":{}, "inventory":{}, "staff":{}, "expenses":{}, "suppliers":{}
}
WORKSHOP = {
    "name":"My Workshop","phone":"","email":"","address":"","hours":"",
    "logo":"🔧","labour_rate":450,"vat_number":"","company_reg":"",
    "bank_details":"","terms":"Payment due within 30 days."
}

def init():
    global _db, DB_READY
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[db] Memory mode"); return
    try:
        from supabase import create_client
        _db = create_client(SUPABASE_URL, SUPABASE_KEY)
        _db.table("workshop").select("id").limit(1).execute()
        DB_READY = True
        print("[db] Supabase connected")
    except Exception as e:
        print(f"[db] Failed: {e}")
        DB_READY = False

def list_all(table):
    if DB_READY:
        try: return _db.table(table).select("*").execute().data or []
        except Exception as e: print(f"[db] list {table}: {e}")
    return list(MEM[table].values())

def get_one(table, id_val):
    if DB_READY:
        try:
            r = _db.table(table).select("*").eq("id", id_val).execute()
            return r.data[0] if r.data else None
        except Exception as e: print(f"[db] get {table}: {e}")
    return MEM[table].get(id_val)

def save_one(table, id_val, row):
    if DB_READY:
        try:
            if get_one(table, id_val):
                _db.table(table).update(row).eq("id", id_val).execute()
            else:
                _db.table(table).insert(row).execute()
            return row
        except Exception as e: print(f"[db] save {table}: {e}")
    MEM[table][id_val] = row
    return row

def delete_one(table, id_val):
    if DB_READY:
        try: _db.table(table).delete().eq("id", id_val).execute(); return True
        except Exception as e: print(f"[db] del {table}: {e}"); return False
    MEM[table].pop(id_val, None); return True

def get_workshop():
    if DB_READY:
        try:
            r = _db.table("workshop").select("*").eq("id", 1).execute()
            if r.data: return r.data[0]
        except Exception as e: print(f"[db] ws: {e}")
    return WORKSHOP

def save_workshop(data):
    if DB_READY:
        try: _db.table("workshop").update(data).eq("id", 1).execute(); return data
        except Exception as e: print(f"[db] ws save: {e}")
    WORKSHOP.update(data); return WORKSHOP

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")
