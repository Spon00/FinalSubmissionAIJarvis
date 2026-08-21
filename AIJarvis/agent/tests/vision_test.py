import base64
import requests

IMAGE_PATH = "agent/webcam.jpg"

print("Loading image...")

with open(IMAGE_PATH, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

print(f"Image loaded: {len(image_base64)} base64 characters")
print("Sending webcam image to Gemma...")

payload = {
    "model": "gemma4:e4b",
    "messages": [
        {
            "role": "user",
            "content": "Describe what you see in this image. Be concise.",
            "images": [image_base64]
        }
    ],
    "stream": False
}

response = requests.post(
    "http://localhost:11434/api/chat",
    json=payload
)

response.raise_for_status()

data = response.json()

print()
print("JARVIS:")
print(data["message"]["content"])