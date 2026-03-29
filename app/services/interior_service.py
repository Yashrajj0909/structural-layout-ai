"""
app/services/interior_service.py

Generates room-by-room interior design data:
  - Furniture placement (position, size, color)
  - Lighting specifications
  - Color palette recommendations
  - Cost estimates for finishing
"""

from __future__ import annotations
from app.models.schemas import (
    InteriorRequest, InteriorResult, InteriorStyle, RoomType,
    FurnitureItem, LightingSpec,
)


# ── Style → palette mapping ───────────────────────────────────────────────────

STYLE_PALETTES = {
    InteriorStyle.MODERN: {
        "primary":  "#3D5A6C",
        "accent":   "#5B8FA8",
        "neutral":  "#F5F0E8",
        "wood":     "#A0826D",
        "highlight":"#B5651D",
    },
    InteriorStyle.WARM: {
        "primary":  "#8B4513",
        "accent":   "#B5651D",
        "neutral":  "#F0E8D5",
        "wood":     "#8B6914",
        "highlight":"#C8A26A",
    },
    InteriorStyle.LUXURY: {
        "primary":  "#1A1A2E",
        "accent":   "#D4AF37",
        "neutral":  "#2C2C2C",
        "wood":     "#2C2A25",
        "highlight":"#D4AF37",
    },
    InteriorStyle.NATURE: {
        "primary":  "#4A7C59",
        "accent":   "#6B8F71",
        "neutral":  "#F0EBE0",
        "wood":     "#B5854D",
        "highlight":"#8CAB7A",
    },
}


# ── Room dimensions (metres) ──────────────────────────────────────────────────

ROOM_SIZES = {
    RoomType.LIVING:   (5.4, 3.6),
    RoomType.BEDROOM1: (3.6, 3.6),
    RoomType.BEDROOM2: (3.6, 3.6),
    RoomType.KITCHEN:  (2.7, 2.7),
    RoomType.BATHROOM: (1.8, 2.1),
    RoomType.EXTERIOR: (12.0, 9.0),
}


# ── Furniture templates per room ──────────────────────────────────────────────

def _living_furniture(pal: dict, req: InteriorRequest) -> list[dict]:
    items = []
    if "sofa" in req.furnishings:
        items += [
            {"id": "sofa-main", "type": "Sofa",       "pos": {"x": -1.5, "y": 0.35, "z": -2.5}, "dim": {"w": 3.0, "h": 0.7, "d": 1.0}, "color": pal["primary"], "material": "Fabric"},
            {"id": "sofa-back", "type": "Sofa Back",   "pos": {"x": -1.5, "y": 0.9,  "z": -2.9}, "dim": {"w": 3.0, "h": 0.8, "d": 0.2}, "color": pal["primary"], "material": "Fabric"},
        ]
    if "chairs" in req.furnishings:
        for i, z in enumerate([-0.5, 0.5]):
            items.append({"id": f"chair-{i}", "type": "Chair", "pos": {"x": 1.2, "y": 0.25, "z": z}, "dim": {"w": 0.6, "h": 0.5, "d": 0.6}, "color": pal["accent"], "material": "Fabric"})
    items.append({"id": "coffee-table", "type": "Coffee Table", "pos": {"x": -1.5, "y": 0.25, "z": -0.8}, "dim": {"w": 1.2, "h": 0.45, "d": 0.8}, "color": pal["wood"], "material": "Wood"})
    items.append({"id": "tv-unit",      "type": "TV Unit",      "pos": {"x": -1.5, "y": 0.25, "z":  3.5}, "dim": {"w": 3.0, "h": 0.5,  "d": 0.45},"color": pal["wood"], "material": "Wood"})
    if "plants" in req.furnishings:
        items.append({"id": "plant-1",  "type": "Planter",      "pos": {"x":  3.5, "y": 0.2,  "z": -2.5},"dim": {"w": 0.4, "h": 1.2, "d": 0.4}, "color": "#4A7C59","material": "Ceramic"})
    if "shelves" in req.furnishings:
        items.append({"id": "shelf-1",  "type": "Bookshelf",    "pos": {"x": -4.5, "y": 1.2,  "z":  0.0},"dim": {"w": 0.3, "h": 2.2, "d": 1.5}, "color": pal["wood"],"material": "Wood"})
    return items


def _bedroom_furniture(pal: dict, req: InteriorRequest) -> list[dict]:
    items = [
        {"id": "bed-frame",   "type": "Bed Frame",    "pos": {"x": 0.0, "y": 0.15, "z": -1.0}, "dim": {"w": 2.0, "h": 0.3, "d": 2.1}, "color": pal["wood"],    "material": "Wood"},
        {"id": "bed-mattress","type": "Mattress",      "pos": {"x": 0.0, "y": 0.45, "z": -1.0}, "dim": {"w": 1.9, "h": 0.3, "d": 2.0}, "color": "#F5F0E8",      "material": "Foam"},
        {"id": "headboard",   "type": "Headboard",     "pos": {"x": 0.0, "y": 0.75, "z": -1.9}, "dim": {"w": 2.0, "h": 0.9, "d": 0.1}, "color": pal["primary"], "material": "Upholstered"},
        {"id": "wardrobe",    "type": "Wardrobe",      "pos": {"x": -1.5,"y": 1.0,  "z":  1.2}, "dim": {"w": 0.6, "h": 2.2, "d": 1.8}, "color": pal["wood"],    "material": "Wood"},
        {"id": "side-table-l","type": "Side Table",    "pos": {"x":-1.15,"y": 0.3,  "z": -1.0}, "dim": {"w": 0.5, "h": 0.5, "d": 0.4}, "color": pal["wood"],    "material": "Wood"},
        {"id": "side-table-r","type": "Side Table",    "pos": {"x": 1.15,"y": 0.3,  "z": -1.0}, "dim": {"w": 0.5, "h": 0.5, "d": 0.4}, "color": pal["wood"],    "material": "Wood"},
    ]
    if "mirror" in req.furnishings:
        items.append({"id": "mirror", "type": "Mirror", "pos": {"x": 1.5, "y": 1.0, "z":  0.5}, "dim": {"w": 0.05,"h": 1.4, "d": 0.6}, "color": "#C8C8C8", "material": "Glass"})
    if "curtains" in req.furnishings:
        items.append({"id": "curtain","type": "Curtains","pos": {"x": 0.0, "y": 1.5, "z": -1.8}, "dim": {"w": 2.0, "h": 2.8, "d": 0.1}, "color": pal["accent"],"material": "Fabric"})
    return items


def _kitchen_furniture(pal: dict, req: InteriorRequest) -> list[dict]:
    return [
        {"id": "counter-l",  "type": "Kitchen Counter", "pos": {"x": -0.8, "y": 0.45, "z": 0.3},  "dim": {"w": 0.6, "h": 0.9, "d": 1.8}, "color": "#D4C9B8", "material": "Granite"},
        {"id": "counter-r",  "type": "Kitchen Counter", "pos": {"x":  0.8, "y": 0.45, "z": 0.3},  "dim": {"w": 0.6, "h": 0.9, "d": 1.8}, "color": "#D4C9B8", "material": "Granite"},
        {"id": "sink",       "type": "Sink",             "pos": {"x": -0.8, "y": 0.9,  "z":-0.8},  "dim": {"w": 0.5, "h": 0.1, "d": 0.4}, "color": "#A0A0A0", "material": "Stainless"},
        {"id": "upper-cab",  "type": "Upper Cabinets",  "pos": {"x": -0.8, "y": 1.65, "z": 0.0},  "dim": {"w": 0.3, "h": 0.7, "d": 1.5}, "color": pal["wood"], "material": "Wood"},
        {"id": "fridge",     "type": "Refrigerator",    "pos": {"x":  0.6, "y": 0.9,  "z":-0.6},  "dim": {"w": 0.7, "h": 1.8, "d": 0.7}, "color": "#D0D0D0", "material": "Metal"},
    ]


def _bathroom_furniture(pal: dict, req: InteriorRequest) -> list[dict]:
    return [
        {"id": "toilet",     "type": "WC",              "pos": {"x":  0.3, "y": 0.25, "z": 0.8},  "dim": {"w": 0.4, "h": 0.5, "d": 0.7}, "color": "#FFFFFF", "material": "Ceramic"},
        {"id": "washbasin",  "type": "Washbasin",       "pos": {"x": -0.4, "y": 0.75, "z":-0.6},  "dim": {"w": 0.6, "h": 0.15,"d": 0.5}, "color": "#FFFFFF", "material": "Ceramic"},
        {"id": "vanity",     "type": "Vanity Unit",     "pos": {"x": -0.4, "y": 0.35, "z":-0.6},  "dim": {"w": 0.6, "h": 0.7, "d": 0.5}, "color": pal["wood"],"material": "Wood"},
        {"id": "shower",     "type": "Shower Screen",   "pos": {"x":  0.3, "y": 1.0,  "z":-0.5},  "dim": {"w": 0.01,"h": 2.0, "d": 0.9}, "color": "#C0D8E8", "material": "Glass"},
    ]


FURNITURE_MAP = {
    RoomType.LIVING:   _living_furniture,
    RoomType.BEDROOM1: _bedroom_furniture,
    RoomType.BEDROOM2: _bedroom_furniture,
    RoomType.KITCHEN:  _kitchen_furniture,
    RoomType.BATHROOM: _bathroom_furniture,
    RoomType.EXTERIOR: lambda p, r: [],
}


# ── Lighting templates ────────────────────────────────────────────────────────

def _lighting(room: RoomType, pal: dict) -> list[dict]:
    base = [{"type": "Ceiling Main", "pos": {"x": 0, "y": 3.5, "z": 0}, "color_temp_k": 3000, "intensity": 1.2}]
    if room in (RoomType.LIVING,):
        base += [
            {"type": "Pendant",   "pos": {"x":  0,    "y": 3.0,  "z": 0},   "color_temp_k": 2700, "intensity": 0.8},
            {"type": "Floor Lamp","pos": {"x":  2.5,  "y": 1.5,  "z": -2.0},"color_temp_k": 2700, "intensity": 0.6},
        ]
    if room in (RoomType.BEDROOM1, RoomType.BEDROOM2):
        base += [
            {"type": "Bedside Lamp L","pos": {"x": -1.2,"y": 0.7, "z": -1.0},"color_temp_k": 2700,"intensity": 0.5},
            {"type": "Bedside Lamp R","pos": {"x":  1.2,"y": 0.7, "z": -1.0},"color_temp_k": 2700,"intensity": 0.5},
        ]
    return base


# ── Cost estimate ─────────────────────────────────────────────────────────────

STYLE_COST_FACTOR = {
    InteriorStyle.MODERN:  1.0,
    InteriorStyle.WARM:    0.9,
    InteriorStyle.LUXURY:  2.2,
    InteriorStyle.NATURE:  1.1,
}

ROOM_BASE_COST = {
    RoomType.LIVING:   3.5,
    RoomType.BEDROOM1: 2.5,
    RoomType.BEDROOM2: 2.5,
    RoomType.KITCHEN:  4.0,
    RoomType.BATHROOM: 2.0,
    RoomType.EXTERIOR: 5.0,
}


# ── Design tips ───────────────────────────────────────────────────────────────

TIPS = {
    InteriorStyle.MODERN: [
        "Use 60-30-10 colour rule: 60% neutral, 30% steel blue, 10% copper accent.",
        "Opt for handleless cabinet profiles for a sleek, uncluttered aesthetic.",
        "Introduce indirect LED coves at cornice level for ambient depth.",
    ],
    InteriorStyle.WARM: [
        "Layer jute rugs over engineered wood for texture without bulk.",
        "Exposed brick feature wall pairs beautifully with terracotta pots.",
        "Use warm white (2700K) lighting throughout to enhance the cosy palette.",
    ],
    InteriorStyle.LUXURY: [
        "Backlit onyx or fluted glass panels add drama to feature walls.",
        "Gold hardware should be brushed (not polished) to avoid appearing brash.",
        "Invest in statement lighting — chandeliers anchor the luxury narrative.",
    ],
    InteriorStyle.NATURE: [
        "Maximise natural light with sheer linen curtains instead of blackouts.",
        "Incorporate living walls or moss art panels for biophilic impact.",
        "Choose stone-look porcelain (not real stone) — easier to maintain.",
    ],
}


# ── Public function ───────────────────────────────────────────────────────────

def generate_interior(req: InteriorRequest) -> InteriorResult:
    pal   = STYLE_PALETTES[req.style]
    w, d  = ROOM_SIZES.get(req.room, (4.0, 4.0))
    area  = round(w * d, 2)

    raw_furniture = FURNITURE_MAP[req.room](pal, req)
    furniture = [
        FurnitureItem(
            id=f["id"], type=f["type"],
            position=f["pos"], dimensions=f["dim"],
            color_hex=f["color"], material=f["material"],
        )
        for f in raw_furniture
    ]

    raw_lights = _lighting(req.room, pal)
    lighting = [
        LightingSpec(type=l["type"], position=l["pos"],
                     color_temp_k=l["color_temp_k"], intensity=l["intensity"])
        for l in raw_lights
    ]

    cost = round(ROOM_BASE_COST.get(req.room, 2.0) * STYLE_COST_FACTOR[req.style], 2)

    return InteriorResult(
        room=req.room,
        style=req.style,
        colors={"wall": req.wall_color, "floor": req.floor_color, "ceiling": req.ceiling_color},
        furniture=furniture,
        lighting=lighting,
        area_m2=area,
        estimated_cost_lakhs=cost,
        tips=TIPS.get(req.style, []),
    )
