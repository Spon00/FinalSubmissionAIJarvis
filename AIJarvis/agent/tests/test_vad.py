import asyncio
from livekit.plugins import silero


async def main():

    print("Loading Silero VAD...")

    vad = silero.VAD.load()

    print("VAD loaded.")

    stream = vad.stream()

    print("VAD stream created.")

    print("Stream type:")
    print(type(stream))

    print()
    print("Stream attributes:")

    for item in dir(stream):

        if not item.startswith("__"):

            print(item)


if __name__ == "__main__":
    asyncio.run(main())