from fastapi import FastAPI, HTTPException
import os
import base64
import uuid
from PIL import Image
import torch
from diffusers import StableDiffusionImg2ImgPipeline
import paho.mqtt.client as mqtt
import json

# === Load AI Settings ===
AI_SETTINGS_PATH = "config/ai_settings.json"
if os.path.exists(AI_SETTINGS_PATH):
    with open(AI_SETTINGS_PATH, "r") as f:
        ai_settings = json.load(f)
else:
    ai_settings = {
        "selected_model": "openjourney_local",
        "selected_approach": "Map Humidity & Temperature"
    }

# === Load Selected AI Model ===
MODEL_PATH = f"./ai_server/models/{ai_settings['selected_model']}"
print(f"🚀 Loading model: {MODEL_PATH} ...")
pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16
).to("cuda")
print("✅ Model loaded successfully!")

# === MQTT Configuration ===
CONFIG_PATH = "config/setting.json"

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"❌ Config file not found: {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

mqtt_config = config.get("mqtt", {})
BROKER_URL = mqtt_config.get("broker_url", "")
PORT = mqtt_config.get("port", 1883)
USERNAME = mqtt_config.get("username", "")
PASSWORD = mqtt_config.get("password", "")
TOPIC = mqtt_config.get("topic2", "")


# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud successfully!")
    else:
        print(f"❌ Failed to connect to HiveMQ Cloud, return code: {rc}")

# Initialize MQTT Client
client = mqtt.Client()
client.tls_set()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.connect(BROKER_URL, PORT, 50)
client.loop_start()

app = FastAPI()

def scale_value(value, old_min, old_max, new_min, new_max):
    """Maps value from [old_min, old_max] to [new_min, new_max]."""
    return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)

def publish_image_to_mqtt(image_path):
    """Publishes generated image to MQTT."""
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "image_data": base64_image,
            "description": "Generated image from Stable Diffusion"
        }

        result = client.publish(TOPIC, json.dumps(payload))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ Successfully published image to MQTT!")
        else:
            print(f"❌ MQTT publish failed with return code: {result.rc}")
    except Exception as e:
        print(f"❌ Failed to publish image to MQTT: {e}")

@app.post("/process_image")
async def process_image(data: dict):
    """
    Processes an input image using Stable Diffusion based on user text and environmental conditions.
    """

    try:
        # === Extract Input Data ===
        image_data = data.get("image_data")
        user_text = data.get("text", "Default prompt")

        raw_temperature = data.get("temperature", "Temperature: 25°C").strip()
        raw_humidity = data.get("humidity", "Humidity: 50%").strip()

        try:
            temperature_value = float(raw_temperature.split("Temperature:")[1].split("°")[0].strip())
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail=f"Invalid temperature format: {raw_temperature}")

        try:
            humidity_value = float(raw_humidity.split("Humidity:")[1].split("%")[0].strip())
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail=f"Invalid humidity format: {raw_humidity}")

        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided.")

        # === Save Input Image ===
        image_bytes = base64.b64decode(image_data)
        input_image_path = f"./temp/temp_input_{uuid.uuid4().hex}.jpg"
        os.makedirs("./temp", exist_ok=True)
        with open(input_image_path, "wb") as f:
            f.write(image_bytes)

        # === Load Input Image ===
        init_image = Image.open(input_image_path).convert("RGB").resize((1280, 720))

        # === Apply Selected AI Processing Approach ===
        selected_approach = ai_settings["selected_approach"]

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # APPROACH 1: Modify Prompt
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if selected_approach == "Modify Prompt":
            if temperature_value > 30:
                user_text += ", extremely hot day"
            elif temperature_value < 15:
                user_text += ", cold and frosty day"

            if humidity_value > 70:
                user_text += ", humid, misty atmosphere"
            elif humidity_value < 30:
                user_text += ", very dry air"

            strength = 0.75
            guidance_scale = 7.5
            generator = None  # No custom seed

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # APPROACH 2: Adjust Random Seed
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif selected_approach == "Adjust Random Seed":
            import random
            combined = f"{temperature_value:.1f}_{humidity_value:.1f}"
            seed_val = hash(combined) % (2**32)
            print(f"Using custom seed based on env data: {seed_val}")
            generator = torch.Generator(device="cuda").manual_seed(seed_val)

            strength = 0.75
            guidance_scale = 7.5

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # APPROACH 3: Map humidity -> strength, temperature -> guidance_scale
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif selected_approach == "Map Humidity & Temperature":
            strength = scale_value(humidity_value, 10, 90, 0.3, 0.9)
            strength = max(0.3, min(strength, 0.9))

            guidance_scale = scale_value(temperature_value, 15, 35, 5.0, 12.0)
            guidance_scale = max(5.0, min(guidance_scale, 12.0))

            generator = None

        else:
            raise HTTPException(status_code=400, detail=f"Invalid approach: {selected_approach}")

        # === Generate Image with Stable Diffusion ===
        print(f"🚀 Generating Image using {selected_approach} approach...")
        result = pipeline(
            prompt=user_text,
            image=init_image,
            strength=strength,
            guidance_scale=guidance_scale,
            generator=generator
        )

        # === Save Output Image ===
        output_image_path = f"./outputs/{uuid.uuid4().hex}_output.png"
        os.makedirs("./outputs", exist_ok=True)
        result.images[0].save(output_image_path)

        # === Publish to MQTT ===
        publish_image_to_mqtt(output_image_path)

        return {
            "status": "Processing Completed",
            "output_image_path": output_image_path,
            "user_text": user_text,
            "strength": strength,
            "guidance_scale": guidance_scale
        }

    except Exception as e:
        print(f"❌ Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"🟢 AI Server running with Model: {ai_settings['selected_model']} | Approach: {ai_settings['selected_approach']}")
    uvicorn.run(app, host="0.0.0.0", port=5000)
