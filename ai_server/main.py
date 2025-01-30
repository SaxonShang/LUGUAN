from fastapi import FastAPI, HTTPException, Depends
from firebase_admin import credentials, initialize_app, storage
import paho.mqtt.client as mqtt
import json

app = FastAPI()

# Firebase Setup
cred = credentials.Certificate("config/firebase_config.json")
initialize_app(cred, {"storageBucket": "your-firebase-bucket"})
bucket = storage.bucket()

# MQTT Configuration
MQTT_BROKER = "your-mqtt-broker"
MQTT_PORT = 1883
MQTT_TOPIC = "ai/image_result"

def send_mqtt_message(image_url):
    """Sends AI-generated image URL via MQTT to Raspberry Pi."""
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, image_url)
    client.disconnect()

@app.post("/process_image")
async def process_image(data: dict):
    """Receives metadata from Raspberry Pi, fetches the image from Firebase, and sends it for AI processing."""
    object_detected = data.get("object_detected")

    # Check if image exists in Firebase
    blob = bucket.blob(f"captured_images/{object_detected}.jpg")
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Image not found in Firebase")

    # AI Processing (Placeholder - Replace with actual AI logic)
    ai_generated_image_url = f"https://your-firebase-bucket/ai_generated/{object_detected}.jpg"

    # Send AI-generated image URL via MQTT
    send_mqtt_message(ai_generated_image_url)

    return {"status": "Processing Started", "image_url": ai_generated_image_url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
