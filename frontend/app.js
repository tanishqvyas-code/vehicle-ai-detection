/**
 * VehicleAI — Frontend Application Logic
 * Handles tab switching, file uploads, API calls, and result rendering.
 */

// ── Config ─────────────────────────────────────────────────────────────────────
// API_BASE is injected by config.js (auto-set per environment).
// On Vercel → points to the Render backend URL.
// Locally   → http://localhost:8000
const API_BASE = (window.VEHICLEAI_API_URL || window.location.origin).replace(/\/$/, "");


// ── Global State ─────────────────────────────────────────────────────────────
let currentConf = 0.30;
let webcamActive = false;
let lastImageB64 = null;


// Class metadata for display
const CLASS_META = {
  car: { icon: "🚗", label: "Car", color: "#00d2ff" },
  two_wheeler: { icon: "🏍️", label: "Two Wheeler", color: "#ffa500" },
  auto: { icon: "🛺", label: "Auto", color: "#32cd32" },
  bus: { icon: "🚌", label: "Bus", color: "#dc143c" },
  truck: { icon: "🚛", label: "Truck", color: "#9400d3" },
  number_plate: { icon: "🔖", label: "Number Plate", color: "#888" },
  blur_number_plate: { icon: "🔖", label: "Blur Plate", color: "#555" },
};


// ── Tab Management ─────────────────────────────────────────────────────────────
const TAB_META = {
  image: { title: "Image Detection", sub: "Upload an image to detect and count vehicles" },
  video: { title: "Video Detection", sub: "Upload a video — unique vehicles counted via tracking" },
  webcam: { title: "Live Webcam", sub: "Real-time detection from your camera" },
};

function switchTab(tab) {
  // Update nav buttons
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.getElementById(`nav-${tab}`).classList.add("active");

  // Show correct panel
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
  document.getElementById(`tab-${tab}`).classList.add("active");

  // Update topbar
  document.getElementById("page-title").textContent = TAB_META[tab].title;
  document.getElementById("page-sub").textContent = TAB_META[tab].sub;

  // Stop webcam if switching away
  if (tab !== "webcam" && webcamActive) stopWebcam();
}


// ── Confidence Slider ──────────────────────────────────────────────────────────
function updateConf(val) {
  currentConf = parseInt(val) / 100;
  document.getElementById("conf-label").textContent = `${val}%`;
}


// ── Drag & Drop ────────────────────────────────────────────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add("drag-over");
}

function handleDragLeave(e, zoneId) {
  document.getElementById(zoneId).classList.remove("drag-over");
}

function handleDrop(e, type) {
  e.preventDefault();
  const zoneId = `${type}-drop-zone`;
  document.getElementById(zoneId).classList.remove("drag-over");

  const file = e.dataTransfer.files[0];
  if (!file) return;

  if (type === "image") handleImageFile(file);
  if (type === "video") handleVideoFile(file);
}


// ── Image Detection ────────────────────────────────────────────────────────────
function handleImageFile(file) {
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    showToast("Please upload an image file (JPEG, PNG, WEBP)", "error");
    return;
  }

  setStatus("Detecting…", true);
  showProgressBar("image", true);
  hideEl("image-results");
  animateProgress("image-progress", 0, 85, 1200);

  const formData = new FormData();
  formData.append("file", file);

  fetch(`${API_BASE}/api/detect/image?conf=${currentConf}`, {
    method: "POST",
    body: formData,
  })
    .then(res => {
      if (!res.ok) return res.json().then(e => Promise.reject(e.detail || "Detection failed"));
      return res.json();
    })
    .then(data => {
      animateProgress("image-progress", 85, 100, 300);
      setTimeout(() => {
        showProgressBar("image", false);
        renderImageResults(data);
        setStatus("Ready", false);
        showToast("Detection complete!", "success");
      }, 350);
    })
    .catch(err => {
      showProgressBar("image", false);
      setStatus("Ready", false);
      showToast(`Error: ${err}`, "error");
    });
}

function renderImageResults(data) {
  // Image
  const img = document.getElementById("result-img");
  img.src = `data:image/jpeg;base64,${data.image_b64}`;
  lastImageB64 = data.image_b64;

  // Counts
  renderCountGrid("image-count-grid", data.stats.vehicles || data.stats.counts);
  animateNumber("image-total", 0, data.stats.total_vehicles || data.stats.total_objects);

  // Latency
  document.getElementById("image-latency").textContent =
    data.latency_ms ? `⚡ ${data.latency_ms} ms inference` : "";

  showEl("image-results");
}

function downloadImage() {
  if (!lastImageB64) return;
  const a = document.createElement("a");
  a.href = `data:image/jpeg;base64,${lastImageB64}`;
  a.download = `detection_${Date.now()}.jpg`;
  a.click();
}


// ── Video Detection ────────────────────────────────────────────────────────────
function handleVideoFile(file) {
  if (!file) return;

  if (!file.type.startsWith("video/")) {
    showToast("Please upload a video file (MP4, AVI, MOV, MKV)", "error");
    return;
  }

  setStatus("Processing video…", true);
  hideEl("video-results");
  showEl("video-processing");
  document.getElementById("video-processing-sub").textContent =
    `Processing "${file.name}" (${(file.size / 1024 / 1024).toFixed(1)} MB)…`;

  const formData = new FormData();
  formData.append("file", file);

  fetch(`${API_BASE}/api/detect/video?conf=${currentConf}`, {
    method: "POST",
    body: formData,
  })
    .then(res => {
      if (!res.ok) return res.json().then(e => Promise.reject(e.detail || "Processing failed"));
      return res.json();
    })
    .then(data => {
      hideEl("video-processing");
      renderVideoResults(data);
      setStatus("Ready", false);
      showToast("Video processed!", "success");
    })
    .catch(err => {
      hideEl("video-processing");
      setStatus("Ready", false);
      showToast(`Error: ${err}`, "error");
    });
}

function renderVideoResults(data) {
  // Video player
  const video = document.getElementById("result-video");
  video.src = data.video_url;
  video.load();

  // Download link
  const dl = document.getElementById("video-download-link");
  dl.href = data.video_url;

  // Counts
  renderCountGrid("video-count-grid", data.stats.vehicles || data.stats.counts);
  animateNumber("video-total", 0, data.stats.total_vehicles || data.stats.total_objects);

  // Meta
  document.getElementById("video-meta").textContent =
    `${data.frame_count} frames · ${data.duration_s}s · tracked unique vehicles`;

  showEl("video-results");
}


// ── Webcam ─────────────────────────────────────────────────────────────────────
function startWebcam() {
  webcamActive = true;
  const img = document.getElementById("webcam-img");
  img.src = `${API_BASE}/api/stream?conf=${currentConf}&_=${Date.now()}`;
  img.classList.remove("hidden");
  document.getElementById("webcam-placeholder").classList.add("hidden");
  showEl("webcam-stop-btn");
  hideEl("webcam-start-btn");
  setStatus("Streaming…", true);
  showToast("Webcam stream started", "info");
}

function stopWebcam() {
  webcamActive = false;
  const img = document.getElementById("webcam-img");
  img.src = "";
  img.classList.add("hidden");
  document.getElementById("webcam-placeholder").classList.remove("hidden");
  hideEl("webcam-stop-btn");
  showEl("webcam-start-btn");
  setStatus("Ready", false);
}


// ── UI helpers ─────────────────────────────────────────────────────────────────

function renderCountGrid(gridId, counts) {
  const grid = document.getElementById(gridId);
  grid.innerHTML = "";

  if (!counts || Object.keys(counts).length === 0) {
    grid.innerHTML = `<p style="color:var(--text-muted);font-size:13px">No vehicles detected</p>`;
    return;
  }

  const max = Math.max(...Object.values(counts), 1);

  Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([cls, count], i) => {
      const meta = CLASS_META[cls] || { icon: "🚘", label: cls, color: "#888" };
      const pct = (count / max) * 100;

      const item = document.createElement("div");
      item.className = "count-item";
      item.style.animationDelay = `${i * 0.07}s`;
      item.innerHTML = `
        <span class="count-icon">${meta.icon}</span>
        <div class="count-info">
          <div class="count-name">${meta.label}</div>
          <div class="count-bar-wrap">
            <div class="count-bar" style="width:0%;background:${meta.color}" data-target="${pct}"></div>
          </div>
        </div>
        <span class="count-val">${count}</span>
      `;
      grid.appendChild(item);
    });

  // Animate bars after DOM paint
  requestAnimationFrame(() => {
    grid.querySelectorAll(".count-bar").forEach(bar => {
      bar.style.width = bar.dataset.target + "%";
    });
  });
}

function animateNumber(elId, from, to) {
  const el = document.getElementById(elId);
  const dur = 700;
  const start = performance.now();

  function step(now) {
    const t = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - t, 3); // ease-out-cubic
    el.textContent = Math.round(from + eased * (to - from));
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function showProgressBar(type, show) {
  const wrap = document.getElementById(`${type}-progress-wrap`);
  if (show) {
    wrap.classList.remove("hidden");
    document.getElementById(`${type}-progress`).style.width = "0%";
  } else {
    wrap.classList.add("hidden");
  }
}

function animateProgress(barId, from, to, duration) {
  const bar = document.getElementById(barId);
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    bar.style.width = (from + t * (to - from)) + "%";
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function setStatus(text, active) {
  document.getElementById("status-text").textContent = text;
  const pulse = document.querySelector("#status-pill .pulse");
  if (active) {
    pulse.style.background = "var(--warning)";
    pulse.style.boxShadow = "0 0 0 0 rgba(245,158,11,0.6)";
  } else {
    pulse.style.background = "var(--success)";
    pulse.style.boxShadow = "0 0 0 0 rgba(34,197,94,0.6)";
  }
}

function showEl(id) { document.getElementById(id).classList.remove("hidden"); }
function hideEl(id) { document.getElementById(id).classList.add("hidden"); }

function showToast(msg, type = "info") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const container = document.getElementById("toast-container");

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(30px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}


// ── Init ───────────────────────────────────────────────────────────────────────
(function init() {
  const statusEl = document.getElementById("status-text");
  const pulse = document.querySelector("#status-pill .pulse");

  // Set initial "Connecting" state
  statusEl.textContent = "Connecting...";
  pulse.style.background = "var(--warning)";

  // Start health check
  const start = Date.now();

  // Show "Waking up" if it takes > 3s
  const wakeUpTimer = setTimeout(() => {
    showToast("Server is waking up... Please wait (up to 1 min)", "info");
    statusEl.textContent = "Waking up...";
  }, 3000);

  fetch(`${API_BASE}/api/health`)
    .then(r => {
      clearTimeout(wakeUpTimer);
      if (!r.ok) throw new Error("Server error");
      return r.json();
    })
    .then(() => {
      showToast("Connected to detection server", "success");
      setStatus("Ready", false);
    })
    .catch(() => {
      clearTimeout(wakeUpTimer);
      showToast("Cannot reach server — make sure backend is running", "error");
      statusEl.textContent = "Disconnected";
      pulse.style.background = "#ef4444";
    });
})();
