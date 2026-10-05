"""AI endpoints: fault code explain, symptom search, context chat."""
import os
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()


def _chat(messages, max_tokens=900, temperature=0.2):
    """Try OpenAI, fall back to Groq. Returns (text, provider)."""
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
            print(f"[ai] openai fail: {type(e).__name__}: {e}")

    if GROQ_KEY:
        try:
            import openai
            c = openai.OpenAI(base_url="https://api.groq.com/openai/v1",
                              api_key=GROQ_KEY, timeout=45.0)
            r = c.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return r.choices[0].message.content, "groq"
        except Exception as e:
            print(f"[ai] groq fail: {type(e).__name__}: {e}")

    raise RuntimeError("No AI provider available")


@router.post("/api/fault-codes/ai")
async def fault_code_ai(r: Request):
    d = await r.json()
    code = (d.get("code") or "").upper().strip().replace(" ", "").replace("-", "")
    vehicle = (d.get("vehicle") or "").strip()
    if not code:
        raise HTTPException(400, "code is required")

    local = {}
    try:
        from data import FAULT_CODES
        local = FAULT_CODES.get(code) or {}
    except Exception:
        pass
    local_desc = local.get("description", "")

    system_msg = (
        "You are RamsTech AI, a master mechanic in South Africa. Explain a diagnostic "
        "trouble code to a mechanic. Structure your answer:\n"
        "1. MEANING — what the code means in plain English\n"
        "2. LIKELY CAUSES — ranked most to least common\n"
        "3. TESTS TO PERFORM — numbered steps with tool needed for each\n"
        "4. REPAIRS — what to replace/repair with approximate ZAR costs\n"
        "Add a SAFETY line if there are high-voltage, fuel, or hot-surface hazards. "
        "Under 400 words. If unsure of a torque spec, say 'refer to OEM manual'."
    )
    user_msg = (
        f"Fault code: {code}\n"
        f"Vehicle: {vehicle or 'not specified'}\n"
        f"Local description: {local_desc or 'not in local DB'}\n\n"
        f"Give me the meaning, causes, tests, and repairs."
    )

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

    return {"success": True, "code": code, "description": local_desc,
            "provider": provider, "reply": reply}


@router.post("/api/fault-codes/ai-search")
async def fault_code_ai_search(r: Request):
    d = await r.json()
    query = (d.get("query") or "").strip()
    vehicle = (d.get("vehicle") or "").strip()
    if not query:
        raise HTTPException(400, "query is required")

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
        "You are RamsTech AI, a diagnostic technician. From the symptom, suggest "
        "3-7 most likely OBD-II codes. For each: code, short title, why it fits. "
        "Then a DIAGNOSTIC PATH: which to check first and one test. "
        "Only use real OBD-II codes (P/B/C/U). Under 350 words."
    )
    user_msg = (
        f"Symptom: {query}\nVehicle: {vehicle or 'unspecified'}\n"
        f"Local matches: {', '.join(m['code'] for m in local_matches) or 'none'}"
    )

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

    return {"success": True, "query": query, "provider": provider,
            "local_matches": local_matches, "reply": reply}


@router.post("/api/ai-context")
async def ai_context(r: Request):
    d = await r.json()
    message = (d.get("message") or "").strip()
    image_b64 = (d.get("image_base64") or "").strip()
    vehicle = (d.get("vehicle") or "").strip()
    active_tab = (d.get("active_tab") or "").strip()
    if not message:
        raise HTTPException(400, "message is required")

    context_parts = []
   try:
    if image_b64:
        if len(image_b64) > 7_000_000:
            raise HTTPException(413, "Image too large")
        import openai
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        r = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": [
                    {"type": "text", "text": user_msg},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "high"
                    }},
                ]},
            ],
            max_tokens=1100,
            temperature=0.2,
        )
        reply = r.choices[0].message.content
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

        q = message.lower()
        if any(w in q for w in ["fault", "code", "p0", "b1", "c0", "u0", "dtc"]):
            hits = {k: v.get("description", "") for k, v in FAULT_CODES.items()
                    if k.lower() in q or any(w in str(v.get("description", "")).lower()
                                             for w in q.split() if len(w) > 4)}
            if hits:
                context_parts.append("Fault codes: " + _c(dict(list(hits.items())[:15])))
        if any(w in q for w in ["torque", "nm", "bolt", "tighten"]):
            context_parts.append("Torque specs: " + _c(dict(list(TORQUE_SPECS.items())[:25])))
        if any(w in q for w in ["pid", "obd", "live data"]):
            context_parts.append("OBD PIDs: " + _c(OBD_PIDS))
        if any(w in q for w in ["wire", "wiring", "circuit"]):
            context_parts.append("Wiring: " + _c(WIRING_LIBRARY))
        if any(w in q for w in ["bulb", "lamp", "light"]):
            context_parts.append("Bulbs: " + _c(BULB_CHART))
        if any(w in q for w in ["battery", "amp"]):
            context_parts.append("Batteries: " + _c(BATTERY_SIZES))
        if any(w in q for w in ["tyre", "tire", "wheel"]):
            context_parts.append("Tyres: " + _c(TYRE_SIZES))
        if any(w in q for w in ["fuse", "fuses"]):
            context_parts.append("Fuses: " + _c(FUSE_BOXES))
    except Exception as e:
        print(f"[ai-context] data load fail: {e}")

    system_msg = (
        "You are RamsTech AI, an expert mechanic in South Africa. Use LOCAL DATA "
        "below as authoritative. If not covered, use general knowledge and say so. "
        "Never invent torque specs, fuse ratings, or part numbers. Use ZAR."
    )
    context_block = "\n\n".join(context_parts) if context_parts else "No specific data."
    user_msg = (
        f"Tab: {active_tab or 'general'}\n"
        f"Vehicle: {vehicle or 'unspecified'}\n\n"
        f"Local data:\n{context_block}\n\n"
        f"Question: {message}"
    )

    try:
        reply, provider = _chat(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1100,
        )
    except Exception as e:
        return {"success": False, "reply": f"AI error: {e}"}

    return {"success": True, "reply": reply, "provider": provider,
            "tab": active_tab, "context_items": len(context_parts)}
