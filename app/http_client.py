import requests
import json

# Load HTTP configuration
with open("config/http_config.json", "r") as f:
    config = json.load(f)

API_URL = config["api_url"]
API_KEY = config["api_key"]

def send_metadata_to_ai(metadata):
    """Send metadata (without image) to AI API via HTTP."""
    payload = {
        "object_detected": metadata["object"],
        "temperature": metadata["temperature"],
        "humidity": metadata["humidity"],
        "user_text": metadata["text"]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"  # If authentication is required
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            print("✅ Metadata sent successfully. AI is processing the image.")
        else:
            print(f"❌ Error sending metadata: {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP Request Failed: {e}")
