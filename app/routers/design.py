"""
app/routers/design.py

POST /api/v1/design/generate
POST /api/v1/design/regenerate/{project_id}
GET  /api/v1/design/{project_id}
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.models.schemas import BuildingParams, DesignResponse
from app.services.structural_engine import run_structural_analysis
from app.services.layout_optimizer import generate_full_design
from app.database import create_project, update_project, get_project

router = APIRouter()


@router.post("/generate", response_model=DesignResponse, summary="Generate optimised building design")
async def generate_design(params: BuildingParams):
    """
    **Core endpoint** — accepts all sidebar parameters and returns:
    - Optimised column grid
    - Structural analysis (IS 456 compliant)
    - Floor plans (room layouts)
    - Material quantities + cost breakdown
    - Before/after comparison
    """
    structural = run_structural_analysis(params)
    design     = generate_full_design(params, structural)

    # Persist in DB (await to ensure it exists for immediate exports)
    if params.project_id:
        await update_project(
            design.project_id,
            params.model_dump(),
            design.model_dump(),
        )
    else:
        await create_project(
            params.model_dump(),
            pid=design.project_id,
            result_dict=design.model_dump(),
        )

    return design


@router.post("/regenerate/{project_id}", response_model=DesignResponse, summary="Re-run optimiser for existing project")
async def regenerate_design(project_id: str, params: BuildingParams):
    """Re-generate design for an existing project ID (e.g. after sidebar changes)."""
    params.project_id = project_id
    return await generate_design(params)


@router.get("/{project_id}", response_model=DesignResponse, summary="Retrieve stored design result")
async def get_design(project_id: str):
    """Retrieve a previously generated design by project ID."""
    row = await get_project(project_id)
    if not row or not row.get("result_json"):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found or not yet generated.")
    import json
    return DesignResponse(**json.loads(row["result_json"]))
