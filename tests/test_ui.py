import sys
import os
import cv2
import random
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage

# --- 模拟 Firebase 操作，用于测试 ---
def dummy_firebase_push(data):
    print("Simulated Firebase push:", data)

def dummy_firebase_upload(file_path, selected_object):
    print(f"Simulated upload of {file_path} for object '{selected_object}'")

# --- 自定义视频容器控件 ---
class VideoContainerWidget(QWidget):
    def __init__(self, video_aspect=4/3, parent=None):
        """
        video_aspect：摄像头视频的宽高比（默认 4:3）
        """
        super().__init__(parent)
        self.video_aspect = video_aspect
        # 创建两个子区域，用于显示实时视频和捕获图片
        self.video_label = QLabel("Camera Feed", self)
        self.captured_image_label = QLabel("Captured Image", self)
        self.video_label.setStyleSheet("background-color: black;")
        self.captured_image_label.setStyleSheet("background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.captured_image_label.setAlignment(Qt.AlignCenter)
    
    def resizeEvent(self, event):
        """
        根据当前容器尺寸，计算两个子区域的最佳尺寸，
        保证每个区域满足视频宽高比（video_aspect）且两者大小一致，
        并水平排列（左边实时视频，右边捕获图片）。
        """
        total_width = self.width()
        total_height = self.height()
        # 每个区域的理论可用宽度（将水平空间均分）
        available_width_per = total_width / 2

        # 根据可用宽度计算理想高度：理想高度 = 可用宽度 / video_aspect
        desired_height = available_width_per / self.video_aspect

        # 如果计算出的高度超过容器高度，则以容器高度为准，并调整宽度
        if desired_height > total_height:
            new_height = total_height
            new_width = new_height * self.video_aspect
        else:
            new_width = available_width_per
            new_height = desired_height

        # 在左半部分居中放置实时视频显示区域
        x1 = (available_width_per - new_width) / 2
        y1 = (total_height - new_height) / 2
        self.video_label.setGeometry(int(x1), int(y1), int(new_width), int(new_height))

        # 在右半部分居中放置捕获图片显示区域
        x2 = total_width / 2 + (available_width_per - new_width) / 2
        self.captured_image_label.setGeometry(int(x2), int(y1), int(new_width), int(new_height))
        super().resizeEvent(event)

# --- 主程序 ---
class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Displayer - Test Version")
        self.resize(1200, 800)
        self.video_aspect_set = False  # 标识是否已经获取到视频比例
        self.init_ui()

        # 初始化本地摄像头（默认摄像头）
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Cannot access webcam!")
        
        # 定时器每 30 毫秒刷新一次视频流
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def init_ui(self):
        """初始化整个 UI 布局"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === 顶部区域：左侧控制区 和 右侧信息区（水平布局） ===
        top_row = QHBoxLayout()
        top_row.setContentsMargins(10, 10, 10, 10)

        # 左侧控制区：垂直布局，包含类别选择和三个按钮
        left_controls = QVBoxLayout()
        self.object_select = QComboBox()
        self.object_select.addItems(["Person", "Tie", "Car", "Dog"])
        self.object_select.setFixedHeight(50)  # 增加高度
        left_controls.addWidget(self.object_select)

        # 按钮样式：悬停和按下效果
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5980;
                margin-top: 4px;
            }
        """

        self.detect_button = QPushButton("Detect")
        self.detect_button.setFixedHeight(50)  # 增加高度
        self.detect_button.setStyleSheet(button_style)
        self.detect_button.clicked.connect(self.detect_environment)
        left_controls.addWidget(self.detect_button)

        self.capture_button = QPushButton("Capture")
        self.capture_button.setFixedHeight(50)  # 增加高度
        self.capture_button.setStyleSheet(button_style)
        self.capture_button.clicked.connect(self.capture_image)
        left_controls.addWidget(self.capture_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(50)  # 增加高度
        self.exit_button.setStyleSheet(button_style)
        self.exit_button.clicked.connect(self.close)
        left_controls.addWidget(self.exit_button)

        # 右侧信息区：垂直布局，上部显示温湿度，下部为多行文本输入
        right_info = QVBoxLayout()
        self.env_label = QLabel("Temperature: --°C  |  Humidity: --%")
        self.env_label.setAlignment(Qt.AlignCenter)
        self.env_label.setFixedHeight(50)  # 增加高度
        # 增大字体到 20px
        self.env_label.setStyleSheet("font-size: 20px; font-weight: bold; background-color: rgba(255,255,255,0.7);")
        right_info.addWidget(self.env_label)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setFixedHeight(150)  # 增加高度
        self.text_input.setStyleSheet("background-color: rgba(255,255,255,0.7);")
        right_info.addWidget(self.text_input)

        top_row.addLayout(left_controls)
        top_row.addLayout(right_info)
        # 顶部区域固定高度，伸缩因子设为 0
        main_layout.addLayout(top_row, 0)

        # === 底部区域：视频容器（实时视频和捕获图片显示区域），始终保持相同尺寸并按摄像头比例显示 ===
        self.video_container = VideoContainerWidget(video_aspect=4/3)
        self.video_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.video_container, 1)

        self.setLayout(main_layout)

    def update_frame(self):
        """读取摄像头画面，并更新实时视频显示区域"""
        ret, frame = self.cap.read()
        if ret:
            # 首次获取帧时，记录摄像头视频的实际宽高比例，并更新容器
            if not self.video_aspect_set:
                h, w = frame.shape[:2]
                self.video_aspect = w / h
                self.video_container.video_aspect = self.video_aspect
                self.video_container.update()
                self.video_aspect_set = True

            # 转换颜色格式并生成 QImage
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            # 将图像缩放到实时视频显示区域大小（保持宽高比）
            target_size = self.video_container.video_label.size()
            pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_container.video_label.setPixmap(pixmap)
        else:
            print("Error: Unable to read frame from webcam.")

    def detect_environment(self):
        """模拟环境数据检测，更新温湿度显示以及模拟推送数据"""
        temperature = round(random.uniform(20.0, 30.0), 1)
        humidity = round(random.uniform(40.0, 70.0), 1)
        self.env_label.setText(f"Temperature: {temperature}°C  |  Humidity: {humidity}%")
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": "2025-02-03 12:00:00",
            "user_message": self.text_input.toPlainText()
        }
        dummy_firebase_push(data)

    def capture_image(self):
        """捕获当前摄像头画面，显示在捕获图片区域，并模拟上传操作"""
        ret, frame = self.cap.read()
        if ret:
            selected_object = self.object_select.currentText().lower()
            image_path = f"{selected_object}.jpg"
            cv2.imwrite(image_path, frame)

            pixmap = QPixmap(image_path)
            # 将捕获图像缩放到捕获图片显示区域大小（保持宽高比）
            target_size = self.video_container.captured_image_label.size()
            pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_container.captured_image_label.setPixmap(pixmap)

            dummy_firebase_upload(image_path, selected_object)
            os.remove(image_path)
            self.object_select.setCurrentIndex(0)
        else:
            print("Error: Unable to capture image from webcam.")

    def closeEvent(self, event):
        """退出程序时释放摄像头资源"""
        if self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
