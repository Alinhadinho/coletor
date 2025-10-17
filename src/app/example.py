import cv2
from pyzbar.pyzbar import decode
import time # Needed for time.sleep()

# ----------------- Part 2 & 3: Live Camera Scan with Reuse Prevention -----------------

# List to store successfully scanned and approved codes (Project Logic)
used_codes = [] 

# Initialize video capture (0 is usually the default webcam)
cap = cv2.VideoCapture(0)

# Optional: Set frame width (3) and height (4)
# cap.set(3, 640)
# cap.set(4, 480)

print("\n--- Live Scanner Initialized ---")
print("Press 'q' to exit the scanner window.")

while True:
    # Read the current frame from the camera
    success, frame = cap.read()

    if not success:
        break

    # Decode all codes in the current frame
    decoded_codes = decode(frame)

    for code in decoded_codes:
        # Decode the code data to a string
        code_data_string = code.data.decode('utf-8')

        # Check the used_codes list (Project Logic)
        if code_data_string not in used_codes:
            print(f"\n✅ APPROVED! You can enter.")
            print(f"Code: {code_data_string}")
            
            # Add the new code to the used list
            used_codes.append(code_data_string)
            
            # Use time.sleep to prevent immediate re-scan (Anti-spamming)
            time.sleep(5)
            
        else:
            print(f"\n❌ SORRY! This code has been already used.")
            print(f"Code: {code_data_string}")
            time.sleep(5) # Delay for user to read the rejection message

    # Display the live video feed
    cv2.imshow("Testing Code Scan", frame)

    # Wait for 1ms. If 'q' is pressed, break the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()