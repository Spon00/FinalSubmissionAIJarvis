# Jarvis Setup Instructions, Architecture, and Known Limitations

## Project Overview

Jarvis is a local AI voice assistant built around:

* Python
* Ollama
* Gemma 3:4B
* Gemma 4:e4b
* Faster-Whisper
* Silero VAD
* Piper TTS
* LiveKit
* OpenCV
* n8n
* Open-Meteo

The primary processing stays local. Ollama handles language and vision processing, Faster-Whisper handles speech recognition, Piper handles speech synthesis, and OpenCV captures webcam images.

n8n provides external tool functionality such as weather information.

#

# Prerequisites

## Hardware

Recommended:

* Windows 10 or Windows 11
* NVIDIA GPU
* At least 8 GB system RAM
* 16 GB+ system RAM recommended
* NVIDIA GPU with sufficient VRAM for the selected Ollama model
* Working microphone
* Working speakers/headphones
* Webcam for vision functionality

The amount of available GPU VRAM directly affects which Ollama models can run comfortably.

---

# Required Software

Install:

* Python 3.13
* Git
* Ollama
* Docker Desktop
* NVIDIA GPU drivers

The project uses a Python virtual environment.

---

# Python Virtual Environment

Open PowerShell in the project directory.

Create the virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Verify Python:

```powershell
python --version
```

Verify pip:

```powershell
python -m pip --version
```

Use:

```powershell
python -m pip
```

instead of relying on the standalone `pip` executable.

---

# Python Dependencies

Install the required packages:

```powershell
python -m pip install numpy
python -m pip install opencv-python
python -m pip install requests
python -m pip install python-dotenv
python -m pip install faster-whisper
python -m pip install piper-tts
python -m pip install livekit
python -m pip install livekit-agents
python -m pip install livekit-plugins-silero
python -m pip install ctranslate2
```

Verify Piper:

```powershell
python -c "import piper; print('Piper import OK')"
```

Verify Faster-Whisper:

```powershell
python -c "import faster_whisper; print('Faster-Whisper import OK')"
```

Verify OpenCV:

```powershell
python -c "import cv2; print('OpenCV import OK')"
```

---

# Ollama Setup

Install Ollama and make sure the Ollama service is running.

Verify:

```powershell
ollama --version
```

Jarvis uses 2 models, gemma4:e4b for n8n workflow and regular conversation and gemma3:4b is used for video frame capture(My gemma4:e4b model was borken adn vision did not work on it):


```text
gemma4:e4b
```

```text
gemma3:4b
```

Pull the models:

```powershell
ollama pull gemma4:e4b
```

```powershell
ollama pull gemma3:4b
```

Verify it:

```powershell
ollama list
```

---


# Piper TTS Setup

Jarvis uses Piper for local text-to-speech.

The current voice configuration uses:

```text
agent/models/en_US-lessac-medium.onnx
```

The corresponding model configuration file should also be present where required by the Piper installation.

The TTS module loads the voice:

```python
voice = PiperVoice.load(MODEL_PATH)
```

Jarvis generates a temporary WAV file and plays it through Windows audio.

Example configuration:

```text
agent/models/en_US-lessac-medium.onnx
```

Test Piper independently before running the full application.

#

# LiveKit Configuration

Jarvis uses LiveKit to transport microphone audio into the Python voice agent.

The LiveKit server must be accessible before starting Jarvis.

The application connects through the LiveKit configuration supplied to the LiveKit Agents CLI.

The required environment variables depend on the LiveKit deployment.

For a LiveKit Cloud configuration, the environment file should contain the credentials supplied by the LiveKit project:

```text
LIVEKIT_URL=your_livekit_server_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

Do not commit these values to Git.

The exact values should come from the LiveKit project configuration.

---

# Environment Variables

Create a `.env` file in the project root.

Example:

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

If additional services are added later, their API credentials should also be stored in `.env`.

Do not place API keys directly inside Python source files.

Do not commit `.env` to Git.

Add it to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
```

---

# n8n Setup

n8n provides Jarvis with external tool functionality.

The current weather workflow uses:

```text
Jarvis
   │
   │ HTTP POST
   ▼
n8n Webhook
   │
   ▼
Geocoding API
   │
   ▼
Open-Meteo Forecast API
   │
   ▼
Weather Response
   │
   ▼
Jarvis
```

n8n is running through Docker.

Start Docker Desktop first.

Then start the n8n container according to the project's Docker configuration.

Verify the n8n editor is accessible at:

```text
http://localhost:5678
```

---

# Importing the n8n Workflow

To import the Jarvis workflow:

1. Start Docker Desktop.
2. Start the n8n container.
3. Open:

```text
http://localhost:5678
```

4. Log into n8n if authentication is enabled.
5. Open the workflow area.
6. Select the option to import a workflow.
7. Select the provided Jarvis n8n workflow JSON file.
8. Import the workflow.
9. Verify the webhook node.
10. Verify the geocoding request.
11. Verify the Open-Meteo request.
12. Save the workflow.
13. Activate the workflow.

The webhook endpoint used by Jarvis is:

```text
http://localhost:5678/webhook/jarvis/weather
```

---


# Starting Jarvis

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Make sure:

* Ollama is running.
* The required Ollama model is available.
* Docker Desktop is running.
* n8n is running.
* LiveKit is configured.
* The webcam is available.
* The microphone is available.

Start the voice agent using the project's normal Python entry point.

For the current implementation, this is the voice agent:

```text
lk agent dev agent/voice_agent.py --url "wss://jarvis-project-zpym1k41.livekit.cloud" --api-key "YOUR_API_KEY" --api-secret "YOUR_API_SECRET"
```

The application should display messages similar to:

```text
Jarvis is connecting to LiveKit...
Jarvis connected to LiveKit!
Jarvis is waiting for microphone audio...
```

---

# 22. Full System Test

Test the system in this order.

## Test 1: Voice Detection

Say:

```text
Hello Jarvis.
```

Expected:

```text
[VAD] >>> START OF SPEECH
[VAD] <<< END OF SPEECH
```

---

## Test 2: Speech Recognition

Jarvis should display the recognized text:

```text
You: Hello Jarvis.
```

---

## Test 3: LLM

Ask:

```text
Hello Jarvis.
```

Jarvis should generate a response through Ollama.

---

## Test 4: TTS

Jarvis should speak the generated response through Piper.

---

## Test 5: Vision

Say:

```text
What do you see?
```

Expected flow:

```text
[VISION] Vision command detected.
[VISION] Looking through webcam...
[VISION] Opening webcam...
[VISION] Image saved...
[VISION] Sending image to Gemma...
[VISION] Ollama status: 200
```

Jarvis should describe the captured image.

---

## Test 6: Weather

Say:

```text
What is the weather in St. John's?
```

Expected flow:

```text
[TOOL] Calling n8n weather tool for: St. John's
[TOOL] n8n status: 200
```

Jarvis should return the weather information.

---

# Known Limitations

## GPU and VRAM

Ollama, Faster-Whisper, and other components can compete for GPU memory.

Larger language models require substantially more VRAM.

Running multiple GPU-intensive models simultaneously can cause resource exhaustion.

The project is therefore better suited to a system with a dedicated NVIDIA GPU and adequate VRAM.

---

## Vision Response Time

Vision requests are slower than normal text requests because Jarvis must:

1. Capture the webcam image.
2. Read the image.
3. Encode the image.
4. Send it to Ollama.
5. Run visual inference.
6. Generate the response.
7. Generate speech with Piper.

---

## Speech Recognition Accuracy

Faster-Whisper can occasionally misinterpret speech.

Accuracy depends on:

* Microphone quality
* Background noise
* Distance from microphone
* Speech clarity
* Accent
* Speaking speed

A recognized location name can therefore differ from what was spoken.

---

## Weather Requires n8n

Weather functionality depends on the n8n workflow.

If n8n is unavailable, Jarvis cannot use the configured weather tool.

Weather information also depends on the external weather service.

---

## LiveKit Dependency

The current voice architecture depends on LiveKit for audio transport.

If the LiveKit service or configuration is unavailable, microphone audio cannot reach the Jarvis voice agent.

---

## LLM Response Latency

Local inference speed depends on:

* GPU performance
* Available VRAM
* Model size
* Context length
* Image size
* Number of simultaneous processes

Longer responses take longer to generate and speak.

---

## No Continuous Conversation Interruption

The current implementation processes speech, waits for the response, and then uses TTS.

It does not yet provide full natural conversation features such as:

* Interrupting Jarvis while it speaks
* Simultaneous listening and speaking
* Advanced turn-taking
* Automatic interruption detection

---


# Security and Privacy

Jarvis is designed around local processing.

The following components operate locally:

* Ollama
* Gemma
* Faster-Whisper
* Silero VAD
* Piper
* OpenCV

The weather tool sends location queries through n8n to external weather services.

LiveKit also handles the audio transport according to the configured LiveKit deployment.

API keys and secrets must never be committed to the project repository.

Use:

```text
.env
```

for credentials.

Add sensitive files to:

```text
.gitignore
```

---

# Current Capabilities

The current Jarvis implementation supports:

* Microphone input
* LiveKit audio transport
* Voice activity detection
* Speech recognition
* Local LLM responses
* Local text-to-speech
* Webcam capture
* Vision commands
* Image analysis through Gemma
* n8n tool calls
* Weather queries
* Spoken weather responses
* Multiple voice interactions in one session

---


# Recommended Startup Checklist

Before starting Jarvis:


- NVIDIA drivers installed
- Python installed
- Virtual environment activated
- Python dependencies installed
- CUDA libraries available
- Ollama installed
- Gemma4:e4b downloaded
- Gemma 3 4B downloaded
- Piper voice model installed
- LiveKit configured
- LiveKit credentials available
- Docker Desktop running
- n8n running
- Weather workflow imported
- Weather workflow activated
- Webcam available
- Microphone available
- Speakers/headphones available

Once these requirements are satisfied, start the Jarvis voice agent and perform the full system test.
