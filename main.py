import json
import time
import paho.mqtt.client as mqtt
from app.camera import Camera
from app.firebase_client import upload_to_firebase
from app.yolo_model import YOLO
from app.temp_sensor import get_temperature, get_humidity

# 读取 MQTT 配置
with open("config/mqtt_config.json", "r") as file:
    mqtt_config = json.load(file)

MQTT_BROKER = mqtt_config["broker"]
MQTT_PORT = mqtt_config["port"]
CAPTURE_TOPIC = "ui/capture_command"
RESULT_TOPIC = "ui/captured_image"

# 初始化对象
camera = Camera()
yolo = YOLO()

# 全局变量，存储当前目标物体
target_object = None

def on_message(client, userdata, message):
    """收到 MQTT 消息后，更新目标物体"""
    global target_object
    data = json.loads(message.payload.decode())
    target_object = data.get("selected_object")
    print(f"📡 收到 UI 选择的目标物体: {target_object}")

# 连接 MQTT 服务器
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(CAPTURE_TOPIC)
client.loop_start()

def main():
    global target_object
    print("🚀 Raspberry Pi 目标检测启动...")

    while True:
        if target_object:  # 仅当用户选择了目标物体时检测
            detected = yolo.detect_from_camera(target_object)
            if detected:
                print(f"✅ 检测到目标物体 {target_object}，拍照并上传...")
                
                # 拍照并上传 Firebase
                image_path = "captured_image.jpg"
                camera.capture_image(image_path)
                image_url = upload_to_firebase(image_path, target_object)

                # 获取温湿度
                metadata = {
                    "temperature": get_temperature(),
                    "humidity": get_humidity(),
                    "object": target_object,
                    "image_url": image_url
                }

                # 发送 MQTT 消息给 UI
                client.publish(RESULT_TOPIC, json.dumps(metadata))
                print(f"📡 发送照片 URL 到 UI: {image_url}")

                # 清空目标物体，等待用户新选择
                target_object = None

            time.sleep(2)  # 避免频繁拍照

if __name__ == "__main__":
    main()
