#!/usr/bin/env python3

import os
import subprocess
import requests
from pathlib import Path
import base64

# ---------------------------------------------------------
#   SECURE API KEY LOADING
# ---------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise SystemExit("ERROR: GEMINI_API_KEY not set. Run: export GEMINI_API_KEY=\"your_key_here\"")

# Official Gemini vision endpoint
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
)

# ---------------------------------------------------------
#   PATHS
# ---------------------------------------------------------
DOWNLOADS_DIR = Path.home() / "Downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

IMAGE_PATH = DOWNLOADS_DIR / "capture.jpg"

# rpicam-still command (Pi Zero 2W)
CAPTURE_CMD = [
    "rpicam-still", "--width", "1920", "--height", "1080", "-o", str(IMAGE_PATH)
]

# ---------------------------------------------------------
#   DISPLAY HEADER
# ---------------------------------------------------------
print("\n" + "*" * 80)
print("ADVANCED CONTROLS INTERFACE — BY PRERITH".center(80))
print("*" * 80 + "\n")


# ---------------------------------------------------------
#   CAPTURE IMAGE
# ---------------------------------------------------------
def capture_image():
    print("[+] Capturing image...")
    subprocess.run(CAPTURE_CMD, check=True)
    print("[+] Image saved at:", IMAGE_PATH)
    return IMAGE_PATH


# ---------------------------------------------------------
#   SEND TO GEMINI (description + broken check)
# ---------------------------------------------------------
def analyze_with_gemini(image_path: Path):
    print("[+] Sending image to Google Gemini...")

    img_bytes = image_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode()

    # Gemini long prompt (description + broken check)
    prompt = (
        "You are an expert visual inspector.\n"
        "Given the image:\n"
        "1. Describe the object in detailed natural language.\n"
        "2. Identify its purpose.\n"
        "3. Check if it appears BROKEN or NOT BROKEN.\n"
        "4. If uncertain, say 'UNCLEAR'.\n"
        "Your output must contain two fields:\n"
        "DESCRIPTION: <your detailed description>\n"
        "STATUS: BROKEN / NOT BROKEN / UNCLEAR\n"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                ]
            }
        ]
    }

    params = {"key": GEMINI_API_KEY}
    headers = {"Content-Type": "application/json"}

    response = requests.post(GEMINI_ENDPOINT, json=payload, params=params, headers=headers)
    data = response.json()

    return data


# ---------------------------------------------------------
#   MAIN
# ---------------------------------------------------------
def main():
    img = capture_image()
    result = analyze_with_gemini(img)

    print("\n" + "=" * 60)
    print("GEMINI ANALYSIS RESULT")
    print("=" * 60)

    # Gemini returns nested content blocks
    try:
        text_output = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        text_output = str(result)

    print(text_output)
    print("\nSaved image at:", IMAGE_PATH)
    print("=" * 60)


if __name__ == "__main__":
    main()
