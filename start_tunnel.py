import subprocess
import re
import time
import sys

# Start cloudflared
process = subprocess.Popen(
    ["cloudflared.exe", "tunnel", "--url", "http://localhost:8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("Starting cloudflared...", flush=True)

# Wait a bit
try:
    for line in iter(process.stderr.readline, ''):
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            url = match.group(0)
            print(f"FOUND_URL: {url}", flush=True)
            with open("tunnel_url.txt", "w") as f:
                f.write(url)
            # Leave the script running so the tunnel stays open
            while True:
                time.sleep(10)
except KeyboardInterrupt:
    process.terminate()
