from app.camera import capture_and_detect
from app.display import display_image
from app.temp_sensor import get_temperature
from app.firebase_client import upload_to_firebase
from app.process_image import process_image
from ui.app_ui import app
import time
import threading

# 配置参数
PHOTO_INTERVAL = 10  # 拍照间隔时间（秒）
LOCAL_PHOTO_PATH = "photos/captured.jpg"
PROCESSED_PHOTO_PATH = "photos/processed.jpg"
CLOUD_PATH = "photos/captured.jpg"

def camera_thread():
    while True:
        # 捕获并检测人脸
        print("捕获图像...")
        photo_path = capture_and_detect(LOCAL_PHOTO_PATH)
        if photo_path:
            print("人脸检测成功，照片已保存")
            # 上传照片到 Firebase
            cloud_url = upload_to_firebase(photo_path, CLOUD_PATH)
            print(f"照片已上传到云端: {cloud_url}")
            # 获取温度和处理图像
            temperature = get_temperature()
            processed_url = process_image(cloud_url, style="impressionism", temperature=temperature)
            print(f"AI 处理完成: {processed_url}")
            # 显示生成的艺术作品
            display_image(processed_url)
        time.sleep(PHOTO_INTERVAL)

def start_ui():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    print("启动智能墨镜项目...")
    # 启动摄像头线程
    camera_thread = threading.Thread(target=camera_thread)
    camera_thread.start()

    # 启动 Flask UI
    start_ui()
