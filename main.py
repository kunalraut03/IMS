import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
import shutil
import threading
import logging

logging.basicConfig(filename="ims_debug.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class IMSApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System (IMS)")
        self.root.geometry("850x700")
        self.root.resizable(True, True)
        
        # Get Python executable - prefer conda environment if available
        self.python_executable = self.get_python_executable()
        
        # Get installation directory from user or use current directory
        self.default_dir = self.get_installation_directory()
        if not self.default_dir:
            messagebox.showerror("Error", "Installation directory is required. Exiting application.")
            root.destroy()
            return
            
        self.config_file = os.path.join(self.default_dir, "config.json")
        
        self.config = self.load_config()
        
        self.workflow_status = {
            "capture": False,
            "append": False,
            "compress": False,
            "train": False,
            "test": False
        }
        
        self.create_ui()
    
    def get_python_executable(self):
        """Get the appropriate Python executable, preferring conda environment"""
        # Check if we're in a conda environment
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            # We're in a conda environment, use its Python
            if os.name == 'nt':  # Windows
                python_exe = os.path.join(conda_prefix, 'python.exe')
            else:  # Unix-like
                python_exe = os.path.join(conda_prefix, 'bin', 'python')
            
            if os.path.exists(python_exe):
                logging.info(f"Using conda environment Python: {python_exe}")
                return python_exe
        
        # Check for environment variable set by build.bat
        env_python = os.environ.get('PYTHON_EXECUTABLE')
        if env_python and os.path.exists(env_python):
            logging.info(f"Using environment Python: {env_python}")
            return env_python
        
        # Fall back to current Python executable
        logging.info(f"Using current Python executable: {sys.executable}")
        return sys.executable
    
    def get_installation_directory(self):
        """Get installation directory from user or config file"""
        # First try to find existing config in current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        temp_config_file = os.path.join(current_dir, "config.json")
        
        if os.path.exists(temp_config_file):
            try:
                with open(temp_config_file, "r") as f:
                    config = json.load(f)
                    if "installation_dir" in config and os.path.exists(config["installation_dir"]):
                        return config["installation_dir"]
            except:
                pass
        
        # If no valid config found, ask user to select directory
        messagebox.showinfo(
            "Setup Required", 
            "Welcome to IMS! Please select the installation directory where the application files are located."
        )
        
        installation_dir = filedialog.askdirectory(
            title="Select IMS Installation Directory",
            initialdir=current_dir
        )
        
        if not installation_dir:
            return None
            
        # Verify required files exist
        required_files = ["capture_images.py", "append_images.py", "compress_images.py", "train.py", "excel_model.py"]
        missing_files = []
        
        for file in required_files:
            if not os.path.exists(os.path.join(installation_dir, file)):
                missing_files.append(file)
        
        if missing_files:
            messagebox.showwarning(
                "Missing Files",
                f"The following required files are missing from the selected directory:\n{', '.join(missing_files)}\n\nPlease ensure all IMS files are in the selected directory."
            )
        
        return installation_dir
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "installation_dir": self.default_dir,
            "data_dir": os.path.join(self.default_dir, "data"),
            "models_dir": os.path.join(self.default_dir, "models"),
            "input_images_dir": os.path.join(self.default_dir, "data"),
            "compressed_images_dir": os.path.join(self.default_dir, "data")
        }
    
    def save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Dashboard")
        
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        
        self.help_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.help_tab, text="Help")
        
        self.logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_tab, text="Logs")
        
        self.build_main_tab()
        self.build_settings_tab()
        self.build_help_tab()
        self.build_logs_tab()
    
    def build_main_tab(self):
        title_frame = ttk.Frame(self.main_tab)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = ttk.Label(title_frame, text="Inventory Management System", 
                                font=("Helvetica", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Control Panel", 
                                  font=("Helvetica", 12))
        subtitle_label.pack()
        
        dir_frame = ttk.LabelFrame(self.main_tab, text="Installation Directory")
        dir_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(dir_frame, text="Current Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_var = tk.StringVar(value=self.config["installation_dir"])
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=60, state="readonly").grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(dir_frame, text="Change", command=self.change_directory).grid(
            row=0, column=2, padx=5, pady=5)
        
        workflow_frame = ttk.LabelFrame(self.main_tab, text="Workflow")
        workflow_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.epoch_progress_var = tk.StringVar(value="Epoch Progress: 0%")
        ttk.Label(workflow_frame, textvariable=self.epoch_progress_var, font=("Helvetica", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.create_workflow_step(workflow_frame, 0, "1. Capture Images", 
                                 "Capture initial images for a new object class", 
                                 self.run_capture_images)
        
        self.create_workflow_step(workflow_frame, 1, "2. Append Images", 
                                 "Add more images to an existing object class", 
                                 self.run_append_images)
        
        self.create_workflow_step(workflow_frame, 2, "3. Image Modification",
                                 "Modify images (compress or enhance) before training",
                                 self.run_image_modification)
        
        self.create_workflow_step_with_epochs(workflow_frame, 3, "4. Train Model", 
                                              "Train the model with the captured images", 
                                              self.run_train_model)
        
        self.create_workflow_step(workflow_frame, 4, "5. Test Model", 
                                 "Test the trained model in real-time", 
                                 self.run_test_model)
        
        bottom_frame = ttk.Frame(self.main_tab)
        bottom_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(bottom_frame, text="Reset Workflow Status", command=self.reset_workflow).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Run Complete Workflow", command=self.run_complete_workflow).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Show Epoch Status", command=self.show_epoch_status).pack(side=tk.RIGHT, padx=5)
    
    def create_workflow_step(self, parent, row, title, description, command):
        step_frame = ttk.Frame(parent)
        step_frame.grid(row=row+1, column=0, sticky=tk.W+tk.E, padx=10, pady=10)
        parent.grid_columnconfigure(0, weight=1)
        
        status_var = tk.StringVar(value="⚪")
        status_key = title.split(".")[1].strip().lower().split(" ")[0]
        if self.workflow_status.get(status_key, False):
            status_var.set("✅")
            
        setattr(self, f"status_{status_key}", status_var)
        
        status_label = ttk.Label(step_frame, textvariable=status_var, font=("Helvetica", 12))
        status_label.pack(side=tk.LEFT, padx=10)
        
        info_frame = ttk.Frame(step_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(info_frame, text=title, font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=description, wraplength=500).pack(anchor=tk.W)
        
        ttk.Button(step_frame, text="Run", command=command).pack(side=tk.RIGHT, padx=10)
    
    def create_workflow_step_with_epochs(self, parent, row, title, description, command):
        step_frame = ttk.Frame(parent)
        step_frame.grid(row=row+1, column=0, sticky=tk.W+tk.E, padx=10, pady=10)
        parent.grid_columnconfigure(0, weight=1)
        
        status_var = tk.StringVar(value="⚪")
        status_key = title.split(".")[1].strip().lower().split(" ")[0]
        if self.workflow_status.get(status_key, False):
            status_var.set("✅")
            
        setattr(self, f"status_{status_key}", status_var)
        
        status_label = ttk.Label(step_frame, textvariable=status_var, font=("Helvetica", 12))
        status_label.pack(side=tk.LEFT, padx=10)
        
        info_frame = ttk.Frame(step_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(info_frame, text=title, font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=description, wraplength=500).pack(anchor=tk.W)
        
        ttk.Label(step_frame, text="Epochs:").pack(side=tk.LEFT, padx=5)
        self.epochs_var = tk.IntVar(value=10)
        ttk.Entry(step_frame, textvariable=self.epochs_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(step_frame, text="Run", command=command).pack(side=tk.RIGHT, padx=10)
    
    def build_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, text="Data Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.data_dir_var = tk.StringVar(value=self.config["data_dir"])
        ttk.Entry(settings_frame, textvariable=self.data_dir_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.data_dir_var)).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="Models Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.models_dir_var = tk.StringVar(value=self.config["models_dir"])
        ttk.Entry(settings_frame, textvariable=self.models_dir_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.models_dir_var)).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).grid(
            row=2, column=1, padx=5, pady=20)
    
    def build_help_tab(self):
        help_frame = ttk.Frame(self.help_tab, padding=20)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(help_frame, text="Help & Instructions", 
                 font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=10)
        
        help_text = """
        Workflow Instructions:
        
        1. Capture Images:
           - Captures initial images for a new object class
           - You will need to provide a name for the object class
           - Draw a bounding box around the object of interest
        
        2. Append Images:
           - Add more images to an existing object class
           - Select the object class you want to append images to
        
        3. Process Images:
           - Compress or enhance the quality of captured images
           - Adjust compression quality or enhancement parameters
        
        4. Train Model:
           - Train the machine learning model using the captured images
           - This process may take some time depending on the dataset size
        
        5. Test Model:
           - Test the trained model in real-time with your webcam
           - The model will try to identify objects it has been trained on
        
        Tips:
        - Make sure you have adequate lighting when capturing images
        - Capture images from different angles
        - Use the "Process Images" step to optimize image quality
        - For best results, follow the workflow in order
        """
        help_textbox = tk.Text(help_frame, wrap=tk.WORD, height=20, width=70)
        help_textbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        help_textbox.insert(tk.END, help_text)
        help_textbox.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(help_textbox, command=help_textbox.yview)
        help_textbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def build_logs_tab(self):
        logs_frame = ttk.Frame(self.logs_tab, padding=20)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(logs_frame, text="Log Management", 
                 font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=10)
        
        # Add Excel folder info
        excel_folder_frame = ttk.Frame(logs_frame)
        excel_folder_frame.pack(fill=tk.X, pady=5)
        
        excel_folder_path = os.path.join(self.config["installation_dir"], "IMS EXCEL")
        ttk.Label(excel_folder_frame, text=f"Excel Folder: {excel_folder_path}").pack(anchor=tk.W)
        
        buttons_frame = ttk.Frame(logs_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="View Logs", command=self.view_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Save Logs as TXT", command=self.save_logs_as_txt).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="View Excel Folder", command=self.view_excel_folder).pack(side=tk.LEFT, padx=5)
        
        # Add autoscroll checkbox
        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(buttons_frame, text="Auto-scroll to latest", variable=self.autoscroll_var).pack(side=tk.RIGHT)
        
        self.log_text = tk.Text(logs_frame, wrap=tk.WORD, height=20, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def view_excel_folder(self):
        """Open the Excel folder to check if files are being created"""
        try:
            excel_folder = os.path.join(self.config["installation_dir"], "IMS EXCEL")
            if not os.path.exists(excel_folder):
                # Create the folder if it doesn't exist
                os.makedirs(excel_folder)
                messagebox.showinfo("Excel Folder Created", f"Excel folder created at: {excel_folder}")
            
            if os.name == 'nt':  # Windows
                os.startfile(excel_folder)
            else:  # macOS and Linux
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', excel_folder])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Excel folder: {e}")
    
    def view_logs(self):
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            
            log_file_path = os.path.join(self.config["installation_dir"], "ims_debug.log")
            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as log_file:
                    content = log_file.read()
                    self.log_text.insert(tk.END, content)
                    
                # Scroll to the bottom if autoscroll is enabled
                if self.autoscroll_var.get():
                    self.log_text.see(tk.END)
            else:
                self.log_text.insert(tk.END, "Log file not found.")
                
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read log file: {e}")
    
    def clear_logs(self):
        try:
            log_file_path = os.path.join(self.config["installation_dir"], "ims_debug.log")
            if os.path.exists(log_file_path):
                with open(log_file_path, "w") as log_file:
                    log_file.write("")
                
                self.log_text.config(state=tk.NORMAL)
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, "Logs have been cleared.")
                self.log_text.config(state=tk.DISABLED)
                
                messagebox.showinfo("Success", "Log file has been cleared.")
            else:
                messagebox.showinfo("Info", "Log file not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear log file: {e}")
    
    def save_logs_as_txt(self):
        try:
            log_file_path = os.path.join(self.config["installation_dir"], "ims_debug.log")
            if not os.path.exists(log_file_path):
                messagebox.showinfo("Info", "Log file not found.")
                return
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt")],
                initialdir=self.config["installation_dir"],
                title="Save Logs As"
            )
            
            if not save_path:
                return
            
            with open(log_file_path, "r") as src_file:
                content = src_file.read()
                
            with open(save_path, "w") as dst_file:
                dst_file.write(content)
            
            messagebox.showinfo("Success", f"Logs saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log file: {e}")
    
    def change_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.config["installation_dir"])
        if not new_dir:
            return
        
        confirm = messagebox.askyesno(
            "Confirm Directory Change",
            "Changing the installation directory will require copying or moving files. Continue?"
        )
        
        if confirm:
            old_dir = self.config["installation_dir"]
            self.config["installation_dir"] = new_dir
            self.dir_var.set(new_dir)
            
            self.config["data_dir"] = os.path.join(new_dir, "data")
            self.config["models_dir"] = os.path.join(new_dir, "models")
            
            self.data_dir_var.set(self.config["data_dir"])
            self.models_dir_var.set(self.config["models_dir"])
            
            os.makedirs(self.config["data_dir"], exist_ok=True)
            os.makedirs(self.config["models_dir"], exist_ok=True)
            
            copy_data = messagebox.askyesno(
                "Copy Data",
                "Do you want to copy existing data and models to the new location?"
            )
            
            if copy_data:
                self.copy_data(old_dir, new_dir)
            
            self.save_config()
    
    def copy_data(self, old_dir, new_dir):
        try:
            old_data_dir = os.path.join(old_dir, "data")
            new_data_dir = os.path.join(new_dir, "data")
            if os.path.exists(old_data_dir):
                for item in os.listdir(old_data_dir):
                    s = os.path.join(old_data_dir, item)
                    d = os.path.join(new_data_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            
            old_models_dir = os.path.join(old_dir, "models")
            new_models_dir = os.path.join(new_dir, "models")
            if os.path.exists(old_models_dir):
                for item in os.listdir(old_models_dir):
                    s = os.path.join(old_models_dir, item)
                    d = os.path.join(new_models_dir, item)
                    shutil.copy2(s, d)
            
            messagebox.showinfo("Success", "Data and models copied successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy data: {e}")
    
    def browse_directory(self, var):
        directory = filedialog.askdirectory(initialdir=var.get())
        if directory:
            var.set(directory)
    
    def save_settings(self):
        self.config["data_dir"] = self.data_dir_var.get()
        self.config["models_dir"] = self.models_dir_var.get()
        
        os.makedirs(self.config["data_dir"], exist_ok=True)
        os.makedirs(self.config["models_dir"], exist_ok=True)
        
        self.save_config()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def show_epoch_status(self):
        try:
            script_path = os.path.join(self.config["installation_dir"], "epoch_status_window.py")
            subprocess.Popen([self.python_executable, script_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open epoch status window: {e}")
    
    def run_capture_images(self):
        try:
            script_path = os.path.join(self.config["installation_dir"], "capture_images.py")
            
            env = os.environ.copy()
            env["IMS_INSTALLATION_DIR"] = self.config["installation_dir"]
            env["IMS_DATA_DIR"] = self.config["data_dir"]
            env["IMS_MODELS_DIR"] = self.config["models_dir"]
            
            subprocess.Popen([self.python_executable, script_path], env=env)
            
            self.workflow_status["capture"] = True
            getattr(self, "status_capture").set("✅")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run capture_images.py: {e}")
    
    def run_append_images(self):
        try:
            script_path = os.path.join(self.config["installation_dir"], "append_images.py")
            
            env = os.environ.copy()
            env["IMS_INSTALLATION_DIR"] = self.config["installation_dir"]
            env["IMS_DATA_DIR"] = self.config["data_dir"]
            env["IMS_MODELS_DIR"] = self.config["models_dir"]
            
            subprocess.Popen([self.python_executable, script_path], env=env)
            
            self.workflow_status["append"] = True
            getattr(self, "status_append").set("✅")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run append_images.py: {e}")
    
    def run_compress_images(self):
        def compress():
            try:
                script_path = os.path.join(self.config["installation_dir"], "compress_images.py")
                logging.info(f"Executing script: {script_path}")
                
                input_dir = self.config.get("input_images_dir")
                output_dir = self.config.get("compressed_images_dir")
                
                if not input_dir or not output_dir:
                    raise ValueError("Input or output directory is not configured properly.")
                
                env = os.environ.copy()
                env["IMS_INPUT_DIR"] = input_dir
                env["IMS_OUTPUT_DIR"] = output_dir
                
                subprocess.run([self.python_executable, script_path], env=env, check=True)
                messagebox.showinfo("Success", "Image compression completed successfully!")
            except Exception as e:
                logging.exception("Failed to execute compress_images.py")
                messagebox.showerror("Error", f"Failed to execute compress_images.py: {e}")

        threading.Thread(target=compress, daemon=True).start()

    def run_image_modification(self):
        def modify():
            try:
                script_path = os.path.join(self.config["installation_dir"], "compress_images.py")
                logging.info(f"Executing script: {script_path}")
                
                env = os.environ.copy()
                env["IMS_INSTALLATION_DIR"] = self.config["installation_dir"]
                env["IMS_DATA_DIR"] = self.config["data_dir"]
                env["IMS_INPUT_DIR"] = self.config["data_dir"]
                env["IMS_OUTPUT_DIR"] = self.config["data_dir"]
                
                subprocess.run([self.python_executable, script_path], env=env, check=True)
                
                self.workflow_status["compress"] = True
                getattr(self, "status_image").set("✅")
                messagebox.showinfo("Success", "Image modification completed successfully!")
            except Exception as e:
                logging.exception("Failed to execute compress_images.py")
                messagebox.showerror("Error", f"Failed to execute compress_images.py: {e}")

        threading.Thread(target=modify, daemon=True).start()

    def run_train_model(self):
        def train():
            try:
                self.show_epoch_status()
                
                script_path = os.path.join(self.config["installation_dir"], "train.py")
                logging.info(f"Starting training script: {script_path}")
                
                # Check for and remove any old signal files
                signal_file = os.path.join(self.config["installation_dir"], "stop_training.signal")
                if os.path.exists(signal_file):
                    try:
                        os.remove(signal_file)
                    except:
                        pass
                
                env = os.environ.copy()
                env["IMS_INSTALLATION_DIR"] = self.config["installation_dir"]
                env["IMS_DATA_DIR"] = self.config["data_dir"]
                env["IMS_MODELS_DIR"] = self.config["models_dir"]
                env["IMS_EPOCHS"] = str(self.epochs_var.get())
                
                process = subprocess.Popen(
                    [self.python_executable, script_path],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                for line in process.stdout:
                    logging.info(f"TRAIN OUTPUT: {line.strip()}")
                    if "Epoch" in line and "/" in line:
                        parts = line.split()
                        for part in parts:
                            if "/" in part:
                                try:
                                    current_epoch, total_epochs = map(int, part.split("/"))
                                    progress = int((current_epoch / total_epochs) * 100)
                                    self.epoch_progress_var.set(f"Epoch Progress: {progress}%")
                                    self.root.update_idletasks()
                                except ValueError:
                                    continue
                    
                    if "Training interrupted" in line or "Training was interrupted" in line:
                        logging.info("Training was interrupted and previous model was used")
                        messagebox.showinfo("Training Interrupted", 
                                          "Training was interrupted. Using previously saved model.")
                
                process.wait()
                if process.returncode == 0:
                    self.workflow_status["train"] = True
                    getattr(self, "status_train").set("✅")
                    messagebox.showinfo("Training Complete", "Model training completed successfully!")
                else:
                    # Even with non-zero return code, we might have a usable model if training was interrupted
                    if os.path.exists(os.path.join(self.config["models_dir"], "model.h5")):
                        self.workflow_status["train"] = True
                        getattr(self, "status_train").set("✅")
                        messagebox.showinfo("Training", 
                                          "Training process finished with issues, but a model is available.")
                    else:
                        error_message = process.stderr.read()
                        logging.error(f"TRAIN ERROR: {error_message}")
                        messagebox.showerror("Training Error", f"Training failed: {error_message}")
            except Exception as e:
                logging.exception("Failed to run train.py")
                messagebox.showerror("Error", f"Failed to run train.py: {e}")

        threading.Thread(target=train, daemon=True).start()

    def run_test_model(self):
        try:
            script_path = os.path.join(self.config["installation_dir"], "excel_model.py")
            
            env = os.environ.copy()
            env["IMS_INSTALLATION_DIR"] = self.config["installation_dir"]
            env["IMS_DATA_DIR"] = self.config["data_dir"]
            env["IMS_MODELS_DIR"] = self.config["models_dir"]
            
            subprocess.Popen([self.python_executable, script_path], env=env)
            
            self.workflow_status["test"] = True
            getattr(self, "status_test").set("✅")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run excel_model.py: {e}")
    
    def run_complete_workflow(self):
        confirm = messagebox.askyesno(
            "Complete Workflow",
            "This will run all steps sequentially. Continue?"
        )
        if not confirm:
            return
        
        self.reset_workflow()
        
        self.run_capture_images()
        
        messagebox.showinfo(
            "Workflow", 
            "After completing image capture, click OK to continue to the next step."
        )
        
        self.run_compress_images()
        
        messagebox.showinfo(
            "Workflow", 
            "After completing image processing, click OK to continue to the next step."
        )
        
        self.run_train_model()
        
        messagebox.showinfo(
            "Workflow", 
            "After training completes, click OK to continue to the final step."
        )
        
        self.run_test_model()
    
    def reset_workflow(self):
        for key in self.workflow_status:
            self.workflow_status[key] = False
            try:
                getattr(self, f"status_{key}").set("⚪")
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = IMSApplication(root)
    root.mainloop()
