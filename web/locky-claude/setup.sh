#!/bin/bash
# Første-gangs opsætning af Locky.
# Kør: bash setup.sh [lokal-ip]
#   lokal-ip er valgfri — detekteres automatisk ud fra netværksgrænseflader.
#   Eksempel:  bash setup.sh 192.168.1.42
#
# Scriptet er idempotent: .env overskrives IKKE hvis den allerede findes.
# Certifikater regenereres hver gang (nødvendigt hvis IP er ændret).

set -e
cd "$(dirname "$0")"

# ── Lokal IP ───────────────────────────────────────────────────────────────
LOCAL_IP=${1:-$(hostname -I | awk '{print $1}')}
if [ -z "$LOCAL_IP" ]; then
    echo "Fejl: kunne ikke detektere lokal IP. Angiv den manuelt: bash setup.sh <ip>"
    exit 1
fi
echo "Lokal IP: $LOCAL_IP"

# ── .env ───────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "ADVARSEL: Oprettet .env fra .env.example."
    echo "  Åbn .env og skift passwords inden du sætter systemet i produktion."
    echo "  Tryk Enter for at fortsætte med standard-passwords, eller Ctrl+C for at afbryde."
    read -r
fi

# Tilføj manglende variabler til .env (kan ske hvis .env er lavet fra en ældre .env.example)
grep -q "^MQTT_CONTROLLER_PASS" .env || echo "MQTT_CONTROLLER_PASS=controller123" >> .env

# Indlæs env-variabler
set -a
# shellcheck source=.env
source .env
set +a

# ── TLS-certifikater ───────────────────────────────────────────────────────
mkdir -p certs
echo "Genererer TLS-certifikater..."

openssl genrsa -out certs/ca.key 4096 2>/dev/null
openssl req -new -x509 -days 1825 -key certs/ca.key -out certs/ca.crt \
    -subj "/C=DK/O=Locky/CN=Locky CA"

openssl genrsa -out certs/server.key 2048 2>/dev/null
openssl req -new -key certs/server.key -out certs/server.csr \
    -subj "/C=DK/O=Locky/CN=$LOCAL_IP"
openssl x509 -req -days 365 \
    -in certs/server.csr \
    -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial \
    -out certs/server.crt \
    -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:%s" "$LOCAL_IP")

rm -f certs/server.csr certs/ca.srl
chmod 644 certs/server.key certs/server.crt certs/ca.crt
echo "Certifikater OK  (SAN: localhost · 127.0.0.1 · $LOCAL_IP)"

# ── Mosquitto passwd ───────────────────────────────────────────────────────
# Touch sikrer filen eksisterer så mosquitto kan starte.
# Ejerskab og indhold rettes inde fra containeren bagefter.
touch mosquitto/passwd
chmod 644 mosquitto/passwd mosquitto/acl

# ── Byg og start stack ─────────────────────────────────────────────────────
echo "Starter Docker Compose stack..."
docker compose up -d --build

# Vent til mosquitto-containeren svarer
echo "Venter på mosquitto..."
RETRIES=30
until docker compose exec mosquitto echo "" >/dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ "$RETRIES" -eq 0 ]; then
        echo "Fejl: mosquitto startede ikke inden for 30 sekunder."
        docker compose logs mosquitto
        exit 1
    fi
    sleep 1
done

# Opret MQTT-brugere.
# Slet filen inde fra containeren som root — undgår to problemer:
#   1) mosquitto_passwd -c afviser at overskrive eksisterende fil (mosquitto 2.x)
#   2) filen kan være ejet af uid 1883 fra forrige kørsel, som host-bruger ikke kan slette
SERVER_PASS=${MQTT_SERVER_PASS:-server123}
CONTROLLER_PASS=${MQTT_CONTROLLER_PASS:-controller123}

docker compose exec -u root mosquitto rm -f /mosquitto/config/passwd
docker compose exec -u root mosquitto \
    mosquitto_passwd -c -b /mosquitto/config/passwd server "$SERVER_PASS"
docker compose exec -u root mosquitto \
    mosquitto_passwd -b /mosquitto/config/passwd controller "$CONTROLLER_PASS"
docker compose exec -u root mosquitto \
    chown mosquitto:mosquitto /mosquitto/config/passwd
docker compose exec -u root mosquitto \
    chmod 700 /mosquitto/config/passwd
docker compose exec -u root mosquitto \
    chown mosquitto:mosquitto /mosquitto/config/acl

docker compose restart mosquitto
echo "Mosquitto brugere oprettet."

# ── Færdig ─────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Locky kører!"
echo ""
echo "   Lokalt:     https://localhost"
echo "   Netværk:    https://$LOCAL_IP"
echo "   MQTT:       mqtts://$LOCAL_IP:8883  (til controller)"
echo ""
echo " For at fjerne browser-certifikat-advarsel:"
echo "   Importer  certs/ca.crt  i din browser/enhed"
echo "   (Android: Indstillinger → Sikkerhed → CA-certifikater)"
echo "   (iOS:     Del filen → Installer profil → Stol på den)"
echo ""
echo " Hvis IP ændrer sig: kør 'bash setup.sh <ny-ip>' igen."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
