"""
FastAPI backend — Vehicle Detection & Counting System
"""
import os
import sys
import uuid
import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Allow imports from backend/ directory
sys.path.insert(0, os.path.dirname(__file__))

from config import HOST, PORT, OUTPUT_VIDEO_DIR, DEFAULT_CONFIDENCE
from detector import detect_image, detect_video, webcam_stream

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Vehicle Detection API",
    description="YOLO-based vehicle detection and counting system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Directory paths ────────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
OUTPUT_DIR   = Path(OUTPUT_VIDEO_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mount processed output videos at /outputs/
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Vehicle Detection API is running"}


# ── Image detection ────────────────────────────────────────────────────────────
@app.post("/api/detect/image")
async def api_detect_image(
    file: UploadFile = File(...),
    conf: float = Query(DEFAULT_CONFIDENCE, ge=0.05, le=1.0),
):
    """Upload an image → receive annotated image (base64) + vehicle counts."""
    allowed = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP images supported")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 20 MB)")

    try:
        result = detect_image(image_bytes, conf=conf)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        log.exception("Image detection failed")
        raise HTTPException(status_code=500, detail=f"Detection failed: {e}")

    return JSONResponse(result)


# ── Video detection ────────────────────────────────────────────────────────────
@app.post("/api/detect/video")
async def api_detect_video(
    file: UploadFile = File(...),
    conf: float = Query(DEFAULT_CONFIDENCE, ge=0.05, le=1.0),
):
    """Upload a video → receive processed video URL + unique vehicle counts."""
    allowed_ext = {".mp4", ".avi", ".mov", ".mkv"}
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(status_code=400, detail="Only MP4/AVI/MOV/MKV videos supported")

    video_bytes = await file.read()
    if not video_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    if len(video_bytes) > 500 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Video too large (max 500 MB)")

    tmp_path = os.path.join(tempfile.gettempdir(), f"upload_{uuid.uuid4().hex}{suffix}")
    try:
        with open(tmp_path, "wb") as f:
            f.write(video_bytes)
        result = detect_video(tmp_path, conf=conf)
    except Exception as e:
        log.exception("Video detection failed")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return JSONResponse({
        "video_url":   f"/outputs/{result['output_filename']}",
        "stats":       result["stats"],
        "frame_count": result["frame_count"],
        "duration_s":  result["duration_s"],
    })


# ── Webcam MJPEG stream ────────────────────────────────────────────────────────
@app.get("/api/stream")
def api_stream(conf: float = Query(DEFAULT_CONFIDENCE, ge=0.05, le=1.0)):
    """Live MJPEG stream from the default webcam (if available)."""
    try:
        return StreamingResponse(
            webcam_stream(conf=conf),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Frontend — explicit routes so API is never shadowed ───────────────────────
@app.get("/")
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"error": "Frontend not found"}, status_code=404)

@app.get("/style.css")
def serve_css():
    f = FRONTEND_DIR / "style.css"
    return FileResponse(str(f), media_type="text/css")

@app.get("/app.js")
def serve_js():
    f = FRONTEND_DIR / "app.js"
    return FileResponse(str(f), media_type="application/javascript")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
