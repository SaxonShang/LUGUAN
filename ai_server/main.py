from fastapi import FastAPI, HTTPException
import os
import base64
import uuid
from PIL import Image
import torch
from diffusers import StableDiffusionImg2ImgPipeline
import paho.mqtt.client as mqtt
import json

# MQTT 配置
BROKER_URL = "45daeea25355436589e73eca1801653e.s1.eu.hivemq.cloud"
PORT = 8883  # Secure MQTT over TLS
USERNAME = "Saxon"  # Your HiveMQ Cloud username
PASSWORD = "030401@Szh"  # Your HiveMQ Cloud password
MQTT_TOPIC = "IC.embedded/LUGUAN/picture"

# MQTT 回调函数
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud successfully!")
    else:
        print(f"❌ Failed to connect to HiveMQ Cloud, return code: {rc}")

# 初始化 MQTT 客户端
client = mqtt.Client()
client.tls_set()  # 使用默认 CA 证书
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.connect(BROKER_URL, PORT, 50)
client.loop_start()

# 初始化 FastAPI
app = FastAPI()

# 加载 Stable Diffusion Img2ImgPipeline
pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
    #"./ai_server/models/sd_v1_5",  # 替换为你的模型路径
    #"./ai_server/models/sd_2_1",
    #"./ai_server/models/dreamlike_photoreal_2",
    "./ai_server/models/openjourney_local",
    torch_dtype=torch.float16
).to("cuda")

# 用于将值从一个范围映射到另一个范围
def scale_value(value, old_min, old_max, new_min, new_max):
    """将 value 从 [old_min, old_max] 映射到 [new_min, new_max]."""
    return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)

# 发布图片到 MQTT
def publish_image_to_mqtt(image_path):
    try:
        # 将图片读取为 Base64 编码
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # 构建消息 payload
        payload = {
            "image_data": base64_image,
            "description": "Generated image from Stable Diffusion"
        }

        # 发布消息到 MQTT
        result = client.publish(MQTT_TOPIC, json.dumps(payload))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ Successfully published image to MQTT!")
        else:
            print(f"❌ MQTT publish failed with return code: {result.rc}")
    except Exception as e:
        print(f"❌ Failed to publish image to MQTT: {e}")

@app.post("/process_image")
async def process_image(data: dict):
    """
    接收 UI 发送的数据，包括图片的 Base64 编码、描述文本、温湿度信息，
    并处理图片后返回生成的结果，同时将生成的图片发送到 MQTT。

    -- Three Approaches to Incorporate Temperature & Humidity --

    1) Modify Prompt (text-based)
    2) Adjust Random Seed (seed-based)
    3) Map humidity -> strength, temperature -> guidance_scale (original method)

    Uncomment exactly ONE block to pick your approach. 
    Each block defines all needed variables (user_text, strength, guidance_scale, generator) 
    so the pipeline call can work directly.
    """

    try:
        # === Extract data from the request ===
        image_data = data.get("image_data")
        user_text = data.get("text", "Default prompt")

        # Parse temperature/humidity from "Temperature: 25°C", "Humidity: 50%"
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

        # === Save input image to disk ===
        image_bytes = base64.b64decode(image_data)
        input_image_path = f"./temp/temp_input_{uuid.uuid4().hex}.jpg"
        os.makedirs("./temp", exist_ok=True)
        with open(input_image_path, "wb") as f:
            f.write(image_bytes)

        # === Load the input image ===
        init_image = Image.open(input_image_path).convert("RGB").resize((1280, 720))

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # APPROACH 1: Modify Prompt
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """
        # 1. Incorporate temperature/humidity as descriptive text
        # 2. Use default or example strength/guidance
        if temperature_value > 30:
            user_text += ", extremely hot day"
        elif temperature_value < 15:
            user_text += ", cold and frosty day"

        if humidity_value > 70:
            user_text += ", humid, misty atmosphere"
        elif humidity_value < 30:
            user_text += ", very dry air"

        # For text2img-like control, let's just keep strength/guidance basic
        strength = 0.75
        guidance_scale = 7.5
        generator = None  # no custom seed
        """

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # APPROACH 2: Adjust Random Seed
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """
        # 1. Keep user_text as is or lightly appended
        # 2. Derive a custom random seed from temperature/humidity
        import random
        combined = f"{temperature_value:.1f}_{humidity_value:.1f}"
        seed_val = hash(combined) % (2**32)
        print(f"Using custom seed based on env data: {seed_val}")
        generator = torch.Generator(device="cuda").manual_seed(seed_val)

        # We'll just keep strength/guidance as defaults
        strength = 0.75
        guidance_scale = 7.5
        """

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # APPROACH 3: Map humidity -> strength, temperature -> guidance_scale
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        strength = scale_value(humidity_value, 10, 90, 0.3, 0.9)
        strength = max(0.3, min(strength, 0.9))

        guidance_scale = scale_value(temperature_value, 15, 35, 5.0, 12.0)
        guidance_scale = max(5.0, min(guidance_scale, 12.0))

        generator = None
        

        # === If none are uncommented, we define some fallback. 
        # But ideally, you only uncomment exactly ONE approach above:
        #strength = 0.75
        #guidance_scale = 7.5
        #generator = None

        print("🚀  Stable Diffusion ...")
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

        # Return info about the generation
        return {
            "status": "Processing Completed",
            "output_image_path": output_image_path,
            "user_text": user_text,
            "strength": strength,
            "guidance_scale": guidance_scale
        }

    except Exception as e:
        print(f"❌ error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
