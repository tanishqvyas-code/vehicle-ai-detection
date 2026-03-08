// Render backend (optimized with ONNX for 50-70ms latency)
const PROD_API_URL = "https://vehicleai-backend.onrender.com";

if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    window.VEHICLEAI_API_URL = PROD_API_URL;
} else {
    window.VEHICLEAI_API_URL = "";
}

