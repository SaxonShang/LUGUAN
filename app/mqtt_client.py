import paho.mqtt.client as mqtt
import json
from app.firebase_client import get_latest_image_metadata
from app.display import display_image
from config import mqtt_config

# MQTT Setup
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback when MQTT successfully connects."""
    print(f"✅ Connected to MQTT Broker with result code {rc}")
    client.subscribe("ui/command")  # UI requests Pi to capture and upload an image
    client.subscribe("ai/processed_image")  # AI sends back processed images

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages."""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic == "ui/command":
            object_name = payload.get("selected_object")
            print(f"📸 Capture requested for: {object_name}")

            # Get latest image from Firebase
            metadata = get_latest_image_metadata(object_name)
            if metadata:
                print(f"✅ Sending latest image metadata for {object_name} to AI")
                client.publish("ai/image_request", json.dumps(metadata))  # Request AI processing
            else:
                print(f"❌ No image found for {object_name}.")

        elif topic == "ai/processed_image":
            image_url = payload.get("image_url")
            print(f"🎨 AI Processed Image Received: {image_url}")

            # Display on LED Screen
            display_image(image_url)

            # Notify UI to update display
            client.publish("ui/captured_image", json.dumps({"image_url": image_url}))
    
    except Exception as e:
        print(f"❌ Error processing message: {e}")

# Connect and loop
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
client.loop_start()
