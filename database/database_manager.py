import firebase_admin
from firebase_admin import credentials, firestore
import json

# Load Firebase credentials
with open("config/firebase_config.json", "r") as f:
    firebase_config = json.load(f)

cred = credentials.Certificate(firebase_config["service_account"])
firebase_admin.initialize_app(cred)
db = firestore.client()

def store_image_metadata(object_name, image_url, temperature, humidity, user_text):
    """Stores metadata of an image in Firebase Firestore."""
    doc_ref = db.collection("images").document(object_name)
    doc_ref.set({
        "image_url": image_url,
        "temperature": temperature,
        "humidity": humidity,
        "user_text": user_text
    })
    print(f"✅ Metadata stored for {object_name}")

def get_image_metadata(object_name):
    """Retrieves image metadata from Firebase Firestore."""
    doc_ref = db.collection("images").document(object_name)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print(f"❌ No metadata found for {object_name}")
        return None
