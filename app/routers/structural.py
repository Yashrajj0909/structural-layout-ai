"""
app/routers/structural.py

POST /api/v1/structural/analyze
POST /api/v1/structural/check-compliance
GET  /api/v1/structural/column/{project_id}/{col_id}
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import BuildingParams, StructuralResult
from app.services.structural_engine import run_structural_analysis, CONCRETE_FCK, STEEL_FY
from app.database import get_project
import json

router = APIRouter()


@router.post("/analyze", response_model=StructuralResult, summary="Run structural analysis only")
async def analyze(params: BuildingParams):
    """
    Run full IS 456 structural analysis without generating floor plans.
    Useful for live recalculation as the user adjusts sliders.
    """
    return run_structural_analysis(params)


class ComplianceCheck(BaseModel):
    beam_span_m:       float
    beam_depth_mm:     int
    slab_thickness_mm: int
    deflection_mm:     float
    allowable_mm:      float
    column_size_mm:    int

class ComplianceResult(BaseModel):
    span_depth_ratio:  float
    span_depth_ok:     bool    # IS 456 Cl. 23.2.1: ≤ 20
    deflection_ok:     bool    # L/250
    slab_ok:           bool    # ≥ L/28
    column_min_ok:     bool    # ≥ 230mm IS 456
    overall:           bool
    notes:             list[str]

@router.post("/check-compliance", response_model=ComplianceResult, summary="Check IS 456 compliance for custom values")
async def check_compliance(data: ComplianceCheck):
    ratio = (data.beam_span_m * 1000) / data.beam_depth_mm
    notes = []
    if ratio > 20:
        notes.append(f"Span/depth ratio {ratio:.1f} exceeds IS 456 limit of 20 — increase beam depth.")
    if data.deflection_mm > data.allowable_mm:
        notes.append(f"Deflection {data.deflection_mm} mm exceeds allowable {data.allowable_mm} mm.")
    if data.slab_thickness_mm < data.beam_span_m * 1000 / 28:
        notes.append("Slab thickness below IS 456 Cl. 24.1 minimum.")
    if data.column_size_mm < 230:
        notes.append("Column size < 230 mm minimum per IS 456.")

    return ComplianceResult(
        span_depth_ratio=round(ratio, 2),
        span_depth_ok=ratio <= 20,
        deflection_ok=data.deflection_mm <= data.allowable_mm,
        slab_ok=data.slab_thickness_mm >= data.beam_span_m * 1000 / 28,
        column_min_ok=data.column_size_mm >= 230,
        overall=len(notes) == 0,
        notes=notes,
    )


@router.get("/column/{project_id}/{xi}/{zi}", summary="Get column detail for clickable 3D inspection")
async def get_column_detail(project_id: str, xi: int, zi: int):
    """
    Returns detailed data for a clicked column — mirrors what the
    frontend shows in the colInfoBox panel.
    """
    row = await get_project(project_id)
    if not row or not row.get("result_json"):
        raise HTTPException(404, "Project not found")

    result = json.loads(row["result_json"])
    structural = result["structural"]
    cols = structural["columns"]

    if xi >= len(cols["x_positions"]) or zi >= len(cols["z_positions"]):
        raise HTTPException(400, "Column index out of range")

    rows_label = ["A", "B", "C", "D", "E", "F"]
    col_label  = ["1", "2", "3", "4", "5", "6"]

    # Approximate load based on grid position (interior cols carry more)
    n_cols_x = len(cols["x_positions"])
    n_cols_z = len(cols["z_positions"])
    is_interior = 0 < xi < n_cols_x - 1 and 0 < zi < n_cols_z - 1
    load_kn = structural["column_load_kn"] * (1.15 if is_interior else 0.7)

    return {
        "id": f"C-{rows_label[xi]}{col_label[zi]}",
        "grid": f"X{xi+1}-Z{zi+1}",
        "position": {
            "x": cols["x_positions"][xi],
            "z": cols["z_positions"][zi],
        },
        "size_mm": cols["size_mm"],
        "load_kn": round(load_kn, 1),
        "type": "Interior" if is_interior else "Corner/Edge",
        "concrete": structural["columns"].get("concrete", "M25"),
        "reinforcement": "4-12Φ bars",
        "floor_count": result["metadata"].get("fsi", 3),
    }
