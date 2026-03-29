# StructAI Designer — Smart House Layout Optimization

**An AI-powered structural engineering and architectural design suite.**  
FastAPI · Python 3.11+ · SQLite · IS 456 / IS 875 / NBC 2016

---

## 🚀 Quick Access Links

| Feature | Local URL | Description |
| :--- | :--- | :--- |
| **Main Dashboard** | [http://localhost:8000/](http://localhost:8000/) | Structural analysis & cost optimization dashboard |
| **2D Floor Plan** | [http://localhost:8000/floorplan](http://localhost:8000/floorplan) | Interactive 2D layout with drag-and-drop & road context |
| **Column Grid Model** | [http://localhost:8000/column-grid](http://localhost:8000/column-grid) | Dynamic 3D column grid with customizable shapes & sizes |
| **Soil Analysis** | [http://localhost:8000/soil](http://localhost:8000/soil) | Soil bearing capacity & FSI calculation tools |
| **API Documentation** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI for all API endpoints |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative API documentation view |

---

## ✨ Key Features

### 📐 2D Floor Plan Generator
- **Manual Edit Mode**: Drag and drop rooms (Living, Bedrooms, Kitchen) to customize your layout.
- **Site Context**: Add a public road with adjustable distance (2m to 30m) from the plot.
- **Orientation**: Integrated compass for North/South/East/West orientation.
- **Furniture Visualization**: Auto-generated furniture layouts for different room types.

### 🏗️ Structural Optimization
- **IS 456 Compliant**: Automatic column and beam grid generation following Indian Standards.
- **Cost Estimation**: Real-time material BOQ (Bill of Quantities) and cost breakdown.
- **Safety Checks**: Compliance validation for concrete grade, steel grade, and seismic zones.

### 🛋️ Interior Design Studio
- **Style Presets**: Generate Modern, Minimalist, or Industrial interior configurations.
- **Material Palettes**: Custom wall, floor, and ceiling color generation.

---

## 🛠️ Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/Yashrajj0909/structural-layout-ai.git
cd structural-layout-ai

# 2. Set up virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📁 Project Structure

```
structAIdesigner/
├── main.py                # FastAPI entry point & route registration
├── app/
│   ├── models/            # Pydantic schemas for request/response
│   ├── services/          # Core logic (Structural Engine, Layout Optimizer)
│   ├── routers/           # API endpoints (Design, Structural, Interior, etc.)
│   └── database.py        # Async SQLite database management
├── static/                # Frontend assets (HTML, JS, CSS)
│   ├── index.html         # Main Dashboard
│   ├── floorplan.html     # 2D Floor Plan Generator
│   └── soil.html          # Soil Analysis Tool
└── tests/                 # Async API test suite
```

---

## ⚖️ Standards & Compliance

- **IS 456:2000**: Plain and Reinforced Concrete
- **IS 875 Part 1 & 2**: Dead and Live Loads
- **IS 1893**: Earthquake Resistant Design
- **NBC 2016**: National Building Code of India

---

## 👨‍💻 Developer Notes
- Uses `aiosqlite` for asynchronous database operations.
- Frontend built with vanilla JavaScript and Canvas API for high-performance 2D rendering.
- Designed for rapid prototyping of residential building layouts.
