import json
import requests
from ollama import chat

def get_weather(city):
    url = "http://localhost:5678/webhook-test/jarvis/weather"

    response = requests.post(url, json={"city": city})

    response.raise_for_status() 

    return response.json()

