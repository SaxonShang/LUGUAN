import json
import time
from app.camera import Camera
from app.firebase_client import upload_to_firebase
from app.http_client import send_metadata_to_ai
from app.mqtt_client import publish_message, subscribe_to_topic
from app.temp_sensor import get_temperature, get_humidity
from app.yolo_model import YOLO
from app.display import display_image

# Load configuration
with open("config/config.json", "r") as file:
    config = json.load(file)

def on_ai_response(client, userdata, message):
    """Handles AI-processed image URL received from MQTT."""
    data = json.loads(message.payload.decode())
    image_url = data.get("image_url")
    print(f"Received AI-processed image: {image_url}")
    display_image(image_url)  # Display AI-generated image on LED

def main():
    print("Starting Raspberry Pi Application...")
    subscribe_to_topic("ai/processed_image", on_ai_response)
    
    camera = Camera()
    yolo = YOLO()
    
    while True:
        image_path = "ui/captured_images/latest_capture.jpg"
        camera.capture_image(image_path)
        
        detected_objects = yolo.detect_objects(image_path)
        if not detected_objects:
            print("❌ No objects detected, skipping upload.")
            time.sleep(5)
            continue
        
        object_name = detected_objects[0]  # Select first detected object
        image_url = upload_to_firebase(image_path, object_name)
        if not image_url:
            print("❌ Firebase upload failed.")
            time.sleep(5)
            continue
        
        metadata = {
            "temperature": get_temperature(),
            "humidity": get_humidity(),
            "text": "User input text",
            "object": object_name
        }
        send_metadata_to_ai(metadata)
        publish_message("ui/captured_image", json.dumps({"image_url": image_url}))
        
        time.sleep(10)

if __name__ == "__main__":
    main()
