#!/usr/bin/env python3
"""
JWT-sikkerhedstest — demonstrerer at /aaben_skab afviser uautoriserede forsøg.

Kør: python test_jwt_security.py
Kræver: pip install requests
"""
import requests, time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE  = "https://localhost"
CERTS = "certs/ca.crt"
PAUSE = 2

def opret_og_login(email, password):
    s = requests.Session()
    s.verify = CERTS
    s.post(f"{BASE}/registrer", data={"username": email, "password": password, "password2": password})
    s.post(f"{BASE}/login", data={"username": email, "password": password})
    return s

def separator(titel):
    print()
    print("─" * 55)
    print(f"  {titel}")
    print("─" * 55)

RC_TEKST = {
    302: "✓ AFVIST — omdirigeret til login (302)",
    403: "✓ AFVIST — 403 Forbidden",
}
RC_TEKST_OK = {
    302: "✓ TILLADT — åbner skab (302)",
}

def print_result(beskrivelse, response, forventet, er_success=False):
    if response.status_code == forventet:
        tekst = RC_TEKST_OK.get(forventet) if er_success else RC_TEKST.get(forventet, f"✓ OK ({forventet})")
    else:
        tekst = f"✗ FEJL — forventet {forventet}, fik {response.status_code}"
    print(f"  {tekst}")
    time.sleep(PAUSE)


print()
print("=" * 55)
print("  JWT Sikkerhedstest")
print("  Systemet sender alle forsøg til /aaben_skab")
print("=" * 55)
time.sleep(PAUSE)


# ── Test 1 ────────────────────────────────────────────────────────────────
separator("Test 1: Forsøg uden login")
print("  En ukendt bruger forsøger direkte at åbne skab #01.")
print("  Ingen session — forventer redirect til login (302).")
time.sleep(PAUSE)

s1 = requests.Session()
s1.verify = CERTS
r = s1.post(f"{BASE}/aaben_skab", data={"skab_id": "01"}, allow_redirects=False)
print_result("Åbn skab uden login", r, 302)


# ── Test 2 ────────────────────────────────────────────────────────────────
separator("Test 2: Logget ind, men ingen booking")
print("  Bruger er registreret og logget ind,")
print("  men har ikke booket et skab — ingen JWT i session.")
print("  Forventer 403 Forbidden.")
time.sleep(PAUSE)

s2 = opret_og_login("angriber@test.dk", "testpassword")
r = s2.post(f"{BASE}/aaben_skab", data={"skab_id": "01"}, allow_redirects=False)
print_result("Åbn skab uden booking", r, 403)


# ── Test 3 ────────────────────────────────────────────────────────────────
separator("Test 3: JWT til skab #01, forsøger at åbne skab #02")
print("  Bruger har booket skab #01 og har et gyldigt JWT.")
print("  Forsøger at bruge samme token til at åbne skab #02.")
print("  JWT indeholder locker_nr=01 — mismatch giver 403.")
time.sleep(PAUSE)

s3 = opret_og_login("bruger@test.dk", "testpassword")
s3.post(f"{BASE}/book_skab", data={"skab_id": "01"})
r = s3.post(f"{BASE}/aaben_skab", data={"skab_id": "02"}, allow_redirects=False)
print_result("Åbn skab #02 med token til skab #01", r, 403)


# ── Test 4 ────────────────────────────────────────────────────────────────
separator("Test 4: Korrekt JWT — kontrol")
print("  Samme bruger åbner sit eget skab #01.")
print("  JWT matcher — forventer success (302 redirect).")
time.sleep(PAUSE)

r = s3.post(f"{BASE}/aaben_skab", data={"skab_id": "01"}, allow_redirects=False)
print_result("Åbn skab #01 med korrekt token", r, 302, er_success=True)


# ── Oprydning ─────────────────────────────────────────────────────────────
print()
print("─" * 55)
print("  Oprydning...")
s2.get(f"{BASE}/logout")
s3.post(f"{BASE}/frigiv_skab", data={"skab_id": "01"})
s3.get(f"{BASE}/logout")
print("  Testbrugere logget ud, booking frigivet.")
print("─" * 55)
print()
