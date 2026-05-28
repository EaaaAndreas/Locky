# Changelog

---

## Session 1 — bugfixes & schema-alignment

### `src/locky/app.py`
- `def decorated(*args **kwargs)` → manglende komma + manglende `return f(*args, **kwargs)` + korrekt `return decorated`
- `if method == "POST"` → `if request.method == "POST"` (to steder)
- `sql.get_user_data()` / `sql.get_email_list()` → `slq.get_user_data()` / `slq.check_email_list()`
- `session["user"] = email` i `registrer()` → `mail`
- `url_for("home")` → `url_for("booking")` (ingen `home`-route eksisterer)

### `src/sql_scripts.py`
- `DATABASE_RUI` → `DATABASE_URL`
- Alle queries omskrevet til parameterized `%s` — SQL injection fjernet
- `check_email_list`: `fetchone()` → `fetchall()` + list comprehension
- `insert_into_access`: literal kolonnenavne i VALUES → faktiske parametre
- `release_locker`: `DELETE FORM` → `DELETE FROM`, forkert SQL-syntaks rettet
- `create_user`: kolonnenavn `password` → `passwd`, overflødig `'` fjernet

### `src/encryption.py`
- `b'{getenv("SECRET_KEY")}'` er ikke en f-string — nøglen var hardcoded. Omskrevet til `_get_key()`

### `backend/Dockerfile`
- `uvicorn main:app` → `gunicorn app:app --bind 0.0.0.0:5000`

### `scripts-til-docker/database.py`
- `password_hash` → `passwd` (matcher resten af kodebasen)
- `bcrypt` → `argon2` (kun én)
- `Access`-tabel: FK-relation → simpel string-model (`locker_nr`, `email`)
- `Locker`-tabel: `location` → `size`, `status`, `floor`, `section` (sidenhen fjernet)

---

## Session 2 — filstruktur & docker-compose

### Ny filstruktur
Alt organiseret så `docker compose up -d` virker fra rodmappen:
```
locky-claude/
├── docker-compose.yaml
├── .env.example
├── nginx/nginx.conf
├── certs/
├── mosquitto/mosquitto.conf
└── backend/  (app.py, sql_scripts.py, encryption.py, generate_token.py,
               database.py, templates/, static/, Dockerfile, requirements.txt)
```

### `docker-compose.yaml`
- Mosquitto: `expose` → `ports: 8883:8883` (controller connecter udefra)
- Flask-port rettet til 5000 (matcher nginx.conf)

### `backend/app.py`
- `app.secret_key` læser `FLASK_SECRET_KEY` fra env
- `init_db()` kaldes ved opstart
- `aaben_skab()`: MQTT publish implementeret med paho-mqtt

### Nye filer
- `backend/requirements.txt`
- `.env.example`
- `mosquitto/mosquitto.conf`

---

## Session 3 — MQTT ACL & testværktøj

### `mosquitto/mosquitto.conf`
- `allow_anonymous false`, `password_file`, `acl_file` tilføjet

### `mosquitto/acl`
- `server`: `topic write locker/#`
- `controller`: `topic read locker/#`

### `mosquitto/create_passwd.sh`
- Engangsscript til oprettelse af MQTT-brugere via `docker compose exec`

### `docker-compose.yaml`
- Mosquitto mounter nu hele `./mosquitto/` så `passwd` og `acl` er tilgængelige

### `backend/app.py`
- MQTT publish sender `auth`-credentials fra env

### `test_mqtt_sub.py`
- Subscriber-script der simulerer controlleren, forbinder med TLS + credentials

---

## Session 4 — debugging & funktionel webapp

### Rettede bugs under kørsel
- `nginx.conf`: manglende `events {}` og `http {}` wrapper → nginx startede ikke
- `postgres:alpine` → `postgres:16-alpine` (version 18 ændrede data-mappestruktur)
- `database.py`: `init_db()` fik retry-logik (op til 10 forsøg med 2s interval) så Flask ikke crasher hvis DB ikke er klar
- `backend/app.py`: `render_template("register.html")` → `registrer.html`
- `backend/app.py`: formfelter `email`/`passwd` → `username`/`password` (matcher HTML-formerne)
- Jinja2 `zfill`-filter ikke indbygget → registreret som custom filter i Flask
- `mosquitto/passwd`: høne-og-æg problem løst med `touch` + korrekte rettigheder

### Implementeret funktionalitet
- `sql_scripts.py`: `RealDictCursor` tilføjet så resultater er dicts (`user_info["passwd"]` virker)
- `book_skab()`: skriver nu til `access`-tabellen i DB
- `manage_skab()`: henter brugerens skab fra DB og sender til template
- `booking()`: markerer brugerens eget skab som "mine"
- `frigiv_skab()`: sletter fra `access`-tabellen
- `laas_skab()`: publisher `"lock"` til MQTT
- `manage_skab.html`: åbn/lås bruger nu `fetch` (ingen sidereload) med 30-sekunders auto-lås timer

### TLS-workaround
- Flask → Mosquitto: `cert_reqs: ssl.CERT_NONE` (self-signed cert matcher ikke `mosquitto`-hostname)
- test_mqtt_sub.py: `tls_insecure_set(True)` + `cert_reqs: ssl.CERT_NONE`

---

## Session 5 — JWT-integration

### `generate_token.py`
- `key` → `locker_nr` i payload (klarere navngivning)
- Udløb bruger nu `datetime.timezone.utc` (undgår deprecation-advarsel)
- `verify_jwt_token` returnerer nu payload-dict (eller `None`) i stedet for `True`/`False`
- Robust exception-håndtering — alle fejl returnerer `None`

### `backend/app.py`
- `book_skab()`: genererer JWT ved booking, gemmer i session
- `aaben_skab()`: validerer JWT fra session — tjekker signatur, udløb og at `locker_nr` matcher det ønskede skab — giver 403 hvis invalid

---

## Session 8 — database-trim, sikkerhedstest & rapport

### `backend/database.py`
- `Locker`-model: `size`, `floor`, `section` fjernet — kun `id` og `status` tilbage
- Seed omskrevet: 5 ledige skabe uden testbruger (tjekker nu på `Locker` ikke `User`)
- Ubrugte imports fjernet (`DateTime`, `PasswordHasher`, `datetime`)

### `backend/app.py`
- `DUMMY_SKABE` trimmet til 5 ledige skabe uden size/floor/section

### `test_jwt_security.py` (ny fil)
- Demonstrerer JWT-validering i fire scenarier:
  1. Åbn uden login → 302 redirect til login
  2. Logget ind uden booking → 403 (ingen token i session)
  3. Gyldig token til skab #01, forsøger skab #02 → 403 (locker_nr mismatch)
  4. Korrekt token → 302 success (kontrol)
- `opret_og_login()` håndterer at testbrugere allerede kan eksistere
- Sleep + forklarende tekst til præsentation

### `test_mqtt_security.py` (ny fil)
- Demonstrerer MQTT-sikkerhed i fem scenarier:
  1. Anonym forbindelse → RC 5
  2. Forkert password → RC 5
  3. Korrekt controller-login → RC 0
  4. Controller forsøger at publicere (kun læserettighed) → blokeret af ACL
  5. Server publicerer → leveret
- ACL-test verificeres via subscriber (controller) der faktisk lytter — ikke via `on_publish` der fyrer klient-side uanset broker-accept

### `rapport-vaerktoejer.md` (ny fil)
- Udkast til rapport-afsnit om Docker, Nginx, Mosquitto, Flask, PostgreSQL, JWT og TLS
- Afsnit om hvorfor Flask ikke eksponeres direkte og hvorfor Docker er valgt
- Forklaring af SQL injection og parameteriserede queries

---

## Session 9 — hardening, bugfixes & dokumentation

### `docker-compose.yaml`
- `no-new-privileges: true` tilføjet på alle services
- `cap_drop: ALL` tilføjet på Flask — ingen Linux-capabilities nødvendige
- `cap_drop: ALL` forsøgt på Mosquitto — fjernet igen da containeren ikke kunne starte

### `backend/Dockerfile`
- Non-root bruger `appuser` oprettet — Gunicorn og Flask kører ikke længere som root
- `chown -R appuser:appuser /app` sikrer at applikationsfiler ejes korrekt

### `backend/app.py`
- `login()`-routen genererer nu JWT ved login hvis brugeren allerede har en aktiv booking — retter fejl hvor telefon ikke kunne åbne skab booket fra anden enhed
- `booking()`-routen viser nu korrekt status for skabe booket af andre brugere

### `backend/sql_scripts.py`
- `get_all_booked_lockers()`: ny funktion der returnerer alle bookede skabsnumre som et set — bruges til at markere optagne skabe i booking-oversigten

### `backend/templates/manage_skab.html`
- Aktivitetslog fjernet helt
- `fetch` i `openLocker()` venter nu på serverens svar inden UI opdateres — fejl er ikke længere stille

### `backend/templates/booking.html`
- Undertitel "Vis ledige skabe..." fjernet
- Footer-tekst "Gymnasiet Skabssystem — 2025" fjernet

### `backend/templates/base.html`
- Log ud-knap erstattet med dropdown på avatar — mobilvenlig, lukkes ved klik udenfor
- Brugernavn skjules på små skærme

### `setup.sh`
- `chown mosquitto:mosquitto /mosquitto/config/acl` tilføjet — retter advarsel om forkert ejerskab

### Nye filer
- `mqtts-dokumentation.md`: tshark- og openssl-kommandoer til at verificere og dokumentere MQTTS
- `sikkerhedsarkitektur.md`: rapportafsnit der gennemgår sikkerhedslag fra netværk til container-niveau
- `test_integration.py`: fuld systemintegrationstest fra HTTP-flow til MQTT-subscriber
- `esp32_controller_example.py`: MicroPython-version af controller-scriptet (erstatter .ino)
- `rapport-vaerktoejer.tex`: LaTeX-version af rapport-vaerktoejer.md

### `rapport-vaerktoejer.md` / `.tex`
- MQTTS-afsnit opkvalificeret og præciseret
- Nyt afsnit om credentials og miljøvariabler under Docker
- Nyt afsnit om OpenSSL og selvsignerede certifikater

### Verifikation
- Snap-installeret Mosquitto på host fjernet — lyttede på port 1883 og svarede på `nc`-test
- MQTTS verificeret med `openssl s_client` og `curl -v` — TLS 1.3, AES-256-GCM, `Verify return code: 0 (ok)`
- `ca.crt` distribueret til telefon via `python3 -m http.server` over LAN

---

## Session 7 — bugfixes, ESP32-kontekst & netværksopsætning

### `backend/app.py`
- `book_skab()`: tjekker nu om brugeren allerede har et skab og om skabet er optaget inden booking — forhindrer dobbeltbooking

### `backend/sql_scripts.py`
- `get_locker_access(locker_nr)`: ny funktion der slår et skab op i `access`-tabellen (bruges til dobbeltbooking-tjek)

### `backend/templates/registrer.html`
- Fornavn/efternavn fjernet
- "Brugernavn" → "Email" med `type="email"` så browser validerer format

### `backend/templates/booking.html`
- Størrelsesfilter (S/M/L) fjernet
- Etage/sektion/størrelse fjernet fra skab-kortene og booking-modal
- `openBookModal` forenklet til kun at tage skab-id

### `backend/templates/manage_skab.html`
- Etage/sektion fjernet fra overskrift
- Størrelse og placering fjernet fra meta-rækken

### `test_mqtt_sub.py`
- Host kan nu angives som argument: `python test_mqtt_sub.py 192.168.1.42`
- Fallback: `MQTT_HOST` env-variabel, derefter `localhost`

### `setup.sh`
- Mosquitto passwd-flow omskrevet til at være konsistent:
  1. `touch passwd` så mosquitto kan starte
  2. `rm` fra container som root (undgår uid 1883-ejerskabsproblem og `-c` afvisning)
  3. `-c` opretter frisk fil, `-b` tilføjer controller
  4. `chown mosquitto` + `chmod 700` — ingen permissions-advarsler
- `MQTT_CONTROLLER_PASS` tilføjes automatisk til `.env` hvis den mangler

### Netværk & RPi
- Statisk IP `10.120.0.241/24` sat via netplan på RPi med `renderer: NetworkManager`
- `ca.crt` importeret i Brave via `certutil` — siden viser "forbindelsen er sikker"
- Konstateret at ESP32 skal have `ca.crt` embedded i firmware for MQTT TLS

---

## Session 6 — LAN-adgang & plug-and-play setup

### `setup.sh` (ny fil)
- Enkelt script der håndterer hele første-gangs opsætning
- Detekterer lokal IP automatisk (`hostname -I`) eller tager den som argument
- Genererer TLS-certifikater med korrekt SAN: `localhost`, `127.0.0.1` og lokal IP
- Løser mosquitto passwd høne-og-æg problem: `touch passwd` → `docker compose up` → `docker compose exec` passwd-oprettelse
- Printer adgangs-URL'er (localhost + LAN) og vejledning til ca.crt-import

### `backend/app.py`
- `booking()`-route manglede `@login_required` → tilføjet (ville crashe med KeyError hvis man ramte `/booking` uden session)
- `session["user"]` → `session.get("user")` i `booking()` som ekstra sikkerhed

### `.env.example`
- `MQTT_CONTROLLER_PASS` tilføjet (bruges i setup.sh og create_passwd.sh)

### `CLAUDE.md`
- Opstart-sektion erstattet af `setup.sh`-dokumentation
- LAN-adgang + certifikat-import vejledning tilføjet per browser/platform

---

## Åbne punkter
- Skabe hentes fra `DUMMY_SKABE` — ikke fra `lockers`-tabellen i DB
- Login-id er `username`-felt der gemmes i `email`-kolonne — gruppen skal beslutte identifikator
- `src/` og `scripts-til-docker/` er forældede og kan slettes
- Aktivitetslog i `manage_skab` ikke implementeret
- Flask-image skal genbygges når Docker Hub-adgang er på plads (kør fra det terminal-vindue der ikke er PyCharm)
