"""
app/routers/interior.py

POST /api/v1/interior/generate
GET  /api/v1/interior/{project_id}
GET  /api/v1/interior/{project_id}/{room}
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import InteriorRequest, InteriorResult
from app.services.interior_service import generate_interior
from app.database import save_interior, get_interiors, get_project

router = APIRouter()


@router.post("/generate", response_model=InteriorResult, summary="Generate interior design for a room")
async def generate_interior_design(req: InteriorRequest):
    """
    Generate furniture placement, lighting specs, and palette for one room.
    Called each time the user clicks **Apply Design** or changes style/room.
    """
    result = generate_interior(req)

    # Persist snapshot if project_id provided
    if req.project_id:
        await save_interior(
            project_id=req.project_id,
            room=req.room.value,
            style=req.style.value,
            req_dict=req.model_dump(),
            result_dict=result.model_dump(),
        )

    return result


@router.get("/{project_id}", summary="Get all interior design snapshots for a project")
async def get_project_interiors(project_id: str):
    """Returns all saved interior design snapshots for a project."""
    if not await get_project(project_id):
        raise HTTPException(404, f"Project '{project_id}' not found")
    snapshots = await get_interiors(project_id)
    import json
    return {
        "project_id": project_id,
        "snapshots": [
            {
                "id":       s["id"],
                "room":     s["room"],
                "style":    s["style"],
                "result":   json.loads(s["result_json"]),
                "created_at": s["created_at"],
            }
            for s in snapshots
        ],
    }


@router.get("/{project_id}/{room}", summary="Get latest interior design for a specific room")
async def get_room_interior(project_id: str, room: str):
    """Returns the most recent interior design snapshot for a given room."""
    snapshots = await get_interiors(project_id)
    room_snaps = [s for s in snapshots if s["room"] == room]
    if not room_snaps:
        raise HTTPException(404, f"No interior design saved for room '{room}' in project '{project_id}'")
    import json
    latest = room_snaps[-1]
    return {
        "project_id": project_id,
        "room":       room,
        "result":     json.loads(latest["result_json"]),
        "created_at": latest["created_at"],
    }
