import torch
from pathlib import Path

class YOLO:
    def __init__(self, model_path="models/yolov5s.pt"):
        """
        Initializes YOLOv5 model.

        Args:
            model_path (str): Path to the YOLOv5 model (.pt file).
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"  # ✅ Auto-select GPU or CPU
        self.model = self.load_model(model_path)

    def load_model(self, model_path):
        """Loads the YOLOv5 model from a given path."""
        if not Path(model_path).exists():
            raise FileNotFoundError(f"❌ Model file not found: {model_path}")

        try:
            model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path, force_reload=False)
            model.to(self.device)  # ✅ Send model to the appropriate device (GPU/CPU)
            print(f"✅ YOLO Model Loaded: {model_path} (Running on {self.device})")
            return model
        except Exception as e:
            raise RuntimeError(f"❌ Error loading YOLO model: {e}")

    def detect_objects(self, image_path):
        """
        Runs object detection on an image and returns detected classes.

        Args:
            image_path (str): Path to the image file.

        Returns:
            List[str]: List of detected object class names.
        """
        if not Path(image_path).exists():
            print(f"❌ Error: Image not found at {image_path}")
            return []

        try:
            results = self.model(image_path)
            detected_classes = results.pandas().xyxy[0]["name"].tolist()
            print(f"✅ Detected objects: {detected_classes}")
            return detected_classes
        except Exception as e:
            print(f"❌ YOLO detection failed: {e}")
            return []

# ✅ Example Usage (for Testing)
if __name__ == "__main__":
    yolo = YOLO()
    test_image = "test.jpg"  # Replace with a valid image path
    objects = yolo.detect_objects(test_image)
    print("🖼️ Detected Objects:", objects)
