# 🚗 Driver Drowsiness Monitoring System

A real-time Driver Drowsiness Monitoring System developed using Computer Vision, IoT, and MQTT communication. The system continuously monitors the driver's eye movements using facial landmark detection and automatically triggers multiple safety actions when drowsiness is detected.

---

## 📌 Project Overview

Road accidents caused by driver fatigue remain one of the leading causes of fatalities worldwide. This project detects prolonged eye closure using the Eye Aspect Ratio (EAR) algorithm and performs automatic safety actions through an ESP32 microcontroller.

The system supports multiple vehicles simultaneously using MQTT communication and provides a centralized web dashboard for monitoring all active vehicles.

---

## ✨ Features

- 👁 Real-time eye closure detection using OpenCV and dlib
- 📐 Eye Aspect Ratio (EAR) based fatigue detection
- 📡 MQTT-based communication between vehicles and dashboard
- 🚨 Multi-level alert system
- 🔊 Buzzer activation
- ⚙ Motor shutdown simulation using ESP32
- 🌐 Flask web dashboard
- 📧 Automatic email alerts
- 🚗 Multiple vehicle monitoring
- 📈 Live fleet status dashboard

---

## 🛠 Technologies Used

### Software

- Python
- OpenCV
- dlib
- Flask
- MQTT (Paho)
- SciPy
- NumPy

### Hardware

- ESP32
- USB Camera
- Buzzer
- Relay Module
- DC Motor

---

## 🚦 Alert Levels

| Driver State | Eye Closed Duration | Action |
|--------------|--------------------|---------|
| Normal | < 5 sec | Monitoring |
| Warning | 5 sec | Buzzer Activated |
| Alert | 10 sec | Motor Control Triggered |
| Critical | 20 sec | Email Alert + Emergency Notification |

---

## 📂 Repository Structure

```
driver-drowsiness-monitoring-system
│
├── python/
├── dashboard/
├── esp32/
├── images/
├── models/
├── dataset/
├── report/
├── requirements.txt
├── README.md
└── LICENSE
```

---

## ⚙ Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/driver-drowsiness-monitoring-system.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶ Running the Project

Start the dashboard

```bash
python dashboard/dashboard.py
```

Run Vehicle 1

```bash
python python/vehicle_1.py
```

Run Vehicle 2

```bash
python python/vehicle_2.py
```

Upload the ESP32 code using Arduino IDE.

---

## 📷 Screenshots

Screenshots are available inside the **images/** folder.

- Dashboard
- Vehicle Detection
- Hardware Setup
- Alert States

---

## 👥 Contributors

- Thershna TK
- Muhamed Ibrahim M
- Sanjeetha Sree P

---

## 📄 License

This project is licensed under the MIT License.
