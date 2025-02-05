from fastapi import FastAPI, HTTPException
import firebase_admin
from firebase_admin import credentials, storage
import requests
import json
from config import ai_config, mqtt_config
import paho.mqtt.client as mqtt

app = FastAPI()

# 🔹 Firebase Setup
cred = credentials.Certificate("config/firebase_config.json")
firebase_admin.initialize_app(cred, {"storageBucket": ai_config["firebase_bucket"]})
bucket = storage.bucket()

# 🔹 MQTT Setup (Using Private Broker)
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
    """✅ Fetches latest image from Firebase and sends it to Stable Diffusion for processing."""
    try:
        object_detected = data.get("object")
        user_text = data.get("text")

        # ✅ **Check if the image exists in Firebase**
        blobs = list(bucket.list_blobs(prefix=f"captured_images/{object_detected}"))
        if not blobs:
            return {"error": "No image found for this object"}

        blob = blobs[-1]  # Get the latest image
        image_url = blob.generate_signed_url(expiration=300)

        print(f"🖼️ Found image: {image_url}")

        # ✅ **Send Image & Metadata to Stable Diffusion**
        ai_payload = {
            "init_images": [image_url],
            "prompt": user_text,
            "controlnet_conditioning_scale": 1.0,
            "controlnet_model": "canny"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(ai_config["api_url"], json=ai_payload, headers=headers)

        if response.status_code == 200:
            ai_generated_image_url = response.json().get("output", None)
            if not ai_generated_image_url:
                return {"error": "No image returned by Stable Diffusion"}

            print(f"🎨 AI Processed Image URL: {ai_generated_image_url}")

            # ✅ **Upload AI Processed Image to Firebase**
            ai_blob = bucket.blob(f"ai_generated/{object_detected}.jpg")
            ai_blob.upload_from_string(requests.get(ai_generated_image_url).content, content_type="image/jpeg")
            ai_blob.make_public()
            ai_generated_image_url = ai_blob.public_url
            print(f"✅ AI Processed Image uploaded to Firebase: {ai_generated_image_url}")

            # ✅ **Send processed image URL via MQTT**
            send_mqtt_message(ai_generated_image_url)

            return {"status": "Processing Completed", "image_url": ai_generated_image_url}
        else:
            return {"error": "AI processing failed", "details": response.text}

    except Exception as e:
        return {"error": "Internal Server Error", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
