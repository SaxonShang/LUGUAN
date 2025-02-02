import requests
import paho.mqtt.client as mqtt
import json
from app.database_manager import get_latest_image_metadata
from config import ai_config, mqtt_config

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f"✅ AI Server Connected to MQTT with result code {rc}")
    client.subscribe("ai/image_request")  # Listen for new image requests from Pi

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        object_name = payload.get("object")

        # Get latest image for the object
        metadata = get_latest_image_metadata(object_name)
        if not metadata:
            print(f"❌ No image found for {object_name}")
            return

        image_url = metadata["image_url"]
        user_text = metadata["user_text"]
        temperature = metadata["temperature"]
        humidity = metadata["humidity"]

        print(f"🖼️ Processing image: {image_url}")

        # Send to AI API for enhancement
        ai_payload = {
            "image_url": image_url,
            "text": user_text,
            "temperature": temperature,
            "humidity": humidity
        }
        response = requests.post(ai_config["api_endpoint"], json=ai_payload)

        if response.status_code == 200:
            processed_image_url = response.json().get("processed_image_url")
            print(f"✅ AI Processed Image URL: {processed_image_url}")

            # Send back to MQTT for Pi to display
            client.publish("ai/processed_image", json.dumps({"image_url": processed_image_url}))

        else:
            print(f"❌ AI processing failed: {response.text}")

    except Exception as e:
        print(f"❌ Error in AI processing: {e}")

# Start MQTT listener
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
client.loop_start()
