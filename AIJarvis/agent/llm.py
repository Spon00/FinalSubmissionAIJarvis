import json
import os
import requests

from ollama import chat
from vision import look


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_OPTIONS = {
    "num_predict": 500,
    "temperature": 0.1
}

N8N_WEATHER_URL = "http://localhost:5678/webhook/jarvis/weather"

CONVERSATION_FILE = os.path.join(os.path.dirname(__file__), "conversation.json")

# Number of previous messages kept in memory.
# The system message is always preserved.
MAX_HISTORY_MESSAGES = 20


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are JARVIS, a helpful local AI assistant.

You communicate naturally and concisely.

You have access to two tools:

1. Weather
   - Provides current weather information for a city.

2. Vision
   - Provides a description of what the webcam currently sees.

The application handles tool execution outside the LLM.

When weather or vision information is provided to you, use that
information to answer the user's original question.

Do not mention internal tools, APIs, JSON, n8n, Ollama, or implementation
details unless the user specifically asks about them.

Keep responses concise and natural because your responses are spoken
through text-to-speech.
"""


# ============================================================
# CONVERSATION MEMORY
# ============================================================

def load_messages():
    """
    Load conversation history from disk.
    """

    try:

        with open(CONVERSATION_FILE, "r", encoding="utf-8") as file:

            messages = json.load(file)

            if not isinstance(messages, list):
                raise ValueError("Conversation file must contain a list.")

            return messages

    except (FileNotFoundError, json.JSONDecodeError, ValueError):

        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]


def save_messages(messages):
    """
    Save conversation history to disk.
    """

    try:

        with open(CONVERSATION_FILE, "w", encoding="utf-8") as file:

            json.dump(messages, file, indent=4, ensure_ascii=False)

    except OSError as e:

        print(f"[MEMORY ERROR] Could not save conversation: {e}")


def trim_messages(messages):
    """
    Keep the system prompt plus the most recent messages.

    This prevents conversation.json from growing indefinitely.
    """

    if not messages:
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    system_message = messages[0]

    if system_message.get("role") != "system":

        system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT
        }

    recent_messages = messages[1:]

    recent_messages = recent_messages[
        -MAX_HISTORY_MESSAGES:
    ]

    return [
        system_message,
        *recent_messages
    ]


messages = load_messages()

messages = trim_messages(messages)


# ============================================================
# OLLAMA
# ============================================================

def prompt_ollama(messages):
    """
    Send conversation to Ollama and return the complete response.
    """

    print(f"[LLM] Sending request to {OLLAMA_MODEL}...")

    try:

        response = chat(model=OLLAMA_MODEL, messages=messages, stream=False, options=OLLAMA_OPTIONS)

        content = response.message.content

        if not content:
            return None

        return content.strip()

    except Exception as e:

        print()
        print("[LLM ERROR]")
        print(f"{type(e).__name__}: {e}")

        return None


# ============================================================
# WEATHER
# ============================================================

def get_weather(city):
    """
    Call the n8n weather workflow.
    """

    print(
        f"[TOOL] Calling n8n weather tool for: {city}"
    )

    try:

        response = requests.post(N8N_WEATHER_URL, json={"city": city}, timeout=30)

        print(f"[TOOL] n8n status: " f"{response.status_code}")

        print(f"[TOOL] n8n response: " f"{response.text}")

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        print(f"[TOOL ERROR] {type(e).__name__}: {e}")

        return None

    except ValueError as e:

        print(f"[TOOL ERROR] Invalid JSON response: {e}")

        return None


# ============================================================
# WEATHER DETECTION
# ============================================================

def is_weather_request(text):

    weather_keywords = [
        "weather",
        "temperature",
        "forecast",
        "raining",
        "rain",
        "snow",
        "wind",
        "humidity"
    ]

    text = text.lower()

    return any(keyword in text for keyword in weather_keywords)


def extract_city(text):

    text = text.strip()

    patterns = [
        "weather in ",
        "weather at ",
        "weather for ",
        "temperature in ",
        "temperature at ",
        "temperature for ",
        "forecast for ",
        "forecast in ",
        "forecast at "
    ]

    lower_text = text.lower()

    for pattern in patterns:

        if pattern in lower_text:

            index = lower_text.index(pattern)

            city = text[
                index + len(pattern):
            ]

            city = city.strip()

            city = city.rstrip("?.!,")

            return city

    return None


# ============================================================
# VISION
# ============================================================

def is_vision_request(text):

    vision_phrases = [
        "what do you see",
        "what can you see",
        "look at this",
        "look at that",
        "look at the camera",
        "look around",
        "what is in front of you",
        "what's in front of you",
        "what is in front of me",
        "what's in front of me",
        "describe what you see",
        "describe the image",
        "describe this",
        "can you see me",
        "do you see me"
    ]

    text = text.lower()

    return any(phrase in text for phrase in vision_phrases)


# ============================================================
# WEATHER RESPONSE
# ============================================================

def answer_weather(user_input, city, weather):
    """
    Give Ollama the weather data and ask it to answer
    the original user question.
    """

    weather_message = {
        "role": "user",
        "content": (
            "Use the following current weather information "
            "to answer the user's original question.\n\n"
            f"User question:\n{user_input}\n\n"
            f"City:\n{city}\n\n"
            f"Weather data:\n"
            f"{json.dumps(weather, ensure_ascii=False)}\n\n"
            "Give a complete, concise spoken response. "
            "Do not mention tools, APIs, JSON, or internal processing."
        )
    }

    response = prompt_ollama([{"role": "system", "content": SYSTEM_PROMPT}, weather_message])

    return response


# ============================================================
# VISION RESPONSE
# ============================================================

def answer_vision(user_input, vision_result):
    """
    Give Ollama the webcam description and ask it to answer
    the original user question.
    """

    vision_message = {
        "role": "user",
        "content": (
            "Use the following webcam vision information "
            "to answer the user's original question.\n\n"
            f"User question:\n{user_input}\n\n"
            f"Webcam description:\n"
            f"{vision_result}\n\n"
            "Give a complete, concise spoken response. "
            "Do not mention tools, APIs, JSON, or internal processing."
        )
    }

    response = prompt_ollama([{"role": "system", "content": SYSTEM_PROMPT}, vision_message])

    return response


# ============================================================
# GENERAL CONVERSATION
# ============================================================

def answer_general(user_input):

    global messages

    messages.append({"role": "user", "content": user_input})

    messages = trim_messages(messages)

    response = prompt_ollama(messages)

    if response:

        messages.append({"role": "assistant", "content": response})

        messages = trim_messages(messages)

        save_messages(messages)

    return response


# ============================================================
# MAIN MESSAGE PROCESSOR
# ============================================================

def process_message(user_input):

    global messages

    if not user_input:
        return None

    user_input = user_input.strip()

    if not user_input:
        return None

    print()
    print(f"[LLM] Processing: {user_input}")

    # ========================================================
    # VISION
    # ========================================================

    if is_vision_request(user_input):

        print("[VISION] Vision request detected.")

        try:

            vision_result = look()

            if not vision_result:

                return ("I couldn't determine what the camera is seeing.")

            print("[VISION] Vision result received.")

            response = answer_vision(user_input, vision_result)

            if response:

                messages.append({"role": "user", "content": user_input})

                messages.append({"role": "assistant", "content": response})

                messages = trim_messages(messages)

                save_messages(messages)

                return response

            return ("I can see the camera image, but I am having trouble processing it.")

        except Exception as e:

            print()
            print("[VISION ERROR]")
            print(f"{type(e).__name__}: {e}")

            return ("I'm having trouble accessing the webcam right now.")

    # ========================================================
    # WEATHER
    # ========================================================

    if is_weather_request(user_input):

        print("[WEATHER] Weather request detected.")

        city = extract_city(user_input)

        if city:

            print(f"[WEATHER] City: {city}")

            weather = get_weather(city)

            if weather:

                response = answer_weather(user_input, city, weather)

                if response:

                    messages.append({"role": "user", "content": user_input})

                    messages.append({"role": "assistant", "content": response})

                    messages = trim_messages(messages)

                    save_messages(messages)

                    return response

                return ("I retrieved the weather data, but I was unable to generate a response.")

            return (f"I couldn't retrieve the weather for {city}.")

        # Weather request without a city

        return ("What city would you like the weather for?")

    # ========================================================
    # GENERAL CHAT
    # ========================================================

    return answer_general(
        user_input
    )


# ============================================================
# OPTIONAL TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 50)
    print("JARVIS LLM TEST")
    print("=" * 50)

    while True:

        try:

            user_input = input("\nYou: ").strip()

        except KeyboardInterrupt:

            print()
            break

        if user_input.lower() == "exit":

            break

        response = process_message(
            user_input
        )

        if response:

            print()
            print(f"JARVIS: {response}")



   



    
