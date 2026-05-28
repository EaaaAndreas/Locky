#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// ── WiFi ──────────────────────────────────────────────────
const char* WIFI_SSID     = "dit-netvaerk";
const char* WIFI_PASSWORD = "dit-wifi-password";

// ── MQTT ──────────────────────────────────────────────────
const char* MQTT_HOST     = "10.120.0.241";
const int   MQTT_PORT     = 8883;
const char* MQTT_USER     = "controller";
const char* MQTT_PASS     = "controller123";  // matcher MQTT_CONTROLLER_PASS i .env
const char* MQTT_TOPIC    = "locker/#";

// ── CA-certifikat (indhold af certs/ca.crt) ───────────────
// Kopier hele indholdet af ca.crt ind her
const char* CA_CERT = R"EOF(
-----BEGIN CERTIFICATE-----
<indsæt indhold af certs/ca.crt her>
-----END CERTIFICATE-----
)EOF";

// ── Callbacks ─────────────────────────────────────────────
void onMessage(char* topic, byte* payload, unsigned int length) {
    String besked = "";
    for (int i = 0; i < length; i++) {
        besked += (char)payload[i];
    }

    Serial.printf("[MQTT] %s → %s\n", topic, besked.c_str());

    if (besked == "open") {
        // TODO: send BLE-signal til lås
        Serial.println("→ Åbner lås");
    } else if (besked == "lock") {
        // TODO: send BLE-signal til lås
        Serial.println("→ Låser");
    }
}

// ── Setup ─────────────────────────────────────────────────
WiFiClientSecure net;
PubSubClient     client(net);

void connectWifi() {
    Serial.printf("Forbinder til WiFi: %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\nForbundet — IP: %s\n", WiFi.localIP().toString().c_str());
}

void connectMQTT() {
    while (!client.connected()) {
        Serial.print("Forbinder til MQTT broker...");
        if (client.connect("esp32-controller", MQTT_USER, MQTT_PASS)) {
            Serial.println(" forbundet");
            client.subscribe(MQTT_TOPIC);
            Serial.printf("Subscriber på: %s\n", MQTT_TOPIC);
        } else {
            Serial.printf(" fejl RC=%d, prøver igen om 5s\n", client.state());
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);

    net.setCACert(CA_CERT);

    connectWifi();

    client.setServer(MQTT_HOST, MQTT_PORT);
    client.setCallback(onMessage);

    connectMQTT();
}

void loop() {
    if (!client.connected()) {
        connectMQTT();
    }
    client.loop();
}
