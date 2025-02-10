# AI Smart Displayer

## Overview
This project is a **smart AI-based detection and capture system** that integrates **YOLO object detection, Firebase for image storage, AI processing, and MQTT for real-time image delivery**. The system is designed to detect objects, capture images, process them using AI, and display the processed images on a Raspberry Pi-connected LED screen.

## Features
- **Object Detection**: Uses YOLOv5 to detect user-selected objects (e.g., person, tie, car, dog) through a camera.
- **Firebase Integration**: Captured images are stored in Firebase Storage for later use.
- **AI Processing via HTTP**: The Raspberry Pi sends metadata to an AI server that retrieves images from Firebase and processes them.
- **MQTT Communication**: AI-processed images are sent back to the Raspberry Pi via MQTT for display.
- **Temperature & Humidity Monitoring**: Real-time sensor data is displayed in the UI.
- **User Interface (UI)**: Provides an intuitive UI for object selection, image display, and interaction.

## System Architecture
1. **User selects an object** (e.g., person, tie) and enters optional text.
2. **The camera captures an image** when the selected object is detected.
3. **The image is uploaded to Firebase Storage**.
4. **Metadata (temperature, humidity, user text) is sent via HTTP to the AI server**.
5. **The AI server sends the processed image to the Raspberry Pi via MQTT**.
7. **The Raspberry Pi displays the AI-generated image on an LED screen**.

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

### Firebase Setup
1. **Create a Firebase Project**  
   - Go to the [Firebase Console](https://console.firebase.google.com/), create a new project (or use an existing one).

2. **Enable Realtime Database**  
   - In the **Build** section of the Firebase console, select **Realtime Database** and click **Create Database** if it’s not already enabled.
   - Follow the prompts to configure read/write rules as desired (or keep defaults for testing).

3. **Download the Service Account JSON**  
   - Navigate to **Project Settings** > **Service Accounts** > **Generate new private key**.
   - Save the JSON file to `config/firebase_config.json` (or wherever your code expects it).

4. **Replace the databaseURL in `ui/app_ui.py`**  
   - Locate the Firebase initialization code, for example:
     ```python
     cred = credentials.Certificate("config/firebase_config.json")
     firebase_admin.initialize_app(cred, {
         "databaseURL": "https://your-project-id.firebaseio.com/"
     })
     ```
   - Replace `"https://your-project-id.firebaseio.com/"` with your **Realtime Database** URL, found in your Firebase console (e.g., `"https://<PROJECT_ID>-default-rtdb.firebaseio.com/"`).

---

### MQTT Setup (HiveMQ Cloud)
1. **Create a HiveMQ Cloud Account**  
   - Visit [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/) and sign up (or log in if you already have an account).

2. **Obtain Broker Details**  
   - In your HiveMQ Cloud dashboard, locate your **hostname**, **port**, **username**, and **password**.  
   - Example:  
     - **Broker/Hostname**: `a1b2c3d4e5f6.s1.eu.hivemq.cloud`  
     - **Port**: `8883` (TLS)  

3. **Update Your MQTT Config in Code**  
   - In your Python scripts (e.g., `ui/app_ui.py`, `pi/main.py`) where you configure MQTT:
     ```python
     BROKER_URL = "a1b2c3d4e5f6.s1.eu.hivemq.cloud"
     PORT = 8883
     USERNAME = "YourHiveMQUsername"
     PASSWORD = "YourHiveMQPassword"
     ```
   - Ensure you call `client.tls_set()` if using **port 8883** (TLS).

4. **Specify Topics**  
   - Subscribe to and publish on the same topics across your devices (e.g., `"IC.embedded/LUGUAN/test"`) so they can communicate properly.

5. **Test the Connection**  
   - Run your script and check the console for a successful connection message (e.g. `"✅ Connected to HiveMQ Cloud!"`).
   - If you encounter errors, verify your hostname, credentials, and port number in the HiveMQ Cloud console.


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
