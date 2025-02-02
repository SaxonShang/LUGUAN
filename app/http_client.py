import requests
import json
import time

# ✅ Load HTTP Configuration
try:
    with open("config/http_config.json", "r") as f:
        config = json.load(f)

    API_URL = config["api_url"]
    API_KEY = config.get("api_key", None)  # API Key is optional

    print("✅ HTTP Client Initialized.")
except Exception as e:
    print(f"❌ Error loading HTTP configuration: {e}")

def send_metadata_to_ai(metadata, retries=3):
    """
    Sends metadata (without image) to AI API via HTTP.
    
    Args:
        metadata (dict): Contains object name, temperature, humidity, user text.
        retries (int): Number of retry attempts in case of failure.
    
    Returns:
        str: Processed image URL if successful, None otherwise.
    """
    payload = {
        "object": metadata["object"],
        "temperature": metadata["temperature"],
        "humidity": metadata["humidity"],
        "text": metadata["text"]
    }

    headers = {
        "Content-Type": "application/json"
    }

    # ✅ Include API Key if required
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                processed_image_url = data.get("processed_image_url", None)

                if processed_image_url:
                    print(f"✅ AI Processing Completed: {processed_image_url}")
                    return processed_image_url
                else:
                    print("⚠️ AI response did not contain a processed image URL.")
                    return None
            else:
                print(f"❌ Error sending metadata: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP Request Failed (Attempt {attempt + 1}/{retries}): {e}")

        attempt += 1
        time.sleep(2)  # Wait before retrying

    print("❌ AI metadata request failed after multiple attempts.")
    return None
