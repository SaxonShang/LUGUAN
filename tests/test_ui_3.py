import sys
import os
import cv2
import json
import random
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage

# Import YOLO Model
from yolo_model import YOLO

# Initialize YOLO
yolo = YOLO(model_path="models/yolov5s.pt")

class VideoStreamThread(QThread):
    """
    Thread to continuously capture video frames and run YOLO detection.
    Emits frames with bounding boxes only for the selected object.
    """
    frame_update = pyqtSignal(QImage)
    object_detected = pyqtSignal()  # Signal to trigger image capture

    def __init__(self, selected_object):
        super().__init__()
        self.selected_object = selected_object
        self.running = True
        self.cap = cv2.VideoCapture(0)  # Use laptop camera

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Detect objects in the frame
            processed_frame = yolo.detect_objects_in_frame(frame, self.selected_object)

            # Convert frame to QImage for PyQt display
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_update.emit(qt_image)

            # Check if the selected object is detected and capture image
            detected_objects = yolo.detect_objects("temp_frame.jpg")
            if any(obj["name"] == self.selected_object for obj in detected_objects):
                self.object_detected.emit()  # Signal main UI to capture

    def stop(self):
        """Stops the video stream."""
        self.running = False
        self.cap.release()

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Detection & Capture - Test Version")
        self.resize(1200, 800)
        self.init_ui()

        # Default selected object
        self.selected_object = "person"
        
        # Start Video Stream
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

        # Buttons
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

        self.capture_button = QPushButton("Manual Capture")
        self.capture_button.setFixedHeight(50)
        self.capture_button.setStyleSheet(button_style)
        self.capture_button.clicked.connect(self.capture_image)
        left_controls.addWidget(self.capture_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(50)
        self.exit_button.setStyleSheet(button_style)
        self.exit_button.clicked.connect(self.close)
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
        self.video_label.setStyleSheet("border: 2px solid blue; font-size: 16px;")
        video_capture_layout.addWidget(self.video_label)

        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setStyleSheet("border: 2px solid green; font-size: 16px;")
        video_capture_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(video_capture_layout)
        self.setLayout(main_layout)

    def update_selected_object(self):
        """Updates the selected object for detection."""
        self.selected_object = self.object_select.currentText().lower()
        self.video_thread.selected_object = self.selected_object
        print(f"🔍 Now detecting: {self.selected_object}")

    def update_video_feed(self, qt_image):
        """Updates the video feed label with YOLO detection output."""
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def capture_image(self):
        """Captures the current frame when the selected object is detected."""
        ret, frame = self.video_thread.cap.read()
        if ret:
            image_path = "captured_image.jpg"
            cv2.imwrite(image_path, frame)

            pixmap = QPixmap(image_path)
            target_size = self.captured_image_label.size()
            pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.captured_image_label.setPixmap(pixmap)

            print(f"📸 Captured Image of {self.selected_object} Saved!")
        else:
            print("❌ Failed to capture image.")

    def closeEvent(self, event):
        """Stops video processing and closes application."""
        self.video_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
