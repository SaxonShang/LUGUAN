import sys
import os
import cv2
import json
import requests
import firebase_admin
from firebase_admin import credentials, storage, db
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage

# === Raspberry Pi Camera Stream (MJPEG Streamer) ===
RASPBERRY_PI_IP = "192.168.1.100"  # Update with your Pi's IP
MJPEG_STREAM_URL = f"http://{RASPBERRY_PI_IP}:8080/?action=snapshot"

# === Firebase Configuration ===
cred = credentials.Certificate("config/firebase_config.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://your-firebase-database.firebaseio.com/",
    "storageBucket": "your-bucket-name.appspot.com"
})
bucket = storage.bucket()
firebase_ref = db.reference("captured_images")

# === YOLO Object Detection ===
from yolo_model import YOLO
yolo = YOLO(model_path="models/yolov5s.pt")

# === Video Stream Processing ===
class VideoStreamThread(QThread):
    frame_update = pyqtSignal(QImage)
    object_detected = pyqtSignal()

    def __init__(self, selected_object):
        super().__init__()
        self.selected_object = selected_object
        self.running = True

    def run(self):
        while self.running:
            response = requests.get(MJPEG_STREAM_URL, stream=True)
            if response.status_code == 200:
                with open("temp_frame.jpg", "wb") as f:
                    f.write(response.content)

                frame = cv2.imread("temp_frame.jpg")
                processed_frame = yolo.detect_objects_in_frame(frame, self.selected_object)

                rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_update.emit(qt_image)

                detected_objects = yolo.detect_objects("temp_frame.jpg")
                if any(obj["name"] == self.selected_object for obj in detected_objects):
                    self.object_detected.emit()

    def stop(self):
        self.running = False

# === Main UI Application ===
class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Detection & Capture - Final Version")
        self.resize(1200, 800)
        self.init_ui()

        self.selected_object = "person"
        self.video_thread = VideoStreamThread(self.selected_object)
        self.video_thread.frame_update.connect(self.update_video_feed)
        self.video_thread.object_detected.connect(self.capture_image)
        self.video_thread.start()

    def init_ui(self):
        """Initialize UI layout with resizable elements."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === Top Section (Buttons & Info) ===
        top_row = QHBoxLayout()
        left_controls = QVBoxLayout()

        # Object Selection
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        self.object_select.setFixedHeight(50)
        self.object_select.currentIndexChanged.connect(self.update_selected_object)
        left_controls.addWidget(self.object_select)

        # History Selection
        self.history_select = QComboBox()
        self.history_select.addItem("Select History")
        self.history_select.setFixedHeight(50)
        self.history_select.currentIndexChanged.connect(self.load_history)
        left_controls.addWidget(self.history_select)

        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5980;
                margin-top: 4px;
            }
        """

        self.capture_button = QPushButton("Capture")
        self.capture_button.setFixedHeight(50)
        self.capture_button.setStyleSheet(button_style)
        self.capture_button.clicked.connect(self.capture_image)
        left_controls.addWidget(self.capture_button)

        self.process_button = QPushButton("Process Image")
        self.process_button.setFixedHeight(50)
        self.process_button.setStyleSheet(button_style)
        self.process_button.clicked.connect(self.process_image)
        left_controls.addWidget(self.process_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(50)
        self.exit_button.setStyleSheet(button_style)
        self.exit_button.clicked.connect(self.clear_database_and_exit)
        left_controls.addWidget(self.exit_button)

        # Right Info Panel
        right_info = QVBoxLayout()
        self.env_label = QLabel("Temperature: --°C  |  Humidity: --%")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setFixedHeight(50)
        self.env_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        right_info.addWidget(self.env_label)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(100)
        right_info.addWidget(self.text_input)

        top_row.addLayout(left_controls)
        top_row.addLayout(right_info)
        main_layout.addLayout(top_row)

        # === Video Feed & Captured Image ===
        video_capture_layout = QHBoxLayout()
        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        video_capture_layout.addWidget(self.video_label)

        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        video_capture_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(video_capture_layout)
        self.setLayout(main_layout)

    def update_selected_object(self):
        """Updates the selected object for detection and fetches history."""
        self.selected_object = self.object_select.currentText().lower()
        self.video_thread.selected_object = self.selected_object
        self.load_history()

    def update_video_feed(self, qt_image):
        """Updates the video feed label with YOLO detection output."""
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def capture_image(self):
        """Captures the detected frame, displays, and uploads to Firebase."""
        response = requests.get(MJPEG_STREAM_URL, stream=True)
        if response.status_code == 200:
            image_path = f"captured_{self.selected_object}.jpg"
            with open(image_path, "wb") as f:
                f.write(response.content)

            pixmap = QPixmap(image_path)
            self.captured_image_label.setPixmap(pixmap)

            blob = bucket.blob(f"{self.selected_object}/{os.path.basename(image_path)}")
            blob.upload_from_filename(image_path)
            os.remove(image_path)

    def load_history(self):
        """Fetches history of selected object from Firebase."""
        self.history_select.clear()
        self.history_select.addItem("Select History")
        category_ref = firebase_ref.child(self.selected_object).get()
        if category_ref:
            for image_key, image_data in category_ref.items():
                self.history_select.addItem(image_data["image_url"])

    def process_image(self):
        """Sends the captured image, text, and environment data to AI."""
        data = {
            "text": self.text_input.toPlainText(),
            "temperature": self.env_label.text(),
            "image_url": self.history_select.currentText()
        }
        requests.post("http://your-ai-server.com/process", json=data)

    def clear_database_and_exit(self):
        """Clears Firebase data and exits application."""
        firebase_ref.set({})
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
