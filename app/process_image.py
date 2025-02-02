from app.camera import Camera
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity
from app.firebase_client import upload_to_firebase
from app.http_client import send_metadata_to_ai
import os

def process_image():
    """
    Captures an image, detects objects using YOLO, uploads it to Firebase, 
    and sends metadata to AI.
    """
    camera = Camera()
    image_path = "ui/captured_images/latest_capture.jpg"

    # ✅ Capture image
    if not camera.capture_image(image_path):
        print("❌ Image capture failed. Aborting process.")
        return
    
    # ✅ Run YOLO Object Detection
    yolo = YOLO(model_path="models/yolov5s.pt")
    detected_objects = yolo.detect_objects(image_path)

    if not detected_objects:
        print("❌ No objects detected in the image. Skipping upload.")
        return

    object_name = detected_objects[0]  # ✅ Select first detected object
    print(f"🔍 Detected object: {object_name}")

    # ✅ Rename image to match detected object
    new_image_path = f"ui/captured_images/{object_name}.jpg"
    os.rename(image_path, new_image_path)

    # ✅ Upload image to Firebase
    image_url = upload_to_firebase(new_image_path, object_name)
    if not image_url:
        print("❌ Firebase upload failed. Aborting metadata send.")
        return

    # ✅ Get sensor data
    metadata = {
        "temperature": get_temperature(),
        "humidity": get_humidity(),
        "text": "User input text",
        "object": object_name
    }

    # ✅ Send metadata to AI for processing
    send_metadata_to_ai(metadata)

    print("✅ Process completed successfully!")

# ✅ Example Usage (for Testing)
if __name__ == "__main__":
    process_image()
