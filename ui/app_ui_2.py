import sys
import os
import json
import cv2
import requests
import firebase_admin
from firebase_admin import credentials, storage, db
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QGroupBox, QFormLayout
)
from PyQt5.QtGui import QPixmap, QImage

# Load MQTT configuration
config_path = os.path.join(os.path.dirname(__file__), "../config/mqtt_config.json")
with open(config_path, "r") as f:
    mqtt_config = json.load(f)

# Initialize Firebase
cred = credentials.Certificate("luguan-8c32d-firebase-adminsdk-fbsvc-6ca84ce42e.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://luguan-8c32d-default-rtdb.europe-west1.firebasedatabase.app/",
    "storageBucket": "your-bucket-name.appspot.com"
})
bucket = storage.bucket()
firebase_ref = db.reference("sensor_data")

class CameraStreamThread(QThread):
    frame_update = pyqtSignal(QImage)

    def run(self):
        self.cap = cv2.VideoCapture(0)  # Assuming camera index 0
        while True:
            ret, frame = self.cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_update.emit(qt_image)

    def stop(self):
        self.cap.release()
        self.quit()

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Detection & Capture")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()
        self.init_firebase()
        self.init_threads()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Control panel
        control_panel = QGroupBox("Control Panel")
        control_layout = QFormLayout()

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        control_layout.addRow("AI Input:", self.text_input)

        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        control_layout.addRow("Object Detection:", self.object_select)

        self.detect_button = QPushButton("Detect")
        self.detect_button.clicked.connect(self.detect_environment)
        control_layout.addRow(self.detect_button)

        self.capture_button = QPushButton("Capture Image")
        self.capture_button.clicked.connect(self.capture_image)
        control_layout.addRow(self.capture_button)

        self.process_button = QPushButton("Process Image")
        self.process_button.clicked.connect(self.send_text_to_ai)
        control_layout.addRow(self.process_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        control_layout.addRow(self.exit_button)

        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)

        # Real-time video display
        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(640, 480)
        main_layout.addWidget(self.video_label)

        # Captured image display
        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setFixedSize(640, 480)
        main_layout.addWidget(self.captured_image_label)

        # Temperature and humidity display
        self.env_label = QLabel("Temperature and Humidity")
        self.env_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.env_label)

        self.setLayout(main_layout)

    def init_firebase(self):
        # Firebase initialization is already done globally
        pass

    def init_threads(self):
        # Initialize camera stream thread
        self.camera_thread = CameraStreamThread()
        self.camera_thread.frame_update.connect(self.update_video_feed)
        self.camera_thread.start()

    def detect_environment(self):
        # Simulate detecting environment temperature and humidity
        temperature = 25.0  # Example temperature
        humidity = 60.0     # Example humidity
        self.env_label.setText(f"Temperature: {temperature}°C, Humidity: {humidity}%")
        # Upload data to Firebase
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": "2025-02-03 12:00:00"  # Example timestamp
        }
        firebase_ref.push(data)

    def capture_image(self):
        # Capture image from camera
        ret, frame = self.camera_thread.cap.read()
        if ret:
            # Display captured image
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.captured_image_label.setPixmap(QPixmap.fromImage(qt_image))
            # Upload image to Firebase Storage
            image_path = "captured_image.jpg"
            cv2.imwrite(image_path, frame)
            blob = bucket.blob(image_path)
            blob.upload_from_filename(image_path)
            os.remove(image_path)

    def send_text_to_ai(self):
        # Send user input text to AI for processing
        text_data = {"text": self.text_input.text()}
        response = requests.post("http://your-ai-server.com/process", json=text_data)
        if response.status_code == 200:
            print("Text data sent successfully to AI.")
        else:
            print("Failed to send text data.")

    def update_video_feed(self, qt_image):
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.camera_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys
::contentReference[oaicite:0]{index=0}
 
