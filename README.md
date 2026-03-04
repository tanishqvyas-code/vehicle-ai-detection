# VehicleAI — Real-Time Vehicle Detection & Counting

[![Deploy Backend to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tanishqvyas-code/vehicle-ai-detection)

[![Frontend on Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)](https://vehicleai-frontend-de14r8kij-tanishqvyas322-3778s-projects.vercel.app)

A production-ready, full-stack vehicle detection and counting system powered by **YOLOv8** with a custom-trained 7-class traffic model.

![Dashboard](frontend/preview.png)

---

## Features

- 📷 **Image Detection** — upload any traffic image, get annotated results + vehicle-wise counts instantly
- 🎥 **Video Detection** — upload a video, vehicles tracked uniquely across frames via centroid tracking
- 📡 **Live Webcam** — real-time MJPEG stream with bounding box overlays
- 🎛️ **Confidence slider** — tune the threshold live (5%–95%)
- 🧠 **7 Classes** — Car, Two Wheeler, Auto, Bus, Truck, Number Plate, Blur Plate
- 🌙 **Dark dashboard UI** — glassmorphism design, animated count bars, toast notifications

---

## Quick Start (Local)

### Prerequisites
- Python 3.10+
- `best.pt` model file in the project root

### Run (Windows)
```bash
# Option 1 — double-click
run.bat

# Option 2 — manual
pip install -r requirements.txt
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Open **http://localhost:8000**

---

## Docker

### Build & run
```bash
docker compose up --build
```
App available at **http://localhost:8000**

### Environment variables (optional)
Copy `.env.example` → `.env` and override any defaults:
```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Server port |
| `WORKERS` | `1` | Uvicorn worker processes |
| `CONFIDENCE` | `0.35` | Default confidence threshold |
| `MODEL_PATH` | `best.pt` | Path to YOLO weights |
| `OUTPUT_VIDEO_DIR` | `backend/outputs` | Where processed videos are saved |

---

## Cloud Deployment

### 🚂 Railway (recommended — free tier)
1. Push the repo to GitHub  
2. New Project → Deploy from GitHub  
3. Set **Start Command**: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add env var `MODEL_PATH=best.pt`  
5. Upload `best.pt` via Railway's volume or bundle it in the repo (it's 6 MB)

### 🎨 Render
1. New → Web Service → connect repo  
2. **Build Command**: `pip install -r requirements.txt`  
3. **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`  
4. Set env vars as needed

### 🌊 Fly.io
```bash
fly launch          # auto-detects Dockerfile
fly deploy
```

### Heroku / any PaaS
The `Procfile` is already configured:
```
web: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

> ⚠️ **Model file** — `best.pt` (6 MB) must be available on the server. For Git-based deploys, either commit it (small enough) or mount it as a volume / download from a URL at startup.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/health` | Health check |
| `POST` | `/api/detect/image?conf=0.35` | Image detection → base64 annotated image + counts |
| `POST` | `/api/detect/video?conf=0.35` | Video detection → processed video URL + unique counts |
| `GET`  | `/api/stream?conf=0.35` | MJPEG live webcam stream |

### Example — image detection
```bash
curl -s -X POST "http://localhost:8000/api/detect/image?conf=0.4" \
     -F "file=@my_traffic_photo.jpg" | python -m json.tool
```

Response:
```json
{
  "image_b64": "<base64 JPEG>",
  "stats": {
    "counts":         { "car": 5, "bus": 1 },
    "vehicles":       { "car": 5, "bus": 1 },
    "total_vehicles": 6,
    "total_objects":  6,
    "display":        { "🚗 Car": 5, "🚌 Bus": 1 }
  },
  "latency_ms": 42.3
}
```

---

## Project Structure

```
Yolo/
├── backend/
│   ├── main.py         FastAPI app — API routes + frontend serving
│   ├── detector.py     YOLO inference (image, video, webcam)
│   ├── tracker.py      Centroid tracker (unique vehicle IDs)
│   ├── utils.py        Drawing, counting, encoding helpers
│   └── config.py       Environment-variable-driven config
├── frontend/
│   ├── index.html      Dashboard shell
│   ├── style.css       Premium dark UI
│   └── app.js          Upload, API calls, animations
├── Dockerfile
├── docker-compose.yml
├── Procfile            Railway / Render / Heroku
├── .env.example        Environment variable template
├── requirements.txt
└── run.bat             Windows one-click launcher
```

---

## Classes Detected

| Class | Counted as Vehicle |
|-------|-------------------|
| Car | ✅ |
| Two Wheeler | ✅ |
| Auto | ✅ |
| Bus | ✅ |
| Truck | ✅ |
| Number Plate | ❌ (detected, not counted) |
| Blur Plate | ❌ (detected, not counted) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Model | YOLOv8 (Ultralytics) — custom-trained |
| Backend | FastAPI + Uvicorn |
| Tracking | Centroid tracker (SciPy) |
| Video | OpenCV |
| Frontend | Vanilla HTML / CSS / JS |
| Container | Docker + Docker Compose |
