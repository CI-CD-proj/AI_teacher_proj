from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.db import Base, engine

Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{full_path:path}")
def spa(full_path: str, request: Request):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")
