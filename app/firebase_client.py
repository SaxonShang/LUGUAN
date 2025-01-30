import firebase_admin
from firebase_admin import credentials, storage
import json
import os

# Load Firebase credentials
with open("config/firebase_config.json", "r") as f:
    firebase_config = json.load(f)

cred = credentials.Certificate(firebase_config["service_account"])
firebase_admin.initialize_app(cred, {"storageBucket": firebase_config["storage_bucket"]})
bucket = storage.bucket()

def upload_to_firebase(image_path, object_name):
    """Uploads an image to Firebase Storage and returns its public URL."""
    blob = bucket.blob(f"captured_images/{object_name}.jpg")
    blob.upload_from_filename(image_path)
    image_url = blob.public_url
    print(f"✅ Uploaded {image_path} to Firebase as {object_name}.jpg")
    return image_url

def get_firebase_image(object_name):
    """Downloads an image from Firebase Storage to local storage."""
    blob = bucket.blob(f"captured_images/{object_name}.jpg")
    local_path = f"ui/captured_images/{object_name}.jpg"

    if blob.exists():
        blob.download_to_filename(local_path)
        print(f"✅ Downloaded {object_name}.jpg from Firebase to {local_path}")
        return local_path
    else:
        print(f"❌ No image found in Firebase for {object_name}")
        return None

def upload_ai_generated_image(image_path, object_name):
    """Uploads AI-generated image to Firebase for future use."""
    blob = bucket.blob(f"ai_generated/{object_name}.jpg")
    blob.upload_from_filename(image_path)
    print(f"✅ Uploaded AI-generated image to Firebase as {object_name}.jpg")
    return blob.public_url
