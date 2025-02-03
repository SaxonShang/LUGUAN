import paho.mqtt.client as mqtt
import json
import time
from app.yolo_model import YOLO
from app.camera import Camera
from app.firebase_client import upload_to_firebase, get_latest_image_metadata
from app.display import display_image
from app.temp_sensor import get_temperature, get_humidity
from config import mqtt_config

# MQTT Setup
client = mqtt.Client()
camera = Camera()
yolo = YOLO()

TARGET_OBJECT = None  # Store selected object to detect

def on_connect(client, userdata, flags, rc):
    """Callback when MQTT successfully connects."""
    print(f"✅ Connected to MQTT Broker with result code {rc}")
    client.subscribe("ui/command")  # UI sends object selection
    client.subscribe("ai/processed_image")  # AI sends back processed images

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages."""
    global TARGET_OBJECT

    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic == "ui/command":
            # UI selects an object for automatic detection
            TARGET_OBJECT = payload.get("selected_object")
            print(f"📡 UI requested object detection: {TARGET_OBJECT}")

        elif topic == "ai/processed_image":
            image_url = payload.get("image_url")
            print(f"🎨 AI Processed Image Received: {image_url}")

            # Display the processed image on LED screen
            display_image(image_url)

            # Notify UI to update the display
            client.publish("ui/captured_image", json.dumps({"image_url": image_url}))

    except Exception as e:
        print(f"❌ Error processing message: {e}")

def auto_detect_and_capture():
    """Continuously detects objects and captures images when the selected object is found."""
    global TARGET_OBJECT
    print("🚀 Automatic Detection Started...")

    while True:
        if TARGET_OBJECT:
            detected = yolo.detect_from_camera(TARGET_OBJECT)
            if detected:
                print(f"✅ Detected '{TARGET_OBJECT}', capturing image...")

                # Capture Image
                image_path = f"captured_{TARGET_OBJECT}.jpg"
                camera.capture_image(image_path)

                # Upload Image to Firebase
                image_url = upload_to_firebase(image_path, TARGET_OBJECT)

                # Fetch Environmental Data
                metadata = {
                    "temperature": get_temperature(),
                    "humidity": get_humidity(),
                    "object": TARGET_OBJECT,
                    "image_url": image_url
                }

                # Notify AI for processing
                client.publish("ai/process_request", json.dumps(metadata))
                print(f"📡 Sent image data to AI for processing: {metadata}")

                # Reset the target object (UI must reselect to trigger new detection)
                TARGET_OBJECT = None

            time.sleep(2)  # Avoid excessive image captures

# Connect to MQTT
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
client.loop_start()

# Start Auto Detection
auto_detect_and_capture()
