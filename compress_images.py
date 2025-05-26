from PIL import Image, ImageEnhance
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import cv2
import numpy as np

class ImageProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Quality Manager")
        self.root.geometry("600x500")
        
        self.input_dir = os.getenv("IMS_INPUT_DIR", "")
        self.output_dir = os.getenv("IMS_OUTPUT_DIR", "")
        
        if not self.input_dir or not self.output_dir:
            default_dir = os.path.join("C://IMS", "data")
            self.input_dir = default_dir
            self.output_dir = default_dir
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        dir_frame = ttk.LabelFrame(main_frame, text="Directory Selection", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        self.dir_var = tk.StringVar(value=self.input_dir)
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=50).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(row=0, column=1, padx=5, pady=5)
        
        quality_frame = ttk.LabelFrame(main_frame, text="Quality Settings", padding="5")
        quality_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quality_frame, text="Compression Quality:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.quality_var = tk.IntVar(value=50)
        self.quality_scale = ttk.Scale(quality_frame, from_=10, to=100, orient=tk.HORIZONTAL, 
                                       variable=self.quality_var, length=300)
        self.quality_scale.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(quality_frame, textvariable=self.quality_var).grid(row=0, column=2, padx=5, pady=5)
        
        enhance_frame = ttk.LabelFrame(main_frame, text="Enhancement Settings", padding="5")
        enhance_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(enhance_frame, text="Brightness:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.brightness_var = tk.DoubleVar(value=1.0)
        ttk.Scale(enhance_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL, 
                  variable=self.brightness_var, length=300).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(enhance_frame, textvariable=self.brightness_var).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(enhance_frame, text="Contrast:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.contrast_var = tk.DoubleVar(value=1.0)
        ttk.Scale(enhance_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL, 
                  variable=self.contrast_var, length=300).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(enhance_frame, textvariable=self.contrast_var).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(enhance_frame, text="Sharpness:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.sharpness_var = tk.DoubleVar(value=1.0)
        ttk.Scale(enhance_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL, 
                  variable=self.sharpness_var, length=300).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(enhance_frame, textvariable=self.sharpness_var).grid(row=2, column=2, padx=5, pady=5)
        
        self.auto_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Auto mode (automatically decide to compress or enhance based on file size)", 
                         variable=self.auto_mode).pack(anchor=tk.W, pady=5)
        
        size_frame = ttk.Frame(main_frame)
        size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(size_frame, text="Target file size (KB):").pack(side=tk.LEFT, padx=5)
        self.target_size_var = tk.IntVar(value=200)
        ttk.Entry(size_frame, textvariable=self.target_size_var, width=6).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=5)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Compress Images", command=self.compress_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Enhance Images", command=self.enhance_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Process (Auto)", command=self.auto_process).pack(side=tk.LEFT, padx=5)
    
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)
    
    def process_images(self, mode='compress'):
        root_dir = self.dir_var.get()
        quality = self.quality_var.get()
        brightness = self.brightness_var.get()
        contrast = self.contrast_var.get()
        sharpness = self.sharpness_var.get()
        target_size = self.target_size_var.get() * 1024
        
        image_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            messagebox.showinfo("No Images", "No image files found in the selected directory.")
            return
        
        processed = 0
        for idx, file_path in enumerate(image_files):
            try:
                file_size = os.path.getsize(file_path)
                
                if mode == 'auto':
                    if file_size > target_size:
                        self._compress_image(file_path, quality)
                        action = "Compressed"
                    else:
                        self._enhance_image(file_path, brightness, contrast, sharpness)
                        action = "Enhanced"
                elif mode == 'compress':
                    self._compress_image(file_path, quality)
                    action = "Compressed"
                else:
                    self._enhance_image(file_path, brightness, contrast, sharpness)
                    action = "Enhanced"
                
                processed += 1
                self.status_var.set(f"{action}: {file_path}")
                self.progress_var.set((idx + 1) / len(image_files) * 100)
                self.root.update_idletasks()
                
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
        
        self.status_var.set(f"Completed! Processed {processed} images.")
        messagebox.showinfo("Complete", f"Processed {processed} out of {len(image_files)} images.")
    
    def _compress_image(self, file_path, quality):
        try:
            with Image.open(file_path) as img:
                img.save(file_path, optimize=True, quality=quality)
        except Exception as e:
            print(f"Error compressing image {file_path}: {e}")
    
    def _enhance_image(self, file_path, brightness, contrast, sharpness):
        try:
            with Image.open(file_path) as img:
                if brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(brightness)
                
                if contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(contrast)
                
                if sharpness != 1.0:
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(sharpness)
                
                img.save(file_path, quality=95)
        except Exception as e:
            print(f"Error enhancing image {file_path}: {e}")
    
    def compress_images(self):
        threading.Thread(target=self.process_images, args=('compress',)).start()
    
    def enhance_images(self):
        threading.Thread(target=self.process_images, args=('enhance',)).start()
    
    def auto_process(self):
        threading.Thread(target=self.process_images, args=('auto',)).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessor(root)
    root.mainloop()

