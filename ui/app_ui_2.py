import sys
import os
import cv2
import json
import requests
import firebase_admin
from firebase_admin import credentials, storage, db
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage

# === Raspberry Pi Camera Stream (MJPEG Streamer) ===
RASPBERRY_PI_IP = "192.168.1.100"  # Update with your Pi's IP
MJPEG_STREAM_URL = f"http://{RASPBERRY_PI_IP}:8080/?action=snapshot"

# === Firebase Setup ===
cred = credentials.Certificate("config/firebase_config.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://your-firebase-database.firebaseio.com/",
    "storageBucket": "your-bucket-name.appspot.com"
})
bucket = storage.bucket()
firebase_ref = db.reference("sensor_data")

# === YOLO Model Integration for Object Detection ===
from app.yolo_model import YOLO
yolo = YOLO(model_path="models/yolov5s.pt")


# === Custom Video Container Widget ===
class VideoContainerWidget(QWidget):
    def __init__(self, video_aspect=4 / 3, parent=None):
        super().__init__(parent)
        self.video_aspect = video_aspect
        self.video_label = QLabel("Camera Feed", self)
        self.captured_image_label = QLabel("Captured Image", self)
        self.video_label.setStyleSheet("background-color: black;")
        self.captured_image_label.setStyleSheet("background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        total_width = self.width()
        total_height = self.height()
        available_width_per = total_width / 2
        desired_height = available_width_per / self.video_aspect

        if desired_height > total_height:
            new_height = total_height
            new_width = new_height * self.video_aspect
        else:
            new_width = available_width_per
            new_height = desired_height

        x1 = (available_width_per - new_width) / 2
        y1 = (total_height - new_height) / 2
        self.video_label.setGeometry(int(x1), int(y1), int(new_width), int(new_height))
        x2 = total_width / 2 + (available_width_per - new_width) / 2
        self.captured_image_label.setGeometry(int(x2), int(y1), int(new_width), int(new_height))
        super().resizeEvent(event)


# === Main Application ===
class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Detection & Capture")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI layout."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === Top Row: Left Control Panel & Right Info Panel ===
        top_row = QHBoxLayout()
        top_row.setContentsMargins(10, 10, 10, 10)

        # --- Left Control Panel ---
        left_controls = QVBoxLayout()
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        self.object_select.setFixedHeight(50)
        left_controls.addWidget(self.object_select)

        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5980;
                margin-top: 4px;
            }
        """

        self.detect_button = QPushButton("Detect")
        self.detect_button.setFixedHeight(50)
        self.detect_button.setStyleSheet(button_style)
        self.detect_button.clicked.connect(self.detect_environment)
        left_controls.addWidget(self.detect_button)

        self.capture_button = QPushButton("Capture")
        self.capture_button.setFixedHeight(50)
        self.capture_button.setStyleSheet(button_style)
        self.capture_button.clicked.connect(self.capture_image)
        left_controls.addWidget(self.capture_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(50)
        self.exit_button.setStyleSheet(button_style)
        self.exit_button.clicked.connect(self.close)
        left_controls.addWidget(self.exit_button)

        # --- Right Info Panel ---
        right_info = QVBoxLayout()
        self.env_label = QLabel("Temperature: --°C  |  Humidity: --%")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setFixedHeight(50)
        self.env_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        right_info.addWidget(self.env_label)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(150)
        right_info.addWidget(self.text_input)

        top_row.addLayout(left_controls)
        top_row.addLayout(right_info)
        main_layout.addLayout(top_row, 0)

        # === Bottom Row: Camera Feed & Captured Image ===
        self.video_container = VideoContainerWidget(video_aspect=4 / 3)
        self.video_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.video_container, 1)

        self.setLayout(main_layout)

    def detect_environment(self):
        """Detect temperature, humidity, and trigger AI model for object detection."""
        from app.temp_sensor import get_temperature, get_humidity

        temperature = get_temperature()
        humidity = get_humidity()
        self.env_label.setText(f"Temperature: {temperature}°C  |  Humidity: {humidity}%")

        # Automatically capture if the object is detected
        image_path = "captured_image.jpg"
        response = requests.get(MJPEG_STREAM_URL, stream=True)
        with open(image_path, "wb") as f:
            f.write(response.content)

        detected_objects = yolo.detect_objects(image_path)
        if self.object_select.currentText().lower() in detected_objects:
            self.capture_image()

    def capture_image(self):
        """Capture an image from Pi Camera, display it, and upload to Firebase."""
        selected_object = self.object_select.currentText().lower()
        image_path = "captured_image.jpg"

        response = requests.get(MJPEG_STREAM_URL, stream=True)
        with open(image_path, "wb") as f:
            f.write(response.content)

        pixmap = QPixmap(image_path)
        target_size = self.video_container.captured_image_label.size()
        pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_container.captured_image_label.setPixmap(pixmap)

        # Upload to Firebase
        blob = bucket.blob(f"captured_images/{selected_object}.jpg")
        blob.upload_from_filename(image_path)

        metadata = {
            "temperature": self.env_label.text(),
            "object": selected_object,
            "text": self.text_input.toPlainText()
        }
        firebase_ref.push(metadata)
        os.remove(image_path)

    def closeEvent(self, event):
        """Exit application."""
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
