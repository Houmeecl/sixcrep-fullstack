from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(title="Sixcrep · II Región API")

ROOT = Path(__file__).parent.parent

@app.get("/")
async def index():
    return FileResponse(ROOT / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "region": "II Región de Antofagasta"}
