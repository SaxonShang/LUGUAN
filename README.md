# AI Smart Displayer

## Overview
This project is a **smart AI-based detection and capture system** that integrates **YOLO object detection, Firebase for image storage, FastAPI for AI processing, and MQTT for real-time image delivery**. The system is designed to detect objects, capture images, process them using AI, and display the processed images on a Raspberry Pi-connected LED screen.

## Features
- **Object Detection**: Uses YOLOv5 to detect user-selected objects (e.g., person, tie, car, dog) through a camera.
- **Firebase Integration**: Captured images are stored in Firebase Storage for later use.
- **AI Processing via HTTP**: The Raspberry Pi sends metadata to an AI server that retrieves images from Firebase and processes them.
- **MQTT Communication**: AI-processed images are sent back to the Raspberry Pi via MQTT for display.
- **Temperature & Humidity Monitoring**: Real-time sensor data is captured along with the images.
- **User Interface (UI)**: Provides an intuitive UI for object selection, image display, and interaction.

## System Architecture
1. **User selects an object** (e.g., person, tie) and enters optional text.
2. **The camera captures an image** when the selected object is detected.
3. **The image is uploaded to Firebase Storage**.
4. **Metadata (temperature, humidity, user text) is sent via HTTP to the AI server**.
5. **The AI server retrieves the image from Firebase**, processes it, and uploads the AI-generated image back to Firebase.
6. **The AI server sends the processed image URL to the Raspberry Pi via MQTT**.
7. **The Raspberry Pi downloads and displays the AI-generated image on an LED screen**.

## Installation
### 1️⃣ Raspberry Pi Setup
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv -y
```
### 2️⃣ Clone the Repository
```bash
git clone https://github.com/your-repo/ai-smart-capture.git
cd ai-smart-capture
```
### 3️⃣ Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```
### 4️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration
### Firebase Setup
1. **Create a Firebase Project** (https://console.firebase.google.com/).
2. **Enable Firebase Storage & Firestore**.
3. **Download the service account JSON file** and place it in `config/firebase_config.json`.

### MQTT Configuration (`config/mqtt_config.json`)
```json
{
    "broker": "mqtt.your-broker.com",
    "port": 1883,
    "publish_topic": "raspberrypi/capture",
    "subscribe_topic": "raspberrypi/generated_image"
}
```
### HTTP API Configuration (`config/http_config.json`)
```json
{
    "api_url": "http://your-ai-server/process_image",
    "api_key": "your-api-key"
}
```

## Running the System
### 1️⃣ Start the AI Server (on a separate machine)
```bash
cd ai_server
uvicorn main:app --host 0.0.0.0 --port 5000
```
### 2️⃣ Run the Raspberry Pi Main Process
```bash
cd app
python main.py
```
### 3️⃣ Run the UI (on Laptop)
```bash
cd ui
python app_ui.py
```

## Testing
Run individual tests using:
```bash
pytest tests/
```

## Troubleshooting
- **MQTT Connection Issues?** Check `config/mqtt_config.json` and ensure the broker is reachable.
- **AI Processing Delays?** Verify `config/http_config.json` and make sure the AI server is running.
- **No Image Display on LED?** Check the MQTT message log for received image URLs.

## Future Improvements
- 🔹 Add more object detection categories.
- 🔹 Enhance AI processing with style transfer for artistic effects.
- 🔹 Implement Web UI for remote control.

## License
MIT License. See `LICENSE` for details.
