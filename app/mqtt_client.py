import paho.mqtt.client as mqtt
import json
import os
from app.led_display import display_image

# Load MQTT configuration
with open("config/mqtt_config.json", "r") as f:
    config = json.load(f)

BROKER = config["broker"]
PORT = config["port"]
PUBLISH_TOPIC = config["publish_topic"]
SUBSCRIBE_TOPIC = config["subscribe_topic"]

# MQTT Client
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback function when connected to MQTT broker."""
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(SUBSCRIBE_TOPIC)  # Listen for AI-generated images

def on_message(client, userdata, msg):
    """Callback function when receiving an AI-generated image."""
    print(f"Received AI image from {msg.topic}")
    image_path = "ui/captured_images/ai_generated.jpg"
    
    # Save received image
    with open(image_path, "wb") as f:
        f.write(msg.payload)

    # Display image on LED screen
    display_image(image_path)

def publish_image(image_path, metadata):
    """Publish image and metadata to AI processing topic."""
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Convert metadata to JSON
    message = {
        "temperature": metadata["temperature"],
        "humidity": metadata["humidity"],
        "user_text": metadata["text"],
        "object_detected": metadata["object"]
    }
    
    client.publish(PUBLISH_TOPIC, json.dumps(message))
    print(f"Published metadata: {message}")
    
    # Publish image separately
    client.publish(PUBLISH_TOPIC + "/image", image_data)
    print(f"Published image to {PUBLISH_TOPIC}/image")

# Configure MQTT Client
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()  # Start MQTT event loop
