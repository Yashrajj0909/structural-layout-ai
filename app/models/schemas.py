"""
app/models/schemas.py
Pydantic v2 request / response schemas for StructAI Designer.
"""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class FloorConfig(str, Enum):
    G1 = "G+1"
    G2 = "G+2"
    G3 = "G+3"
    G4 = "G+4"

class BHKConfig(str, Enum):
    BHK1 = "1 BHK"
    BHK2 = "2 BHK"
    BHK3 = "3 BHK"
    BHK4 = "4 BHK"

class BuildingStyle(str, Enum):
    MODERN      = "Modern"
    TRADITIONAL = "Traditional"
    COLONIAL    = "Colonial"
    MINIMALIST  = "Minimalist"

class ConcreteGrade(str, Enum):
    M20 = "M20"
    M25 = "M25"
    M30 = "M30"
    M35 = "M35"

class SteelGrade(str, Enum):
    FE415 = "Fe415"
    FE500 = "Fe500"
    FE550 = "Fe550"

class RoomType(str, Enum):
    LIVING   = "living"
    BEDROOM1 = "bedroom1"
    BEDROOM2 = "bedroom2"
    KITCHEN  = "kitchen"
    BATHROOM = "bathroom"
    EXTERIOR = "exterior"

class InteriorStyle(str, Enum):
    MODERN  = "modern"
    WARM    = "warm"
    LUXURY  = "luxury"
    NATURE  = "nature"

class SeismicZone(str, Enum):
    ZONE_II  = "II"
    ZONE_III = "III"
    ZONE_IV  = "IV"
    ZONE_V   = "V"

class ExportFormat(str, Enum):
    PDF = "pdf"
    DWG = "dwg"
    XLS = "xls"
    GLB = "glb"


# ── Building Parameters (sidebar inputs) ─────────────────────────────────────

class BuildingParams(BaseModel):
    """Full building parameter payload from the sidebar."""
    plot_length:        float        = Field(12.0, ge=5,  le=50,  description="Plot length in metres")
    plot_width:         float        = Field(9.0,  ge=4,  le=40,  description="Plot width in metres")
    floors:             FloorConfig  = Field(FloorConfig.G2,       description="Number of floors above ground")
    bhk:                BHKConfig    = Field(BHKConfig.BHK2,       description="Flat configuration")
    style:              BuildingStyle= Field(BuildingStyle.MODERN,  description="Architectural style")
    max_beam_span:      float        = Field(5.0,  ge=3,  le=8,   description="Max beam span in metres")
    column_spacing:     float        = Field(3.0,  ge=2,  le=6,   description="Column spacing in metres")
    allowable_deflection: float      = Field(25.0, ge=5,  le=50,  description="Allowable deflection in mm")
    concrete_grade:     ConcreteGrade= Field(ConcreteGrade.M25,    description="Concrete grade")
    steel_grade:        SteelGrade   = Field(SteelGrade.FE500,     description="Steel grade")
    budget_lakhs:       float        = Field(45.0, ge=5,  le=500, description="Budget in Indian Rupees Lakhs")
    seismic_zone:       SeismicZone  = Field(SeismicZone.ZONE_III, description="IS 1893 seismic zone")
    project_id:         str | None   = Field(None, description="Existing project ID to update")

    @model_validator(mode="after")
    def validate_plot(self):
        if self.plot_length < self.plot_width:
            # swap so length is always the longer dimension
            self.plot_length, self.plot_width = self.plot_width, self.plot_length
        return self


# ── Structural Results ────────────────────────────────────────────────────────

class ColumnGrid(BaseModel):
    x_positions: list[float]
    z_positions: list[float]
    count:       int
    size_mm:     int = 300

class BeamSpec(BaseModel):
    span_m:       float
    width_mm:     int
    depth_mm:     int
    reinforcement: str

class SlabSpec(BaseModel):
    thickness_mm: int
    type:         str   = "Two-way"

class StructuralResult(BaseModel):
    columns:           ColumnGrid
    beams:             BeamSpec
    slab:              SlabSpec
    max_beam_span_m:   float
    actual_deflection_mm: float
    column_load_kn:    float
    shear_capacity_kn: float
    safety_score:      int          = Field(..., ge=0, le=100)
    safety_status:     str
    compliance:        dict[str, bool]
    warnings:          list[str]


# ── Cost & Material ──────────────────────────────────────────────────────────

class FloorMaterial(BaseModel):
    floor_label:      str
    concrete_m3:      float
    steel_quintals:   float
    brickwork_m3:     float
    cost_lakhs:       float

class CostBreakdown(BaseModel):
    foundation:        float
    structure:         float
    masonry:           float
    finishing:         float
    mep:               float          # Mechanical / Electrical / Plumbing
    total:             float
    budget:            float
    saved:             float
    within_budget:     bool

class MaterialSchedule(BaseModel):
    per_floor:         list[FloorMaterial]
    totals:            dict[str, float]
    cost_breakdown:    CostBreakdown


# ── Full Design Response ──────────────────────────────────────────────────────

class RoomLayout(BaseModel):
    name:        str
    width_m:     float
    depth_m:     float
    area_m2:     float
    position:    dict[str, float]   # {x, z} origin

class FloorPlan(BaseModel):
    floor_index: int
    label:       str
    rooms:       list[RoomLayout]
    total_area_m2: float

class OptimizationComparison(BaseModel):
    before_cost_lakhs:  float
    after_cost_lakhs:   float
    before_columns:     int
    after_columns:      int
    before_beam_spans:  int
    after_beam_spans:   int
    before_safety:      int
    after_safety:       int
    material_saved_pct: float

class DesignResponse(BaseModel):
    project_id:         str
    structural:         StructuralResult
    floor_plans:        list[FloorPlan]
    materials:          MaterialSchedule
    comparison:         OptimizationComparison
    workflow_step:      int = 3
    metadata:           dict[str, Any]


# ── Interior Design ──────────────────────────────────────────────────────────

class InteriorRequest(BaseModel):
    room:         RoomType         = RoomType.LIVING
    style:        InteriorStyle    = InteriorStyle.MODERN
    wall_color:   str              = Field("#F5F0E8", pattern=r"^#[0-9A-Fa-f]{6}$")
    floor_color:  str              = Field("#C8A26A", pattern=r"^#[0-9A-Fa-f]{6}$")
    ceiling_color:str              = Field("#FFFFFF",  pattern=r"^#[0-9A-Fa-f]{6}$")
    furnishings:  list[str]        = Field(default_factory=lambda: ["sofa","chairs","plants","lighting"])
    project_id:   str | None       = None

class FurnitureItem(BaseModel):
    id:           str
    type:         str
    position:     dict[str, float]   # {x, y, z}
    dimensions:   dict[str, float]   # {w, h, d}
    color_hex:    str
    material:     str

class LightingSpec(BaseModel):
    type:         str
    position:     dict[str, float]
    color_temp_k: int
    intensity:    float

class InteriorResult(BaseModel):
    room:         RoomType
    style:        InteriorStyle
    colors:       dict[str, str]
    furniture:    list[FurnitureItem]
    lighting:     list[LightingSpec]
    area_m2:      float
    estimated_cost_lakhs: float
    tips:         list[str]


# ── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    project_id:   str
    format:       ExportFormat
    include_interior: bool = True

class ExportResponse(BaseModel):
    download_url: str
    filename:     str
    size_kb:      float
    format:       ExportFormat


# ── Project ──────────────────────────────────────────────────────────────────

class ProjectSummary(BaseModel):
    id:           str
    name:         str
    bhk:          str
    floors:       str
    cost_lakhs:   float
    safety_score: int
    created_at:   str
    updated_at:   str

class ProjectListResponse(BaseModel):
    projects:     list[ProjectSummary]
    total:        int
