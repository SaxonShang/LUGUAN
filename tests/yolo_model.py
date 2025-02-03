import torch
import cv2
import numpy as np
from pathlib import Path

class YOLO:
    def __init__(self, model_path="models/yolov5s.pt"):
        """
        Initializes YOLOv5 model.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"  # ✅ Auto-select GPU or CPU
        self.model = self.load_model(model_path)

    def load_model(self, model_path):
        """Loads the YOLOv5 model from a given path."""
        if not Path(model_path).exists():
            print(f"⚠️ Custom model not found. Loading default YOLOv5s model...")
            model_path = "yolov5s.pt"  # Download from Ultralytics if not found

        try:
            model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path, force_reload=False)
            model.to(self.device)  # ✅ Send model to the appropriate device (GPU/CPU)
            print(f"✅ YOLO Model Loaded: {model_path} (Running on {self.device})")
            return model
        except Exception as e:
            raise RuntimeError(f"❌ Error loading YOLO model: {e}")

    def detect_objects(self, image_path):
        """
        Runs object detection on an image and returns detected objects with bounding box coordinates.

        Returns:
            List[dict]: Detected objects with bounding boxes.
        """
        if not Path(image_path).exists():
            print(f"❌ Error: Image not found at {image_path}")
            return []

        try:
            results = self.model(image_path)
            detections = results.pandas().xyxy[0]  # Convert to Pandas DataFrame
            detected_objects = []

            for _, row in detections.iterrows():
                detected_objects.append({
                    "name": row["name"],
                    "xmin": int(row["xmin"]),
                    "ymin": int(row["ymin"]),
                    "xmax": int(row["xmax"]),
                    "ymax": int(row["ymax"]),
                    "confidence": float(row["confidence"])
                })

            print(f"✅ Detected objects: {detected_objects}")
            return detected_objects  # Return list of dictionaries

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
        cap = cv2.VideoCapture(0)  # Open laptop camera
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

                detected_objects = self.detect_objects(temp_image_path)
                for obj in detected_objects:
                    if obj["name"] == target_object:
                        print(f"🎯 Target object '{target_object}' detected!")
                        cap.release()
                        return True  # Stop detection when object is found

        except KeyboardInterrupt:
            print("🛑 Stopping camera detection...")
        finally:
            cap.release()

        return False

    def detect_objects_in_frame(self, frame, target_object=None):
        """
        Detect objects in a given frame and return bounding box details.

        Args:
            frame (numpy.ndarray): The frame/image for detection.
            target_object (str, optional): If specified, only show bounding boxes for this object.

        Returns:
            numpy.ndarray: The frame with bounding boxes drawn (if applicable).
        """
        temp_image_path = "temp_frame.jpg"
        cv2.imwrite(temp_image_path, frame)
        detections = self.detect_objects(temp_image_path)

        if isinstance(detections, list):
            for obj in detections:
                if target_object is None or obj["name"] == target_object:
                    x1, y1, x2, y2 = obj["xmin"], obj["ymin"], obj["xmax"], obj["ymax"]
                    confidence = obj["confidence"]

                    # Draw bounding box on the frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{obj['name']} {confidence:.2f}",
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame  # Return frame with bounding box

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
