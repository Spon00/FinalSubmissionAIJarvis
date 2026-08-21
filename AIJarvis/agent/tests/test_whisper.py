import time
import sounddevice as sd
import numpy as np
import os
import sys

venv = os.environ.get("VIRTUAL_ENV")

if venv:
    cublas_path = os.path.join(
        venv,
        "Lib",
        "site-packages",
        "nvidia",
        "cublas",
        "bin"
    )

    cudnn_path = os.path.join(
        venv,
        "Lib",
        "site-packages",
        "nvidia",
        "cudnn",
        "bin"
    )

    os.add_dll_directory(cublas_path)
    os.add_dll_directory(cudnn_path)

    os.environ["PATH"] = (
        cublas_path
        + os.pathsep
        + cudnn_path
        + os.pathsep
        + os.environ["PATH"]
    )

from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
RECORD_SECONDS = 5


print("Loading Whisper...")

whisper = WhisperModel(
    "base",
    device="cuda",
    compute_type="float16"
)

print("Whisper loaded.")

print()
print("Speak for 5 seconds...")
print()

audio = sd.rec(
    int(RECORD_SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32"
)

sd.wait()

audio = np.squeeze(audio)

print("Recording finished.")
print("Transcribing...")

start = time.perf_counter()

segments, info = whisper.transcribe(
    audio,
    beam_size=5,
    language="en"
)

text = ""

for segment in segments:
    text += segment.text

elapsed = time.perf_counter() - start

print()
print("You said:")
print(text.strip())

print()
print(f"Transcription time: {elapsed:.2f} seconds")