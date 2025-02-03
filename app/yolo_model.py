import torch
import cv2
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

    def detect_from_camera(self, target_object):
        """
        Continuously captures frames from the camera, detects objects, 
        and returns True if the target_object is found.

        Args:
            target_object (str): The object to detect.

        Returns:
            bool: True if the object is detected, False otherwise.
        """
        cap = cv2.VideoCapture(0)  # Open camera (use 0 for default camera)
        if not cap.isOpened():
            print("❌ Error: Cannot open camera")
            return False

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to capture frame")
                    continue

                # Convert frame to image file for YOLO detection
                temp_image_path = "temp_frame.jpg"
                cv2.imwrite(temp_image_path, frame)

                detected_classes = self.detect_objects(temp_image_path)
                if target_object in detected_classes:
                    print(f"🎯 Target object '{target_object}' detected!")
                    return True  # Stop detection when object is found

        except KeyboardInterrupt:
            print("🛑 Stopping camera detection...")
        finally:
            cap.release()

        return False

# ✅ Example Usage (for Testing)
if __name__ == "__main__":
    yolo = YOLO()
    
    # Test 1: Detect objects from an image
    test_image = "test.jpg"  # Replace with a valid image path
    objects = yolo.detect_objects(test_image)
    print("🖼️ Detected Objects:", objects)

    # Test 2: Real-time object detection from camera
    detected = yolo.detect_from_camera("person")  # Replace "person" with any target class
    print(f"📸 Object Detected: {detected}")
