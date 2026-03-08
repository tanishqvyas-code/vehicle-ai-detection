
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from backend.config import MODEL_PATH, FALLBACK_MODEL_PATH
    from backend.detector import load_model, detect_image
    import numpy as np
    
    print(f"DEBUG: MODEL_PATH={MODEL_PATH}")
    print(f"DEBUG: File exists? {os.path.exists(MODEL_PATH)}")
    
    print("DEBUG: Attempting to load model...")
    model = load_model()
    print("DEBUG: Model loaded successfully.")
    
    # Create dummy image
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    import cv2
    _, img_encoded = cv2.imencode('.jpg', dummy_img)
    
    print("DEBUG: Attempting detection...")
    result = detect_image(img_encoded.tobytes())
    print("DEBUG: Detection successful!")
    print(f"DEBUG: Stats: {result['stats']}")

except Exception as e:
    import traceback
    print("\n--- ERROR DETECTED ---")
    traceback.print_exc()
    sys.exit(1)
