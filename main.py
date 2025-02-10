import time
import smbus2
import paho.mqtt.client as mqtt
import json
import firebase_admin
from firebase_admin import credentials, db
import os
import base64
import subprocess
import threading


bus = smbus2.SMBus(1)
# 启动 MJPG-Streamer
def start_mjpg_streamer():
    try:
        subprocess.Popen([
            "mjpg_streamer",
            "-i", "/usr/local/lib/mjpg-streamer/input_uvc.so -d /dev/video0 -r 640x480 -f 30",
            "-o", "/usr/local/lib/mjpg-streamer/output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"
        ])
        print("MJPG-Streamer 已启动")
    except Exception as e:
        print(f"启动 MJPG-Streamer 时出错: {e}")

# 初始化 Firebase
cred = credentials.Certificate("luguan-8c32d-firebase-adminsdk-fbsvc-6ca84ce42e.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://luguan-8c32d-default-rtdb.europe-west1.firebasedatabase.app/"
})

# MQTT 代理信息
BROKER_URL = "45daeea25355436589e73eca1801653e.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "Saxon"
PASSWORD = "030401@Szh"
MQTT_TOPIC = "IC.embedded/LUGUAN/test"
MQTT_TOPIC2 = "IC.embedded/LUGUAN/picture"
IMAGE_PATH = "/home/pi/received_image.jpg"

# 处理 MQTT 连接
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to HiveMQ Cloud successfully!")
        client.subscribe(MQTT_TOPIC2)
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

# 处理接收到的 MQTT 消息
def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC2:  # 处理图片
        try:
            data = json.loads(msg.payload.decode())
            image_data = base64.b64decode(data.get('image_data'))
            with open(IMAGE_PATH, "wb") as f:
                f.write(image_data)
            print(f"图片已保存到 {IMAGE_PATH}")
            os.system(f"feh -F {IMAGE_PATH}")  
        except Exception as e:
            print(f"图片处理失败: {e}")
    elif msg.topic == MQTT_TOPIC:  # 处理传感器数据
        print(f"收到传感器数据: {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.tls_set()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_URL, PORT, 60)
client.loop_start()

# 读取温湿度
def read_temperature():
    cmd_meas_temp = smbus2.i2c_msg.write(0x40, [0xF3])
    read_result = smbus2.i2c_msg.read(0x40, 2)
    bus.i2c_rdwr(cmd_meas_temp)
    time.sleep(0.1)
    bus.i2c_rdwr(read_result)
    temperature_raw = int.from_bytes(bytes(read_result), 'big')
    return ((temperature_raw * 175.72) / 65536) - 46.85

def read_humidity():
    cmd_meas_humidity = smbus2.i2c_msg.write(0x40, [0xF5])
    read_result = smbus2.i2c_msg.read(0x40, 2)
    bus.i2c_rdwr(cmd_meas_humidity)
    time.sleep(0.1)
    bus.i2c_rdwr(read_result)
    humidity_raw = int.from_bytes(bytes(read_result), 'big')
    return ((humidity_raw * 125) / 65536) - 6

# 循环读取并上传数据
def read_and_upload_sensor_data():
    while True:
        temp = read_temperature()
        hum = read_humidity()
        payload = {"temperature": round(temp, 2), "humidity": round(hum, 2), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        client.publish(MQTT_TOPIC, json.dumps(payload))
        db.reference("sensor_data").push(payload)
        print(f"已上传: {payload}")
        time.sleep(3)

threading.Thread(target=read_and_upload_sensor_data, daemon=True).start()
start_mjpg_streamer()

while True:
    time.sleep(1)
