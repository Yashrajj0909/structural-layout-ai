"""
app/routers/projects.py

GET    /api/v1/projects/
POST   /api/v1/projects/
GET    /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import ProjectSummary, ProjectListResponse
from app.database import list_projects, get_project, create_project, delete_project

router = APIRouter()


class NewProjectRequest(BaseModel):
    name: str | None = None


@router.get("/", response_model=ProjectListResponse, summary="List all projects")
async def list_all_projects(limit: int = 20):
    rows = await list_projects(limit=limit)
    projects: list[ProjectSummary] = []
    for r in rows:
        result_json = r.get("result_json") or "{}"
        result = json.loads(result_json) if result_json else {}
        struct = result.get("structural", {})
        cost   = result.get("materials", {}).get("cost_breakdown", {})
        params = json.loads(r.get("params_json", "{}"))
        projects.append(ProjectSummary(
            id=r["id"],
            name=r["name"],
            bhk=params.get("bhk", "2 BHK"),
            floors=params.get("floors", "G+2"),
            cost_lakhs=cost.get("total", 0.0),
            safety_score=struct.get("safety_score", 0),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        ))
    return ProjectListResponse(projects=projects, total=len(projects))


@router.get("/{project_id}", summary="Get a single project")
async def get_single_project(project_id: str):
    row = await get_project(project_id)
    if not row:
        raise HTTPException(404, f"Project '{project_id}' not found")
    return {
        "id":         row["id"],
        "name":       row["name"],
        "params":     json.loads(row["params_json"]),
        "result":     json.loads(row["result_json"]) if row.get("result_json") else None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.delete("/{project_id}", summary="Delete a project")
async def delete_single_project(project_id: str):
    deleted = await delete_project(project_id)
    if not deleted:
        raise HTTPException(404, f"Project '{project_id}' not found")
    return {"deleted": True, "id": project_id}
