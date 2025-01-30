from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox
from PyQt5.QtGui import QPixmap
from app.camera import Camera
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity
from app.firebase_client import upload_to_firebase
from app.http_client import send_metadata_to_ai

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
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        main_layout.addWidget(self.object_select)

        self.capture_button = QPushButton("Capture & Process")
        self.capture_button.clicked.connect(self.capture_and_process)
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

    def capture_and_process(self):
        object_name = self.object_select.currentText().lower()
        image_path = f"ui/captured_images/{object_name}.jpg"
        self.camera.capture_image(image_path)
        upload_to_firebase(image_path, object_name)

        metadata = {
            "temperature": get_temperature(),
            "humidity": get_humidity(),
            "text": self.text_input.text(),
            "object": object_name
        }

        send_metadata_to_ai(metadata)
