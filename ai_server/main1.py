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

# 指定 Stable Diffusion 模型路径
pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
    "./stable_diffusion_2_1_img2img_model",  # 替换为你的模型路径
    torch_dtype=torch.float16
).to("cuda")  # 如果设备支持 GPU

# 映射函数
def scale_value(value, old_min, old_max, new_min, new_max):
    """将值从一个范围映射到另一个范围"""
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
    """
    try:
        # 从请求中提取数据
        image_data = data.get("image_data")
        user_text = data.get("text", "Default prompt")

        # 解析并清理温度和湿度
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

        # 映射湿度到 strength (范围 0.3 - 0.9)
        strength = scale_value(humidity_value, 10, 90, 0.3, 0.9)
        strength = max(0.3, min(strength, 0.9))

        # 映射温度到 guidance_scale (范围 5.0 - 12.0)
        guidance_scale = scale_value(temperature_value, 15, 35, 5.0, 12.0)
        guidance_scale = max(5.0, min(guidance_scale, 12.0))

        # Base64 解码图片
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided.")
        image_bytes = base64.b64decode(image_data)
        input_image_path = f"./temp/temp_input_{uuid.uuid4().hex}.jpg"
        os.makedirs("./temp", exist_ok=True)
        with open(input_image_path, "wb") as f:
            f.write(image_bytes)

        # 加载图片并调整大小
        input_image = Image.open(input_image_path).convert("RGB").resize((512, 512))

        # 使用 Stable Diffusion 处理图片
        print("🚀 开始使用 Stable Diffusion 处理图片...")
        result = pipeline(
            prompt=user_text,
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale
        )

        # 保存生成的图片
        output_image_path = f"./outputs/{uuid.uuid4().hex}_output.png"
        os.makedirs("./outputs", exist_ok=True)
        result.images[0].save(output_image_path)

        # 发布图片到 MQTT
        publish_image_to_mqtt(output_image_path)

        # 返回处理结果
        return {
            "status": "Processing Completed",
            "output_image_path": output_image_path,
            "strength": strength,
            "guidance_scale": guidance_scale
        }

    except Exception as e:
        print(f"❌ 处理图片时发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
