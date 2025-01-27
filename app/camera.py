import cv2
from yolo_model import YOLO

def capture_and_detect(output_path="captured.jpg"):
    camera = cv2.VideoCapture(0)  # 默认摄像头
    yolo = YOLO()
    ret, frame = camera.read()
    if not ret:
        print("无法读取摄像头画面")
        return None
    
    # 检测人脸
    detections = yolo.detect_faces(frame)
    if detections:
        cv2.imwrite(output_path, frame)
        print(f"照片保存到: {output_path}")
        return output_path
    return None
