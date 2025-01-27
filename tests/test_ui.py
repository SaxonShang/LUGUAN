import pytest
from app.ui.app_ui import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200, "主页无法正常访问"

def test_set_style(client):
    response = client.post("/set_style", data={"style": "impressionism"})
    assert response.status_code == 200, "风格设置失败"
assert "风格已更新".encode("utf-8") in response.data, "未返回正确的响应内容"

