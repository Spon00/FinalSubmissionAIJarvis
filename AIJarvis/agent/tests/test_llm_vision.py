from llm import process_message

print("Testing JARVIS vision command...")

response = process_message(
    "Jarvis, what do you see?"
)

print()
print("JARVIS:")
print(response)