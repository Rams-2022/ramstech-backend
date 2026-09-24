from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import os

from app.services.ai_service import AIService
from app.routers import fault_codes, vin, parts, sessions, statistics

app = FastAPI(title="RamsTech API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("RAMSTECH_API_KEY", "ramstech-2024-secret")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "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")


async def verify_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class DiagnosisRequest(BaseModel):
    symptoms: str
    vehicle: Optional[str] = None
    system: Optional[str] = None


@app.get("/")
def root():
    return {"app": "RamsTech API", "version": "1.0.0", "status": "online"}


@app.get("/health")
def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}


@app.post("/api/chat")
async def chat(req: ChatRequest, key: str = Depends(verify_key)):
    try:
        ai = AIService(OPENAI_KEY)
        reply = await ai.chat(req.message, req.context, req.history or [])
        return {"reply": reply, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diagnose")
async def diagnose(req: DiagnosisRequest, key: str = Depends(verify_key)):
    try:
        ai = AIService(OPENAI_KEY)
        result = await ai.diagnose(req.symptoms, req.vehicle, req.system)
        return {"diagnosis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(fault_codes.router, prefix="/api/fault-codes", tags=["Fault Codes"])
app.include_router(vin.router, prefix="/api/vin", tags=["VIN"])
app.include_router(parts.router, prefix="/api/parts", tags=["Parts"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["Statistics"])
