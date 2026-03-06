"""
YOLO detector — image inference, video processing, webcam streaming.
"""
import io
import os
import sys
import uuid
import time
import logging
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

# Allow running directly from backend/ dir
sys.path.insert(0, os.path.dirname(__file__))

from config import (
    MODEL_PATH, FALLBACK_MODEL_PATH,
    DEFAULT_CONFIDENCE, DEFAULT_IOU, IMG_SIZE,
    OUTPUT_VIDEO_DIR,
)
from utils import draw_boxes, count_classes, build_stats, frame_to_base64, frame_to_bytes
from tracker import CentroidTracker

log = logging.getLogger(__name__)


# ── Model loading ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_model() -> YOLO:
    """Load the YOLO model once and cache it."""
    if os.path.exists(MODEL_PATH):
        log.info(f"Loading custom model: {MODEL_PATH}")
        return YOLO(MODEL_PATH)
    log.warning(f"Custom model not found at {MODEL_PATH}, falling back to {FALLBACK_MODEL_PATH}")
    return YOLO(FALLBACK_MODEL_PATH)


# ── Image detection ────────────────────────────────────────────────────────────

def detect_image(image_bytes: bytes, conf: float = DEFAULT_CONFIDENCE) -> dict:
    """
    Run YOLO on a single image.

    Parameters
    ----------
    image_bytes : raw image bytes (JPEG / PNG / etc.)
    conf        : confidence threshold

    Returns
    -------
    {
        "image_b64": str,       # base64 JPEG of annotated image
        "stats":     dict,      # counts, vehicles, total_vehicles, display
        "latency_ms": float,
    }
    """
    model = load_model()

    # Decode
    np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
    frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image bytes")

    t0      = time.perf_counter()
    results = model.predict(
        source=frame,
        conf=conf,
        iou=DEFAULT_IOU,
        imgsz=IMG_SIZE,
        augment=True,        # Test-time augmentation: multi-scale + flip merging
        max_det=300,         # Allow up to 300 detections for dense traffic
        save=False,
        verbose=False,
        agnostic_nms=True,
        half=False,          # CPU-safe (set True only if CUDA is available)
    )
    latency = (time.perf_counter() - t0) * 1000

    annotated  = draw_boxes(frame, results, conf_threshold=conf)
    raw_counts = count_classes(results)
    stats      = build_stats(raw_counts)

    return {
        "image_b64":  frame_to_base64(annotated),
        "stats":      stats,
        "latency_ms": round(latency, 1),
    }


# ── Video detection ────────────────────────────────────────────────────────────

def detect_video(
    video_path: str,
    conf: float = DEFAULT_CONFIDENCE,
    use_tracker: bool = True,
) -> dict:
    """
    Process a video file frame-by-frame and write an annotated output.

    Returns
    -------
    {
        "output_path": str,       # absolute path to annotated output video
        "output_filename": str,   # basename for URL building
        "stats":  dict,           # cumulative counts across whole video
        "frame_count": int,
        "duration_s":  float,
    }
    """
    model   = load_model()
    tracker = CentroidTracker(max_disappeared=30, max_distance=80) if use_tracker else None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS) or 25
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_filename = f"output_{uuid.uuid4().hex[:8]}.mp4"
    out_path     = os.path.join(OUTPUT_VIDEO_DIR, out_filename)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    frame_count        = 0
    cumulative_raw: dict[str, int] = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        results = model.predict(
            source=frame,
            conf=conf,
            iou=DEFAULT_IOU,
            imgsz=IMG_SIZE,
            max_det=300,
            save=False,
            verbose=False,
            agnostic_nms=True,
            half=False,
        )

        # Tracker update
        if tracker is not None and results and results[0].boxes is not None:
            names = results[0].names
            detections = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "bbox":       (x1, y1, x2, y2),
                    "class_name": names.get(int(box.cls[0]), "unknown"),
                })
            tracker.update(detections)

        annotated = draw_boxes(frame, results, conf_threshold=conf)

        # Overlay unique vehicle count (top-left HUD)
        if tracker:
            unique = tracker.get_unique_counts()
            hud_y  = 30
            cv2.putText(
                annotated,
                f"Total Vehicles: {sum(v for k, v in unique.items() if k not in ('number_plate','blur_number_plate'))}",
                (10, hud_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 210, 255), 2, cv2.LINE_AA,
            )

        writer.write(annotated)

        # Accumulate per-frame counts for summary (per-frame, not unique)
        raw = count_classes(results)
        for k, v in raw.items():
            cumulative_raw[k] = cumulative_raw.get(k, 0) + v

    cap.release()
    writer.release()

    # Use tracker unique counts as final stats if available
    if tracker:
        final_raw = tracker.get_unique_counts()
    else:
        final_raw = cumulative_raw

    stats = build_stats(final_raw)

    return {
        "output_path":     out_path,
        "output_filename": out_filename,
        "stats":           stats,
        "frame_count":     frame_count,
        "duration_s":      round(frame_count / fps, 2),
    }


# ── Webcam streaming ───────────────────────────────────────────────────────────

def webcam_stream(conf: float = DEFAULT_CONFIDENCE):
    """
    Generator that yields MJPEG frame bytes from the default webcam.
    Usage: mount as a StreamingResponse endpoint in FastAPI.
    """
    model = load_model()
    cap   = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("No webcam found")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results  = model.predict(source=frame, conf=conf, imgsz=IMG_SIZE, max_det=300, save=False, verbose=False, agnostic_nms=True, half=False)
            annotated = draw_boxes(frame, results, conf_threshold=conf)
            jpg_bytes = frame_to_bytes(annotated)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"
            )
    finally:
        cap.release()
