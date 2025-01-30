import time
from app.camera import Camera
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity
from app.firebase_client import upload_to_firebase
from app.http_client import send_metadata_to_ai
from app.mqtt_client import client as mqtt_client
from app.display import display_image

# Object to detect (User-Selected)
DETECTED_OBJECTS = ["person", "tie", "car", "dog"]  # Expand if needed

def main():
    """Main loop for object detection, AI processing, and display."""
    print("🚀 System Initialized: Waiting for object detection...")

    camera = Camera()
    yolo = YOLO()

    while True:
        image_path = "ui/captured_images/temp.jpg"
        camera.capture_image(image_path)

        detected_objects = yolo.detect_objects(image_path)
        detected_target = [obj for obj in detected_objects if obj in DETECTED_OBJECTS]

        if detected_target:
            print(f"✅ Detected target: {detected_target}")

            # Upload image to Firebase
            object_name = detected_target[0]
            image_url = upload_to_firebase(image_path, object_name)

            # Get sensor data
            temperature = get_temperature()
            humidity = get_humidity()
            user_text = "User-defined text"

            # Send metadata to AI server
            metadata = {
                "object": object_name,
                "temperature": temperature,
                "humidity": humidity,
                "text": user_text
            }
            send_metadata_to_ai(metadata)

            print(f"📡 Sent metadata to AI: {metadata}")
        
        else:
            print("❌ No target object detected. Retrying...")

        time.sleep(5)  # Wait before capturing next frame

if __name__ == "__main__":
    mqtt_client.loop_start()  # Start listening for AI-generated images
    main()
