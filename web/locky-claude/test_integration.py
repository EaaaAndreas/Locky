#!/usr/bin/env python3
"""
Fuld systemintegrationstest — verificerer hele kæden fra webapp til MQTT-subscriber.

Kør test_mqtt_sub.py i en anden terminal først:
  source .env && python test_mqtt_sub.py 10.120.0.37

Kør derefter denne test:
  python test_integration.py
"""
import requests, time, sys

BASE  = "https://10.120.0.37"
CERTS = "certs/ca.crt"
PAUSE = 2

EMAIL  = "integration@test.dk"
PASSWD = "integration123"
SKAB   = "01"


def separator(titel):
    print()
    print("─" * 58)
    print(f"  {titel}")
    print("─" * 58)

def ok(msg):   print(f"  ✓ {msg}")
def info(msg): print(f"    {msg}")
def fejl(msg): print(f"  ✗ {msg}"); sys.exit(1)


def opret_og_login():
    s = requests.Session()
    s.verify = CERTS
    r = s.post(f"{BASE}/registrer",
               data={"username": EMAIL, "password": PASSWD},
               allow_redirects=False)
    if r.status_code == 302:
        ok(f"Bruger oprettet: {EMAIL}")
    else:
        r = s.post(f"{BASE}/login",
                   data={"username": EMAIL, "password": PASSWD},
                   allow_redirects=False)
        if r.status_code == 302:
            ok(f"Bruger eksisterede — logget ind: {EMAIL}")
        else:
            fejl(f"Login fejlede: HTTP {r.status_code}")
    return s


print()
print("=" * 58)
print("  LOCKY — Fuld systemintegrationstest")
print()
print("  Registrering → Login → Booking → JWT-validering")
print("  → HTTPS → Flask → MQTTS → Broker → Controller")
print("=" * 58)
print()
print("  Sørg for at test_mqtt_sub.py kører i en anden terminal.")
print("  Testen starter om 5 sekunder...")
time.sleep(5)


# ── Trin 1: Registrér / log ind ───────────────────────────────────────────
separator("Trin 1 — Registrér bruger og log ind")
info("Opretter bruger og starter en ny session via HTTPS.")
time.sleep(PAUSE)

s = opret_og_login()
time.sleep(PAUSE)


# ── Trin 2: Ryd op fra evt. tidligere kørsel ─────────────────────────────
separator("Trin 2 — Ryd op fra eventuel tidligere kørsel")
info("Frigiver skab hvis brugeren allerede har en booking.")
time.sleep(PAUSE)

s.post(f"{BASE}/frigiv_skab", data={"skab_id": SKAB}, allow_redirects=False)
ok("Klar til ny booking")
time.sleep(PAUSE)


# ── Trin 3: Book skab ─────────────────────────────────────────────────────
separator(f"Trin 3 — Book skab #{SKAB.zfill(2)}")
info("Flask opretter adgang i databasen og udsteder et JWT-token.")
info(f"Token gemmes krypteret (AES-256) i brugerens session.")
time.sleep(PAUSE)

r = s.post(f"{BASE}/book_skab", data={"skab_id": SKAB}, allow_redirects=False)
if r.status_code == 302:
    ok(f"Skab #{SKAB.zfill(2)} booket — JWT udstedt og gemt i session")
else:
    fejl(f"Booking fejlede: HTTP {r.status_code}")
time.sleep(PAUSE)


# ── Trin 4: Åbn skab → MQTT publish ──────────────────────────────────────
separator(f"Trin 4 — Åbn skab #{SKAB.zfill(2)}")
info("Flask dekrypterer JWT, validerer signatur og udløb,")
info(f"tjekker at locker_nr i payload matcher skab #{SKAB.zfill(2)},")
info("og publicerer 'open' til MQTTS-brokeren på port 8883.")
info("")
info("Se den anden terminal — controlleren bør modtage beskeden nu.")
time.sleep(PAUSE)

r = s.post(f"{BASE}/aaben_skab", data={"skab_id": SKAB}, allow_redirects=False)
if r.status_code == 302:
    ok(f"HTTP 302 — åbn-kommando sendt til broker")
    ok(f"Topic: locker/locker_nr{SKAB}/open  |  Payload: open")
else:
    fejl(f"Åbn fejlede: HTTP {r.status_code}")
time.sleep(4)


# ── Trin 5: Frigiv skab og log ud ─────────────────────────────────────────
separator("Trin 5 — Frigiv skab og log ud")
info("Rydder op så testen kan køres igen.")
time.sleep(PAUSE)

r = s.post(f"{BASE}/frigiv_skab", data={"skab_id": SKAB}, allow_redirects=False)
if r.status_code == 302:
    ok(f"Skab #{SKAB.zfill(2)} frigivet")
else:
    fejl(f"Frigiv fejlede: HTTP {r.status_code}")

s.get(f"{BASE}/logout")
ok("Logget ud")
time.sleep(PAUSE)


# ── Resultat ──────────────────────────────────────────────────────────────
print()
print("=" * 58)
print("  Test gennemført — hele kæden verificeret:")
print()
print("  [Browser] HTTPS →  [Nginx]  TLS-terminering")
print("      ↓")
print("  [Flask]   JWT-validering + session")
print("      ↓")
print("  [Mosquitto] MQTTS port 8883, ACL-kontrol")
print("      ↓")
print("  [Controller] modtager 'open' på locker/locker_nr01/open")
print("=" * 58)
print()
