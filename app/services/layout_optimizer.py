"""
app/services/layout_optimizer.py

Generates optimised floor plans (room layout) and detailed cost/material
estimates for the given BuildingParams + StructuralResult.
"""

from __future__ import annotations
import math
import uuid
from typing import NamedTuple

from app.models.schemas import (
    BuildingParams, BHKConfig, FloorConfig,
    ConcreteGrade, SteelGrade,
    RoomLayout, FloorPlan,
    FloorMaterial, CostBreakdown, MaterialSchedule,
    OptimizationComparison, DesignResponse,
    StructuralResult,
)
from app.services.structural_engine import FLOOR_HEIGHTS


# ── Rate schedule (₹ per unit, 2024 India market rates) ──────────────────────

RATES = {
    "concrete_m3":   7_500,    # M25 ready-mix incl. placing
    "steel_kg":      75,       # Fe500 TMT bars
    "brickwork_m3":  4_800,
    "plaster_m2":    180,
    "floor_tile_m2": 350,
    "paint_m2":      90,
    "doors_each":    18_000,
    "windows_each":  8_500,
    "electrical":    1_50_000, # per floor lump
    "plumbing":      1_20_000, # per floor lump
    "foundation_m3": 5_500,    # PCC + RCC combined
}

FLOOR_HEIGHT_M = 3.2   # storey height used for wall calculations


# ── Room templates per BHK ────────────────────────────────────────────────────

def _room_templates(bhk: BHKConfig, L: float, W: float) -> list[dict]:
    """
    Return a list of room dicts for the given BHK config on a L×W plot.
    Positions are approximate; structural grid will clip to column lines.
    """
    if bhk == BHKConfig.BHK1:
        return [
            {"name": "Living / Dining", "w": L * 0.55, "d": W * 0.55},
            {"name": "Bedroom",         "w": L * 0.45, "d": W * 0.55},
            {"name": "Kitchen",         "w": L * 0.35, "d": W * 0.45},
            {"name": "Bathroom",        "w": L * 0.20, "d": W * 0.45},
            {"name": "Toilet",          "w": L * 0.25, "d": W * 0.30},
        ]
    elif bhk == BHKConfig.BHK2:
        return [
            {"name": "Living / Dining", "w": L * 0.55, "d": W * 0.40},
            {"name": "Bedroom 1",       "w": L * 0.45, "d": W * 0.40},
            {"name": "Bedroom 2",       "w": L * 0.45, "d": W * 0.40},
            {"name": "Kitchen",         "w": L * 0.30, "d": W * 0.30},
            {"name": "Bathroom",        "w": L * 0.20, "d": W * 0.23},
            {"name": "Toilet",          "w": L * 0.20, "d": W * 0.23},
        ]
    elif bhk == BHKConfig.BHK3:
        return [
            {"name": "Living / Dining", "w": L * 0.50, "d": W * 0.35},
            {"name": "Master Bedroom",  "w": L * 0.40, "d": W * 0.35},
            {"name": "Bedroom 2",       "w": L * 0.35, "d": W * 0.32},
            {"name": "Bedroom 3",       "w": L * 0.35, "d": W * 0.32},
            {"name": "Kitchen",         "w": L * 0.28, "d": W * 0.28},
            {"name": "Master Bath",     "w": L * 0.18, "d": W * 0.20},
            {"name": "Bathroom",        "w": L * 0.16, "d": W * 0.20},
            {"name": "Toilet",          "w": L * 0.14, "d": W * 0.18},
        ]
    else:  # 4 BHK
        return [
            {"name": "Living Room",     "w": L * 0.48, "d": W * 0.35},
            {"name": "Dining Room",     "w": L * 0.30, "d": W * 0.28},
            {"name": "Master Bedroom",  "w": L * 0.40, "d": W * 0.33},
            {"name": "Bedroom 2",       "w": L * 0.35, "d": W * 0.28},
            {"name": "Bedroom 3",       "w": L * 0.35, "d": W * 0.28},
            {"name": "Bedroom 4",       "w": L * 0.30, "d": W * 0.28},
            {"name": "Kitchen",         "w": L * 0.28, "d": W * 0.26},
            {"name": "Utility",         "w": L * 0.18, "d": W * 0.18},
            {"name": "Master Bath",     "w": L * 0.18, "d": W * 0.20},
            {"name": "Bathroom 2",      "w": L * 0.16, "d": W * 0.20},
            {"name": "Toilet",          "w": L * 0.14, "d": W * 0.18},
        ]


def _snap_to_grid(value: float, positions: list[float]) -> float:
    """Snap a dimension to the nearest column grid interval."""
    return min(positions, key=lambda p: abs(p - value))


def generate_floor_plans(params: BuildingParams, structural: StructuralResult) -> list[FloorPlan]:
    """Generate per-floor room layouts aligned to structural grid."""
    n_floors = FLOOR_HEIGHTS[params.floors]
    templates = _room_templates(params.bhk, params.plot_length, params.plot_width)
    floors: list[FloorPlan] = []

    for f in range(n_floors):
        rooms: list[RoomLayout] = []
        cursor_x, cursor_z = 0.0, 0.0
        row_max_d = 0.0

        for i, t in enumerate(templates):
            w = round(t["w"], 2)
            d = round(t["d"], 2)
            # Wrap to next row if overflows
            if cursor_x + w > params.plot_length + 0.5:
                cursor_x  = 0.0
                cursor_z += row_max_d + 0.05
                row_max_d = 0.0
            rooms.append(RoomLayout(
                name=t["name"],
                width_m=w,
                depth_m=d,
                area_m2=round(w * d, 2),
                position={"x": round(cursor_x, 2), "z": round(cursor_z, 2)},
            ))
            cursor_x  += w + 0.05
            row_max_d  = max(row_max_d, d)

        total_area = round(sum(r.area_m2 for r in rooms), 2)
        label = f"Ground Floor" if f == 0 else f"Floor {f}"
        floors.append(FloorPlan(
            floor_index=f,
            label=label,
            rooms=rooms,
            total_area_m2=total_area,
        ))
    return floors


# ── Material & Cost Estimation ────────────────────────────────────────────────

def _concrete_volume(params: BuildingParams, structural: StructuralResult) -> float:
    """Total concrete volume per floor (m³)."""
    n_cols   = structural.columns.count
    col_size = structural.columns.size_mm / 1000  # m
    col_vol  = n_cols * col_size * col_size * FLOOR_HEIGHT_M

    beam_vol = 0.0
    bw = structural.beams.width_mm  / 1000
    bd = structural.beams.depth_mm  / 1000
    # Beams along X (z-grid count rows of x-spans)
    nzp = len(structural.columns.z_positions)
    nxs = len(structural.columns.x_positions) - 1
    for i in range(nzp):
        for j in range(nxs):
            span = structural.columns.x_positions[j+1] - structural.columns.x_positions[j]
            beam_vol += bw * bd * span

    slab_vol = (params.plot_length * params.plot_width * structural.slab.thickness_mm / 1000)

    return round(col_vol + beam_vol + slab_vol, 2)


def _steel_kg(concrete_m3: float) -> float:
    """Approx steel consumption: 100–130 kg per m³ of RCC (IS practice)."""
    return round(concrete_m3 * 115, 1)


def estimate_materials(params: BuildingParams, structural: StructuralResult) -> MaterialSchedule:
    n_floors = FLOOR_HEIGHTS[params.floors]
    per_floor: list[FloorMaterial] = []
    total_concrete = total_steel = total_brick = total_cost = 0.0

    for f in range(n_floors):
        # Concrete tapers with height (fewer walls higher up)
        factor = 1.0 - f * 0.08
        conc   = round(_concrete_volume(params, structural) * factor, 2)
        steel  = _steel_kg(conc)
        steel_qt = round(steel / 100, 2)  # quintals
        # Brickwork: perimeter × height × wall thickness
        perimeter = 2 * (params.plot_length + params.plot_width)
        brick_vol = round(perimeter * FLOOR_HEIGHT_M * 0.23 * factor, 2)

        # Cost per floor (₹)
        cost_floor = (
            conc   * RATES["concrete_m3"]  +
            steel  * RATES["steel_kg"]     +
            brick_vol * RATES["brickwork_m3"] +
            params.plot_length * params.plot_width * RATES["floor_tile_m2"] +
            params.plot_length * params.plot_width * RATES["paint_m2"] +
            RATES["electrical"] + RATES["plumbing"]
        )
        cost_lakhs = round(cost_floor / 1e5, 2)

        label = "GF" if f == 0 else f"Floor {f}"
        per_floor.append(FloorMaterial(
            floor_label=label,
            concrete_m3=conc,
            steel_quintals=steel_qt,
            brickwork_m3=brick_vol,
            cost_lakhs=cost_lakhs,
        ))
        total_concrete += conc
        total_steel    += steel
        total_brick    += brick_vol
        total_cost     += cost_lakhs

    # Foundation (PCC + RCC footings)
    foundation_vol = params.plot_length * params.plot_width * 0.6
    foundation_cost = round(foundation_vol * RATES["foundation_m3"] / 1e5, 2)

    # Finishing & MEP lump-sum
    finishing = round(params.plot_length * params.plot_width * n_floors * 350 / 1e5, 2)
    mep       = round(n_floors * (RATES["electrical"] + RATES["plumbing"]) / 1e5, 2)

    structure_cost = round(total_cost - mep - finishing, 2)
    masonry_cost   = round(total_brick * RATES["brickwork_m3"] / 1e5, 2)
    grand_total    = round(total_cost + foundation_cost, 2)
    saved          = round(params.budget_lakhs - grand_total, 2)

    return MaterialSchedule(
        per_floor=per_floor,
        totals={
            "concrete_m3":   round(total_concrete, 2),
            "steel_quintals":round(total_steel / 100, 2),
            "brickwork_m3":  round(total_brick, 2),
        },
        cost_breakdown=CostBreakdown(
            foundation=foundation_cost,
            structure=structure_cost,
            masonry=masonry_cost,
            finishing=finishing,
            mep=mep,
            total=grand_total,
            budget=params.budget_lakhs,
            saved=saved,
            within_budget=grand_total <= params.budget_lakhs,
        ),
    )


# ── Optimisation comparison (before vs after) ─────────────────────────────────

def compute_comparison(params: BuildingParams, structural: StructuralResult) -> OptimizationComparison:
    """Simulate a 'naïve' (unoptimised) baseline for comparison."""
    # Baseline: uniform 3m grid regardless of beam span constraint
    nx_base = math.floor(params.plot_length / 3) + 1
    nz_base = math.floor(params.plot_width  / 3) + 1
    cols_before = nx_base * nz_base
    cost_before = round(params.budget_lakhs * 0.97, 2)  # approx 97% of budget
    safety_before = max(60, structural.safety_score - 9)

    mat_saved_pct = round(
        (cols_before - structural.columns.count) / cols_before * 100, 1
    )

    est_cost_after = round(
        params.budget_lakhs - abs(structural.slab.thickness_mm - 100) * 0.01
        - (cols_before - structural.columns.count) * 0.25,
        2,
    )

    return OptimizationComparison(
        before_cost_lakhs=cost_before,
        after_cost_lakhs=est_cost_after,
        before_columns=cols_before,
        after_columns=structural.columns.count,
        before_beam_spans=math.floor(params.max_beam_span) + 1,
        after_beam_spans=math.ceil(structural.beams.span_m),
        before_safety=safety_before,
        after_safety=structural.safety_score,
        material_saved_pct=mat_saved_pct,
    )


# ── Top-level design generator ────────────────────────────────────────────────

def generate_full_design(params: BuildingParams, structural: StructuralResult) -> DesignResponse:
    project_id  = params.project_id or str(uuid.uuid4())
    floor_plans = generate_floor_plans(params, structural)
    materials   = estimate_materials(params, structural)
    comparison  = compute_comparison(params, structural)

    return DesignResponse(
        project_id=project_id,
        structural=structural,
        floor_plans=floor_plans,
        materials=materials,
        comparison=comparison,
        workflow_step=3,
        metadata={
            "plot_area_m2":  round(params.plot_length * params.plot_width, 2),
            "built_area_m2": round(
                params.plot_length * params.plot_width * FLOOR_HEIGHTS[params.floors] * 0.85, 2
            ),
            "fsi":           round(FLOOR_HEIGHTS[params.floors] * 0.85, 2),
            "standard":      "IS 456:2000, IS 875 Part 1 & 2, NBC 2016",
            "seismic_zone":  params.seismic_zone.value,
        },
    )
