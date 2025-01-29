import sys
import cv2
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer
from app.camera import Camera
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("AI Smart Detection & Capture")
        self.setGeometry(100, 100, 800, 600)

        # Layouts
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()

        # Large Text Input Box
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(50)
        main_layout.addWidget(self.text_input)

        # Object Selection Dropdown
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie"])
        main_layout.addWidget(self.object_select)

        # Sensor Selection Dropdown
        self.sensor_select = QComboBox()
        self.sensor_select.addItems(["Temperature", "Humidity"])
        main_layout.addWidget(self.sensor_select)

        # Capture Button
        self.capture_button = QPushButton("Capture Manually")
        self.capture_button.clicked.connect(self.capture_image)
        control_layout.addWidget(self.capture_button)

        # Exit Button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        control_layout.addWidget(self.exit_button)

        main_layout.addLayout(control_layout)

        # Image Display
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(640, 480)
        main_layout.addWidget(self.image_label)

        self.setLayout(main_layout)

        # Load styles
        self.load_styles()

        # Initialize camera and YOLO model
        self.camera = Camera()
        self.yolo = YOLO(model_path="models/yolov5s.pt")

        # Timer for automatic object detection
        self.timer = QTimer()
        self.timer.timeout.connect(self.detect_and_capture)
        self.timer.start(1000)  # Check every second

    def load_styles(self):
        """Loads the CSS styles."""
        try:
            with open("ui/styles/style.css", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("Error loading CSS:", e)

    def detect_and_capture(self):
        """Automatically capture an image if the selected object is detected."""
        frame = self.camera.capture_frame()
        detections = self.yolo.detect_objects(frame)

        selected_object = self.object_select.currentText().lower()

        for obj in detections:
            if obj == selected_object:
                image_path = "ui/captured_images/captured.jpg"
                self.camera.capture_image(image_path)
                self.display_image(image_path)
                print(f"Captured image: {image_path}")
                break

    def capture_image(self):
        """Manually capture an image."""
        image_path = "ui/captured_images/manual_capture.jpg"
        self.camera.capture_image(image_path)
        self.display_image(image_path)

    def display_image(self, image_path):
        """Displays the captured image."""
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
