from vision import look

try:
    description = look()

    print()
    print("JARVIS:")
    print(description)

except Exception as e:
    print()
    print("VISION ERROR:")
    print(e)