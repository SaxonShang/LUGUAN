import pytest
from app.firebase_client import upload_to_firebase

def test_upload_to_firebase():
    try:
        url = upload_to_firebase(local_path="tests/test_image.jpg", cloud_path="test_image.jpg")
        assert url.startswith("https://"), "返回的URL格式不正确"
    except Exception as e:
        pytest.fail(f"Firebase上传失败: {e}")
