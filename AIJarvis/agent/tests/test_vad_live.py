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

    async def monitor():

        async for event in stream:

            print(
                f"[VAD] "
                f"speaking={event.speaking} "
                f"probability={event.probability:.2f} "
                f"speech={event.speech_duration:.2f}s "
                f"silence={event.silence_duration:.2f}s"
            )

    monitor_task = asyncio.create_task(
        monitor()
    )

    print()
    print("Generating silence...")

    silence = np.zeros(
        16000,
        dtype=np.int16
    )

    for i in range(10):

        frame = rtc.AudioFrame(
            data=silence[
                i * 512:
                (i + 1) * 512
            ].tobytes(),

            sample_rate=16000,
            num_channels=1,
            samples_per_channel=512
        )

        stream.push_frame(frame)

        await asyncio.sleep(0.032)

    print()
    print("Finished sending audio.")

    stream.end_input()

    await monitor_task

    print("Done.")


asyncio.run(main())