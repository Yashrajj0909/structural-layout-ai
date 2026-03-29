"""
tests/test_api.py

Run with:  pytest tests/ -v
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import pytest_asyncio

# patch DB path before importing app
import sys, os
os.environ["STRUCTAI_TEST"] = "1"

from main import app


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


BASE_PARAMS = {
    "plot_length":          12.0,
    "plot_width":           9.0,
    "floors":               "G+2",
    "bhk":                  "2 BHK",
    "style":                "Modern",
    "max_beam_span":        5.0,
    "column_spacing":       3.0,
    "allowable_deflection": 25.0,
    "concrete_grade":       "M25",
    "steel_grade":          "Fe500",
    "budget_lakhs":         45.0,
    "seismic_zone":         "III",
}


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Design Generation ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_design(client):
    r = await client.post("/api/v1/design/generate", json=BASE_PARAMS)
    assert r.status_code == 200
    data = r.json()

    assert "project_id"  in data
    assert "structural"  in data
    assert "floor_plans" in data
    assert "materials"   in data
    assert "comparison"  in data

    struct = data["structural"]
    assert 0 <= struct["safety_score"] <= 100
    assert struct["columns"]["count"] > 0
    assert struct["max_beam_span_m"] <= 5.0

    cost = data["materials"]["cost_breakdown"]
    assert cost["total"] > 0
    assert cost["budget"] == 45.0


@pytest.mark.asyncio
async def test_floor_plans_match_bhk(client):
    r = await client.post("/api/v1/design/generate", json=BASE_PARAMS)
    data = r.json()
    # G+2 → 3 floor plans
    assert len(data["floor_plans"]) == 3
    rooms = data["floor_plans"][0]["rooms"]
    # 2 BHK → at least 4 rooms
    assert len(rooms) >= 4


@pytest.mark.asyncio
async def test_budget_over_limit(client):
    params = {**BASE_PARAMS, "budget_lakhs": 10.0}
    r = await client.post("/api/v1/design/generate", json=params)
    assert r.status_code == 200
    cost = r.json()["materials"]["cost_breakdown"]
    assert cost["within_budget"] is False or cost["saved"] < 0


# ── Structural Analysis ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_structural_analyze(client):
    r = await client.post("/api/v1/structural/analyze", json=BASE_PARAMS)
    assert r.status_code == 200
    struct = r.json()
    assert "safety_score" in struct
    assert "columns" in struct
    assert "beams" in struct
    assert "slab" in struct


@pytest.mark.asyncio
async def test_compliance_check_pass(client):
    payload = {
            "beam_span_m": 4.8,
            "beam_depth_mm": 400,
            "slab_thickness_mm": 175,
            "deflection_mm": 18.0,
            "allowable_mm": 25.0,
            "column_size_mm": 300,
        }
    r = await client.post("/api/v1/structural/check-compliance", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["overall"] is True
    assert d["span_depth_ratio"] == pytest.approx(12.0, rel=0.01)


@pytest.mark.asyncio
async def test_compliance_check_fail_column(client):
    payload = {
        "beam_span_m": 5.0,
        "beam_depth_mm": 350,
        "slab_thickness_mm": 100,
        "deflection_mm": 30.0,
        "allowable_mm": 25.0,
        "column_size_mm": 200,   # below IS 456 minimum
    }
    r = await client.post("/api/v1/structural/check-compliance", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["overall"] is False
    assert d["column_min_ok"] is False
    assert d["deflection_ok"] is False


# ── Interior Design ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_interior_living_modern(client):
    payload = {
        "room":          "living",
        "style":         "modern",
        "wall_color":    "#F5F0E8",
        "floor_color":   "#C8A26A",
        "ceiling_color": "#FFFFFF",
        "furnishings":   ["sofa", "chairs", "plants", "lighting"],
    }
    r = await client.post("/api/v1/interior/generate", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["room"] == "living"
    assert d["style"] == "modern"
    assert len(d["furniture"]) > 0
    assert len(d["lighting"]) > 0
    assert d["estimated_cost_lakhs"] > 0


@pytest.mark.asyncio
async def test_interior_kitchen(client):
    payload = {
        "room":  "kitchen",
        "style": "warm",
        "wall_color": "#F0E8D5",
        "floor_color": "#8B6914",
        "ceiling_color": "#F5F0E8",
        "furnishings": ["lighting"],
    }
    r = await client.post("/api/v1/interior/generate", json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d["room"] == "kitchen"


# ── Projects ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_projects_list(client):
    # generate one project first
    await client.post("/api/v1/design/generate", json=BASE_PARAMS)
    r = await client.get("/api/v1/projects/")
    assert r.status_code == 200
    d = r.json()
    assert "projects" in d
    assert "total" in d


# ── Input Validation ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_plot_size(client):
    bad = {**BASE_PARAMS, "plot_length": 1.0}  # too small
    r = await client.post("/api/v1/design/generate", json=bad)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_concrete_grade(client):
    bad = {**BASE_PARAMS, "concrete_grade": "M10"}  # not in enum
    r = await client.post("/api/v1/design/generate", json=bad)
    assert r.status_code == 422
