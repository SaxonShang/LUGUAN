import unittest
from app.yolo_model import YOLO

class TestYOLOModel(unittest.TestCase):
    def setUp(self):
        self.yolo = YOLO()

    def test_detection(self):
        result = self.yolo.detect_objects("tests/sample_image.jpg")
        self.assertTrue(len(result) > 0)

if __name__ == "__main__":
    unittest.main()
