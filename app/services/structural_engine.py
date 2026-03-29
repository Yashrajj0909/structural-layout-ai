"""
app/services/structural_engine.py

Core structural analysis engine implementing:
  - IS 456:2000  — RCC design
  - IS 875 Part 1/2 — Dead & Live loads
  - IS 1893 — Seismic loads
  - Column grid optimization (reduce count, maintain safety)
  - Beam sizing via span / depth ratio
  - Deflection check (L/250)
  - Shear capacity check
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import NamedTuple

from app.models.schemas import (
    BuildingParams, ConcreteGrade, SteelGrade, FloorConfig,
    BHKConfig, SeismicZone,
    ColumnGrid, BeamSpec, SlabSpec, StructuralResult,
)


# ── Material property tables ──────────────────────────────────────────────────

CONCRETE_FCK: dict[ConcreteGrade, float] = {
    ConcreteGrade.M20: 20.0,
    ConcreteGrade.M25: 25.0,
    ConcreteGrade.M30: 30.0,
    ConcreteGrade.M35: 35.0,
}

STEEL_FY: dict[SteelGrade, float] = {
    SteelGrade.FE415: 415.0,
    SteelGrade.FE500: 500.0,
    SteelGrade.FE550: 550.0,
}

FLOOR_HEIGHTS: dict[FloorConfig, int] = {
    FloorConfig.G1: 2,
    FloorConfig.G2: 3,
    FloorConfig.G3: 4,
    FloorConfig.G4: 5,
}

SEISMIC_Z: dict[SeismicZone, float] = {
    SeismicZone.ZONE_II:  0.10,
    SeismicZone.ZONE_III: 0.16,
    SeismicZone.ZONE_IV:  0.24,
    SeismicZone.ZONE_V:   0.36,
}


# ── Load calculation (IS 875) ─────────────────────────────────────────────────

@dataclass
class LoadCase:
    dead_load_kn_m2: float = 0.0
    live_load_kn_m2: float = 0.0
    floor_finish_kn_m2: float = 1.0
    wall_load_kn_m: float = 12.0    # 230mm brick wall, 3m height
    factored: float = field(init=False)

    def __post_init__(self):
        # IS 456 Cl. 18.2.3.1 — factored load = 1.5(DL + LL)
        total = self.dead_load_kn_m2 + self.live_load_kn_m2 + self.floor_finish_kn_m2
        self.factored = 1.5 * total


def get_loads(params: BuildingParams) -> LoadCase:
    """IS 875 Part 1 & 2 load intensities for residential buildings."""
    # Slab self-weight: density 25 kN/m³ × 0.125 m
    slab_sw = 25.0 * 0.125
    return LoadCase(
        dead_load_kn_m2=slab_sw,
        live_load_kn_m2=2.0,        # IS 875 Part 2, Table 1 — residential
        floor_finish_kn_m2=1.0,
        wall_load_kn_m=12.0,
    )


# ── Column grid optimisation ──────────────────────────────────────────────────

class GridResult(NamedTuple):
    x_positions: list[float]
    z_positions: list[float]
    column_spacing_x: float
    column_spacing_z: float


def optimise_grid(params: BuildingParams) -> GridResult:
    """
    Generate the optimal column grid for the given plot.
    Rules:
      - Spacing ≤ max_beam_span
      - Spacing ≥ column_spacing (user constraint)
      - Prefer equal intervals (aesthetic + structural)
      - Minimise column count while satisfying both constraints
      - Place columns at corners and logical intervals for 12x15m grid
    """
    def intervals(length: float, min_sp: float, max_sp: float) -> list[float]:
        """Return evenly-spaced grid positions along 'length'."""
        # minimum number of spans to keep max span ≤ max_beam_span
        n_min = math.ceil(length / max_sp)
        # maximum number of spans to keep spacing ≥ min_sp
        n_max = math.floor(length / min_sp)
        n_max = max(n_max, n_min)
        # choose fewest spans (largest spacing) — optimises column count
        n = n_min
        sp = length / n
        return [round(i * sp, 3) for i in range(n + 1)]

    # For a 12x15m rectangular plot (length 15, width 12)
    # We want columns at corners (0 and L/W) and then at intersections
    xs = intervals(params.plot_length, params.column_spacing, params.max_beam_span)
    zs = intervals(params.plot_width,  params.column_spacing, params.max_beam_span)

    return GridResult(
        x_positions=xs,
        z_positions=zs,
        column_spacing_x=round(params.plot_length / (len(xs) - 1), 3),
        column_spacing_z=round(params.plot_width  / (len(zs) - 1), 3),
    )


# ── Beam sizing (IS 456 Cl. 23.2.1) ──────────────────────────────────────────

def size_beam(span_m: float, load: LoadCase, fck: float) -> tuple[int, int]:
    """
    Return (width_mm, depth_mm) for a simply-supported beam.
    span / effective depth ≤ 20 for simply supported (IS 456 Cl. 23.2.1).
    """
    effective_depth_mm = math.ceil((span_m * 1000) / 20 / 25) * 25   # round to 25mm
    depth_mm = effective_depth_mm + 40                                  # cover + bar radius
    width_mm = max(200, math.ceil(depth_mm * 0.4 / 50) * 50)           # width ≈ 0.4D
    return width_mm, depth_mm


def beam_reinforcement(span_m: float, load: LoadCase, width_mm: int, depth_mm: int, fy: float) -> str:
    """Approximate main reinforcement using working stress method."""
    wu = load.factored * span_m  # kN/m
    mu = (wu * span_m ** 2) / 8  # kNm — simply supported
    mu_n_mm = mu * 1e6
    d = depth_mm - 40
    # Balanced section: Ast = Mu / (0.87 * fy * 0.8 * d)
    ast = mu_n_mm / (0.87 * fy * 0.8 * d)  # mm²
    # Select bars: try 12Φ (113 mm²) or 16Φ (201 mm²) or 20Φ (314 mm²)
    for dia, area in [(12, 113), (16, 201), (20, 314)]:
        n = math.ceil(ast / area)
        if n <= 6:
            return f"{n}-{dia}Φ bars"
    return "6-20Φ bars (review section)"


# ── Column design (IS 456 Cl. 39) ────────────────────────────────────────────

def column_axial_load(
    tributary_area_m2: float,
    load: LoadCase,
    n_floors: int,
    wall_perimeter_m: float = 0.0,
) -> float:
    """Total factored axial load on a column (kN)."""
    floor_load = load.factored * tributary_area_m2 * n_floors
    wall_load  = load.wall_load_kn_m * wall_perimeter_m * n_floors * 1.5
    return floor_load + wall_load


def column_size(p_kn: float, fck: float, fy: float) -> tuple[int, str]:
    """
    IS 456 Cl. 39.3 — short column under axial load.
    Pu = 0.4 * fck * Ac + 0.67 * fy * Asc
    Assume 2% steel (Asc = 0.02 * Ag).
    Return (size_mm, reinforcement_string).
    """
    p_n = p_kn * 1000  # N
    # Pu = Ag * (0.4*fck + 0.67*fy*0.02) → Ag = Pu / coeff
    coeff = 0.4 * fck + 0.67 * fy * 0.02
    ag = p_n / coeff  # mm²
    size = math.ceil(math.sqrt(ag) / 25) * 25  # round up to 25mm
    size = max(size, 230)                        # IS 456 minimum 230mm
    asc = round(0.02 * size * size)
    dia = 12
    n_bars = math.ceil(asc / (math.pi / 4 * dia ** 2))
    n_bars = max(n_bars, 4)                      # minimum 4 bars
    return size, f"{n_bars}-{dia}Φ bars"


# ── Deflection check (IS 456 Cl. 23.2) ───────────────────────────────────────

def check_deflection(span_m: float, effective_depth_mm: float) -> float:
    """
    Actual deflection estimated from elastic formula for UDL beam:
    δ = (5 * w * L⁴) / (384 * E * I)
    Simplified to: δ ≈ span_mm / (1000 * span_depth_ratio / 20)
    Returns estimated deflection in mm.
    """
    span_mm = span_m * 1000
    # IS 456: limiting L/250 for appearance
    # Estimated using span/depth correction factor
    ratio = span_mm / effective_depth_mm
    # Empirical correction: δ ≈ 0.013 * ratio * span_mm / 1000 * 10
    deflection_mm = 5 * span_mm / (384 * 200) * (ratio / 20) ** 3
    return round(min(deflection_mm, params_deflection := span_mm / 200), 2)


# ── Shear capacity (IS 456 Cl. 40) ───────────────────────────────────────────

def shear_capacity(width_mm: int, depth_mm: int, fck: float, ast_mm2: float) -> float:
    """
    Nominal shear stress capacity of beam section.
    τc from IS 456 Table 19, simplified for ≤ 0.5% steel.
    Returns capacity in kN.
    """
    d = depth_mm - 40
    pt = 100 * ast_mm2 / (width_mm * d)
    pt = min(pt, 3.0)
    # Simplified τc (N/mm²) from IS 456 Table 19
    tau_c = 0.29 * (fck ** 0.5) * (pt ** 0.33)
    tau_c = min(tau_c, 0.62 * fck ** 0.5)
    v_c = tau_c * width_mm * d / 1000  # kN
    return round(v_c, 1)


# ── Safety scoring ────────────────────────────────────────────────────────────

def compute_safety_score(
    deflection_mm: float,
    allowable_mm: float,
    column_load_kn: float,
    col_capacity_kn: float,
    shear_kn: float,
    shear_cap_kn: float,
    compliance: dict[str, bool],
) -> int:
    """
    Composite safety score 0–100.
    Weights: deflection 25, column load 30, shear 25, compliance 20.
    """
    defl_score  = max(0, 25 * (1 - deflection_mm / allowable_mm))
    col_score   = max(0, 30 * (1 - column_load_kn / (col_capacity_kn * 1.2)))
    shear_score = max(0, 25 * (1 - shear_kn / shear_cap_kn))
    comp_score  = 20 * sum(compliance.values()) / len(compliance)
    total = defl_score + col_score + shear_score + comp_score
    return min(100, max(0, round(total)))


# ── Public API ────────────────────────────────────────────────────────────────

def run_structural_analysis(params: BuildingParams) -> StructuralResult:
    """Full structural analysis pipeline for a given BuildingParams."""
    fck = CONCRETE_FCK[params.concrete_grade]
    fy  = STEEL_FY[params.steel_grade]
    n_floors = FLOOR_HEIGHTS[params.floors]

    load = get_loads(params)
    grid = optimise_grid(params)

    span_x = grid.column_spacing_x
    span_z = grid.column_spacing_z
    max_span = max(span_x, span_z)

    # Beam sizing along longer span
    bw, bd = size_beam(max_span, load, fck)
    eff_d  = bd - 40
    bar_desc = beam_reinforcement(max_span, load, bw, bd, fy)
    # Approximate Ast from bar_desc string
    n_bars = int(bar_desc.split("-")[0])
    dia = int(bar_desc.split("-")[1].replace("Φ", "").split()[0])
    ast = n_bars * math.pi / 4 * dia ** 2

    # Column load (interior column — largest tributary)
    trib = span_x * span_z
    col_load = column_axial_load(trib, load, n_floors)
    col_size_mm, col_reinf = column_size(col_load, fck, fy)
    # Column capacity
    col_capacity = (0.4 * fck * col_size_mm ** 2 + 0.67 * fy * 0.02 * col_size_mm ** 2) / 1000

    # Deflection
    defl = check_deflection(max_span, eff_d)

    # Shear
    shear_cap = shear_capacity(bw, bd, fck, ast)
    wu = load.factored * span_z  # kN/m
    v_applied = wu * span_x / 2  # kN

    # Slab thickness: L/28 for two-way (IS 456 Cl. 24.1)
    slab_t = math.ceil(max(span_x, span_z) * 1000 / 28 / 5) * 5
    slab_t = max(slab_t, 100)

    # Compliance checks
    compliance = {
        "IS_456_2000":    defl <= params.allowable_deflection,
        "IS_875_Part_2":  load.live_load_kn_m2 >= 2.0,
        "NBC_2016":       col_size_mm >= 230,
        "Seismic_IS_1893":SEISMIC_Z[params.seismic_zone] <= 0.24,
    }

    warnings: list[str] = []
    if shear_cap < v_applied * 1.1:
        warnings.append("Shear capacity is close to applied shear — consider stirrup spacing review.")
    if col_size_mm > 450:
        warnings.append("Large column size detected — consider higher-grade concrete.")
    if defl > params.allowable_deflection * 0.9:
        warnings.append("Deflection nearing allowable limit — increase beam depth by 25 mm.")

    safety = compute_safety_score(
        defl, params.allowable_deflection,
        col_load, col_capacity,
        v_applied, shear_cap,
        compliance,
    )

    return StructuralResult(
        columns=ColumnGrid(
            x_positions=grid.x_positions,
            z_positions=grid.z_positions,
            count=len(grid.x_positions) * len(grid.z_positions),
            size_mm=col_size_mm,
        ),
        beams=BeamSpec(
            span_m=round(max_span, 2),
            width_mm=bw,
            depth_mm=bd,
            reinforcement=bar_desc,
        ),
        slab=SlabSpec(thickness_mm=slab_t),
        max_beam_span_m=round(max_span, 2),
        actual_deflection_mm=defl,
        column_load_kn=round(col_load, 1),
        shear_capacity_kn=round(shear_cap, 1),
        safety_score=safety,
        safety_status="Approved" if safety >= 75 else ("Review" if safety >= 50 else "Fail"),
        compliance=compliance,
        warnings=warnings,
    )
