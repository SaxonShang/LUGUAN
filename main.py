import json
import time
import requests
import paho.mqtt.client as mqtt
from app.firebase_client import upload_to_firebase
from app.http_client import send_metadata_to_ai
from app.display import display_image
from config import mqtt_config

# === Raspberry Pi Camera Stream (MJPEG Streamer) ===
RASPBERRY_PI_IP = "192.168.1.100"  # Update with your Pi's IP
MJPEG_STREAM_URL = f"http://{RASPBERRY_PI_IP}:8080/?action=snapshot"

# === MQTT Client Setup ===
mqtt_client = mqtt.Client()

def on_ai_response(client, userdata, message):
    """Handles AI-processed image URL received from MQTT."""
    try:
        data = json.loads(message.payload.decode())
        image_url = data.get("image_url")
        print(f"🎨 AI-Processed Image Received: {image_url}")

        # Display processed image on LED Screen
        display_image(image_url)

    except Exception as e:
        print(f"❌ Error processing AI response: {e}")

def main():
    """Main function for handling object detection, image capturing, and AI processing."""
    print("🚀 Starting Raspberry Pi Application...")
    
    mqtt_client.on_message = on_ai_response
    mqtt_client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
    mqtt_client.subscribe("ai/processed_image")
    mqtt_client.loop_start()

    while True:
        print("📸 Capturing Image from Pi Camera...")
        image_path = "captured_image.jpg"
        response = requests.get(MJPEG_STREAM_URL, stream=True)

        if response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(response.content)

            print("🔍 Uploading image to Firebase...")
            image_url = upload_to_firebase(image_path, "auto-detection")

            if image_url:
                metadata = {
                    "image_url": image_url,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                print("📡 Sending metadata to AI for processing...")
                send_metadata_to_ai(metadata)

                mqtt_client.publish("ui/captured_image", json.dumps(metadata))
        
        else:
            print("❌ Error: Failed to retrieve image from Pi Camera")

        time.sleep(5)  # Adjust detection interval

if __name__ == "__main__":
    main()
