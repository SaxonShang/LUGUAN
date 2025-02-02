import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime

# Load Firebase credentials
with open("config/firebase_config.json", "r") as f:
    firebase_config = json.load(f)

cred = credentials.Certificate(firebase_config["service_account"])
firebase_admin.initialize_app(cred)
db = firestore.client()

def store_image_metadata(object_name, image_url, temperature, humidity, user_text):
    """Stores metadata of an image in Firebase Firestore."""
    try:
        timestamp = datetime.datetime.utcnow().isoformat()
        doc_ref = db.collection("images").document(object_name).collection("captures").document(timestamp)
        doc_ref.set({
            "image_url": image_url,
            "temperature": temperature,
            "humidity": humidity,
            "user_text": user_text,
            "timestamp": timestamp
        })
        print(f"✅ Metadata stored for {object_name} at {timestamp}")
    except Exception as e:
        print(f"❌ Error storing metadata: {e}")

def get_latest_image_metadata(object_name):
    """Retrieves the latest stored image metadata for a specific object."""
    try:
        captures_ref = db.collection("images").document(object_name).collection("captures").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
        docs = captures_ref.stream()
        for doc in docs:
            return doc.to_dict()
        print(f"❌ No metadata found for {object_name}")
        return None
    except Exception as e:
        print(f"❌ Error retrieving metadata: {e}")
        return None

def get_all_images():
    """Retrieves all stored image metadata."""
    try:
        images = {}
        images_ref = db.collection("images").stream()
        for image in images_ref:
            object_name = image.id
            captures_ref = db.collection("images").document(object_name).collection("captures").stream()
            images[object_name] = [doc.to_dict() for doc in captures_ref]
        return images
    except Exception as e:
        print(f"❌ Error retrieving all images: {e}")
        return None
