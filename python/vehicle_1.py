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

# --------------------------------------------------------
# Main Detection Loop
# --------------------------------------------------------

while True:

    ret, frame = cap.read()

    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector(gray)

    status_payload = {

        "publisher_ip": VEHICLE_ID,

        "eye_count": int(duration),

        "buzzer_count": total_buzzer_triggers,

        "motor_count": total_motor_triggers,

        "eye_closed": False

    }

    for face in faces:

        shape = predictor(gray, face)

        coords = [

            (shape.part(i).x, shape.part(i).y)

            for i in range(68)

        ]

        left_eye = [coords[i] for i in LEFT_EYE]

        right_eye = [coords[i] for i in RIGHT_EYE]

        left_ear = eye_aspect_ratio(left_eye)

        right_ear = eye_aspect_ratio(right_eye)

        ear = (left_ear + right_ear) / 2.0

        # ----------------------------------------
        # Driver Eyes Closed
        # ----------------------------------------

        if ear < EAR_THRESHOLD:

            if start_time is None:

                start_time = time.time()

            duration = round(

                time.time() - start_time,

                2

            )

            status_payload["eye_closed"] = True

            status_payload["eye_count"] = int(duration)

            cv2.putText(

                frame,

                f"Eyes Closed : {duration}s",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 0, 255),

                2

            )

            # ----------------------------
            # Warning Level
            # ----------------------------

            if duration > BUZZER_THRESHOLD:

                if not buzzer_active:

                    total_buzzer_triggers += 1

                    buzzer_active = True

                    client.publish(

                        CONTROL_TOPIC,

                        "BUZZER_ON"

                    )

            # ----------------------------
            # Alert Level
            # ----------------------------

            if duration > MOTOR_THRESHOLD:

                if not motor_active:

                    total_motor_triggers += 1

                    motor_active = True

                    client.publish(

                        CONTROL_TOPIC,

                        "MOTOR_ON"

                    )

            # ----------------------------
            # Emergency Level
            # ----------------------------

            if duration > EMAIL_THRESHOLD:

                if not email_sent:

                    send_email_alert()

                    email_sent = True

        # ----------------------------------------
        # Driver Awake
        # ----------------------------------------

        else:

            start_time = None

            duration = 0

            email_sent = False

            buzzer_active = False

            motor_active = False

            status_payload["eye_closed"] = False

            status_payload["eye_count"] = 0

            cv2.putText(

                frame,

                "Eyes Open",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 255, 0),

                2

            )

            client.publish(

                CONTROL_TOPIC,

                "BUZZER_OFF"

            )

            client.publish(

                CONTROL_TOPIC,

                "MOTOR_OFF"

            )

    # ----------------------------------------
    # Publish Dashboard Data
    # ----------------------------------------

    client.publish(

        STATUS_TOPIC,

        json.dumps(status_payload)

    )

    # ----------------------------------------
    # Display Camera Feed
    # ----------------------------------------

    cv2.imshow(

        f"{VEHICLE_ID} Driver Monitor",

        frame

    )

    key = cv2.waitKey(1) & 0xFF

    if key == 27:

        break

# --------------------------------------------------------
# Cleanup
# --------------------------------------------------------

cap.release()

cv2.destroyAllWindows()

client.loop_stop()

client.disconnect()

print("\nVehicle monitoring stopped.")
