from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from app.camera import Camera
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity
from app.firebase_client import upload_to_firebase, get_firebase_image_url

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Smart Detection & Capture")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(50)
        main_layout.addWidget(self.text_input)

        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog", "Bike", "Cat", "Laptop", "Phone", "Bottle", "Book"])
        self.object_select.currentIndexChanged.connect(self.update_displayed_image)
        main_layout.addWidget(self.object_select)

        self.sensor_select = QComboBox()
        self.sensor_select.addItems(["Temperature", "Humidity"])
        main_layout.addWidget(self.sensor_select)

        self.capture_button = QPushButton("Capture Manually")
        self.capture_button.clicked.connect(self.capture_image)
        control_layout.addWidget(self.capture_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        control_layout.addWidget(self.exit_button)

        main_layout.addLayout(control_layout)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(640, 480)
        main_layout.addWidget(self.image_label)

        self.setLayout(main_layout)

        self.camera = Camera()
        self.yolo = YOLO(model_path="models/yolov5s.pt")

        self.timer = QTimer()
        self.timer.timeout.connect(self.detect_and_store)
        self.timer.start(1000)

        self.detected_objects = {}

    def detect_and_store(self):
        """Detects objects and captures their images (first time only)."""
        frame = self.camera.capture_frame()
        detections = self.yolo.detect_objects(frame)

        detected_image_path = None
        new_objects = []

        for obj in detections:
            if obj not in self.detected_objects:
                image_path = f"ui/captured_images/{obj}.jpg"
                self.camera.capture_image(image_path)
                self.detected_objects[obj] = image_path
                detected_image_path = image_path
                new_objects.append(obj)

        if detected_image_path:
            # Upload all newly detected objects to Firebase (same image if they appear in the same frame)
            for obj in new_objects:
                upload_to_firebase(detected_image_path, obj)

        self.update_displayed_image()

    def capture_image(self):
        """Manually captures an image."""
        image_path = "ui/captured_images/manual_capture.jpg"
        self.camera.capture_image(image_path)
        self.display_image(image_path)

    def update_displayed_image(self):
        """Updates the displayed image based on the selected object."""
        selected_object = self.object_select.currentText().lower()
        if selected_object in self.detected_objects:
            self.display_image(self.detected_objects[selected_object])
        else:
            firebase_url = get_firebase_image_url(selected_object)
            if firebase_url:
                self.display_image(firebase_url)
            else:
                print(f"No image found for {selected_object}")

    def display_image(self, image_path):
        """Displays the selected image."""
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)
