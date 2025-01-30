from app.camera import Camera
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity
from app.firebase_client import upload_to_firebase
from app.http_client import send_metadata_to_ai

def process_image():
    """Captures an image, uploads it to Firebase, and sends metadata to AI."""
    camera = Camera()
    object_name = "person"  # Example, this can be user-selected
    image_path = f"ui/captured_images/{object_name}.jpg"

    camera.capture_image(image_path)

    # Upload image to Firebase
    image_url = upload_to_firebase(image_path, object_name)

    # Get temperature and humidity readings
    metadata = {
        "temperature": get_temperature(),
        "humidity": get_humidity(),
        "text": "User input text",
        "object": object_name
    }

    # Send metadata to AI for processing
    send_metadata_to_ai(metadata)
