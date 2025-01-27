# Smart Art Displayer Project

## Introduction

The Smart Art Glasses project is built on a Raspberry Pi Zero, utilizing a YOLO model, Pi Camera, temperature sensor, and AI art tools to create personalized artworks. It detects faces, automatically takes photos, and adjusts the artistic style dynamically based on user input and real-time temperature data. The final artworks are displayed on an LED screen.

---

## Features

1. **Face Detection and Photography**  
   - Real-time face detection using the YOLO model with automatic photo capture.  
   - Allows users to set a custom time interval for photo capturing.

2. **AI Art Processing**  
   - Uploads captured photos to Firebase and processes them using AI art tools.  
   - Dynamically adjusts the artistic style based on user input and temperature data.

3. **LED Screen Display**  
   - Displays the generated artworks in real-time on an LED screen.

4. **User Interface**  
   - A simple user interface to:  
     - Input text to describe emotions.  
     - Select an art style.  
     - View real-time temperature data.  
     - Clear stored photos from the database.

---

## Requirements

### Hardware
- Raspberry Pi Zero
- Pi Camera
- LED Screen
- Temperature Sensor

### Software
- Python 3.9 or higher
- Firebase project and storage setup
- MQTT Broker

