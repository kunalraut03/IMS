import os
import sys
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, Callback
import socket
import json
import platform
import logging
import signal
import threading
from stop_signal_handler import StopSignalHandler

root_dir = "C://IMS\\kaymh\\Downloads\\VIGYAN ASHRAM files\\IMS\\ver3.1"
data_dir = os.path.join(root_dir, "data")
models_dir = os.path.join(root_dir, "models")
labels_path = os.path.join(models_dir, "labels1.txt")
model_path = os.path.join(models_dir, "model.h5")
temp_model_path = os.path.join(models_dir, "model_temp.h5")
backup_model_path = os.path.join(models_dir, "model_backup.h5")

training_interrupted = False
stop_training_event = threading.Event()

def get_gpu_info():
    gpus = tf.config.list_physical_devices('GPU')
    if not gpus:
        return "No GPU available"
    
    gpu_info = []
    for gpu in gpus:
        try:
            gpu_details = tf.config.experimental.get_device_details(gpu)
            if "device_name" in gpu_details:
                gpu_info.append(gpu_details["device_name"])
            else:
                gpu_info.append(f"GPU {gpu.name}")
        except:
            gpu_info.append(f"GPU {gpu.name}")
    
    return ", ".join(gpu_info)

class StopTrainingCallback(Callback):
    def on_batch_end(self, batch, logs=None):
        if stop_training_event.is_set():
            self.model.stop_training = True
            global training_interrupted
            training_interrupted = True
            logging.info("Training stopped by user")

class StatusCallback(Callback):
    def __init__(self):
        super().__init__()
        self.epoch = 0
        self.total_epochs = 0
        self.system_info = {
            "python_version": platform.python_version(),
            "tensorflow_version": tf.__version__,
            "gpu_info": get_gpu_info()
        }
        
    def on_train_begin(self, logs=None):
        self.total_epochs = self.params['epochs']
        self.send_status({
            **self.system_info,
            'message': 'Training started',
            'total_epochs': self.total_epochs,
            'epoch': 0,
            'progress': 0,
            'loss': 0,
            'accuracy': 0,
            'can_interrupt': True
        })
        logging.info(f"Python Version: {self.system_info['python_version']}")
        logging.info(f"TensorFlow Version: {self.system_info['tensorflow_version']}")
        logging.info(f"GPU Information: {self.system_info['gpu_info']}")
        
    def on_epoch_begin(self, epoch, logs=None):
        self.epoch = epoch + 1
        self.send_status({
            **self.system_info,
            'message': f'Starting epoch {self.epoch}/{self.total_epochs}',
            'epoch': self.epoch,
            'total_epochs': self.total_epochs,
            'progress': int((self.epoch - 1) / self.total_epochs * 100),
            'can_interrupt': True
        })
        
    def on_batch_end(self, batch, logs=None):
        if batch % 10 == 0:
            batch_total = self.params['steps']
            self.send_status({
                **self.system_info,
                'message': f'Epoch {self.epoch}/{self.total_epochs}, Batch {batch+1}/{batch_total}',
                'epoch': self.epoch,
                'total_epochs': self.total_epochs,
                'progress': int(((self.epoch - 1) + (batch + 1) / batch_total) / self.total_epochs * 100),
                'loss': logs.get('loss', 0),
                'accuracy': logs.get('accuracy', 0),
                'can_interrupt': True
            })
            
    def on_epoch_end(self, epoch, logs=None):
        # Save temporary model at the end of each epoch
        if not stop_training_event.is_set():
            try:
                self.model.save(temp_model_path)
                logging.info(f"Temporary model saved at epoch {self.epoch}")
            except Exception as e:
                logging.error(f"Failed to save temporary model: {e}")
                
        self.send_status({
            **self.system_info,
            'message': f'Completed epoch {self.epoch}/{self.total_epochs}',
            'epoch': self.epoch,
            'total_epochs': self.total_epochs,
            'progress': int(self.epoch / self.total_epochs * 100),
            'loss': logs.get('loss', 0),
            'accuracy': logs.get('accuracy', 0),
            'val_loss': logs.get('val_loss', 0),
            'val_accuracy': logs.get('val_accuracy', 0),
            'can_interrupt': True
        })
        
    def on_train_end(self, logs=None):
        interrupted_msg = " (Interrupted by user)" if training_interrupted else ""
        self.send_status({
            **self.system_info,
            'message': f'Training completed{interrupted_msg}',
            'epoch': self.epoch,
            'total_epochs': self.total_epochs,
            'progress': 100,
            'can_interrupt': False,
            'interrupted': training_interrupted
        })
        
    def send_status(self, data):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", 5678))
            client.sendall(json.dumps(data).encode('utf-8'))
            client.close()
        except:
            pass

def signal_handler(sig, frame):
    stop_training_event.set()
    logging.info("Interrupt signal received, stopping training gracefully...")
    print("\nInterrupt signal received, stopping training gracefully...")
    print("Training will stop after the current batch. Please wait...")

def create_data_generator():
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True
    )

    train_data = datagen.flow_from_directory(
        data_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='training'
    )

    val_data = datagen.flow_from_directory(
        data_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='validation'
    )

    return train_data, val_data

def build_model(num_classes):
    base_model = keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    
    base_model.trainable = False
    
    inputs = keras.Input(shape=(224, 224, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = keras.Model(inputs, outputs)
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def backup_existing_model():
    if os.path.exists(model_path):
        try:
            if os.path.exists(backup_model_path):
                os.remove(backup_model_path)
            os.rename(model_path, backup_model_path)
            logging.info(f"Existing model backed up to {backup_model_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to backup existing model: {e}")
    return False

def restore_from_backup():
    if os.path.exists(temp_model_path):
        # If we have a temp model, use that (it's the latest epoch)
        try:
            if os.path.exists(model_path):
                os.remove(model_path)
            os.rename(temp_model_path, model_path)
            logging.info("Training interrupted, using latest epoch model")
            return True
        except Exception as e:
            logging.error(f"Failed to use temp model: {e}")
            
    if os.path.exists(backup_model_path):
        # Fall back to the backup model if temp model isn't available or can't be used
        try:
            if os.path.exists(model_path):
                os.remove(model_path)
            os.rename(backup_model_path, model_path)
            logging.info("Training interrupted, restored previous model")
            return True
        except Exception as e:
            logging.error(f"Failed to restore backup model: {e}")
    
    return False

def main():
    logging.basicConfig(filename="ims_debug.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info(f"Starting training with TensorFlow {tf.__version__}")
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize the stop signal handler
    stop_handler = StopSignalHandler(stop_training_event)
    stop_handler.start()
    
    os.makedirs(models_dir, exist_ok=True)
    
    # Backup existing model
    has_backup = backup_existing_model()
    
    train_data, val_data = create_data_generator()
    
    with open(labels_path, "w") as f:
        for label, index in train_data.class_indices.items():
            f.write(f"{index}: {label}\n")
    
    model = build_model(len(train_data.class_indices))
    
    try:
        num_epochs = int(os.environ.get("IMS_EPOCHS", 10))
    except ValueError:
        raise ValueError("Invalid value for IMS_EPOCHS. Please provide a valid integer.")
    
    status_callback = StatusCallback()
    stop_callback = StopTrainingCallback()
    
    try:
        model.fit(
            train_data,
            validation_data=val_data,
            epochs=num_epochs,
            callbacks=[
                status_callback,
                stop_callback,
                EarlyStopping(patience=5),
                ModelCheckpoint(model_path, save_best_only=True)
            ]
        )

        if training_interrupted:
            logging.info("Training was interrupted, checking for model to use...")
            restored = restore_from_backup()
            if not restored:
                logging.warning("No previous model available, using partial training results")
    except KeyboardInterrupt:
        logging.info("Training interrupted manually")
        restored = restore_from_backup()
        if not restored:
            logging.warning("No previous model available, using partial training results")
    except Exception as e:
        logging.exception(f"Training error: {e}")
        restored = restore_from_backup()
        if not restored and not os.path.exists(model_path) and has_backup:
            # If training failed and we don't have a model, restore the backup
            if os.path.exists(backup_model_path):
                try:
                    os.rename(backup_model_path, model_path)
                    logging.info("Training failed, restored previous model")
                except Exception as e:
                    logging.error(f"Failed to restore backup model: {e}")
    finally:
        # Stop the signal handler
        stop_handler.stop()
        
        # Clean up temp files
        if os.path.exists(temp_model_path):
            try:
                os.remove(temp_model_path)
            except:
                pass
                
        if os.path.exists(backup_model_path) and os.path.exists(model_path):
            try:
                os.remove(backup_model_path)
            except:
                pass

if __name__ == "__main__":
    main()