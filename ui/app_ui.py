import sys
import os
import cv2
import json
import requests
import time  # <-- Needed for timing logic
import firebase_admin
from firebase_admin import credentials, db
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage
from datetime import datetime
import base64
import paho.mqtt.client as mqtt

# === Raspberry Pi Camera Stream (MJPEG STREAMER) ===
RASPBERRY_PI_IP = "192.168.141.100"  # Update with actual Pi IP
MJPEG_STREAM_URL = f"http://{RASPBERRY_PI_IP}:8080/?action=stream"

# === Firebase Configuration ===
cred = credentials.Certificate("config/firebase_config.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://luguan-8c32d-default-rtdb.europe-west1.firebasedatabase.app/",
})
firebase_ref = db.reference("captured_images")
firebase_tem = db.reference("captured_images")

# === YOLO Object Detection ===
from yolo_model import YOLO
yolo = YOLO(model_path="models/yolov5s.pt")

# === MQTT Settings ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed, return code {rc}")

def on_message(client, userdata, msg):
    global temperature, humidity
    try:
        data = json.loads(msg.payload.decode())
        temperature = data.get('temperature')
        humidity = data.get('humidity')
    except json.JSONDecodeError:
        print("Failed to decode JSON message")

BROKER_URL = "45daeea25355436589e73eca1801653e.s1.eu.hivemq.cloud"
PORT = 8883  # Secure MQTT over TLS
USERNAME = "Saxon"
PASSWORD = "030401@Szh"
TOPIC = "IC.embedded/LUGUAN/test"

client = mqtt.Client()
client.tls_set()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_URL, PORT, keepalive=60)
client.loop_start()

def check_sensor_data():
    if temperature is not None and humidity is not None:
        return temperature, humidity
    else:
        print("No latest sensor data available")
        return None, None

# === Video Stream Thread with 3-Second Detection Logic ===
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

        # 3-second continuous detection logic
        self.detection_start_time = None
        self.detection_threshold = 1.0  # seconds required to see the object continuously

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Unable to read video frame")
                continue

            self.last_frame = frame.copy()

            # Draw bounding boxes (for display)
            processed_frame = yolo.detect_objects_in_frame(frame, self.selected_object)

            # Convert frame for PyQt
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_update.emit(qt_image)

            # Detect object in the raw frame
            detected_objects = yolo.detect_objects(frame)
            target_found = False
            for obj in detected_objects:
                if obj["name"].lower() == self.selected_object.lower():
                    target_found = True
                    break

            # If object is found, start or continue the timer
            if target_found:
                if self.detection_start_time is None:
                    # First time we see the object
                    self.detection_start_time = time.time()
                else:
                    # Check how long it's been visible
                    elapsed = time.time() - self.detection_start_time
                    if elapsed >= self.detection_threshold:
                        # We've seen the object continuously for at least 3 seconds
                        self.object_detected.emit()
                        # Reset so we only capture once (or comment this out for repeated captures)
                        self.detection_start_time = None
            else:
                # Object lost; reset timer
                self.detection_start_time = None

        self.cap.release()

    def stop(self):
        self.running = False

# === Main UI ===
class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart AI Detection - Version 1.0")
        self.resize(1200, 800)
        self.init_ui()

        self.selected_object = "person"
        self.load_history()

        # Controlling capture flow
        self.can_capture = True
        self.last_captured_frame = None

        # Timer for sensor data
        self.sensor_timer = QTimer(self)
        self.sensor_timer.timeout.connect(self.detect_ht)
        self.sensor_timer.start(3000)  # update every 3 seconds

        # Start the video thread
        self.video_thread = VideoStreamThread(self.selected_object)
        self.video_thread.frame_update.connect(self.update_video_feed)
        self.video_thread.object_detected.connect(self.capture_image)
        self.video_thread.start()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Top Section ---
        top_row = QHBoxLayout()

        # Left Controls
        left_controls = QVBoxLayout()

        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Vase", "Car", "Dog","Book","Bottle","Clock","Potted Plant","Window","Lamp"])
        self.object_select.setFixedHeight(50)
        self.object_select.currentIndexChanged.connect(self.update_selected_object)
        left_controls.addWidget(self.object_select)

        self.history_select = QComboBox()
        self.history_select.addItem("Select History")
        self.history_select.setFixedHeight(50)
        self.history_select.currentIndexChanged.connect(self.display_history_image)
        left_controls.addWidget(self.history_select)

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

        self.clear_button = QPushButton("Clear Database")
        self.clear_button.setFixedHeight(50)
        self.clear_button.setStyleSheet(button_style)
        self.clear_button.clicked.connect(self.clear_database)
        left_controls.addWidget(self.clear_button)

        self.detection_indicator = QPushButton("Detecting")
        self.detection_indicator.setFixedHeight(50)
        self.detection_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.detection_indicator.setStyleSheet("background-color: green; border: 1px solid black; font-size: 18px;")
        self.detection_indicator.clicked.connect(self.reset_detection)
        left_controls.addWidget(self.detection_indicator)

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

        top_row.addLayout(left_controls, 1)
        top_row.addLayout(right_info, 3)
        main_layout.addLayout(top_row)

        # --- Bottom Section ---
        video_capture_layout = QHBoxLayout()

        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True)
        video_capture_layout.addWidget(self.video_label)

        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setScaledContents(True)
        video_capture_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(video_capture_layout)
        self.setLayout(main_layout)

    def update_selected_object(self):
        self.selected_object = self.object_select.currentText().lower()
        self.video_thread.selected_object = self.selected_object
        self.load_history()

    def update_video_feed(self, qt_image):
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        if self.can_capture:
            self.update_indicator("green")

    def capture_image(self):
        """
        Called automatically after 3s of detection by `object_detected`,
        or manually by self.capture_button clicked (if you want that).
        """
        if not self.can_capture:
            return
        if self.video_thread.last_frame is not None:
            frame = self.video_thread.last_frame
            self.last_captured_frame = frame.copy()
            qt_image = QImage(frame.data, frame.shape[1], frame.shape[0],
                              frame.shape[2] * frame.shape[1], QImage.Format_BGR888)
            self.captured_image_label.setPixmap(QPixmap.fromImage(qt_image))

            self.update_indicator("red")
            self.can_capture = False

            # Reset history select to default
            self.history_select.setCurrentIndex(0)
        else:
            print("No video frame available.")

    def process_image(self):
        """
        Upload the captured image if no history is selected,
        then send it to your AI server.
        """
        if self.history_select.currentIndex() <= 0:
            if self.last_captured_frame is not None:
                frame = self.last_captured_frame
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
                os.remove(image_path)
            else:
                print("No captured image to process.")
                return

        # Auto-select latest history if none was chosen
        if self.history_select.currentIndex() <= 0 and self.history_select.count() > 1:
            self.history_select.setCurrentIndex(self.history_select.count() - 1)
        if self.history_select.currentIndex() <= 0:
            print("No history image available to process.")
            return

        key = self.history_select.currentData()
        if not key:
            print("No valid history key found.")
            return

        ref = db.reference(f"image_capture/{self.selected_object}/image_capture/{key}")
        data = ref.get()
        if not data or "image_data" not in data:
            print("No image_data found in Firebase for this entry.")
            return

        image_data = data["image_data"]
        payload = {
            "text": self.text_input.toPlainText(),
            "temperature": self.env_label.text(),
            "image_data": image_data
        }
        response = requests.post("http://your-private-server-ip:5000/process_image", json=payload)
        print("Process response:", response.json())

    def detect_ht(self):
        """Update temperature and humidity every 3s."""
        temperature, humidity = check_sensor_data()
        if temperature is not None and humidity is not None:
            self.env_label.setText(f"Temperature: {temperature}°C  |  Humidity: {humidity}%")
        else:
            self.env_label.setText("Temperature: --°C  |  Humidity: --%")
        self.env_label.repaint()

    def load_history(self):
        """Load timestamps from Firebase for the selected object."""
        ref = db.reference(f"image_capture/{self.selected_object}/image_capture")
        data = ref.get()
        self.history_select.clear()
        self.history_select.addItem("Select History")
        if data:
            for key, value in data.items():
                timestamp = value.get("timestamp", "Unknown")
                self.history_select.addItem(timestamp, key)

    def display_history_image(self):
        """Display the image for the selected history timestamp."""
        if self.history_select.currentIndex() <= 0:
            return
        key = self.history_select.currentData()
        if not key:
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
        if status.lower() == "green":
            self.detection_indicator.setStyleSheet("background-color: green; border: 1px solid black; font-size: 18px;")
            self.detection_indicator.setText("Detecting")
        elif status.lower() == "red":
            self.detection_indicator.setStyleSheet("background-color: red; border: 1px solid black; font-size: 18px;")
            self.detection_indicator.setText("Captured")

    def reset_detection(self):
        """When the indicator is red, click to re-enable detection."""
        if not self.can_capture:
            self.can_capture = True
            self.update_indicator("green")
            # Reset the history select to default
            self.history_select.setCurrentIndex(0)

    def clear_database(self):
        """Clear the entire captured_images data."""
        firebase_ref.set({})
        firebase_tem.set({})
        print("Database cleared.")

    def closeEvent(self, event):
        """Ensure we stop the thread on UI close."""
        self.video_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
