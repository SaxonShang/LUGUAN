import torch
from pathlib import Path

class YOLO:
    def __init__(self, model_path="models/yolov5s.pt"):
        self.model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path)

    def detect_objects(self, image_path):
        """Runs object detection on an image and returns detected classes."""
        results = self.model(image_path)
        detected_classes = results.pandas().xyxy[0]["name"].tolist()
        print(f"✅ Detected objects: {detected_classes}")
        return detected_classes
