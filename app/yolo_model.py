import torch
import cv2
import numpy as np

class YOLO:
    def __init__(self, model_path="models/yolov5s.pt"):
        self.model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path)

    def detect_objects(self, frame):
        """Detect objects in a frame and return class labels."""
        results = self.model(frame)
        detections = []
        for *box, conf, cls in results.xyxy[0]:
            detections.append(self.model.names[int(cls)])
        return detections
