import cv2
import time

class Camera:
    def __init__(self, camera_index=0):
        """Initialize the camera."""
        self.camera = cv2.VideoCapture(camera_index)

        if not self.camera.isOpened():
            raise Exception("❌ Camera initialization failed. Check connection.")

        # ✅ Ensure camera is ready
        time.sleep(2)  # Allow camera to warm up

    def capture_image(self, save_path):
        """Captures an image and saves it to the specified path."""
        for _ in range(3):  # Try 3 times if the first attempt fails
            ret, frame = self.camera.read()
            if ret:
                cv2.imwrite(save_path, frame)
                print(f"✅ Image saved: {save_path}")
                return save_path
            print("⚠️ Retrying camera capture...")
            time.sleep(1)

        print("❌ Failed to capture image")
        return None

    def release(self):
        """Releases the camera."""
        self.camera.release()
        cv2.destroyAllWindows()
        print("📷 Camera released.")

# ✅ Example Usage (For testing)
if __name__ == "__main__":
    cam = Camera()
    cam.capture_image("test_image.jpg")
    cam.release()

