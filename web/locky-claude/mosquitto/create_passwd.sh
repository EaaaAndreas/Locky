#!/bin/bash
# Kør én gang efter 'docker compose up -d':
#   bash mosquitto/create_passwd.sh
#
# Opretter passwd-filen med to brugere:
#   server      — Flask-appen (publish)
#   controller  — låsecontrolleren (subscribe)

set -e

SERVER_PASS=${MQTT_SERVER_PASS:-server123}
CONTROLLER_PASS=${MQTT_CONTROLLER_PASS:-controller123}

echo "Opretter MQTT-brugere..."

docker compose exec mosquitto \
    mosquitto_passwd -c -b /mosquitto/config/passwd server "$SERVER_PASS"

docker compose exec mosquitto \
    mosquitto_passwd -b /mosquitto/config/passwd controller "$CONTROLLER_PASS"

echo "Genstarter mosquitto..."
docker compose restart mosquitto

echo "Færdig. Brugere oprettet: server, controller"
