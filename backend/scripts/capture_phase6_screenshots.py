"""
Captures real headless Chromium (Microsoft Edge) responsive screenshots of the built web app:
- Mobile: 360x640
- Tablet: 768x1024
- Desktop: 1280x800
Saves them to docs/test_screenshots/
"""
import os
import sys
import time
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEB_DIST = _REPO_ROOT / "web" / "dist"
_SCREENSHOT_DIR = _REPO_ROOT / "docs" / "test_screenshots"
_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class SinglePageAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(_WEB_DIST), **kwargs)

    def do_GET(self):
        # Serve index.html for client-side routing
        path = self.translate_path(self.path)
        if not os.path.exists(path) or os.path.isdir(path):
            self.path = "/index.html"
        return super().do_GET()


def run_capture():
    print(f"Starting static web server from: {_WEB_DIST}")
    server = HTTPServer(("127.0.0.1", 5174), SinglePageAppHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    time.sleep(1)

    viewports = [
        ("mobile_360x640.png", "360,640"),
        ("tablet_768x1024.png", "768,1024"),
        ("desktop_1280x800.png", "1280,800"),
    ]

    for filename, window_size in viewports:
        target_file = _SCREENSHOT_DIR / filename
        cmd = [
            EDGE_PATH,
            "--headless",
            "--disable-gpu",
            f"--window-size={window_size}",
            f"--screenshot={target_file}",
            "http://127.0.0.1:5174/",
        ]
        print(f"Capturing {filename} with window size {window_size}...")
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=15)
            if target_file.exists():
                print(f"  Saved: {target_file} ({target_file.stat().st_size} bytes)")
            else:
                print(f"  Failed to save {filename}: {res.stderr.decode()}")
        except Exception as exc:
            print(f"  Error capturing {filename}: {exc}")

    server.shutdown()
    print("Screenshots capture complete!")


if __name__ == "__main__":
    run_capture()

