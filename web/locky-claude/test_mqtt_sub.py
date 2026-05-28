#!/usr/bin/env python3
"""
Kør fra projektets rodmappe: python test_mqtt_sub.py [host]
  python test_mqtt_sub.py              # forbinder til localhost
  python test_mqtt_sub.py 192.168.1.42 # forbinder til RPi/server på LAN
Alternativt: sæt MQTT_HOST i env.
"""
import paho.mqtt.client as mqtt
import ssl, os, sys

CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")
HOST = sys.argv[1] if len(sys.argv) > 1 else os.getenv("MQTT_HOST", "localhost")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Forbundet til MQTT broker")
        client.subscribe("locker/#")
        print("Subscriber på: locker/#\n")
    else:
        codes = {
            1: "forkert protokolversion",
            2: "afvist klient-id",
            3: "broker utilgængelig",
            4: "forkert brugernavn/kodeord",
            5: "ikke autoriseret",
        }
        print(f"Forbindelsesfejl: {codes.get(rc, rc)}")


def on_message(client, userdata, msg):
    print(f"[MQTT]  {msg.topic}  →  {msg.payload.decode()}")


client = mqtt.Client()
client.username_pw_set(
    username=os.getenv("MQTT_CONTROLLER_USER", "controller"),
    password=os.getenv("MQTT_CONTROLLER_PASS", "controller123"),
)
client.tls_set(
    tls_version=ssl.PROTOCOL_TLS,
    cert_reqs=ssl.CERT_NONE,
)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message

print(f"Forbinder til {HOST}:8883 ...")
client.connect(HOST, 8883)
client.loop_forever()
