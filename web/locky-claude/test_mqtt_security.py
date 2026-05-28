#!/usr/bin/env python3
"""
MQTT-sikkerhedstest — demonstrerer at brokeren afviser uautoriserede forbindelser.

Kør: source .env && python test_mqtt_security.py
"""
import paho.mqtt.client as mqtt
import ssl, os, time, threading

CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")
HOST     = os.getenv("MQTT_HOST", "localhost")
PORT     = int(os.getenv("MQTT_PORT", 8883))

RESULTS = {}

def make_client(name, username, password):
    c = mqtt.Client(client_id=name, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    c.username_pw_set(username, password)
    c.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    return c

def test_connect(beskrivelse, username, password, forventet_rc):
    result = {}
    c = make_client(beskrivelse, username, password)

    def on_connect(client, userdata, flags, rc):
        result["rc"] = rc
        client.disconnect()

    c.on_connect = on_connect
    try:
        c.connect(HOST, PORT)
        c.loop_start()
        time.sleep(1.5)
        c.loop_stop()
    except Exception as e:
        result["rc"] = f"exception: {e}"

    rc = result.get("rc", "ingen svar")
    status = "✓ OK" if rc == forventet_rc else "✗ FEJL"
    print(f"{status}  {beskrivelse}")
    print(f"       Forventet rc={forventet_rc}  |  Fik rc={rc}\n")


def test_publish_acl(beskrivelse, publisher_user, publisher_pass, topic, forventet_leveret):
    """
    Verificerer ACL ved at have en subscriber (server-bruger) lytte mens
    publisher forsøger at sende. Beskeden tæller kun hvis brokeren leverer den.
    """
    received = threading.Event()

    # Subscriber (controller-bruger har læserettighed til locker/#)
    sub = make_client("acl-sub", "controller",
                      os.getenv("MQTT_CONTROLLER_PASS", "controller123"))

    def on_sub_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(topic)

    def on_message(client, userdata, msg):
        received.set()

    sub.on_connect = on_sub_connect
    sub.on_message = on_message
    sub.connect(HOST, PORT)
    sub.loop_start()
    time.sleep(0.5)

    # Publisher
    pub = make_client("acl-pub", publisher_user, publisher_pass)
    pub_result = {}

    def on_pub_connect(client, userdata, flags, rc):
        pub_result["rc"] = rc
        if rc == 0:
            client.publish(topic, "acl-test", qos=1)

    pub.on_connect = on_pub_connect
    pub.connect(HOST, PORT)
    pub.loop_start()
    time.sleep(2)
    pub.loop_stop()
    sub.loop_stop()
    sub.disconnect()

    leveret = received.is_set()
    status = "✓ OK" if leveret == forventet_leveret else "✗ FEJL"
    forventet_tekst = "leveret" if forventet_leveret else "blokeret af ACL"
    faktisk_tekst   = "leveret" if leveret else "blokeret af ACL"
    print(f"{status}  {beskrivelse}")
    print(f"       Forventet: {forventet_tekst}  |  Fik: {faktisk_tekst}\n")


print("=" * 55)
print(" MQTT Sikkerhedstest")
print(f" Broker: {HOST}:{PORT}")
print("=" * 55 + "\n")

# ── Forbindelsesforsøg ────────────────────────────────────────────────────
print("── Autentifikation ──────────────────────────────────────\n")

test_connect(
    "Ingen credentials (anonym)",
    username="", password="",
    forventet_rc=5,
)
test_connect(
    "Forkert password",
    username="controller", password="forkert123",
    forventet_rc=5,
)
test_connect(
    "Korrekt controller-login",
    username="controller", password=os.getenv("MQTT_CONTROLLER_PASS", "controller123"),
    forventet_rc=0,
)

# ── ACL-test ──────────────────────────────────────────────────────────────
print("── ACL (adgangskontrol) ─────────────────────────────────\n")

test_publish_acl(
    "Controller forsøger at publicere (kun læserettighed)",
    publisher_user="controller",
    publisher_pass=os.getenv("MQTT_CONTROLLER_PASS", "controller123"),
    topic="locker/locker_nr01/open",
    forventet_leveret=False,
)
test_publish_acl(
    "Server publicerer korrekt (skriverettighed)",
    publisher_user=os.getenv("MQTT_SERVER_USER", "server"),
    publisher_pass=os.getenv("MQTT_SERVER_PASS", "server123"),
    topic="locker/locker_nr01/open",
    forventet_leveret=True,
)
