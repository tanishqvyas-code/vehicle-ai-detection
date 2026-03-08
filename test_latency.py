import requests
import time
import numpy as np
from PIL import Image
import io

# Create a random dummy image
img_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
img = Image.fromarray(img_array)
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_bytes = img_byte_arr.getvalue()

url = "http://localhost:8000/api/detect/image"

print("Sending request to warmup...")
try:
    res = requests.post(url, files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    print(res.json())
except Exception as e:
    print(f"Error during warmup: {e}")

print("Sending request for latency test...")
try:
    start_time = time.time()
    res = requests.post(url, files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    end_time = time.time()
    data = res.json()
    print(f"Server reported latency: {data.get('latency_ms')} ms")
    print(f"Total roundtrip time: {(end_time - start_time) * 1000:.2f} ms")
except Exception as e:
    print(f"Error: {e}")
