import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel


print("Loading Whisper...")

model = WhisperModel("base", device="cuda", compute_type="float16")

print("Whisper loaded.")


def listen():
    sample_rate = 16000
    chunk_duration = 0.1
    chunk_size = int(sample_rate * chunk_duration)

    silence_threshold = 0.01
    silence_duration = 1.2
    max_duration = 10

    print("\nListening...")

    audio_chunks = []
    speaking = False
    silence_time = 0
    total_time = 0

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=chunk_size
    ) as stream:

        while total_time < max_duration:

            audio, overflowed = stream.read(chunk_size)

            audio = audio.flatten()

            volume = np.sqrt(np.mean(audio ** 2))

            audio_chunks.append(audio)

            if volume > silence_threshold:
                speaking = True
                silence_time = 0

            elif speaking:
                silence_time += chunk_duration

                if silence_time >= silence_duration:
                    break

            total_time += chunk_duration

    print("Recording finished.")
    print("Transcribing...")

    audio = np.concatenate(audio_chunks)

    segments, info = model.transcribe(audio, beam_size=5)

    text = " ".join(segment.text for segment in segments).strip()

    return text