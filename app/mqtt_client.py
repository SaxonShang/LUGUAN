import json
import paho.mqtt.client as mqtt
from app.display import display_image
from config import mqtt_config

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """✅ Connect to MQTT Broker."""
    if rc == 0:
        print(f"✅ Connected to MQTT Broker: {mqtt_config['broker']}")
    else:
        print(f"❌ Failed to connect to MQTT Broker. Return code {rc}")

    client.subscribe("ui/command")  # Listen for capture requests
    client.subscribe("ai/processed_image")  # AI sends back processed images

def on_message(client, userdata, msg):
    """Handles incoming MQTT messages from AI."""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic == "ai/processed_image":
            image_url = payload.get("image_url")
            if image_url:
                print(f"🎨 AI Processed Image Received: {image_url}")
                display_image(image_url)
                client.publish("ui/captured_image", json.dumps({"image_url": image_url}))
            else:
                print("⚠️ AI processing failed. No image received.")

    except Exception as e:
        print(f"❌ Error processing MQTT message: {e}")

# ✅ Connect and Start MQTT Loop
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
client.loop_start()
