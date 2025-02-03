import sys
import time
import json
import firebase_admin
from firebase_admin import credentials, db
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QListWidget

# 连接 Firebase
cred = credentials.Certificate("luguan-8c32d-firebase-adminsdk-fbsvc-6ca84ce42e.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://luguan-8c32d-default-rtdb.europe-west1.firebasedatabase.app/"
})

# 访问 Firebase 数据库
firebase_ref = db.reference("sensor_data")  # 数据存储路径

class SmartArtDisplayer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # 存储历史数据
        self.temp_history = []

        # **加载 Firebase 数据**
        self.load_firebase_data()

        # 监听 Firebase 数据更新
        self.listen_firebase_updates()

    def initUI(self):
        self.setWindowTitle("Smart Art Displayer")
        self.setGeometry(100, 100, 500, 700)

        layout = QVBoxLayout()

        # 实时数据
        self.temp_label = QLabel("Temperature: Fetching...")
        layout.addWidget(self.temp_label)

        # 历史数据
        self.history_label = QLabel("Temperature & Humidity History:")
        layout.addWidget(self.history_label)
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)

        self.clear_button = QPushButton("Clear History")
        self.clear_button.clicked.connect(self.clear_history)
        layout.addWidget(self.clear_button)

        self.setLayout(layout)

    def load_firebase_data(self):
        """ 从 Firebase 加载历史数据 """
        data = firebase_ref.get()
        if data:
            sorted_data = sorted(data.values(), key=lambda x: x["timestamp"])  # 按时间排序

            # 如果 Firebase 数据不为空，取最新的温度和湿度数据
            if sorted_data:
                latest_entry = sorted_data[-1]
                temperature = latest_entry.get('temperature', 'Unknown temperature')
                humidity = latest_entry.get('humidity', 'Unknown humidity')

                # 更新实时数据显示
                temp_text = f"Temperature: {temperature}°C, Humidity: {humidity}%"
                self.temp_label.setText(temp_text)

            for entry in sorted_data:
                history_entry = f"[{entry['timestamp']}] Temperature: {entry['temperature']}°C, Humidity: {entry['humidity']}%"
                self.temp_history.append(history_entry)

            # 更新 UI
            self.history_list.addItems(self.temp_history)

    def listen_firebase_updates(self):
        """ 监听 Firebase 数据更新 """
        def listener(event):
            if event.data:
                entry = event.data

                # 检查 entry 是否包含 'timestamp'，如果没有则跳过
                timestamp = entry.get('timestamp', 'Unknown time')
                temperature = entry.get('temperature', 'Unknown temperature')
                humidity = entry.get('humidity', 'Unknown humidity')

                # 生成历史记录条目
                history_entry = f"[{timestamp}] Temperature: {temperature}°C, Humidity: {humidity}%"
                self.temp_history.append(history_entry)

                # 只保留最新 10 条记录
                if len(self.temp_history) > 10:
                    self.temp_history.pop(0)

                # 更新 UI
                self.history_list.clear()
                self.history_list.addItems(self.temp_history)

        firebase_ref.listen(listener)

    def clear_history(self):
        """ 清除历史记录 """
        self.temp_history.clear()
        self.history_list.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartArtDisplayer()
    window.show()
    sys.exit(app.exec_())
