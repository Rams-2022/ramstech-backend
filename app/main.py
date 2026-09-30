# main.py — FastAPI app entry point
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import init
from app.ui import HTML

init()

app = FastAPI(title="RamsTech", version="17.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/", response_class=HTMLResponse)
async def home(): return HTML
