#include <WiFi.h>
#include <PubSubClient.h>

// ---------------- WiFi Configuration ----------------

const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// ---------------- MQTT Configuration ----------------

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

// Vehicle Topic
const char* mqtt_topic = "vehicle_control/Vehicle-1";

// ---------------- Pin Configuration ----------------

#define BUZZER_PIN 5
#define RELAY_PIN 4

WiFiClient espClient;
PubSubClient client(espClient);

// ---------------- MQTT Callback ----------------

void callback(char* topic, byte* payload, unsigned int length) {

  String message = "";

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message Received : ");
  Serial.println(message);

  if (message == "BUZZER_ON") {

    digitalWrite(BUZZER_PIN, HIGH);

  }

  else if (message == "BUZZER_OFF") {

    digitalWrite(BUZZER_PIN, LOW);

  }

  else if (message == "MOTOR_ON") {

    digitalWrite(RELAY_PIN, LOW);

  }

  else if (message == "MOTOR_OFF") {

    digitalWrite(RELAY_PIN, HIGH);

  }

}

// ---------------- WiFi Connection ----------------

void connectWiFi() {

  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);
    Serial.print(".");

  }

  Serial.println();
  Serial.println("WiFi Connected");
  Serial.print("IP Address : ");
  Serial.println(WiFi.localIP());

}

// ---------------- MQTT Connection ----------------

void reconnectMQTT() {

  while (!client.connected()) {

    Serial.print("Connecting to MQTT...");

    if (client.connect("ESP32_Vehicle_1")) {

      Serial.println("Connected");

      client.subscribe(mqtt_topic);

    }

    else {

      Serial.print("Failed. Error : ");

      Serial.println(client.state());

      delay(2000);

    }

  }

}

// ---------------- Setup ----------------

void setup() {

  Serial.begin(115200);

  pinMode(BUZZER_PIN, OUTPUT);

  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(BUZZER_PIN, LOW);

  digitalWrite(RELAY_PIN, HIGH);

  connectWiFi();

  client.setServer(mqtt_server, mqtt_port);

  client.setCallback(callback);

}

// ---------------- Loop ----------------

void loop() {

  if (!client.connected()) {

    reconnectMQTT();

  }

  client.loop();

}
