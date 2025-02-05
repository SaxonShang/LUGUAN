import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime

# ✅ Load Firebase credentials
try:
    with open("config/firebase_config.json", "r") as f:
        firebase_config = json.load(f)

    cred = credentials.Certificate(firebase_config["service_account"])
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firestore initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing Firestore: {e}")

def store_processed_image(object_name, ai_image_url):
    """Stores AI-processed image URL in Firebase Firestore."""
    try:
        timestamp = datetime.datetime.utcnow().isoformat()
        doc_ref = db.collection("ai_generated").document(object_name).collection("images").document(timestamp)
        doc_ref.set({
            "ai_image_url": ai_image_url,
            "timestamp": timestamp
        })
        print(f"✅ AI Processed Image stored for {object_name} at {timestamp}")
    except Exception as e:
        print(f"❌ Error storing AI-processed image: {e}")
