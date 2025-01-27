import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"MQTT连接状态: {rc}")

def on_message(client, userdata, msg):
    print(f"收到消息: {msg.topic} -> {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

def connect_mqtt(broker, port):
    client.connect(broker, port, 60)
    client.loop_start()
