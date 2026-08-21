import cv2

print("Opening webcam...")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("Webcam opened.")
print("Press SPACE to capture a frame.")
print("Press ESC to exit.")

while True:
    ret, frame = camera.read()

    if not ret:
        print("ERROR: Could not read frame.")
        break

    cv2.imshow("JARVIS Webcam", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 32:  # SPACE
        cv2.imwrite("agent/webcam.jpg", frame)
        print("Frame captured: agent/webcam.jpg")
        break

    elif key == 27:  # ESC
        print("Cancelled.")
        break

camera.release()
cv2.destroyAllWindows()