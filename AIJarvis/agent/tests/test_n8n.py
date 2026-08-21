import requests

url = "http://localhost:5678/webhook/jarvis/weather"

data = {
    "city": "St. John's"
}

response = requests.post(url, json=data)

print("Status:", response.status_code)
print("Response:", response.text)