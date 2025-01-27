import os

def save_style(style):
    with open("style.txt", "w") as f:
        f.write(style)

def clear_database():
    for file in os.listdir("photos/"):
        os.remove(f"photos/{file}")
    print("数据库已清理")
