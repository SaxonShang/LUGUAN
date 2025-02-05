import requests
import json
import time

# ✅ Load HTTP Configuration
try:
    with open("config/ai_config.json", "r") as f:
        config = json.load(f)

    API_URL = config["api_url"]
    API_KEY = config.get("api_key", None)  # Not required for local API

    print("✅ HTTP Client Initialized.")
except Exception as e:
    print(f"❌ Error loading AI configuration: {e}")

def send_image_to_ai(metadata, retries=3):
    """
    Sends image + metadata to Stable Diffusion API.
    
    Args:
        metadata (dict): Contains object name, user text, and image URL.
        retries (int): Number of retry attempts.
    
    Returns:
        str: Processed image URL if successful, None otherwise.
    """
    if "image_url" not in metadata:
        print("❌ Error: Metadata missing required 'image_url' key.")
        return None

    payload = {
        "init_images": [metadata.get("image_url", "")],
        "prompt": metadata.get("text", "No user text provided"),
        "controlnet_conditioning_scale": 1.0,
        "controlnet_model": "canny"
    }

    headers = {"Content-Type": "application/json"}

    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                processed_image_url = data.get("output", None)

                if processed_image_url:
                    print(f"✅ AI Processing Completed: {processed_image_url}")
                    return processed_image_url
                else:
                    print("⚠️ AI response did not contain a processed image URL.")
                    return None
            else:
                print(f"❌ Error sending image: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP Request Failed (Attempt {attempt + 1}/{retries}): {e}")

        attempt += 1
        time.sleep(2)  # Wait before retrying

    print("❌ AI request failed after multiple attempts.")
    return None
