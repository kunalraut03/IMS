import os
import socket
import json
import threading
import time

class StopSignalHandler:
    def __init__(self, stop_event):
        self.stop_event = stop_event
        self.is_running = True
        self.server_thread = None
        self.file_check_thread = None
        self.signal_file = "C://IMS\\stop_training.signal"
    def start(self):
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        self.file_check_thread = threading.Thread(target=self._check_signal_file, daemon=True)
        self.file_check_thread.start()
        if os.path.exists(self.signal_file):
            try:
                os.remove(self.signal_file)
            except:
                pass
    def _run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 5679))
            server.settimeout(1.0)
            server.listen(1)
            while self.is_running:
                try:
                    client, _ = server.accept()
                    data = b""
                    while True:
                        chunk = client.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                    try:
                        message = json.loads(data.decode('utf-8'))
                        if message.get("command") == "stop":
                            self.stop_event.set()
                            print("Stop command received via socket")
                    except json.JSONDecodeError:
                        pass
                    finally:
                        client.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Stop signal server error: {e}")
        finally:
            server.close()
    def _check_signal_file(self):
        while self.is_running:
            if os.path.exists(self.signal_file):
                try:
                    os.remove(self.signal_file)
                    self.stop_event.set()
                    print("Stop command received via signal file")
                except:
                    pass
            time.sleep(1)
    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    stop_event = threading.Event()
    handler = StopSignalHandler(stop_event)
    handler.start()
    while not stop_event.is_set():
        time.sleep(1)
    print("Stop event received")
    handler.stop()
