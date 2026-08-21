import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
RECORD_SECONDS = 5


print("Loading Whisper...")
model = WhisperModel(
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

print("Recording finished.")
print("Transcribing...")


audio = np.squeeze(audio)

segments, info = model.transcribe(
    audio,
    beam_size=5
)


text = ""

for segment in segments:
    text += segment.text


print()
print("You said:")
print(text.strip())