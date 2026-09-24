from fastapi import APIRouter
from app.services.database_service import DatabaseService

router = APIRouter()
db = DatabaseService()


@router.get("/")
def get_statistics():
    return db.get_statistics()
