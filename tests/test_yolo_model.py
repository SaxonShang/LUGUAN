import pytest
from app.yolo_model import YOLO
import cv2
import numpy as np

def test_yolo_model_initialization():
    yolo = YOLO()
    assert yolo.model is not None, "YOLO模型加载失败"

def test_yolo_face_detection():
    yolo = YOLO()
    # 创建模拟输入（黑色空白图像）
    fake_frame = np.zeros((640, 480, 3), dtype=np.uint8)
    detections = yolo.detect_faces(fake_frame)
    assert isinstance(detections, list), "输出结果不是列表"
