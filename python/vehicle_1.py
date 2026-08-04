"""
----------------------------------------------------------
Vehicle 1 - Driver Drowsiness Detection

Description:
This module detects driver drowsiness using the Eye Aspect
Ratio (EAR) algorithm with OpenCV and dlib. It communicates
with an ESP32 over MQTT, updates the central dashboard,
and sends an emergency email when the driver's eyes remain
closed for a prolonged duration.

Features
--------
- Real-time eye detection
- EAR-based drowsiness detection
- MQTT communication
- ESP32 buzzer and motor control
- Email alert system
- Multi-vehicle support

Author:
Thershna TK
Muhamed Ibrahim
Sanjeetha Sree P
----------------------------------------------------------
"""

import cv2
import dlib
import json
import time
import smtplib

from email.message import EmailMessage
from scipy.spatial import distance
import paho.mqtt.client as mqtt

# --------------------------------------------------------
# Vehicle Information
# --------------------------------------------------------

VEHICLE_ID = "Vehicle-1"

# --------------------------------------------------------
# Email Configuration
# Replace these values with your own before running.
# Do NOT store real credentials in GitHub.
# --------------------------------------------------------

EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"
ALERT_RECEIVER = "receiver@example.com"

# --------------------------------------------------------
# MQTT Configuration
# --------------------------------------------------------

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

STATUS_TOPIC = f"drowsiness/{VEHICLE_ID}"
CONTROL_TOPIC = f"vehicle_control/{VEHICLE_ID}"

client = mqtt.Client(client_id=VEHICLE_ID)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# --------------------------------------------------------
# Detection Parameters
# --------------------------------------------------------

EAR_THRESHOLD = 0.25

BUZZER_THRESHOLD = 5
MOTOR_THRESHOLD = 10
EMAIL_THRESHOLD = 20

# --------------------------------------------------------
# Email Function
# --------------------------------------------------------

def send_email_alert():

    msg = EmailMessage()

    msg["Subject"] = f"Emergency Alert - {VEHICLE_ID}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ALERT_RECEIVER

    msg.set_content(
        f"""
Driver Drowsiness Alert

Vehicle : {VEHICLE_ID}

The driver's eyes have remained closed
for more than {EMAIL_THRESHOLD} seconds.

Immediate attention is required.
"""
    )

    try:

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

            smtp.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            smtp.send_message(msg)

            print("Emergency email sent.")

    except Exception as e:

        print("Email Error:", e)


# --------------------------------------------------------
# Eye Aspect Ratio Calculation
# --------------------------------------------------------

def eye_aspect_ratio(eye):

    vertical_1 = distance.euclidean(
        eye[1],
        eye[5]
    )

    vertical_2 = distance.euclidean(
        eye[2],
        eye[4]
    )

    horizontal = distance.euclidean(
        eye[0],
        eye[3]
    )

    return (
        vertical_1 + vertical_2
    ) / (2.0 * horizontal)


# --------------------------------------------------------
# Load Facial Landmark Model
# --------------------------------------------------------

print("Loading facial landmark predictor...")

detector = dlib.get_frontal_face_detector()

predictor = dlib.shape_predictor(
    "shape_predictor_68_face_landmarks.dat"
)

LEFT_EYE = list(range(42, 48))
RIGHT_EYE = list(range(36, 42))

# --------------------------------------------------------
# Start Camera
# --------------------------------------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    raise RuntimeError(
        "Unable to access webcam."
    )

print(f"{VEHICLE_ID} monitoring started.")
print("Press ESC to exit.\n")

# --------------------------------------------------------
# Runtime Variables
# --------------------------------------------------------

start_time = None
duration = 0

email_sent = False

buzzer_active = False
motor_active = False

total_buzzer_triggers = 0
total_motor_triggers = 0
