from stt import listen


while True:
    text = listen()

    if text.lower() == "exit":
        break

    print(f"\nYou said: {text}")