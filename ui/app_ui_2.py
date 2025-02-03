import sys
import os
import json
import cv2
import requests
import firebase_admin
from firebase_admin import credentials, storage, db
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QGroupBox, QFormLayout, QComboBox
)
from PyQt5.QtGui import QPixmap, QImage

# MJPEG Streamer URL (树莓派摄像头流)
RASPBERRY_PI_IP = "192.168.1.100"  # 请修改为你的树莓派IP
MJPEG_STREAM_URL = f"http://{RASPBERRY_PI_IP}:8080/?action=stream"

# Firebase 配置
cred = credentials.Certificate("config/firebase_config.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://your-firebase-database.firebaseio.com/",
    "storageBucket": "your-bucket-name.appspot.com"
})
bucket = storage.bucket()
firebase_ref = db.reference("sensor_data")

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Detection & Capture")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        """初始化 UI 界面"""
        main_layout = QVBoxLayout()

        # 按钮 & 物体选择框
        control_layout = QHBoxLayout()

        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])  # 选择检测物体
        control_layout.addWidget(self.object_select)

        self.detect_button = QPushButton("Detect")
        self.detect_button.clicked.connect(self.detect_environment)
        control_layout.addWidget(self.detect_button)

        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(self.capture_image)
        control_layout.addWidget(self.capture_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        control_layout.addWidget(self.exit_button)

        main_layout.addLayout(control_layout)

        # 文本输入框（支持换行）
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(80)
        main_layout.addWidget(self.text_input)

        # 温湿度显示
        self.env_label = QLabel("Temperature: --°C  |  Humidity: --%")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(self.env_label)

        # 视频流 & 拍摄图片
        video_capture_layout = QHBoxLayout()

        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(640, 480)
        video_capture_layout.addWidget(self.video_label)

        self.captured_image_label = QLabel("Captured Image")
        self.captured_image_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setFixedSize(640, 480)
        video_capture_layout.addWidget(self.captured_image_label)

        main_layout.addLayout(video_capture_layout)
        self.setLayout(main_layout)

        # 加载实时视频流
        self.load_camera_stream()

    def load_camera_stream(self):
        """加载 Raspberry Pi 的 MJPEG Streamer 视频流"""
        pixmap = QPixmap()
        pixmap.loadFromData(requests.get(MJPEG_STREAM_URL, stream=True).content)
        self.video_label.setPixmap(pixmap)

    def detect_environment(self):
        """检测环境温湿度，并上传至 Firebase"""
        temperature = 25.0  # 模拟数据
        humidity = 60.0
        self.env_label.setText(f"Temperature: {temperature}°C  |  Humidity: {humidity}%")

        data = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": "2025-02-03 12:00:00"
        }
        firebase_ref.push(data)

    def capture_image(self):
        """拍摄照片，展示到 UI 并上传 Firebase"""
        selected_object = self.object_select.currentText().lower()
        image_path = f"{selected_object}.jpg"

        # 获取摄像头流并保存
        response = requests.get(MJPEG_STREAM_URL, stream=True)
        with open(image_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        # 显示拍摄图片
        pixmap = QPixmap(image_path)
        self.captured_image_label.setPixmap(pixmap)

        # 上传到 Firebase Storage
        blob = bucket.blob(f"captured_images/{selected_object}.jpg")
        blob.upload_from_filename(image_path)
        os.remove(image_path)

        # 清空类别选择
        self.object_select.setCurrentIndex(0)

    def closeEvent(self, event):
        """退出程序"""
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
