from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, initialize_app, storage
import paho.mqtt.client as mqtt
import json
import requests
from config import ai_config, mqtt_config

app = FastAPI()

# 🔹 Firebase Setup
cred = credentials.Certificate("config/firebase_config.json")
initialize_app(cred, {"storageBucket": ai_config["firebase_bucket"]})
bucket = storage.bucket()

# 🔹 MQTT Setup
MQTT_BROKER = mqtt_config["broker"]
MQTT_PORT = mqtt_config["port"]
MQTT_TOPIC = "ai/processed_image"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

def send_mqtt_message(image_url):
    """✅ Sends AI-generated image URL via MQTT to Raspberry Pi."""
    try:
        payload = json.dumps({"image_url": image_url})
        mqtt_client.publish(MQTT_TOPIC, payload)
        print(f"✅ AI-generated image sent via MQTT: {image_url}")
    except Exception as e:
        print(f"❌ Error sending MQTT message: {e}")

@app.post("/process_image")
async def process_image(data: dict):
    """✅ Receives metadata from UI, fetches image from Firebase, and sends it for AI processing."""
    try:
        object_detected = data.get("object")
        user_text = data.get("text")
        temperature = data.get("temperature")
        humidity = data.get("humidity")

        # ✅ **Check if the image exists in Firebase**
        blobs = list(bucket.list_blobs(prefix=f"captured_images/{object_detected}"))
        if not blobs:
            raise HTTPException(status_code=404, detail=f"❌ Image not found for {object_detected}")

        blob = blobs[-1]  # Get the latest image for this object
        image_url = blob.generate_signed_url(expiration=300)  # Generate temporary download link

        print(f"🖼️ Found image: {image_url}")

        # ✅ **Send Image & Metadata to AI Processing API**
        ai_payload = {
            "image_url": image_url,
            "text": user_text,
            "temperature": temperature,
            "humidity": humidity
        }
        response = requests.post(ai_config["api_endpoint"], json=ai_payload)

        if response.status_code == 200:
            ai_generated_image_url = response.json().get("processed_image_url")
            print(f"🎨 AI Processed Image URL: {ai_generated_image_url}")

            # ✅ **Send processed image URL via MQTT**
            send_mqtt_message(ai_generated_image_url)

            return {"status": "Processing Completed", "image_url": ai_generated_image_url}
        else:
            print(f"❌ AI processing failed: {response.text}")
            raise HTTPException(status_code=500, detail="AI processing failed")

    except Exception as e:
        print(f"❌ Error processing image: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
