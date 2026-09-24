from datetime import datetime
from typing import List, Dict, Optional


class DatabaseService:
    """In-memory database. Replace with PostgreSQL for production."""

    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self._load_demo()

    def _load_demo(self):
        self.sessions["demo1"] = {
            "id": "demo1",
            "vehicle": "2018 Toyota Hilux",
            "vin": "AHTFR22G50...",
            "started_at": datetime.now().isoformat(),
            "fault_codes": ["P0101", "P0300"],
            "notes": "Rough idle at cold start",
            "technician": "Demo User",
        }

    def save_session(self, session: dict) -> str:
        sid = session.get("id") or f"s{len(self.sessions)+1}"
        session["id"] = sid
        session["saved_at"] = datetime.now().isoformat()
        self.sessions[sid] = session
        return sid

    def get_session(self, sid: str) -> Optional[dict]:
        return self.sessions.get(sid)

    def list_sessions(self) -> List[dict]:
        return list(self.sessions.values())

    def delete_session(self, sid: str) -> bool:
        return self.sessions.pop(sid, None) is not None

    def get_statistics(self) -> dict:
        total = len(self.sessions)
        all_codes = []
        for s in self.sessions.values():
            all_codes.extend(s.get("fault_codes", []))
        code_counts = {}
        for c in all_codes:
            code_counts[c] = code_counts.get(c, 0) + 1
        top = sorted(code_counts.items(), key=lambda x: -x[1])[:5]
        return {
            "total_sessions": total,
            "total_fault_codes": len(all_codes),
            "top_fault_codes": [{"code": c, "count": n} for c, n in top],
  }
