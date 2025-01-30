import cv2

class Camera:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)  # Use Raspberry Pi Camera

    def capture_image(self, save_path):
        """Captures an image and saves it to the specified path."""
        ret, frame = self.camera.read()
        if ret:
            cv2.imwrite(save_path, frame)
            print(f"✅ Image saved: {save_path}")
            return save_path
        else:
            print("❌ Failed to capture image")
            return None

    def release(self):
        """Releases the camera."""
        self.camera.release()
