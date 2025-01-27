import torch

class YOLO:
    def __init__(self, model_path="yolov5n.pt"):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
    
    def detect_faces(self, frame):
        results = self.model(frame)
        detections = []
        for *box, conf, cls in results.xyxy[0]:
            if int(cls) == 0:  # 0代表'person'
                x1, y1, x2, y2 = map(int, box)
                detections.append((x1, y1, x2 - x1, y2 - y1))
        return detections
