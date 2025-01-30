import paho.mqtt.client as mqtt
import json
import base64
import os

# Load MQTT configuration
with open("config/mqtt_config.json", "r") as f:
    config = json.load(f)

BROKER = config["broker"]
PORT = config["port"]
SUBSCRIBE_TOPIC = config["subscribe_topic"]

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback function when connected to MQTT broker."""
    print(f"✅ Connected to MQTT Broker with result code {rc}")
    client.subscribe(SUBSCRIBE_TOPIC)  # Listen for AI-generated images

def on_message(client, userdata, msg):
    """Callback function when AI-generated image is received via MQTT."""
    print(f"📡 Received AI-generated image from {msg.topic}")
    image_path = "ui/captured_images/ai_generated.jpg"

    # Decode and save the AI-generated image
    with open(image_path, "wb") as f:
        f.write(msg.payload)

    print(f"✅ Saved AI-generated image to {image_path}")

# MQTT Client Configuration
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()  # Start listening for AI-generated images
