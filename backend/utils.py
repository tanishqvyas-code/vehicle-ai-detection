"""
Helper utilities: box drawing, class counting, frame encoding.
"""
import cv2
import numpy as np
import base64
from config import CLASS_NAMES, CLASS_COLORS, VEHICLE_CLASSES, DISPLAY_LABELS


# ── Drawing ────────────────────────────────────────────────────────────────────

def draw_boxes(frame: np.ndarray, results, conf_threshold: float = 0.0) -> np.ndarray:
    """Draw bounding boxes + labels on *frame* using model results."""
    annotated = frame.copy()
    if results is None or len(results) == 0:
        return annotated

    result = results[0]
    if result.boxes is None or len(result.boxes) == 0:
        return annotated

    names = result.names  # {int: str} from the model

    for box in result.boxes:
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue

        cls_idx  = int(box.cls[0])
        cls_name = names.get(cls_idx, "unknown")
        color    = CLASS_COLORS[cls_idx % len(CLASS_COLORS)]

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label background
        label = f"{cls_name} {conf:.0%}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)

        # Label text
        cv2.putText(
            annotated, label,
            (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (255, 255, 255), 1, cv2.LINE_AA,
        )

    return annotated


# ── Counting ───────────────────────────────────────────────────────────────────

def count_classes(results) -> dict:
    """
    Return {class_name: count} for all detected objects.
    Uses the model's own names dict so it works with any model.
    """
    counts: dict[str, int] = {}
    if results is None or len(results) == 0:
        return counts

    result = results[0]
    if result.boxes is None:
        return counts

    names = result.names
    for box in result.boxes:
        cls_idx  = int(box.cls[0])
        cls_name = names.get(cls_idx, "unknown")
        counts[cls_name] = counts.get(cls_name, 0) + 1

    return counts


def vehicle_only_counts(raw_counts: dict) -> dict:
    """Filter raw counts to only vehicle classes."""
    return {k: v for k, v in raw_counts.items() if k in VEHICLE_CLASSES}


def build_stats(raw_counts: dict) -> dict:
    """
    Build a stats payload ready for the frontend:
    {
        "counts":  {"car": 3, "bus": 1, ...},   # all detected classes
        "vehicles":{"car": 3, "bus": 1},         # vehicle classes only
        "total_vehicles": 4,
        "total_objects": 5,
        "display": {"🚗 Car": 3, "🚌 Bus": 1},   # emoji labels
    }
    """
    vehicle_counts   = vehicle_only_counts(raw_counts)
    display_counts   = {DISPLAY_LABELS.get(k, k): v for k, v in vehicle_counts.items()}
    return {
        "counts":          raw_counts,
        "vehicles":        vehicle_counts,
        "total_vehicles":  sum(vehicle_counts.values()),
        "total_objects":   sum(raw_counts.values()),
        "display":         display_counts,
    }


# ── Encoding ───────────────────────────────────────────────────────────────────

def frame_to_base64(frame: np.ndarray, quality: int = 92) -> str:
    """Encode a BGR numpy frame to a base-64 JPEG string."""
    success, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not success:
        raise RuntimeError("Failed to encode frame as JPEG")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def frame_to_bytes(frame: np.ndarray, quality: int = 80) -> bytes:
    """Encode a BGR numpy frame to raw JPEG bytes (for MJPEG streaming)."""
    success, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not success:
        raise RuntimeError("Failed to encode frame")
    return buf.tobytes()
