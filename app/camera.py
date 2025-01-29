import cv2
from picamera2 import Picamera2

class Camera:
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.start()

    def capture_frame(self):
        """Capture a frame from the camera."""
        return self.picam2.capture_array()

    def capture_image(self, path="captured.jpg"):
        """Capture and save an image."""
        self.picam2.capture_file(path)
