from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.database_service import DatabaseService

router = APIRouter()
db = DatabaseService()


class SessionModel(BaseModel):
    vehicle: str
    vin: Optional[str] = None
    fault_codes: List[str] = []
    notes: str = ""
    technician: str = ""


@router.get("/")
def list_sessions():
    return {"sessions": db.list_sessions()}


@router.post("/")
def create_session(s: SessionModel):
    sid = db.save_session(s.dict())
    return {"id": sid, "status": "created"}


@router.get("/{sid}")
def get_session(sid: str):
    s = db.get_session(sid)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


@router.delete("/{sid}")
def delete_session(sid: str):
    if not db.delete_session(sid):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}
