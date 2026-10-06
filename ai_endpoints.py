import os
import hashlib
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()


def _client():
    try:
        import db
        return db.get_client() if db.is_ready() else None
    except Exception:
        return None


def _cache_key(endpoint, parts):
    raw = endpoint + "|" + "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.lower().encode()).hexdigest()[:32]


def _cache_get(key):
    c = _client()
    if not c:
        return None
    try:
        r = c.table("ai_cache").select("reply, provider").eq("cache_key", key).execute()
        if r.data:
            return r.data[0]
    except Exception as e:
        print(f"[cache] get fail: {e}")
    return None


def _cache_set(key, endpoint, active_tab, vehicle, question, reply, provider):
    c = _client()
    if not c:
        return
    try:
        c.table("ai_cache").insert({
            "cache_key": key,
            "endpoint": endpoint,
            "active_tab": active_tab,
            "vehicle": vehicle,
            "question": (question or "")[:500],
            "reply": reply,
            "provider": provider,
        }).execute()
    except Exception as e:
        print(f"[cache] set fail: {e}")


def _chat(messages, max_tokens=900, temperature=0.2):
    if OPENAI_KEY:
        try:
            import openai
            c = openai.OpenAI(api_key=OPENAI_KEY, timeout=45.0)
            r = c.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return r.choices[0].message.content, "openai"
        except Exception as e:
            print(f"[ai] openai fail: {e}")
    if GROQ_KEY:
        try:
            import openai
            c = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_KEY,
                timeout=45.0,
            )
            r = c.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return r.choices[0].message.content, "groq"
        except Exception as e:
            print(f"[ai] groq fail: {e}")
    raise RuntimeError("No AI provider available")


@router.post("/api/fault-codes/ai")
async def fault_code_ai(r: Request):
    d = await r.json()
    code = (d.get("code") or "").upper().strip().replace(" ", "").replace("-", "")
    vehicle = (d.get("vehicle") or "").strip()
    if not code:
        raise HTTPException(400, "code is required")

    # ── Cache lookup ──
    key = _cache_key("code", [code, vehicle])
    hit = _cache_get(key)
    if hit:
        return {
            "success": True,
            "code": code,
            "provider": "cache",
            "reply": hit["reply"],
            "cached": True,
        }

    local_desc = ""
    try:
        from data import FAULT_CODES
        local_desc = (FAULT_CODES.get(code) or {}).get("description", "")
    except Exception:
        pass
    system_msg = (
        "You are RamsTech AI, a master mechanic in South Africa. Explain a "
        "diagnostic trouble code. Structure:\n"
        "1. MEANING\n2. LIKELY CAUSES (ranked)\n3. TESTS TO PERFORM (numbered, "
        "with tool for each)\n4. REPAIRS with approximate ZAR costs\n"
        "Add a SAFETY line if needed. Under 400 words."
    )
    user_msg = f"Code: {code}\nVehicle: {vehicle or 'unspecified'}\nLocal: {local_desc or 'none'}"
    try:
        reply, provider = _chat(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1000,
        )
    except Exception as e:
        return {"success": False, "code": code, "reply": f"AI error: {e}"}

    _cache_set(key, "code", "", vehicle, f"code:{code}", reply, provider)
    return {"success": True, "code": code, "description": local_desc,
            "provider": provider, "reply": reply}


@router.post("/api/fault-codes/ai-search")
async def fault_code_ai_search(r: Request):
    d = await r.json()
    query = (d.get("query") or "").strip()
    vehicle = (d.get("vehicle") or "").strip()
    if not query:
        raise HTTPException(400, "query is required")

    key = _cache_key("search", [query, vehicle])
    hit = _cache_get(key)
    if hit:
        return {
            "success": True,
            "query": query,
            "provider": "cache",
            "local_matches": [],
            "reply": hit["reply"],
            "cached": True,
        }

    local_matches = []
    try:
        from data import FAULT_CODES
        q = query.lower()
        kws = [w for w in q.split() if len(w) > 2]
        for code, info in FAULT_CODES.items():
            text = (code + " " + str(info.get("description", ""))).lower()
            if any(k in text for k in kws) or q in text:
                local_matches.append({
                    "code": code,
                    "description": info.get("description", ""),
                    "source": "local",
                })
            if len(local_matches) >= 15:
                break
    except Exception:
        pass
    system_msg = (
        "You are RamsTech AI, a diagnostic technician. From the symptom, "
        "suggest 3-7 likely OBD-II codes. For each: code, title, why it fits. "
        "Then a DIAGNOSTIC PATH. Only real OBD-II codes. Under 350 words."
    )
    user_msg = f"Symptom: {query}\nVehicle: {vehicle or 'unspecified'}"
    try:
        reply, provider = _chat(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=900,
        )
    except Exception as e:
        return {"success": False, "query": query,
                "local_matches": local_matches, "reply": f"AI error: {e}"}

    _cache_set(key, "search", "", vehicle, query, reply, provider)
    return {"success": True, "query": query, "provider": provider,
            "local_matches": local_matches, "reply": reply}


@router.post("/api/ai-context")
async def ai_context(r: Request):
    d = await r.json()
    message = (d.get("message") or "").strip()
    vehicle = (d.get("vehicle") or "").strip()
    active_tab = (d.get("active_tab") or "").strip()
    image_b64 = (d.get("image_base64") or "").strip()
    if not message and not image_b64:
        raise HTTPException(400, "message or image required")
    if not message:
        message = "Diagnose what you see in this photo."

    # ── Cache lookup (skip for photos) ──
    key = _cache_key("context", [active_tab, vehicle, message])
    if not image_b64:
        hit = _cache_get(key)
        if hit:
            return {
                "success": True,
                "reply": hit["reply"],
                "provider": "cache",
                "tab": active_tab,
                "cached": True,
            }

    context_parts = []
    try:
        from data import (FAULT_CODES, TORQUE_SPECS, OBD_PIDS, WIRING_LIBRARY,
                          BULB_CHART, BATTERY_SIZES, TYRE_SIZES, FUSE_BOXES)
        import json as _j
        q = message.lower()
        if any(w in q for w in ["fault", "code", "p0", "b1", "c0", "u0", "dtc"]):
            hits = {k: v.get("description", "") for k, v in FAULT_CODES.items()
                    if k.lower() in q or any(w in str(v.get("description", "")).lower()
                                             for w in q.split() if len(w) > 4)}
            if hits:
                context_parts.append("Fault codes: " + _j.dumps(dict(list(hits.items())[:15]), default=str)[:2500])
        if any(w in q for w in ["torque", "nm", "bolt", "tighten"]):
            context_parts.append("Torque: " + _j.dumps(dict(list(TORQUE_SPECS.items())[:25]), default=str)[:2500])
        if any(w in q for w in ["pid", "obd"]):
            context_parts.append("OBD PIDs: " + _j.dumps(OBD_PIDS, default=str)[:2500])
        if any(w in q for w in ["wire", "wiring", "circuit"]):
            context_parts.append("Wiring: " + _j.dumps(WIRING_LIBRARY, default=str)[:2500])
        if any(w in q for w in ["bulb", "lamp", "light"]):
            context_parts.append("Bulbs: " + _j.dumps(BULB_CHART, default=str)[:2500])
        if any(w in q for w in ["battery", "amp"]):
            context_parts.append("Batteries: " + _j.dumps(BATTERY_SIZES, default=str)[:2500])
        if any(w in q for w in ["tyre", "tire", "wheel"]):
            context_parts.append("Tyres: " + _j.dumps(TYRE_SIZES, default=str)[:2500])
        if any(w in q for w in ["fuse", "fuses"]):
            context_parts.append("Fuses: " + _j.dumps(FUSE_BOXES, default=str)[:2500])
    except Exception as e:
        print(f"[ai-context] data load: {e}")

    context_block = "\n\n".join(context_parts) if context_parts else "No local data."
    system_msg = (
        "You are RamsTech AI, an expert mechanic in South Africa. Use LOCAL DATA "
        "as authoritative. If not covered, use general knowledge and say so. "
        "Use ZAR. If an image is attached, diagnose what you see."
    )
    user_msg = (
        f"Tab: {active_tab or 'general'}\nVehicle: {vehicle or 'unspecified'}\n\n"
        f"Local data:\n{context_block}\n\nQuestion: {message}"
    )

    try:
        if image_b64:
            import openai
            c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
            rr = c.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_msg},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                            "detail": "high"}},
                    ]},
                ],
                max_tokens=1100,
                temperature=0.2,
            )
            reply = rr.choices[0].message.content
            provider = "openai-vision"
        else:
            reply, provider = _chat(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=1100,
            )
    except Exception as e:
        return {"success": False, "reply": f"AI error: {e}"}

    if not image_b64:
        _cache_set(key, "context", active_tab, vehicle, message, reply, provider)

    return {"success": True, "reply": reply, "provider": provider,
            "tab": active_tab, "context_items": len(context_parts)}
