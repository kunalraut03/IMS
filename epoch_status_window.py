import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json
import os

class EpochStatusWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Training Progress")
        self.root.geometry("500x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_ui()
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        self.is_running = True
        self.can_interrupt = False
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Training Progress", font=("Helvetica", 14, "bold")).pack(pady=10)
        system_frame = ttk.LabelFrame(main_frame, text="System Information", padding="10")
        system_frame.pack(fill=tk.X, pady=10)
        ttk.Label(system_frame, text="Python Version:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.python_var = tk.StringVar(value="N/A")
        ttk.Label(system_frame, textvariable=self.python_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(system_frame, text="TensorFlow Version:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.tf_var = tk.StringVar(value="N/A")
        ttk.Label(system_frame, textvariable=self.tf_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(system_frame, text="GPU:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.gpu_var = tk.StringVar(value="N/A")
        ttk.Label(system_frame, textvariable=self.gpu_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        ttk.Label(status_frame, text="Epoch:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.epoch_var = tk.StringVar(value="0/0")
        ttk.Label(status_frame, textvariable=self.epoch_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(status_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, length=300)
        self.progress_bar.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(status_frame, text="Loss:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.loss_var = tk.StringVar(value="0.0")
        ttk.Label(status_frame, textvariable=self.loss_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(status_frame, text="Accuracy:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.acc_var = tk.StringVar(value="0.0")
        ttk.Label(status_frame, textvariable=self.acc_var).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.message_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.message_var).pack(pady=5)
        stop_frame = ttk.Frame(main_frame)
        stop_frame.pack(fill=tk.X, pady=10)
        self.stop_button = tk.Button(
            stop_frame,
            text="STOP TRAINING",
            command=self.stop_training,
            bg="red",
            fg="white",
            font=("Helvetica", 12, "bold"),
            height=2,
            state=tk.NORMAL
        )
        self.stop_button.pack(fill=tk.X, padx=20, pady=10)
        self.interrupt_status_var = tk.StringVar(value="")
        self.interrupt_status = ttk.Label(
            main_frame,
            textvariable=self.interrupt_status_var,
            foreground="red",
            font=("Helvetica", 10, "bold")
        )
        self.interrupt_status.pack(pady=5)
    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 5678))
        server.settimeout(1.0)
        server.listen(5)
        while self.is_running:
            try:
                client, _ = server.accept()
                data = b""
                while True:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.update_ui(message)
                except json.JSONDecodeError:
                    pass
                finally:
                    client.close()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Server error: {e}")
                break
        server.close()
    def update_ui(self, data):
        if "python_version" in data:
            self.python_var.set(data["python_version"])
        if "tensorflow_version" in data:
            self.tf_var.set(data["tensorflow_version"])
        if "gpu_info" in data:
            self.gpu_var.set(data["gpu_info"])
        if "epoch" in data and "total_epochs" in data:
            self.epoch_var.set(f"{data['epoch']}/{data['total_epochs']}")
            if data['epoch'] > 0 and data['epoch'] <= data['total_epochs']:
                self.can_interrupt = True
                self.stop_button.config(state=tk.NORMAL, bg="red", fg="white")
                self.interrupt_status_var.set("You can stop training if needed")
        if "progress" in data:
            self.progress_var.set(data["progress"])
        if "loss" in data:
            self.loss_var.set(f"{data['loss']:.4f}")
        if "accuracy" in data:
            self.acc_var.set(f"{data['accuracy']:.2%}")
        if "message" in data:
            self.message_var.set(data["message"])
        if "can_interrupt" in data:
            self.can_interrupt = data["can_interrupt"]
            if self.can_interrupt:
                self.stop_button.config(state=tk.NORMAL, bg="red", fg="white")
            else:
                self.stop_button.config(state=tk.DISABLED, bg="gray75", fg="gray25")
        if "interrupted" in data and data["interrupted"]:
            self.interrupt_status_var.set("Training was interrupted. Using previously saved model.")
            self.stop_button.config(state=tk.DISABLED, bg="gray75", fg="gray25")
    def stop_training(self):
        if not self.can_interrupt:
            self.interrupt_status_var.set("No active training session to stop")
            return
        confirm = messagebox.askyesno(
            "Confirm Stop Training",
            "Are you sure you want to stop the training? The system will use the previously saved model."
        )
        if confirm:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(2.0)
                client.connect(("127.0.0.1", 5679))
                client.sendall(json.dumps({"command": "stop"}).encode('utf-8'))
                client.close()
                self.interrupt_status_var.set("Stopping training... Please wait")
                self.stop_button.config(state=tk.DISABLED, bg="gray75", fg="gray25")
                self.can_interrupt = False
            except Exception as e:
                print(f"Failed to send stop command via socket: {e}")
                try:
                    import os
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    signal_file = os.path.join(current_dir, "stop_training.signal")
                    with open(signal_file, "w") as f:
                        f.write("stop")
                    self.interrupt_status_var.set("Stop signal sent via file")
                    self.stop_button.config(state=tk.DISABLED, bg="gray75", fg="gray25")
                    self.can_interrupt = False
                except Exception as e:
                    print(f"Failed to create signal file: {e}")
                    messagebox.showerror("Error", "Failed to send stop command")
    def on_close(self):
        self.is_running = False
        self.root.destroy()

if __name__ == "__main__":
    window = EpochStatusWindow()
    window.root.mainloop()
