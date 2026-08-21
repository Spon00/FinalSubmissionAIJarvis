from piper import PiperVoice
import wave
import winsound
import os


# --------------------------------------------------
# PIPER
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "agent", "models", "en_US-lessac-medium.onnx")

OUTPUT_FILE = os.path.join(BASE_DIR, "agent", "tts_output.wav")


print("[TTS] Loading Piper...")

voice = PiperVoice.load(MODEL_PATH)

print("[TTS] Piper loaded.")


# --------------------------------------------------
# SPEAK
# --------------------------------------------------

def speak(text):

    if not text:
        return

    print(f"[TTS] Speaking: {text}")

    with wave.open(OUTPUT_FILE, "wb") as wav_file:

        voice.synthesize_wav(text, wav_file)

    winsound.PlaySound(OUTPUT_FILE, winsound.SND_FILENAME)

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)