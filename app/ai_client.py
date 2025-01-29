import requests
import json
import os

# Load AI API configuration
with open("config/ai_config.json", "r") as f:
    config = json.load(f)

API_URL = config["api_url"]
API_KEY = config["api_key"]

def generate_ai_image(user_text, temperature, humidity, image_path):
    """Send data to AI API and get a generated image."""
    prompt = f"{user_text}, inspired by a temperature of {temperature}°C and humidity of {humidity}%."

    # API request payload
    payload = {
        "text": prompt
    }
    
    headers = {"api-key": API_KEY}

    print(f"Sending request to AI API with prompt: {prompt}")

    response = requests.post(API_URL, data=payload, headers=headers)

    if response.status_code == 200:
        image_url = response.json().get("output_url")
        if image_url:
            download_ai_image(image_url)
        else:
            print("Error: No image URL received from API.")
    else:
        print(f"Error generating image: {response.text}")

def download_ai_image(image_url):
    """Download the AI-generated image and save it locally."""
    response = requests.get(image_url)

    if response.status_code == 200:
        ai_image_path = "ui/captured_images/ai_generated.jpg"
        with open(ai_image_path, "wb") as f:
            f.write(response.content)

        print(f"AI-generated image saved: {ai_image_path}")
        return ai_image_path
    else:
        print(f"Error downloading AI image: {response.text}")
        return None
