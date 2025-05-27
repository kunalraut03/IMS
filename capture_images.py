import cv2
import os
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess

class ObjectNameDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Enter object name:").grid(row=0)
        self.entry = tk.Entry(master)
        self.entry.grid(row=0, column=1)
        return self.entry

    def apply(self):
        self.object_name = self.entry.get().strip().lower().replace(" ", "_")

def get_object_name():
    root = tk.Tk()
    root.withdraw()
    while True:
        dialog = ObjectNameDialog(root)
        object_name = dialog.object_name
        if object_name is None:
            exit("No object name provided!")
        if 0 < len(object_name) <= 20 and object_name.isalnum():
            break
        messagebox.showerror("Invalid Input", "Please enter a valid name (alphanumeric, 1-20 characters)")
    root.destroy()
    return object_name

root_dir = os.environ.get("IMS_INSTALLATION_DIR", os.path.dirname(os.path.abspath(__file__)))
data_dir = os.environ.get("IMS_DATA_DIR", os.path.join(root_dir, "data"))

def check_duplicate_object(object_name):
    save_dir = os.path.join(data_dir, object_name)
    if os.path.exists(save_dir):
        root = tk.Tk()
        root.withdraw()
        response = simpledialog.askstring("Duplicate Object", f"Object '{object_name}' already exists. Enter 1 to overwrite, 2 to append, 3 to cancel:", parent=root)
        root.destroy()
        if response == '1':
            return 'overwrite'
        elif response == '2':
            return 'append'
        elif response == '3':
            return 'cancel'
        else:
            messagebox.showerror("Invalid Input", "Please enter a valid option (1, 2, or 3)")
            return check_duplicate_object(object_name)
    return 'new'

def get_next_image_index(save_dir, object_name):
    existing_images = [f for f in os.listdir(save_dir) if f.startswith(object_name) and f.endswith('.jpg')]
    if not existing_images:
        return 1
    existing_indices = [int(f.split('_')[-1].split('.')[0]) for f in existing_images]
    return max(existing_indices) + 1

def select_webcam():
    root = tk.Tk()
    root.withdraw()
    while True:
        dialog = simpledialog.askstring("Select Webcam", "Enter webcam index (0, 1, 2, ...):", parent=root)
        if dialog is None:
            exit("No webcam index provided!")
        try:
            webcam_index = int(dialog)
            break
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for webcam index")
    root.destroy()
    return webcam_index

while True:
    object_name = get_object_name()
    action = check_duplicate_object(object_name)
    save_dir = os.path.join(data_dir, object_name)
    if action == 'overwrite':
        if os.path.exists(save_dir):
            for file in os.listdir(save_dir):
                os.remove(os.path.join(save_dir, file))
        break
    elif action == 'append':
        subprocess.run(["python", "append_images.py"])
        exit()
    elif action == 'cancel':
        exit("Operation cancelled by user.")
    else:
        break

os.makedirs(save_dir, exist_ok=True)

webcam_index = select_webcam()
cap = cv2.VideoCapture(webcam_index)
cap.set(cv2.CAP_PROP_FPS, 30)
fps = 30
capture_duration = 10
total_images = min(1500, 300 if action == 'append' else fps * capture_duration)
count = get_next_image_index(save_dir, object_name) - 1

drawing = False
top_left = None
bottom_right = None
confirmed_box = False

def draw_rectangle(event, x, y, flags, param):
    global drawing, top_left, bottom_right, confirmed_box
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        top_left = (x, y)
        bottom_right = None
        confirmed_box = False
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        bottom_right = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        bottom_right = (x, y)

cv2.namedWindow("Image Capture", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Image Capture", draw_rectangle)

start_capture = False
while not start_capture:
    ret, frame = cap.read()
    if not ret:
        break

    if top_left and bottom_right:
        box_color = (255, 0, 0) if confirmed_box else (0, 255, 0)
        cv2.rectangle(frame, top_left, bottom_right, box_color, 2)

    cv2.putText(frame, "Draw box, ESC to reset, Y to confirm", (25, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Press 'S' to start capturing", (25, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "Press 'E' to stop capturing", (25, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 139), 2)
    cv2.putText(frame, f"Object: {object_name}", (25, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Image Capture", frame)

    key = cv2.waitKey(1)
    if key == 27:
        top_left = None
        bottom_right = None
        confirmed_box = False
    elif key == ord('y'):
        if top_left and bottom_right:
            confirmed_box = True
    elif key == ord('s'):
        if (top_left and bottom_right and confirmed_box) or (not top_left and not bottom_right):
            start_capture = True
        else:
            print("Please confirm the bounding box (press 'Y') or press 'S' without drawing a box to capture full frame.")
            continue
    elif key == ord('e'):
        cap.release()
        cv2.destroyAllWindows()
        exit("User exited before capture")

start_time = time.time()
while count < total_images:
    ret, frame = cap.read()
    if not ret:
        break

    if top_left and bottom_right and confirmed_box:
        x1, y1 = top_left
        x2, y2 = bottom_right
        cropped_frame = frame[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
    else:
        cropped_frame = frame

    window_height, window_width = frame.shape[:2]
    resized_frame = cv2.resize(cropped_frame, (window_width, window_height))

    display_frame = resized_frame.copy()
    cv2.putText(display_frame, f"Captured: {count}/{total_images}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Image Capture", display_frame)

    img_path = os.path.join(save_dir, f"{object_name}_{count+1:03d}.jpg")
    cv2.imwrite(img_path, cropped_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    count += 1

    if cv2.waitKey(1) & 0xFF == ord('e'):
        break

    elapsed_time = time.time() - start_time
    if elapsed_time < count / fps:
        time.sleep((count / fps) - elapsed_time)

cap.release()
cv2.destroyAllWindows()
print(f"Captured {count} images of '{object_name}' in {save_dir}")