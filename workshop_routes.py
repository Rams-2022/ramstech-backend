"""Workshop Assistant: parts, DTC codes, repair procedures, and AI assistant."""
import os
import re
import httpx
from fastapi import APIRouter, HTTPException, Request

import db
from workshop_ai import chat, embed

router = APIRouter(prefix="/workshop", tags=["Workshop Assistant"])


def _client():
    return db.get_client()


def _is_ready():
    return db.is_ready()


# ═══════════════════════════════════════════
# PARTS (Supabase local)
# ═══════════════════════════════════════════
@router.get("/parts/search")
def search_parts(
    q: str = None,
    make: str = None,
    model: str = None,
    year: int = None,
    engine_type: str = None,
    vehicle_type: str = None,
    category: str = None,
    part_number: str = None,
    limit: int = 25,
):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")

    c = _client()
    query = c.table("parts").select("*, supplier_prices(*, suppliers(*))")

    if part_number:
        query = query.ilike("part_number", f"%{part_number}%")
    if make:
        query = query.ilike("make", f"%{make}%")
    if model:
        query = query.ilike("model", f"%{model}%")
    if category:
        query = query.eq("category", category)
    if engine_type:
        query = query.eq("engine_type", engine_type)
    if vehicle_type:
        query = query.eq("vehicle_type", vehicle_type)
    if year:
        query = query.lte("year_from", year).gte("year_to", year)
    if q:
        query = query.or_(f"description.ilike.%{q}%,part_number.ilike.%{q}%")

    result = query.limit(limit).execute()
    return {"count": len(result.data or []), "parts": result.data or []}


@router.get("/parts/{part_number}")
def get_part(part_number: str):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    c = _client()
    r = c.table("parts").select("*, supplier_prices(*, suppliers(*)")\
        .eq("part_number", part_number).execute()
    if not r.data:
        raise HTTPException(404, f"Part {part_number} not found")
    return r.data[0]


@router.post("/parts")
async def add_part(r: Request):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    d = await r.json()
    c = _client()
    result = c.table("parts").insert(d).execute()
    return {"success": True, "part": result.data[0] if result.data else d}


@router.post("/suppliers")
async def add_supplier(r: Request):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    d = await r.json()
    c = _client()
    result = c.table("suppliers").insert(d).execute()
    return {"success": True, "supplier": result.data[0] if result.data else d}


@router.post("/prices")
async def add_price(r: Request):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    d = await r.json()
    c = _client()
    result = c.table("supplier_prices").insert(d).execute()
    return {"success": True, "price": result.data[0] if result.data else d}


# ═══════════════════════════════════════════
# DTC CODES (Supabase local — cache)
# ═══════════════════════════════════════════
@router.get("/dtc/{code}")
def get_dtc(code: str):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    code = code.upper().strip()
    c = _client()
    r = c.table("dtc_codes").select("*, dtc_repairs(*)").eq("code", code).execute()
    if not r.data:
        raise HTTPException(404, f"Code {code} not found")
    row = r.data[0]
    row["dtc_repairs"] = sorted(row.get("dtc_repairs", []),
                                 key=lambda x: x.get("likelihood_rank") or 99)
    return row


@router.get("/dtc/search/{prefix}")
def search_dtc(prefix: str, limit: int = 50):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    c = _client()
    r = c.table("dtc_codes").select("code, description, category, severity")\
        .ilike("code", f"{prefix.upper()}%").limit(limit).execute()
    return {"count": len(r.data or []), "codes": r.data or []}


# ═══════════════════════════════════════════
# PROCEDURES (vector search)
# ═══════════════════════════════════════════
@router.post("/procedures/search")
async def search_procedures(r: Request):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    d = await r.json()
    query_text = d.get("query", "").strip()
    if not query_text:
        raise HTTPException(400, "query is required")

    try:
        vec = embed(query_text)
    except Exception as e:
        raise HTTPException(503, f"Embedding failed: {e}")

    c = _client()
    result = c.rpc("match_procedures", {
        "query_embedding": vec,
        "match_count": int(d.get("limit", 5)),
        "filter_make": d.get("vehicle_make"),
        "filter_system": d.get("system"),
    }).execute()
    return {"count": len(result.data or []), "procedures": result.data or []}


@router.post("/procedures")
async def add_procedure(r: Request):
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    d = await r.json()
    content = d.get("content", "")
    if not content:
        raise HTTPException(400, "content is required")
    try:
        d["embedding"] = embed(content)
    except Exception as e:
        raise HTTPException(503, f"Embedding failed: {e}")
    c = _client()
    result = c.table("procedures").insert(d).execute()
    return {"success": True, "procedure": result.data[0] if result.data else d}


@router.post("/procedures/embed-all")
def embed_all_procedures():
    if not _is_ready():
        raise HTTPException(503, "Database not configured")
    c = _client()
    rows = c.table("procedures").select("id, title, content")\
        .is_("embedding", "null").execute().data or []
    done = 0
    for row in rows:
        try:
            vec = embed(f"{row['title']}\n{row['content']}")
            c.table("procedures").update({"embedding": vec}).eq("id", row["id"]).execute()
            done += 1
        except Exception as e:
            print(f"[embed] Failed for {row['id']}: {e}")
    return {"success": True, "embedded": done, "remaining": len(rows) - done}


# ═══════════════════════════════════════════
# UNIFIED AI ASSISTANT (OLP + Supabase procedures)
# ═══════════════════════════════════════════
@router.post("/ai/ask")
async def ai_ask(r: Request):
    d = await r.json()
    question = d.get("question", "").strip()
    if not question:
        raise HTTPException(400, "question is required")

    context_parts = []
    sources = []

    # 1. DTC lookup via OLP API (synchronous httpx — no async needed)
    codes = re.findall(r"\b[PBCU]\d{4}\b", question.upper())
    olp_key = os.getenv("OLP_API_KEY", "").strip()
    if codes and olp_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                for code in codes[:3]:
                    try:
                        resp = client.get(
                            f"https://openlaborproject.com/api/v1/dtc/{code}",
                            headers={"x-api-key": olp_key}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            context_parts.append(
                                f"DTC {code}: {data.get('description', 'N/A')}. "
                                f"Severity: {data.get('severity', 'N/A')}."
                            )
                            sources.append(f"OLP DTC {code}")
                    except Exception as e:
                        print(f"[ai] OLP lookup failed for {code}: {e}")
        except Exception as e:
            print(f"[ai] OLP client error: {e}")

    # 2. Semantic search on procedures (Supabase)
    if _is_ready():
        try:
            vec = embed(question)
            c = _client()
            proc = c.rpc("match_procedures", {
                "query_embedding": vec,
                "match_count": 3,
                "filter_make": d.get("vehicle_make"),
                "filter_system": d.get("system"),
            }).execute()
            for p in (proc.data or []):
                context_parts.append(
                    f"Procedure: {p['title']} ({p.get('vehicle_make','')} "
                    f"{p.get('vehicle_model','')}). Tools: {p.get('tools_required','')}. "
                    f"Content: {p.get('content','')[:600]}"
                )
                sources.append(p["title"])
        except Exception as e:
            print(f"[ai/ask] procedure search failed: {e}")

    # 3. Basic parts lookup if vehicle_make provided
    if d.get("vehicle_make") and _is_ready():
        try:
            c = _client()
            pr = c.table("parts").select("part_number, description")\
                .ilike("make", f"%{d['vehicle_make']}%").limit(3).execute()
            for p in (pr.data or []):
                context_parts.append(f"Part: {p['part_number']} - {p['description']}")
        except Exception as e:
            print(f"[ai/ask] parts lookup failed: {e}")

    context = "\n\n".join(context_parts) if context_parts else "No specific database matches found."

    messages = [
        {"role": "system", "content": (
            "You are RamsTech AI, an expert mechanic assistant for Rams Auto Solutions "
            "in South Africa. Answer using ONLY the context provided. If the context "
            "does not cover the question, say so and give general best-practice guidance. "
            "Always mention safety precautions and required tools when relevant. "
            "Use South African terminology and ZAR pricing."
        )},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    try:
        answer, provider = chat(messages)
    except Exception as e:
        raise HTTPException(503, f"AI unavailable: {e}")

    return {"answer": answer, "provider": provider, "sources": sources[:5]}


# ═══════════════════════════════════════════
# TEMPORARY SEED ROUTES (remove after use)
# ═══════════════════════════════════════════
@router.get("/admin/seed-dtc")
def admin_seed_dtc():
    import workshop_seed
    return workshop_seed.seed_dtc()


@router.get("/admin/seed-procedures")
def admin_seed_procedures():
    import workshop_seed
    return workshop_seed.seed_procedures()
