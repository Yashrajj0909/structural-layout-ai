
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

class SoilAnalysisRequest(BaseModel):
    city: str
    pincode: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    soil_type: Optional[str] = None
    plot_area: float = Field(..., gt=0)
    locality_type: str

SOIL_PROPERTIES = {
    "Clay": {"bearing_capacity": 20, "water_retention": 80, "suitability_score": 45, "foundation": "Pile foundation"},
    "Sandy": {"bearing_capacity": 50, "water_retention": 20, "suitability_score": 70, "foundation": "Raft foundation"},
    "Loamy": {"bearing_capacity": 80, "water_retention": 50, "suitability_score": 95, "foundation": "Isolated footing"},
    "Black Soil": {"bearing_capacity": 30, "water_retention": 70, "suitability_score": 60, "foundation": "Pile foundation"},
}

FSI_RATES = {
    "urban": 2.5,
    "semi-urban": 1.5,
    "rural": 1.0,
}

@router.post("/analyze", summary="Analyze soil and FSI data")
async def analyze_soil_fsi(req: SoilAnalysisRequest):
    soil_type = req.soil_type or "Clay"  # Mock detection
    soil_props = SOIL_PROPERTIES.get(soil_type, SOIL_PROPERTIES["Clay"])

    fsi_rate = FSI_RATES.get(req.locality_type, 1.0)
    max_construction_area = req.plot_area * fsi_rate

    suitability_score = soil_props["suitability_score"]
    if suitability_score > 75:
        suitability_status = "Highly Suitable"
    elif 50 <= suitability_score <= 75:
        suitability_status = "Moderately Suitable"
    else:
        suitability_status = "Not Recommended"

    ai_insights = [
        f"This soil supports up to {int(soil_props['bearing_capacity'] / 20)} floors.",
        f"High water retention ({soil_props['water_retention']}%) suggests a robust drainage system is advisable.",
        f"FSI allows expansion up to {max_construction_area:.2f} sq.m."
    ]

    return {
        "soil_analysis": {
            "type": soil_type,
            "bearing_capacity": f"{soil_props['bearing_capacity']} kN/m^2",
            "water_retention": f"{soil_props['water_retention']} %",
            "suitability_score": suitability_score,
            "health": "Good" if suitability_score > 75 else "Moderate" if suitability_score > 50 else "Poor",
        },
        "fsi_analysis": {
            "allowed_fsi": fsi_rate,
            "max_construction_area": max_construction_area,
            "max_floors": int(max_construction_area / 100),
        },
        "construction_suitability": {
            "status": suitability_status,
            "recommendations": [f"Foundation type: {soil_props['foundation']}"],
        },
        "ai_insights": ai_insights,
    }
