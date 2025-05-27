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

def check_duplicate_object(object_name, save_dir):
    if os.path.exists(save_dir):
        root = tk.Tk()
        root.withdraw()
        while True:
            response = simpledialog.askstring(
                "Duplicate Object",
                f"Object '{object_name}' already exists. Enter 1 to overwrite, 2 to append, 3 to cancel:",
                parent=root
            )
            if response is None:
                root.destroy()
                exit("No option selected!")
            if response == '1':
                root.destroy()
                return 'overwrite'
            elif response == '2':
                root.destroy()
                return 'append'
            elif response == '3':
                root.destroy()
                exit("Operation cancelled by user.")
            else:
                messagebox.showerror("Invalid Input", "Please enter a valid option (1, 2, or 3)")
    return 'new'

object_name = get_object_name()

root_dir = os.environ.get("IMS_INSTALLATION_DIR", os.path.dirname(os.path.abspath(__file__)))
save_dir = os.environ.get("IMS_DATA_DIR", os.path.join(root_dir, "data"))
save_dir = os.path.join(save_dir, object_name)

action = check_duplicate_object(object_name, save_dir)
if action == 'overwrite':
    if os.path.exists(save_dir):
        for file in os.listdir(save_dir):
            os.remove(os.path.join(save_dir, file))
elif action == 'append':
    pass

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)
fps = 30

if object_name.lower() == "noobject":
    total_images = 1500
else:
    total_images = 300

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
