# MicroPython MQTT-controller til Locky
#
# Filer der skal uploades til ESP32:
#   main.py  (denne fil)
#   ca.crt   (fra certs/ca.crt i projektmappen)
#
# Kræver: umqtt.simple (inkluderet i standard MicroPython-firmware til ESP32)

import network
import time
from umqtt.simple import MQTTClient
import ssl

# ── WiFi ──────────────────────────────────────────────────
WIFI_SSID     = "dit-netvaerk"
WIFI_PASSWORD = "dit-wifi-password"

# ── MQTT ──────────────────────────────────────────────────
MQTT_HOST  = "10.120.0.241"
MQTT_PORT  = 8883
MQTT_USER  = "controller"
MQTT_PASS  = "controller123"
MQTT_TOPIC = b"locker/#"


# ── WiFi ──────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return
    print("Forbinder til WiFi:", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.5)
        print(".", end="")
    print("\nForbundet — IP:", wlan.ifconfig()[0])


# ── MQTT callback ─────────────────────────────────────────
def on_message(topic, msg):
    topic = topic.decode()
    msg   = msg.decode()
    print("[MQTT]", topic, "→", msg)

    if msg == "open":
        # TODO: send BLE-signal til lås
        print("→ Åbner lås")
    elif msg == "lock":
        # TODO: send BLE-signal til lås
        print("→ Låser")


# ── MQTT ──────────────────────────────────────────────────
def connect_mqtt():
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.load_verify_locations("ca.crt")

    client = MQTTClient(
        client_id="esp32-controller",
        server=MQTT_HOST,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASS,
        ssl=ssl_ctx,
        keepalive=60,
    )
    client.set_callback(on_message)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print("Forbundet til MQTT — subscriber på:", MQTT_TOPIC.decode())
    return client


# ── Hovedloop ─────────────────────────────────────────────
connect_wifi()

client = None
while True:
    try:
        if client is None:
            client = connect_mqtt()
        client.check_msg()
        time.sleep(0.1)
    except Exception as e:
        print("Forbindelsesfejl:", e, "— prøver igen om 5s")
        client = None
        time.sleep(5)
