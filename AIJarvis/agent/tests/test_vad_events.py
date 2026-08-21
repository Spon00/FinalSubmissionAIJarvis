import asyncio
import numpy as np

from livekit import rtc
from livekit.plugins import silero


async def main():

    print("Loading Silero VAD...")

    vad = silero.VAD.load()

    print("VAD loaded.")

    stream = vad.stream()

    print("VAD stream created.")
    print("Listening for VAD events...")

    async def read_events():

        async for event in stream:

            print()
            print("EVENT RECEIVED")
            print("Type:", type(event))
            print("Event:", event)
            print("Attributes:", dir(event))
            print()

    event_task = asyncio.create_task(read_events())

    print("Creating test audio...")

    # 1 second of silence
    silence = np.zeros(
        16000,
        dtype=np.int16
    )

    frame = rtc.AudioFrame(
        data=silence.tobytes(),
        sample_rate=16000,
        num_channels=1,
        samples_per_channel=16000
    )

    print("Sending audio to VAD...")

    stream.push_frame(frame)

    await asyncio.sleep(2)

    print("Closing VAD stream...")

    stream.end_input()

    await event_task

    print("Finished.")


asyncio.run(main())