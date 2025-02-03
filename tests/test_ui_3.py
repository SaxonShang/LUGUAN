import sys
import os
import cv2
import json
import requests
import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage

# === Import Updated YOLO Model ===
from yolo_model import YOLO
yolo = YOLO(model_path="models/yolov5s.pt")

# === Test Mode: Using Laptop Camera ===
TEST_MODE = True

# === Video Processing Thread ===
class VideoStreamThread(QThread):
    frame_update = pyqtSignal(QImage)
    object_detected = pyqtSignal(np.ndarray)  # Emits frame when the selected object is detected

    def __init__(self, selected_object):
        super().__init__()
        self.selected_object = selected_object
        self.running = True
        self.cap = cv2.VideoCapture(0)  # Open laptop camera

    def run(self):
        if not self.cap.isOpened():
            print("❌ Error: Cannot open laptop camera!")
            return

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Failed to capture frame")
                continue

            # Process frame for bounding boxes (ONLY in video)
            processed_frame = yolo.detect_objects_in_frame(frame.copy(), self.selected_object)

            # Convert frame to QImage for display
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_update.emit(qt_image)

            # Check if the selected object is detected → Emit raw frame for capture
            detected_objects = yolo.detect_objects(frame)
            if any(obj["name"].lower() == self.selected_object.lower() for obj in detected_objects):
                self.object_detected.emit(frame)

    def stop(self):
        self.running = False
        self.cap.release()

# === Main UI Application ===
class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Displayer - Test Version")
        self.resize(1200, 800)
        self.video_aspect_set = False  # Flag to record whether the actual camera aspect ratio has been set
        self.init_ui()

        # Start Video Stream
        self.selected_object = "person"
        self.video_thread = VideoStreamThread(self.selected_object)
        self.video_thread.frame_update.connect(self.update_video_feed)
        self.video_thread.object_detected.connect(self.capture_image)
        self.video_thread.start()

    def init_ui(self):
        """Initialize UI layout and components."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === Top Section: Button Controls and Info ===
        top_row = QHBoxLayout()
        left_controls = QVBoxLayout()

        # Object Selection Dropdown
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        self.object_select.setFixedHeight(50)
        self.object_select.currentIndexChanged.connect(self.update_selected_object)
        left_controls.addWidget(self.object_select)

        # History Selection Dropdown
        self.history_select = QComboBox()
        self.history_select.addItem("Select History")
        self.history_select.setFixedHeight(50)
        left_controls.addWidget(self.history_select)

        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5980;
                margin-top: 4px;
            }
        """

        # Capture Button
        self.capture_button = QPushButton("Capture")
        self.capture_button.setFixedHeight(50)
        self.capture_button.setStyleSheet(button_style)
        self.capture_button.clicked.connect(self.manual_capture)
        left_controls.addWidget(self.capture_button)

        # Process Button
        self.process_button = QPushButton("Process Image")
        self.process_button.setFixedHeight(50)
        self.process_button.setStyleSheet(button_style)
        self.process_button.clicked.connect(self.process_image)
        left_controls.addWidget(self.process_button)

        # Exit Button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(50)
        self.exit_button.setStyleSheet(button_style)
        self.exit_button.clicked.connect(self.close_application)
        left_controls.addWidget(self.exit_button)

        # === Right Section: Info Panel ===
        right_info = QVBoxLayout()
        # Reduce the temperature and humidity display height to one button height (50px)
        self.env_label = QLabel("Temperature: --°C  |  Humidity: --%")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setFixedHeight(50)  # Same as a single button height
        self.env_label.setStyleSheet("font-size: 20px; font-weight: bold; background-color: rgba(255,255,255,0.7);")
        right_info.addWidget(self.env_label)

        # Increase the text input height so that the total right panel height matches the button section (200px)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(150)  # Now 50 (env_label) + 150 (text_input) = 200 total
        right_info.addWidget(self.text_input)

        top_row.addLayout(left_controls)
        top_row.addLayout(right_info)
        main_layout.addLayout(top_row)

        # === Bottom Section: Video and Captured Image Side by Side ===
        video_capture_layout = QHBoxLayout()

        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setScaledContents(True)  # Enables auto-resizing of the pixmap
        video_capture_layout.addWidget(self.video_label)

        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.captured_image_label.setMinimumSize(1, 1)
        self.captured_image_label.setScaledContents(True)  # Enables auto-resizing of the pixmap
        video_capture_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(video_capture_layout)
        self.setLayout(main_layout)

    def update_selected_object(self):
        """Update selected object and restart detection thread."""
        self.selected_object = self.object_select.currentText().lower()
        self.video_thread.selected_object = self.selected_object

    def update_video_feed(self, qt_image):
        """Update video feed display."""
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def capture_image(self, frame):
        """Capture and display image when object is detected."""
        image_path = f"captured_{self.selected_object}.jpg"
        cv2.imwrite(image_path, frame)
        pixmap = QPixmap(image_path)
        self.captured_image_label.setPixmap(pixmap)

    def manual_capture(self):
        """Manual capture button trigger."""
        ret, frame = self.video_thread.cap.read()
        if ret:
            self.capture_image(frame)

    def process_image(self):
        """Send the captured image and data to AI processing."""
        data = {
            "text": self.text_input.toPlainText(),
            "temperature": self.env_label.text(),
            "image_url": self.history_select.currentText()
        }
        response = requests.post("http://your-ai-server.com/process", json=data)
        print("✅ Process Request Sent:", response.json())

    def close_application(self):
        """Stop the video thread and exit."""
        self.video_thread.stop()
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
