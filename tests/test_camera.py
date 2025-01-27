import pytest
from app.camera import capture_and_detect

def test_capture_and_detect():
    # 测试是否能正确保存图片
    result = capture_and_detect(output_path="test_image.jpg")
    assert result is not None, "摄像头未捕获到图像"
