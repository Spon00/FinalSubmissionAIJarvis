import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# --------------------------------------------------
# CUDA DLL PATH
# --------------------------------------------------

venv = os.environ.get("VIRTUAL_ENV")

if not venv:
    raise RuntimeError("VIRTUAL_ENV is not set.")

CUDA_BIN = os.path.join(venv, "Lib", "site-packages", "nvidia", "cublas", "bin")

CUDNN_BIN = os.path.join(venv, "Lib", "site-packages", "nvidia", "cudnn", "bin")

print(f"[CUDA] cuBLAS path: {CUDA_BIN}")
print(f"[CUDA] cuDNN path:  {CUDNN_BIN}")

if not os.path.exists(
    os.path.join(CUDA_BIN, "cublas64_12.dll")
):
    raise RuntimeError(
        "cublas64_12.dll was not found."
    )

if not os.path.exists(
    os.path.join(CUDNN_BIN, "cudnn64_9.dll")
):
    raise RuntimeError(
        "cudnn64_9.dll was not found."
    )

# IMPORTANT:
# Keep these handles alive for the entire process.
_cuda_dll_handle = os.add_dll_directory(CUDA_BIN)
_cudnn_dll_handle = os.add_dll_directory(CUDNN_BIN)

# Also put them on PATH.
os.environ["PATH"] = (CUDA_BIN + os.pathsep + CUDNN_BIN + os.pathsep + os.environ["PATH"])

print("[CUDA] DLL directories configured.")


# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

import asyncio
import numpy as np

from dotenv import load_dotenv
from faster_whisper import WhisperModel

from livekit import agents, rtc
from livekit.agents.vad import VADEventType
from livekit.plugins import silero
from livekit.agents import vad
from agent.tts import speak

from llm import process_message
from vision import look


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

import ctranslate2

print()
print("=" * 50)
print("[CUDA] Testing CTranslate2...")
print("=" * 50)

print("[CUDA] Device count:", ctranslate2.get_cuda_device_count())

print("[CUDA] Supported CUDA types:", ctranslate2.get_supported_compute_types("cuda"))

# --------------------------------------------------
# WHISPER
# --------------------------------------------------

print("Loading Whisper...")

whisper = WhisperModel("base", device="cuda",compute_type="float16")

print("Whisper loaded.")


# --------------------------------------------------
# LIVEKIT
# --------------------------------------------------

server = agents.AgentServer()


# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------

@server.rtc_session()
async def entrypoint(ctx: agents.JobContext):

    print("Jarvis is connecting to LiveKit...")

    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

    print("Jarvis connected to LiveKit!")
    print(f"Room: {ctx.room.name}")
    print("Jarvis is waiting for microphone audio...")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):

        print()
        print("=" * 50)
        print("[TRACK] Track subscribed!")
        print(f"[TRACK] Participant: {participant.identity}")
        print(f"[TRACK] Kind: {track.kind}")
        print("=" * 50)

        if track.kind != rtc.TrackKind.KIND_AUDIO:
            print("[TRACK] Not an audio track. Ignoring.")
            return

        print("[TRACK] Audio track confirmed.")
        print("[TRACK] Starting process_audio()...")

        asyncio.create_task(process_audio(track))


# --------------------------------------------------
# TRANSCRIPTION
# --------------------------------------------------

def transcribe_audio(audio):

    segments, info = whisper.transcribe(audio, beam_size=5, language="en")

    text = ""

    for segment in segments:
        text += segment.text

    return text.strip()



def is_vision_command(text):

    text = text.lower().strip()

    vision_commands = [
        "what do you see",
        "what can you see",
        "look around",
        "look at this",
        "describe what you see",
        "describe this",
        "what is in front of you",
        "what's in front of you",
        "what is in front of me",
        "what's in front of me",
    ]

    return any(command in text for command in vision_commands)
# --------------------------------------------------
# AUDIO PROCESSING
# --------------------------------------------------


async def process_audio(track):

    print()
    print("=" * 50)
    print("[AUDIO] process_audio() STARTED")
    print("=" * 50)

    audio_stream = rtc.AudioStream(track, sample_rate=16000, num_channels=1)

    print("[AUDIO] AudioStream created.")

    print("[VAD] Loading Silero VAD...")

    vad = silero.VAD.load()

    print("[VAD] VAD loaded.")

    vad_stream = vad.stream()

    print("[VAD] VAD stream created.")

    # Store incoming audio frames
    audio_frames = []

    # Track whether the user is speaking
    speaking = False

    print("[VAD] Listening for speech...")

    async def feed_vad():

        async for event in audio_stream:

            frame = event.frame

            vad_stream.push_frame(frame)

    # Start feeding audio into VAD
    asyncio.create_task(feed_vad())

    # Process VAD events
    async for event in vad_stream:

        # -----------------------------------------
        # START OF SPEECH
        # -----------------------------------------

        if event.type == VADEventType.START_OF_SPEECH:

            print()
            print("[VAD] >>> START OF SPEECH")

            speaking = True
            audio_frames = []

            audio_frames.extend(event.frames)

        # -----------------------------------------
        # SPEECH CONTINUES
        # -----------------------------------------

        elif event.type == VADEventType.INFERENCE_DONE:

            if speaking:
                audio_frames.extend(event.frames)

        # -----------------------------------------
        # END OF SPEECH
        # -----------------------------------------

        elif event.type == VADEventType.END_OF_SPEECH:

            print()
            print("[VAD] <<< END OF SPEECH")

            speaking = False

            if not audio_frames:

                print("[VAD] No audio frames captured.")

                continue

            print(
                f"[AUDIO] Captured {len(audio_frames)} frames."
            )

            # -----------------------------------------
            # Convert LiveKit frames to numpy
            # -----------------------------------------

            samples = []

            for frame in audio_frames:

                data = np.frombuffer(frame.data, dtype=np.int16)

                samples.append(data)

            if not samples:

                print("[AUDIO] No samples available.")

                audio_frames = []

                continue

            audio = np.concatenate(samples)

            # Convert int16 -> float32
            audio = audio.astype(np.float32)

            audio /= 32768.0

            print(f"[AUDIO] Samples: {len(audio)}")
            

            print(f"[AUDIO] Duration: {len(audio) / 16000:.2f}s")

            # -----------------------------------------
            # Whisper
            # -----------------------------------------

            print()
            print("[WHISPER] Transcribing...")

            try:

                text = await asyncio.to_thread(transcribe_audio, audio)

            except Exception as e:

                print(f"[WHISPER ERROR] {type(e).__name__}: {e}")

                audio_frames = []

                continue

            text = text.strip()

            print()
            print(f"You: {text}")

            if not text:

                print("[WHISPER] No speech detected.")

                audio_frames = []

                continue

            # -----------------------------------------
            # EXIT
            # -----------------------------------------

            if text.lower() == "exit":

                print("[JARVIS] Exiting.")

                break

            # -----------------------------------------
            # RESPONSE
            # -----------------------------------------

            response = None

            # -----------------------------------------
            # VISION
            # -----------------------------------------

            if is_vision_command(text):

                print()
                print("[JARVIS] Vision command detected.")
                print("[VISION] Looking through webcam...")

                try:

                    response = await asyncio.to_thread(look)

                except Exception as e:

                    print()
                    print("[VISION ERROR]")
                    print(f"{type(e).__name__}: {e}")

                    response = ("I'm having trouble accessing my vision.")

            # -----------------------------------------
            # NORMAL LLM
            # -----------------------------------------

            else:

                print()
                print("[JARVIS] Sending to LLM...")

                try:

                    response = await asyncio.to_thread(process_message, text)

                except Exception as e:

                    print()
                    print("[LLM ERROR]")
                    print(f"{type(e).__name__}: {e}")

                    response = ("I'm having trouble processing that.")

            # -----------------------------------------
            # JARVIS RESPONSE
            # -----------------------------------------

            if response:

                response = response.strip()

                print()
                print(f"JARVIS: {response}")

                # Piper TTS
                try:

                    await asyncio.to_thread(speak, response)

                except Exception as e:

                    print()
                    print("[TTS ERROR]")
                    print(f"{type(e).__name__}: {e}")

            print()
            print("[VAD] Ready for next command.")

            audio_frames = []

# --------------------------------------------------
# START
# --------------------------------------------------

if __name__ == "__main__":

    agents.cli.run_app(server)