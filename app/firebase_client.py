import firebase_admin
from firebase_admin import credentials, storage
import json

# Load Firebase credentials
with open("config/firebase_config.json", "r") as f:
    firebase_config = json.load(f)

cred = credentials.Certificate(firebase_config["service_account"])
firebase_admin.initialize_app(cred, {"storageBucket": firebase_config["storage_bucket"]})
bucket = storage.bucket()

def upload_to_firebase(image_path, object_name):
    """Uploads image to Firebase Storage."""
    blob = bucket.blob(f"captured_images/{object_name}.jpg")
    blob.upload_from_filename(image_path)
    print(f"Uploaded {image_path} to Firebase as {object_name}.jpg")
    return blob.public_url

def get_firebase_image_url(object_name):
    """Gets the Firebase URL for an image if it exists."""
    blob = bucket.blob(f"captured_images/{object_name}.jpg")
    if blob.exists():
        return blob.public_url
    return None
