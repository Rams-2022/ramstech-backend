"""
External API integrations: Open Labor Project (OLP) for DTC codes.
Falls back to Supabase if OLP key is missing or the API fails.
"""
import os
import httpx
from fastapi import APIRouter, HTTPException

import db

router = APIRouter(prefix="/workshop/api", tags=["External APIs"])

OLP_API_KEY = os.getenv("OLP_API_KEY", "").strip()
OLP_BASE_URL = "https://openlaborproject.com/api/v1"


@router.get("/dtc/{code}")
async def get_dtc_external(code: str):
    """Look up a DTC code via Open Labor Project.
    If OLP fails or key is missing, fall back to Supabase dtc_codes table."""
    code = code.upper().strip()

    # ── Try OLP first ───────────────────────────────
    if OLP_API_KEY:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    f"{OLP_BASE_URL}/dtc/{code}",
                    headers={"x-api-key": OLP_API_KEY},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {"source": "olp", "data": data}
                elif resp.status_code == 404:
                    # Code doesn't exist in OLP — try Supabase
                    pass
                else:
                    print(f"[olp] HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                print(f"[olp] request failed: {e}")

    # ── Fallback: Supabase ──────────────────────────
    if db.is_ready():
        c = db.get_client()
        r = c.table("dtc_codes").select("*, dtc_repairs(*)")\
            .eq("code", code).execute()
        if r.data:
            row = r.data[0]
            row["dtc_repairs"] = sorted(
                row.get("dtc_repairs", []),
                key=lambda x: x.get("likelihood_rank") or 99,
            )
            return {"source": "supabase", "data": row}

    raise HTTPException(404, f"Code {code} not found in OLP or local database")
