import pytest
from app.mqtt_client import connect_mqtt, client

def test_mqtt_connection():
    # 测试是否能成功连接MQTT Broker
    try:
        connect_mqtt(broker="test.mosquitto.org", port=1883)
        assert client.is_connected(), "MQTT未成功连接"
    except Exception as e:
        pytest.fail(f"MQTT连接失败: {e}")
