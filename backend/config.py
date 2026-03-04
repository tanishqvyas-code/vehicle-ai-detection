"""
Central configuration for the Vehicle Detection System.
All values can be overridden via environment variables or a .env file.
"""
import os
from pathlib import Path

# ── .env file loading (optional — only if python-dotenv installed) ─────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass   # python-dotenv not installed; env vars must be set by the OS/container

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.resolve()

MODEL_PATH          = os.environ.get("MODEL_PATH",          str(BASE_DIR / "best.pt"))
FALLBACK_MODEL_PATH = os.environ.get("FALLBACK_MODEL_PATH", str(BASE_DIR / "yolov8n.pt"))

# ── Inference ──────────────────────────────────────────────────────────────────
DEFAULT_CONFIDENCE = float(os.environ.get("CONFIDENCE", "0.35"))
DEFAULT_IOU        = float(os.environ.get("IOU",        "0.45"))
IMG_SIZE           = int(os.environ.get("IMG_SIZE",     "640"))

# ── Class definitions ──────────────────────────────────────────────────────────
CLASS_NAMES = [
    "car",
    "number_plate",
    "blur_number_plate",
    "two_wheeler",
    "auto",
    "bus",
    "truck",
]

VEHICLE_CLASSES = {"car", "two_wheeler", "auto", "bus", "truck"}

DISPLAY_LABELS = {
    "car":               "\U0001f697 Car",
    "two_wheeler":       "\U0001f3cd\ufe0f Two Wheeler",
    "auto":              "\U0001f6fa Auto",
    "bus":               "\U0001f68c Bus",
    "truck":             "\U0001f69b Truck",
    "number_plate":      "\U0001f516 Number Plate",
    "blur_number_plate": "\U0001f516 Blur Plate",
}

# RGB colors for bounding boxes (one per class index)
CLASS_COLORS = [
    (0,   210, 255),   # car           — electric blue
    (160, 160, 160),   # number_plate  — grey
    (100, 100, 100),   # blur_plate    — dark grey
    (255, 165,   0),   # two_wheeler   — orange
    (50,  205,  50),   # auto          — green
    (220,  20,  60),   # bus           — crimson
    (148,   0, 211),   # truck         — violet
]

# ── Server ─────────────────────────────────────────────────────────────────────
HOST    = os.environ.get("HOST",    "0.0.0.0")
PORT    = int(os.environ.get("PORT", "8000"))
WORKERS = int(os.environ.get("WORKERS", "1"))

# ── Storage ────────────────────────────────────────────────────────────────────
_output_dir = os.environ.get("OUTPUT_VIDEO_DIR", str(BASE_DIR / "backend" / "outputs"))
OUTPUT_VIDEO_DIR = str(Path(_output_dir).resolve())
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)
