import unittest
from app.camera import Camera
import os

class TestCamera(unittest.TestCase):
    def setUp(self):
        self.camera = Camera()
        self.image_path = "tests/test_image.jpg"

    def test_capture_image(self):
        result = self.camera.capture_image(self.image_path)
        self.assertTrue(os.path.exists(self.image_path))

    def tearDown(self):
        if os.path.exists(self.image_path):
            os.remove(self.image_path)

if __name__ == "__main__":
    unittest.main()
