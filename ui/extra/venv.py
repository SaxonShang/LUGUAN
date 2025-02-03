# 1. 安装 Python venv（如果未安装）
sudo apt install python3-venv -y

# 2. 创建一个新的虚拟环境
python3 -m venv my_env

# 3. 激活虚拟环境
source my_env/bin/activate

# 4. 在虚拟环境中安装依赖
pip install firebase-admin smbus2 paho-mqtt

# 5. 运行你的 Python 代码
python main.py

deactivate
