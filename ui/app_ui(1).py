import sys
import os
import cv2
import json
import requests
import firebase_admin
from firebase_admin import credentials, storage, db
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage
from datetime import datetime
import base64
import paho.mqtt.client as mqtt
import json

# === Raspberry Pi Camera Stream (MJPEG Streamer) ===
RASPBERRY_PI_IP = "192.168.141.100"  # Update with your actual Pi IP
MJPEG_STREAM_URL = f"http://{RASPBERRY_PI_IP}:8080/?action=stream"

# === Firebase Configuration ===
cred = credentials.Certificate("config/firebase_config.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://luguan-8c32d-default-rtdb.europe-west1.firebasedatabase.app/",
    "storageBucket": "your-bucket-name.appspot.com"
})
bucket = storage.bucket()
# These references are used when clearing data:
firebase_ref = db.reference("captured_images")
firebase_tem = db.reference("captured_images")

# === YOLO Object Detection ===
from yolo_model import YOLO
yolo = YOLO(model_path="models/yolov5s.pt")

def on_connect(client, userdata, flags, rc):
    """Callback when connected to the MQTT broker."""
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed, return code {rc}")

def on_message(client, userdata, msg):
    """Callback when an MQTT message is received."""
    global temperature, humidity
    try:
        data = json.loads(msg.payload.decode())
        temperature = data.get('temperature')
        humidity = data.get('humidity')
    except json.JSONDecodeError:
        print("Failed to decode JSON message")

# === MQTT Broker Configuration (Private Broker) ===
BROKER_URL = "45daeea25355436589e73eca1801653e.s1.eu.hivemq.cloud"
PORT = 8883  # Secure MQTT over TLS
USERNAME = "Saxon"  # Your HiveMQ Cloud username
PASSWORD = "030401@Szh"  # Your HiveMQ Cloud password
TOPIC = "IC.embedded/LUGUAN/test"

client = mqtt.Client()
client.tls_set()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_URL, PORT, keepalive=60)
client.loop_start()

def get_sensor_data():
    if temperature is not None and humidity is not None:
        return temperature, humidity
    else:
        print("No latest sensor data available")
        return 30, 30

# === Video Stream Processing Thread ===
class VideoStreamThread(QThread):
    frame_update = pyqtSignal(QImage)
    object_detected = pyqtSignal()

    def __init__(self, selected_object):
        super().__init__()
        self.selected_object = selected_object
        self.running = True
        self.cap = cv2.VideoCapture(MJPEG_STREAM_URL)
        if not self.cap.isOpened():
            print("Unable to connect to video stream")
        self.last_frame = None

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.last_frame = frame.copy()
                processed_frame = yolo.detect_objects_in_frame(frame, self.selected_object)
                rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_update.emit(qt_image)
                detected_objects = yolo.detect_objects(frame)
                if self.selected_object in detected_objects:
                    self.object_detected.emit()
            else:
                print("Unable to read video frame")
        self.cap.release()

    def stop(self):
        self.running = False

# === Main UI Application ===
class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Detection & Capture - Final Version")
        self.resize(1200, 800)
        self.init_ui()
        # Set default selected object and load its history immediately.
        self.selected_object = "person"
        self.load_history()
        # Flag to control whether a new capture is allowed.
        self.can_capture = True

        self.sensor_timer = QTimer(self)
        self.sensor_timer.timeout.connect(self.detect_ht)
        self.sensor_timer.start(3000)  # Update sensor data every 3 seconds

        self.video_thread = VideoStreamThread(self.selected_object)
        self.video_thread.frame_update.connect(self.update_video_feed)
        self.video_thread.object_detected.connect(self.capture_image)
        self.video_thread.start()

    def init_ui(self):
        """Initialize UI layout with resizable elements."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Top Section: Button Controls and Info Panel ---
        top_row = QHBoxLayout()

        # Left Controls (Buttons & Dropdowns) – occupies less horizontal space.
        left_controls = QVBoxLayout()
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        self.object_select.setFixedHeight(50)
        self.object_select.currentIndexChanged.connect(self.update_selected_object)
        left_controls.addWidget(self.object_select)
        
        self.history_select = QComboBox()
        self.history_select.addItem("Select History")
        self.history_select.setFixedHeight(50)
        self.history_select.currentIndexChanged.connect(self.display_history_image)
        left_controls.addWidget(self.history_select)

        # Common button style (font size 18px)
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 18px;
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

        # Renamed "Exit" to "Clear Database" (it only clears the Firebase node)
        self.clear_button = QPushButton("Clear Database")
        self.clear_button.setFixedHeight(50)
        self.clear_button.setStyleSheet(button_style)
        self.clear_button.clicked.connect(self.clear_database)
        left_controls.addWidget(self.clear_button)

        # Detection Indicator as a button (same size as other buttons)
        self.detection_indicator = QPushButton("Detecting")
        self.detection_indicator.setFixedHeight(50)
        self.detection_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.detection_indicator.setStyleSheet("background-color: green; border: 1px solid black; font-size: 18px;")
        self.detection_indicator.clicked.connect(self.reset_detection)
        left_controls.addWidget(self.detection_indicator)

        # Right Info Panel (Temperature/Humidity & Text Input) – occupies more horizontal space.
        right_info = QVBoxLayout()
        self.env_label = QLabel("Temperature: --°C  |  Humidity: --%")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setFixedHeight(50)  # One button's height
        self.env_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        right_info.addWidget(self.env_label)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(150)  # Total = 200px (50 + 150)
        right_info.addWidget(self.text_input)

        # Add left controls and right info with stretch factors: left takes 1 part, right takes 3 parts.
        top_row.addLayout(left_controls, 1)
        top_row.addLayout(right_info, 3)
        main_layout.addLayout(top_row)

        # --- Bottom Section: Video Feed & Captured Image Side by Side ---
        video_capture_layout = QHBoxLayout()

        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setScaledContents(True)
        video_capture_layout.addWidget(self.video_label)

        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.captured_image_label.setMinimumSize(1, 1)
        self.captured_image_label.setScaledContents(True)
        video_capture_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(video_capture_layout)
        self.setLayout(main_layout)

    def update_selected_object(self):
        """Update the selected object and reload history."""
        self.selected_object = self.object_select.currentText().lower()
        self.video_thread.selected_object = self.selected_object
        self.load_history()

    def update_video_feed(self, qt_image):
        """Update the video feed label with YOLO detection output."""
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        if self.can_capture:
            self.update_indicator("green")

    def capture_image(self):
        """
        Capture the detected frame, display it, upload it to Firebase,
        update history, and set the indicator to red.
        Only capture if allowed (i.e. can_capture is True).
        """
        if not self.can_capture:
            return
        if self.video_thread.last_frame is not None:
            frame = self.video_thread.last_frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = f"captured_{self.selected_object}_{timestamp}.jpg"
            cv2.imwrite(image_path, frame)
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            ref = db.reference(f"image_capture/{self.selected_object}/image_capture")
            new_ref = ref.push()
            new_ref.set({
                "timestamp": timestamp,
                "image_data": img_base64,
                "object": self.selected_object
            })
            self.load_history()
            qt_image = QImage(frame.data, frame.shape[1], frame.shape[0],
                              frame.shape[2] * frame.shape[1], QImage.Format_BGR888)
            self.captured_image_label.setPixmap(QPixmap.fromImage(qt_image))
            self.update_indicator("red")
            self.can_capture = False
            os.remove(image_path)
        else:
            print("No video frame available.")

    def manual_capture(self):
        """Manual capture trigger."""
        ret, frame = self.video_thread.cap.read()
        if ret:
            self.capture_image()

    def process_image(self):
        """
        Process the captured image:
        - If no history item is manually selected (i.e. if the history_select is at the default),
          automatically select the latest history entry.
        - Then, retrieve the image_data (Base64) from Firebase and package it with text
          and environment readings, and send it to the AI processing endpoint.
        """
        # If no history is selected and there is at least one history entry, auto-select the last.
        if self.history_select.currentIndex() <= 0 and self.history_select.count() > 1:
            self.history_select.setCurrentIndex(self.history_select.count() - 1)
        if self.history_select.currentIndex() <= 0:
            print("No history image available to process.")
            return
        key = self.history_select.currentData()
        if key is None:
            print("No valid history key found.")
            return
        ref = db.reference(f"image_capture/{self.selected_object}/image_capture/{key}")
        data = ref.get()
        if not data or "image_data" not in data:
            print("No image data found for the selected history entry.")
            return
        image_data = data["image_data"]
        payload = {
            "text": self.text_input.toPlainText(),
            "temperature": self.env_label.text(),
            "image_data": image_data
        }
        response = requests.post("http://127.0.0.1:5000/process_image", json=payload)

        print("Process response:", response.json())

    def detect_ht(self):
        """Update temperature and humidity every 3 seconds."""
        temperature, humidity = get_sensor_data()
        if temperature is not None and humidity is not None:
            self.env_label.setText(f"Temperature: {temperature}°C  |  Humidity: {humidity}%")
        else:
            self.env_label.setText("Temperature: --°C  |  Humidity: --%")
        self.env_label.repaint()

    def load_history(self):
        """Load history options from Firebase for the selected object."""
        ref = db.reference(f"image_capture/{self.selected_object}/image_capture")
        data = ref.get()
        self.history_select.clear()
        self.history_select.addItem("Select History")
        if data:
            for key, value in data.items():
                timestamp = value.get("timestamp", "Unknown")
                self.history_select.addItem(timestamp, key)

    def display_history_image(self):
        """Display the corresponding captured image for the selected history timestamp."""
        if self.history_select.currentIndex() <= 0:
            return
        key = self.history_select.currentData()
        if key is None:
            return
        ref = db.reference(f"image_capture/{self.selected_object}/image_capture/{key}")
        data = ref.get()
        if data:
            base64_str = data.get("image_data")
            if base64_str:
                image_bytes = base64.b64decode(base64_str)
                qt_image = QImage.fromData(image_bytes)
                self.captured_image_label.setPixmap(QPixmap.fromImage(qt_image))
                self.update_indicator("red")
                self.can_capture = False

    def update_indicator(self, status):
        """Update the detection indicator button.
           Green ('Detecting') means actively detecting.
           Red ('Captured') means detection is paused.
        """
        if status.lower() == "green":
            self.detection_indicator.setStyleSheet("background-color: green; border: 1px solid black; font-size: 18px;")
            self.detection_indicator.setText("Detecting")
        elif status.lower() == "red":
            self.detection_indicator.setStyleSheet("background-color: red; border: 1px solid black; font-size: 18px;")
            self.detection_indicator.setText("Captured")

    def reset_detection(self):
        """
        When the detection indicator button is clicked while red,
        reset it to green to allow capturing again.
        """
        if not self.can_capture:
            self.can_capture = True
            self.update_indicator("green")

    def clear_database(self):
        """Clear the captured_images node in Firebase."""
        firebase_ref.set({})
        firebase_tem.set({})

    def closeEvent(self, event):
        """Stop the video thread when the window is closed."""
        self.video_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
