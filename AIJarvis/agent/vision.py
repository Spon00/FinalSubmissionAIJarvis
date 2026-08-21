import base64
import os
import cv2
import requests
import json


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:4b"

IMAGE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "webcam.jpg"
    )
)


def capture_frame():

    print("[VISION] Opening webcam...")

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("Could not open webcam.")

    ret, frame = camera.read()

    camera.release()

    if not ret:
        raise RuntimeError("Could not capture webcam frame.")

    success = cv2.imwrite(IMAGE_PATH, frame)

    if not success:
        raise RuntimeError("Could not save webcam frame.")

    print(f"[VISION] Image saved: {IMAGE_PATH}")

    return IMAGE_PATH


def look():

    image_path = capture_frame()

    print("[VISION] Reading image...")

    with open(image_path, "rb") as f:
        image_data = f.read()

    print(f"[VISION] Image bytes: {len(image_data)}")

    image_base64 = base64.b64encode(image_data).decode("utf-8")

    print(f"[VISION] Base64 size: {len(image_base64)}")

    payload = {
        "model": "gemma3:4b",
        "messages": [{
                "role": "user",
                "content": "Describe this image. Be concise.",
                "images": [image_base64]
            }], "stream": False
    }

    print("[VISION] Sending image to Gemma...")

    print("[VISION] Model:", payload["model"])
    print("[VISION] Messages:", len(payload["messages"]))
    print("[VISION] Image count:", len(payload["messages"][0]["images"]))
    print("[VISION] Image Base64 length:", len(payload["messages"][0]["images"][0]))

    with open("agent/debug_payload.json", "w", encoding="utf-8") as f: json.dump(payload, f,indent=2)

    print("[VISION] Debug payload saved.")

    response = requests.post(OLLAMA_URL, json=payload,timeout=120)

    print(f"[VISION] Ollama status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    print("[VISION] Ollama received the request.")

    return data["message"]["content"].strip()