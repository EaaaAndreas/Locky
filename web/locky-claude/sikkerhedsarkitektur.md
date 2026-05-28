# Sikkerhedsarkitektur

Systemets sikkerhed er opbygget i lag, hvor hvert lag begrænser hvad en angriber kan gøre selv hvis et andet lag kompromitteres.

## Netværksisolation

Docker opretter et internt netværk hvor services udelukkende kommunikerer med hinanden ved servicenavn. PostgreSQL har ingen eksponerede porte og er fuldstændigt utilgængelig fra netværket — kun Flask kan nå den via det interne Docker-netværk. Udefra er alene port 80 (HTTP-omdirigering), 443 (HTTPS) og 8883 (MQTTS) tilgængelige.

## Indgangspunkt

Al indkommende trafik rammer Nginx først. Nginx terminerer TLS og videresender forespørgsler til Flask via det interne netværk. Flask eksponeres aldrig direkte mod netværket og behøver ikke forholde sig til kryptering eller netværksrobusthed.

## Applikationslaget

Flask-applikationen kører som en dedikeret uprivilegeret bruger (`appuser`) oprettet i Docker-imaget — ikke som root. Alle Linux-capabilities er fjernet (`cap_drop: ALL`), og `no-new-privileges` forhindrer at processen kan eskalere til højere rettigheder undervejs, f.eks. via setuid-binaries. Tilsammen betyder det at selv hvis en angriber opnår kodeeksekvering i applikationen, er de begrænset til hvad en normal uprivilegeret bruger må.

Adgangskoder og hemmelige nøgler gemmes aldrig i kildekoden men injiceres som miljøvariabler via en `.env`-fil der ikke committes til versionsstyring. Brugeradgangskoder hashes med Argon2 inden lagring. Alle databaseforespørgsler er parameteriserede og beskytter mod SQL injection. Adgangskontrol til routes håndteres med en `login_required`-decorator der omdirigerer til login hvis brugeren ikke har en aktiv session.

## Skabsåbning og JWT

Når en bruger booker et skab udstedes et JWT-token med brugerens email, skabsnummer og udløbstidspunkt. Tokenet signeres med HMAC-SHA256 og krypteres med AES-256 inden det gemmes i brugerens session. Ved åbning af et skab dekrypteres og valideres tokenet — serveren tjekker signaturen, at tokenet ikke er udløbet, og at skabsnummeret i payload matcher det ønskede skab. Kun hvis alle tre tjek består publiceres åbn-kommandoen til MQTT-brokeren. Serveren forespørger ikke databasen ved denne validering — tokenet er selvstændigt og kan ikke forfalskes uden kendskab til den hemmelige nøgle.

## Mæglerlaget

Mosquitto kører som en dedikeret uprivilegeret bruger (uid 1883) og er konfigureret med `no-new-privileges`. Port 1883 (ukrypteret MQTT) er ikke eksponeret — al kommunikation sker udelukkende over MQTTS på port 8883 med TLS 1.3. Anonym adgang er deaktiveret og to brugere er oprettet med adgangskode: `server` (Flask-applikationen) og `controller` (ESP32-controlleren). En ACL begrænser adgangsrettigheder per bruger: `server` må kun publicere til `locker/#`, og `controller` må kun abonnere på samme topics.

ESP32-controlleren har CA-certifikatet embeddet i sin firmware og verificerer brokerens certifikat ved forbindelse. Et man-in-the-middle-angreb — hvor en angriber placerer sig mellem broker og controller og forsøger at udgive sig for brokeren — afvises fordi et falsk certifikat ikke kan valideres mod den kendte CA.

## Oversigt

| Trussel | Beskyttelse |
|---|---|
| Aflytning af netværkstrafik | TLS 1.3 på HTTPS og MQTTS |
| Man-in-the-middle mod controller | CA-certifikat embeddet i ESP32-firmware |
| Uautoriseret MQTT-adgang | Autentifikation og ACL |
| Åbning af andres skab | JWT kryptografisk bundet til bruger og skab |
| SQL injection | Parameteriserede queries |
| Adgang uden login | `login_required` og session-validering |
| Credentials i kildekode | Miljøvariabler via `.env` |
| Privilege escalation i container | Uprivilegeret bruger, `cap_drop: ALL`, `no-new-privileges` |
| Direkte databaseadgang udefra | PostgreSQL uden eksponerede porte |
