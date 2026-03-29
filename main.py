"""
StructAI Designer — FastAPI Backend
Smart House Layout Optimization System

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Interactive Documentation:
    http://localhost:8000/docs
    http://localhost:8000/redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routers import (
    design,
    structural,
    interior,
    export,
    projects,
    soil,
)
from app.database import init_db

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await init_db()
    yield
    # Shutdown logic (none for now)

# ── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="StructAI Designer API",
    lifespan=lifespan,
    description="""
## Smart House Layout Optimization System

A full-stack structural engineering AI backend that powers:

- **Design Generation** — AI-optimized column/beam/slab layouts
- **Structural Analysis** — IS 456 / IS 875 compliant safety checks
- **Cost Estimation** — Material BOQ with per-floor breakdowns
- **Interior Design** — Style-aware room configuration generation
- **Export** — PDF reports, CAD data, material schedules

### Standards Compliance
- IS 456:2000 (Plain and Reinforced Concrete)
- IS 875 Part 1 & 2 (Dead & Live Loads)
- NBC 2016 (National Building Code of India)
""",
    version="2.1.0",
    contact={"name": "StructAI Team", "email": "team@structai.in"},
    license_info={"name": "MIT"},
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://structai-designer.onrender.com"],          # allow all for flexibility, specifically adding the production URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(design.router,     prefix="/api/v1/design",     tags=["Design"])
app.include_router(structural.router, prefix="/api/v1/structural", tags=["Structural Analysis"])
app.include_router(interior.router,   prefix="/api/v1/interior",   tags=["Interior Design"])
app.include_router(export.router,     prefix="/api/v1/export",     tags=["Export"])
app.include_router(projects.router,   prefix="/api/v1/projects",   tags=["Projects"])
app.include_router(soil.router,       prefix="/api/v1/soil",       tags=["Soil & FSI"])

# ── Static / Frontend ────────────────────────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/soil", include_in_schema=False)
    async def serve_soil_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "soil.html"))

    @app.get("/floorplan", include_in_schema=False)
    async def serve_floorplan_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "floorplan.html"))

    @app.get("/column-grid", include_in_schema=False)
    async def serve_column_grid_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "column_grid.html"))

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "2.1.0", "engine": "active"}
