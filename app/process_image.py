import requests

def process_image(image_url, style, temperature):
    payload = {"image_url": image_url, "style": style, "temperature": temperature}
    response = requests.post("https://ai-art-api.com/process", json=payload)
    processed_image_url = response.json().get("processed_image_url")
    print(f"AI处理后的图片地址: {processed_image_url}")
    return processed_image_url
