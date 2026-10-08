"""Simple GET endpoint to trigger embedding of procedures (browser-friendly)."""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/embed-all")
def embed_all():
    import db
    if not db.is_ready():
        raise HTTPException(503, "DB not ready")
    c = db.get_client()
    try:
        rows = c.table("procedures").select("id,title,content")\
            .is_("embedding", "null").execute().data or []
    except Exception as e:
        return {"success": False, "error": str(e)}

    if not rows:
        return {"success": True, "embedded": 0, "message": "All procedures already have embeddings"}

    try:
        import workshop_ai
    except Exception as e:
        return {"success": False, "error": f"workshop_ai not available: {e}"}

    done = 0
    failed = 0
    for row in rows:
        try:
            text = f"{row.get('title','')}\n{row.get('content','')}"
            vec = workshop_ai.embed(text[:8000])
            c.table("procedures").update({"embedding": vec}).eq("id", row["id"]).execute()
            done += 1
        except Exception as e:
            print(f"[embed] {row.get('id')} failed: {e}")
            failed += 1

    return {"success": True, "embedded": done, "failed": failed, "total": len(rows)}
