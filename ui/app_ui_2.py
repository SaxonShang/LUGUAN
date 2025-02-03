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
    QPushButton, QLineEdit, QComboBox, QGroupBox
)
from PyQt5.QtGui import QPixmap, QImage, QFont

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
        main_layout = QVBoxLayout()

        # Top Row: Buttons (Left) + Text Input (Right)
        top_layout = QHBoxLayout()

        # Button Panel (Left)
        button_layout = QVBoxLayout()
        self.detect_button = self.create_button("Detect", self.detect_environment)
        self.capture_button = self.create_button("Capture", self.capture_image)
        self.process_button = self.create_button("Process", self.send_text_to_ai)
        self.exit_button = self.create_button("Exit", self.close)

        for button in [self.detect_button, self.capture_button, self.process_button, self.exit_button]:
            button_layout.addWidget(button)

        top_layout.addLayout(button_layout)

        # Text Input (Right)
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text for AI processing...")
        self.text_input.setFont(QFont("Arial", 12))
        self.text_input.setFixedHeight(140)  # Match button panel height
        top_layout.addWidget(self.text_input)

        main_layout.addLayout(top_layout)

        # Middle Row: Temperature & Humidity Display
        self.env_label = QLabel("Temperature: -- °C  |  Humidity: -- %")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(self.env_label)

        # Bottom Row: Camera Feed (Left) + Captured Image (Right)
        image_layout = QHBoxLayout()

        # Live Camera Feed
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("border: 2px solid black;")
        image_layout.addWidget(self.video_label)

        # Captured Image Display
        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setFixedSize(640, 480)
        self.captured_image_label.setStyleSheet("border: 2px solid black;")
        image_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(image_layout)
        self.setLayout(main_layout)

    def create_button(self, text, func):
        """Creates a styled button with hover/click effects and reduces text size."""
        button = QPushButton(text)
        button.setFixedHeight(35)  # Reduced height
        button.setFixedWidth(180)  # Adjusted width
        button.setFont(QFont("Arial", 10, QFont.Bold))  # **Smaller font size**
        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c598a;
                border-style: inset;
            }
        """)
        button.clicked.connect(func)
        return button

    def init_firebase(self):
        """Ensures Firebase initialization is handled correctly."""
        pass

    def init_threads(self):
        """Starts camera feed thread."""
        self.camera_thread = CameraStreamThread()
        self.camera_thread.frame_update.connect(self.update_video_feed)
        self.camera_thread.start()

    def detect_environment(self):
        """Simulates temperature & humidity detection and uploads to Firebase."""
        temperature = 25.0  # Example temperature
        humidity = 60.0     # Example humidity
        self.env_label.setText(f"Temperature: {temperature}°C  |  Humidity: {humidity}%")

        # Upload data to Firebase
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": "2025-02-03 12:00:00"
        }
        firebase_ref.push(data)

    def capture_image(self):
        """Captures image from camera and uploads to Firebase."""
        ret, frame = self.camera_thread.cap.read()
        if ret:
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
        """Sends user input text to AI for processing."""
        text_data = {"text": self.text_input.text()}
        response = requests.post("http://your-ai-server.com/process", json=text_data)
        if response.status_code == 200:
            print("Text data sent successfully to AI.")
        else:
            print("Failed to send text data.")

    def update_video_feed(self, qt_image):
        """Updates the live camera feed in UI."""
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        """Handles application close event."""
        self.camera_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_()) 
