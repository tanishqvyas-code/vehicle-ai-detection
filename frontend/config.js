// Use Render backend if on public Vercel, otherwise fallback to local server
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    window.VEHICLEAI_API_URL = "https://painted-softball-willow-explicit.trycloudflare.com";
} else {
    window.VEHICLEAI_API_URL = ""; // Fallback to window.location.origin
}

