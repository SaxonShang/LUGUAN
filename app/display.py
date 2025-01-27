from PIL import Image
import some_display_library  # 替换为实际使用的LED屏库

def display_image(image_path):
    img = Image.open(image_path)
    some_display_library.display(img)
    print(f"展示图片: {image_path}")
