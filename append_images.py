import cv2
import os
import time
import tkinter as tk
from tkinter import simpledialog, messagebox

def get_object_name():
    root = tk.Tk()
    root.withdraw()
    while True:
        dialog = simpledialog.askstring("Object Name", "Renter object name:", parent=root)
        if dialog is None:
            exit("No object name provided!")
        object_name = dialog.strip().lower().replace(" ", "_")
        if 0 < len(object_name) <= 20 and object_name.isalnum():
            break
        messagebox.showerror("Invalid Input", "Please enter a valid name (alphanumeric, 1-20 characters)")
    root.destroy()
    return object_name

def get_next_image_index(save_dir, object_name):
    existing_images = [f for f in os.listdir(save_dir) if f.startswith(object_name) and f.endswith('.jpg')]
    if not existing_images:
        return 1
    existing_indices = [int(f.split('_')[-1].split('.')[0]) for f in existing_images]
    return max(existing_indices) + 1

object_name = get_object_name()

root_dir = "C:\\Users\\kaymh\\Downloads\\VIGYAN ASHRAM files\\IMS\\ver3.1"
save_dir = os.path.join(root_dir, "data", object_name)

if not os.path.exists(save_dir):
    exit(f"Object '{object_name}' does not exist. Please capture initial images first.")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)
fps = 30
total_images = 1500
count = get_next_image_index(save_dir, object_name) - 1

cv2.namedWindow("Image Capture", cv2.WINDOW_NORMAL)

start_capture = False
while not start_capture:
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.putText(frame, "Press 'S' to start capturing", (25, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "Press 'E' to stop capturing", (25, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 139), 2)
    cv2.putText(frame, f"Object: {object_name}", (25, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Image Capture", frame)
    
    key = cv2.waitKey(1)
    if key == ord('s'):
        start_capture = True
    elif key == ord('e'):
        cap.release()
        cv2.destroyAllWindows()
        exit("User exited before capture")

start_time = time.time()
while count < total_images:
    ret, frame = cap.read()
    if not ret:
        break

    display_frame = frame.copy()
    cv2.putText(display_frame, f"Captured: {count}/{total_images}", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Image Capture", display_frame)

    img_path = os.path.join(save_dir, f"{object_name}_{count+1:03d}.jpg")
    cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    count += 1

    if cv2.waitKey(1) & 0xFF == ord('e'):
        break

    elapsed_time = time.time() - start_time
    if elapsed_time < count / fps:
        time.sleep((count / fps) - elapsed_time)

cap.release()
cv2.destroyAllWindows()
print(f"Captured {count} images of '{object_name}' in {save_dir}")
