from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox
from PyQt5.QtGui import QPixmap
import paho.mqtt.client as mqtt
import json
import requests
from config import mqtt_config

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Smart Detection & Capture")
        self.setGeometry(100, 100, 800, 600)

        # Layouts
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()

        # Text Input (For AI Processing)
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(50)
        main_layout.addWidget(self.text_input)

        # Object Selection (User chooses the object they want detected)
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        main_layout.addWidget(self.object_select)

        # Capture Button (Sends MQTT Command to Pi)
        self.capture_button = QPushButton("Capture Image")
        self.capture_button.clicked.connect(self.send_capture_command)
        control_layout.addWidget(self.capture_button)

        # Process Button (Sends Text Input to AI via HTTP)
        self.process_button = QPushButton("Process Image")
        self.process_button.clicked.connect(self.send_text_to_ai)
        control_layout.addWidget(self.process_button)

        # Exit Button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        control_layout.addWidget(self.exit_button)

        # Add layouts
        main_layout.addLayout(control_layout)

        # Image Display
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(640, 480)
        main_layout.addWidget(self.image_label)

        self.setLayout(main_layout)

        # MQTT Setup
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
        self.mqtt_client.subscribe("ui/captured_image")
        self.mqtt_client.on_message = self.display_captured_image
        self.mqtt_client.loop_start()

    def send_capture_command(self):
        """Send MQTT command to Pi to capture image."""
        selected_object = self.object_select.currentText().lower()
        message = json.dumps({"selected_object": selected_object})
        self.mqtt_client.publish("ui/command", message)
        print(f"Sent capture command: {message}")

    def send_text_to_ai(self):
        """Send user input text to AI via HTTP."""
        text_data = {
            "text": self.text_input.text()
        }
        response = requests.post("http://your-ai-server.com/process", json=text_data)
        if response.status_code == 200:
            print("Text data sent successfully to AI.")
        else:
            print("Failed to send text data.")

    def display_captured_image(self, client, userdata, message):
        """Display captured image from Raspberry Pi."""
        data = json.loads(message.payload.decode())
        image_url = data.get("image_url")
        if image_url:
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(image_url).content)
            self.image_label.setPixmap(pixmap)
            print(f"Displaying captured image: {image_url}")

if __name__ == "__main__":
    app = QApplication([])
    window = CameraApp()
    window.show()
    app.exec_()
