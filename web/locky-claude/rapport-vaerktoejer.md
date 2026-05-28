# Anvendte værktøjer og teknologier

## Docker

Docker er en platform til containerisering af software. En container er en isoleret kørende proces der indeholder alt hvad en applikation har brug for: kode, runtime, biblioteker og konfiguration. I modsætning til virtuelle maskiner deler containere operativsystemets kerne, hvilket gør dem markant lettere og hurtigere at starte.

### Hvorfor Docker til dette projekt

Et system som Locky kræver at flere komponenter med vidt forskellige teknologier kører side om side: en Python-webapplikation, en relationsdatabase og en MQTT-broker. Uden containerisering skulle alle tre installeres og konfigureres direkte på værtsmaskinen — med risiko for konflikter mellem versioner og afhængigheder, og med en opsætningsproces der er svær at reproducere på en ny maskine.

Med Docker beskrives hele opsætningen i konfigurationsfiler (`Dockerfile` og `docker-compose.yaml`). En ny maskine — f.eks. en Raspberry Pi — kræver blot at Docker er installeret og et enkelt script køres. Systemet starter identisk uanset underliggende operativsystem og konfiguration.

Derudover giver Docker netværksisolation: services kommunikerer via et internt Docker-netværk og er ikke tilgængelige udefra medmindre en port eksplicit eksponeres. PostgreSQL er eksempelvis slet ikke tilgængelig fra netværket — kun Flask kan nå den.

### Containerisering og reproducerbarhed

Et centralt problem i softwareudvikling er at et program kan opføre sig forskelligt afhængigt af hvilken maskine det kører på — forskellig Python-version, manglende biblioteker eller afvigende systemkonfiguration. Docker løser dette ved at pakke applikationen og dens hele miljø i et image, som bygges én gang og kører identisk overalt. I dette projekt betyder det at Flask-applikationen, databasen og MQTT-brokeren opfører sig ens uanset om de kører på en udviklerens laptop eller på en Raspberry Pi 5.

### Dockerfile

Et Dockerfile er en opskrift på hvordan et image bygges. Projektets Flask-image tager udgangspunkt i et officielt Python 3.12-image, installerer de nødvendige Python-pakker og kopierer applikationskoden ind:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

De øvrige services (Nginx, Mosquitto, PostgreSQL) anvender officielle images direkte uden modificering.

### Docker Compose

Når en applikation består af flere services der skal kommunikere, anvendes Docker Compose. Med en enkelt `docker-compose.yaml`-fil defineres alle services, deres netværk, porte og delte filer. Projektet kører fire services:

| Service | Image | Formål |
|---|---|---|
| nginx | nginx:alpine | TLS-terminering og reverse proxy |
| flask | Lokalt bygget | Flask-webapplikation |
| mosquitto | eclipse-mosquitto | MQTT-broker |
| db | postgres:16-alpine | PostgreSQL-database |

Hele systemet startes med én kommando: `docker compose up -d`. Services kommunikerer via et internt Docker-netværk og er isolerede fra hinanden og fra værtsmaskinen, med undtagelse af de porte der eksplicit eksponeres.

### Persistens

Docker-containere er som udgangspunkt midlertidige — data der skrives i en container forsvinder når containeren slettes. Til PostgreSQL anvendes et named volume (`db_data`) der lever uafhængigt af containeren og bevarer data på tværs af genstarter.

### Håndtering af credentials med miljøvariabler

Adgangskoder og hemmelige nøgler — til databasen, MQTT-brokeren, JWT-signering og sessionskryptering — må aldrig stå direkte i kildekoden. Kildekode lægges typisk i versionsstyring (Git), og credentials der skrives ind i koden risikerer at blive eksponeret for alle der kan se repositoriet.

Docker Compose løser dette med en `.env`-fil: alle følsomme værdier samles ét sted, og filen tilføjes til `.gitignore` så den aldrig committes. Docker Compose læser filen automatisk og injicerer variablerne som miljøvariabler i de relevante containere ved opstart. Koden henter dem derfra med `os.getenv()`:

```python
app.secret_key = getenv("FLASK_SECRET_KEY")
auth={"username": getenv("MQTT_SERVER_USER"), "password": getenv("MQTT_SERVER_PASS")}
```

Resultatet er at kildekoden ikke indeholder en eneste adgangskode — kun navne på de variabler der forventes at eksistere i miljøet. En ny maskine får credentials ved at kopiere `.env`-filen, ikke ved at ændre i koden.

---

## Nginx

Nginx er en højtydende webserver der i dette projekt udelukkende anvendes som reverse proxy og TLS-terminering — ikke til at serve indhold direkte.

### Hvorfor ikke eksponere Flask direkte?

Flask leveres med en indbygget udviklingsserver, men den er eksplicit ikke beregnet til produktion. Den er enkelttrådет, håndterer kun én forespørgsel ad gangen og har ingen beskyttelse mod langsomme eller ondsindede klienter der kan blokere serveren ved at holde forbindelser åbne.

I projektet anvendes Gunicorn som WSGI-server foran Flask. Gunicorn håndterer samtidige forespørgsler via worker-processer, men er stadig ikke egnet til at stå direkte eksponeret mod et netværk — den mangler effektiv håndtering af TLS, HTTP/2, statiske filer og beskyttelse mod langsomme klienter (slow-client attacks).

Nginx løser alle disse problemer. Det er skrevet i C, afvikler asynkront og er designet til at håndtere tusindvis af samtidige forbindelser med minimal ressourceanvendelse. I dette projekt fungerer Nginx som det eneste indgangspunkt udadtil: det terminerer TLS, videresender forespørgsler til Gunicorn/Flask via det interne Docker-netværk og omdirigerer HTTP til HTTPS. Flask behøver dermed aldrig forholde sig til kryptering eller netværksrobusthed.

### Reverse proxy

En reverse proxy modtager indkommende forespørgsler og videresender dem til en bagvedliggende service. Browseren kommunikerer udelukkende med Nginx; Flask-applikationen er aldrig direkte eksponeret. Dette giver én central indgang til systemet og gør det muligt at håndtere TLS ét sted frem for i selve applikationen.

### TLS-terminering

Al kommunikation mellem browser og server er krypteret med TLS 1.3. Nginx modtager HTTPS-forespørgsler på port 443, dekrypterer dem og videresender dem ukrypteret til Flask på port 5000 via det interne Docker-netværk. HTTP-forespørgsler på port 80 omdirigeres automatisk til HTTPS.

Certifikaterne er selvsignerede med projektets egen Certificate Authority (CA). Browsere og enheder der skal tilgå systemet importerer CA-certifikatet én gang for at etablere tillid.

---

## Mosquitto (MQTT)

Eclipse Mosquitto er en open source MQTT-broker. MQTT (Message Queuing Telemetry Transport) er en letvægts publish/subscribe-protokol designet til enheder med begrænset ressourcer og ustabile netværksforbindelser — egenskaber der gør den velegnet til IoT-kommunikation.

I dette projekt anvendes MQTTS frem for ukrypteret MQTT, da kommandoerne der sendes — `open` og `lock` — styrer fysiske låse. Uden kryptering ville en angriber på samme netværk kunne aflytte eller forfalske disse kommandoer ved at placere sig mellem brokeren og controlleren (et såkaldt man-in-the-middle-angreb). MQTTS løser begge problemer: al trafik krypteres så indholdet ikke kan aflæses, og ESP32-controlleren verificerer brokerens identitet ved hjælp af CA-certifikatet der er embeddet i dens firmware — et falsk certifikat fra en uægte broker vil blive afvist.

### Publish/subscribe-modellen

I stedet for direkte kommunikation mellem afsender og modtager kommunikerer enheder via en central broker. En publisher sender en besked til et topic (f.eks. `locker/locker_nr02/open`), og alle subscribers på det pågældende topic modtager beskeden. Publisher og subscriber behøver ikke kende hinanden og behøver ikke være online samtidig.

I dette projekt publicerer Flask-applikationen åbn- og lås-kommandoer til brokeren, og ESP32-controlleren subscriber og udfører de fysiske handlinger.

### Sikkerhed

Mosquitto er konfigureret med tre sikkerhedslag:

**TLS (MQTTS på port 8883):** Al kommunikation er krypteret med samme CA og certifikat som Nginx anvender. Ukrypterede forbindelser accepteres ikke.

**Autentifikation:** Anonym adgang er deaktiveret. To brugere er oprettet med adgangskode: `server` (Flask-applikationen) og `controller` (ESP32-controlleren).

**ACL (Access Control List):** Adgangsrettigheder er begrænset per bruger. `server` må kun publicere (`write`) til `locker/#`, og `controller` må kun abonnere (`read`) på samme topics. Ingen bruger har bredere adgang end nødvendigt.

---

## Flask

Flask er et letvægts webframework til Python. Det håndterer HTTP-forespørgsler, session-styring og rendering af HTML-templates via Jinja2. I projektet definerer Flask alle routes — login, registrering, booking, skabsadministration og MQTT-publish-endepunkter. Applikationen serveres i produktion via Gunicorn, der er en WSGI-server der håndterer samtidige forespørgsler.

Adgangskontrol implementeres med en `login_required`-decorator der omdirigerer til login hvis brugeren ikke har en aktiv session. Passwords hashes med Argon2 inden lagring, og JWT-tokens udstedes ved booking og valideres kryptografisk ved skabsåbning uden at forespørge databasen.

---

## PostgreSQL

PostgreSQL er en open source relationsdatabase der anvendes til at persistere brugere og bookinger. Databaseskemaet består af tre tabeller:

| Tabel | Indhold |
|---|---|
| `users` | Email og hashed password |
| `lockers` | Skabsinformation |
| `access` | Aktive bookinger (kobling mellem bruger og skab) |

Applikationen forbinder via psycopg2 med parameteriserede queries. SQLAlchemy anvendes til at oprette tabellerne ved opstart (`init_db()`), mens de løbende forespørgsler håndteres direkte med psycopg2 og `RealDictCursor` så resultater returneres som dictionaries frem for tupler.

### Parameteriserede queries og SQL injection

SQL injection er et angreb hvor en bruger skriver SQL-kode ind i et inputfelt i stedet for normale data. Uden beskyttelse kunne en forespørgsel bygges ved at sætte brugerens input direkte ind i en tekststreng:

```python
query = "SELECT * FROM users WHERE email = '" + email + "'"
```

Skriver en angriber `' OR '1'='1` i email-feltet bliver forespørgslen:

```sql
SELECT * FROM users WHERE email = '' OR '1'='1'
```

`'1'='1'` er altid sandt — forespørgslen returnerer alle brugere og angriberen er logget ind uden at kende noget password.

Parameteriserede queries løser dette ved at adskille SQL-koden fra data. Brugerens input sendes som en separat parameter og behandles aldrig som SQL:

```python
curr.execute("SELECT * FROM users WHERE email = %s", (email,))
```

Databasen modtager kode og data som to adskilte ting — ligegyldigt hvad brugeren skriver, fortolkes det aldrig som SQL-kode.

---

## JWT (JSON Web Token)

JWT er en åben standard (RFC 7519) til at repræsentere og udveksle påstande (claims) mellem to parter på en kompakt og selvstændig måde. Et JWT-token består af tre Base64-kodede dele adskilt af punktummer:

- **Header**: algoritme og token-type
- **Payload**: de data tokenet indeholder (claims)
- **Signatur**: kryptografisk hash der garanterer at tokenet ikke er manipuleret

I dette projekt udstedes et JWT-token når en bruger booker et skab. Payload indeholder brugerens email, skabsnummeret og et udløbstidspunkt (8 timer). Tokenet signeres med HMAC-SHA256 (HS256) og en hemmelig nøgle, og krypteres efterfølgende med AES inden det gemmes i brugerens Flask-session.

Når brugeren trykker "Åbn", sendes tokenet til serveren, dekrypteres og valideres — serveren tjekker signaturen, at tokenet ikke er udløbet, og at skabsnummeret i payload matcher det ønskede skab. Kun hvis alle tre tjek består, publiceres åbn-kommandoen til MQTT-brokeren.

Den centrale fordel ved denne tilgang er at serveren ikke behøver slå noget op i databasen ved hver åbn-handling. Tokenet er selvstændigt og bærer al nødvendig information — adgangstilladelsen er kryptografisk bundet til den specifikke bruger og det specifikke skab og kan ikke forfalskes uden kendskab til den hemmelige nøgle.

---

## TLS (Transport Layer Security)

TLS er en kryptografisk protokol der sikrer fortrolighed og integritet for data der transmitteres over et netværk. Projektet anvender TLS 1.3 — den nyeste version — på to forbindelser: HTTPS (port 443) og MQTTS (port 8883).

Certifikaterne er selvsignerede, dvs. udstedt af projektets egen Certificate Authority (CA) frem for en offentlig tredjepart. For at browsere og enheder skal stole på certifikatet skal CA-certifikatet importeres manuelt. Alternativt ville et offentligt certifikat fra eksempelvis Let's Encrypt eliminere dette trin, men kræver et registreret domænenavn og ekstern internetadgang til verifikation — ikke egnet til et lukket skolenetværk.
