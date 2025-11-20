#!/usr/bin/env python3

import os
import subprocess
import time
import requests
import json
import sys
from pathlib import Path

# ---------------------
# Secure Key Loading
# ---------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY")

if not GEMINI_API_KEY:
    raise SystemExit("ERROR: GEMINI_API_KEY environment variable is not set.")

if not NIM_API_KEY:
    raise SystemExit("ERROR: NVIDIA_NIM_API_KEY environment variable is not set.")

# ---------------------
# Endpoints (provided by you)
# ---------------------
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"

NIM_ENDPOINT = "https://integrate.api.nvidia.com/v1/microsoft/trellis"

# ---------------------
# Paths
# ---------------------
DOWNLOADS_DIR = Path.home() / "Downloads"
CAPTURE_PATH = DOWNLOADS_DIR / "capture_for_3d.jpg"
OUTPUT_3D_PATH = DOWNLOADS_DIR / "trellis_output.glb"

CAPTURE_CMD = [
    "rpicam-still", "--width", "1920", "--height", "1080", "-o", str(CAPTURE_PATH)
]

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "*" * 80)
print("ADVANCED CONTROLS INTERFACE — BY PRERITH".center(80))
print("*" * 80 + "\n")


# ---------------------
# Camera
# ---------------------
def capture_image():
    print("[+] Capturing image...")
    subprocess.run(CAPTURE_CMD, check=True)
    print("[+] Image saved:", CAPTURE_PATH)
    return CAPTURE_PATH


# ---------------------
# Gemini Vision — "Broken or Not"
# ---------------------
def analyze_with_gemini(image_path):
    print("[+] Sending to Gemini Vision...")

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    img_bytes = image_path.read_bytes()
    img_b64 = img_bytes.encode("base64") if hasattr(img_bytes, "encode") else None

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Is the main object BROKEN or NOT BROKEN? Answer clearly."},
                    {"image": {"data": img_bytes.decode("latin1")}}
                ]
            }
        ]
    }

    r = requests.post(GEMINI_ENDPOINT, params=params, json=payload)
    response = r.json()
    print("[Gemini Response]", response)
    return response


# ---------------------
# NVIDIA NIM → TRELLIS 3D asset generation
# ---------------------
def generate_3d_trellis(image_path):
    print("[+] Uploading to NVIDIA TRELLIS...")

    headers = {"Authorization": f"Bearer {NIM_API_KEY}"}
    files = {"image": open(image_path, "rb")}
    data = {"output_format": "glb"}

    # Create job
    job_create = requests.post(f"{NIM_ENDPOINT}/jobs", headers=headers, files=files, data=data)
    job_json = job_create.json()

    job_id = job_json["id"]
    print("[+] TRELLIS Job ID:", job_id)

    # Poll
    while True:
        time.sleep(4)
        st = requests.get(f"{NIM_ENDPOINT}/jobs/{job_id}", headers=headers).json()
        print("[TRELLIS Status]", st["status"])

        if st["status"] == "succeeded":
            download_url = st["result"]["assets"]["glb"]["url"]
            break
        elif st["status"] == "failed":
            raise RuntimeError("TRELLIS job failed.")

    print("[+] Downloading 3D asset...")
    glb_data = requests.get(download_url).content

    with open(OUTPUT_3D_PATH, "wb") as f:
        f.write(glb_data)

    print("[+] 3D asset saved to:", OUTPUT_3D_PATH)
    return OUTPUT_3D_PATH


# ---------------------
# Main
# ---------------------
def main():
    img = capture_image()
    analyze_with_gemini(img)
    generate_3d_trellis(img)


if __name__ == "__main__":
    main()
