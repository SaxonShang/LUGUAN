import requests
import paho.mqtt.client as mqtt
import json
from app.database_manager import get_latest_image_metadata
from config import ai_config, mqtt_config

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """✅ AI Client Connected to MQTT Broker."""
    if rc == 0:
        print(f"✅ Connected to MQTT Broker: {mqtt_config['broker']}")
    else:
        print(f"❌ Failed to connect to MQTT Broker. Return code {rc}")

    client.subscribe("ai/image_request")  # Listen for new image requests from Pi

def on_message(client, userdata, msg):
    """Handles image requests from Raspberry Pi and sends them to Stable Diffusion."""
    try:
        payload = json.loads(msg.payload.decode())
        object_name = payload.get("object")

        # ✅ Get latest image for the object from Firebase
        metadata = get_latest_image_metadata(object_name)
        if not metadata or "image_url" not in metadata:
            print(f"⚠️ No image found for {object_name}. Sending empty response.")
            client.publish("ai/processed_image", json.dumps({"error": "No image found"}))
            return

        image_url = metadata["image_url"]
        user_text = metadata.get("user_text", "")

        print(f"🖼️ Sending image to Stable Diffusion: {image_url}")

        # ✅ Send Image & Metadata to Stable Diffusion
        ai_payload = {
            "init_images": [image_url],
            "prompt": user_text,
            "controlnet_conditioning_scale": 1.0,
            "controlnet_model": "canny"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(ai_config["api_url"], json=ai_payload, headers=headers)

        if response.status_code == 200:
            processed_image_url = response.json().get("output", None)

            if not processed_image_url:
                print("⚠️ AI response did not contain a processed image URL.")
                client.publish("ai/processed_image", json.dumps({"error": "AI processing failed"}))
                return

            print(f"✅ AI Processed Image URL: {processed_image_url}")

            # ✅ Send AI-processed image URL via MQTT to Raspberry Pi
            client.publish("ai/processed_image", json.dumps({"image_url": processed_image_url}))

        else:
            print(f"❌ AI processing failed: {response.text}")
            client.publish("ai/processed_image", json.dumps({"error": "AI processing failed"}))

    except Exception as e:
        print(f"❌ Error in AI processing: {e}")
        client.publish("ai/processed_image", json.dumps({"error": str(e)}))

# ✅ Connect & Start MQTT Listener
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
client.loop_start()
