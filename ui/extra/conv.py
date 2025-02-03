import base64
from pathlib import Path

def save_as_base64(image_path, output_path):
    """将图片转换为 Base64 并保存为文本文件"""
    with open(image_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode("utf-8")
    with open(output_path, "w") as b64_file:
        b64_file.write(base64_data)
    print(f"Base64 文件已保存: {output_path}")

def save_as_binary(image_path, output_path):
    """将图片直接存为二进制文件"""
    with open(image_path, "rb") as img_file:
        binary_data = img_file.read()
    with open(output_path, "wb") as bin_file:
        bin_file.write(binary_data)
    print(f"二进制文件已保存: {output_path}")

def restore_from_base64(base64_path, output_path):
    """从 Base64 文件恢复图片"""
    with open(base64_path, "r") as b64_file:
        base64_data = b64_file.read()
    with open(output_path, "wb") as img_file:
        img_file.write(base64.b64decode(base64_data))
    print(f"图片已恢复: {output_path}")

def restore_from_binary(binary_path, output_path):
    """从二进制文件恢复图片"""
    with open(binary_path, "rb") as bin_file:
        binary_data = bin_file.read()
    with open(output_path, "wb") as img_file:
        img_file.write(binary_data)
    print(f"图片已恢复: {output_path}")

if __name__ == "__main__":
    # ✅ 修正路径，使用 pathlib 以避免 Windows 转义问题
    image_path = Path(r"C:\Users\Admin\Desktop\Weixin Image_20250127150846.jpg")
    
    base64_file = image_path.with_suffix(".b64")  # 生成 Base64 文件路径
    binary_file = image_path.with_suffix(".bin")  # 生成二进制文件路径
    restored_image_from_b64 = image_path.with_name("restored_from_b64.jpg")
    restored_image_from_bin = image_path.with_name("restored_from_bin.jpg")

    # 1️⃣ 图片转换为 Base64 和二进制
    save_as_base64(image_path, base64_file)
    save_as_binary(image_path, binary_file)

    # 2️⃣ 从 Base64 和二进制文件恢复原图
    restore_from_base64(base64_file, restored_image_from_b64)
    restore_from_binary(binary_file, restored_image_from_bin)
