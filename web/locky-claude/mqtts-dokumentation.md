# MQTTS-dokumentation

## Hvor et MITM-angreb ville sidde

```
Flask ──(Docker internt)──► Mosquitto ──(skolens LAN)──► ESP32
                                 ↑
                          Her er truslen
```

Flask og Mosquitto kører begge i Docker på RPi'en og kommunikerer over et internt Docker-netværk (`locky-claude_default`). En angriber på skolenetværket kan ikke se denne trafik — de skal have lokal adgang til selve maskinen.

Forbindelsen fra Mosquitto til ESP32-controlleren krydser derimod det fysiske netværk. Her er et MITM-angreb realistisk: en angriber på samme LAN kan forsøge ARP-spoofing og sætte sig imellem RPi og ESP32. TLS blokerer dette på to måder:

1. ESP32 har `ca.crt` embedded i firmware og verificerer brokerens certifikat — et falsk certifikat afvises
2. Selv hvis TCP-strømmen aflyttes er al payload krypteret og ulæselig

---

## Verificer med tshark

Kør disse kommandoer på RPi'en. Åbn derefter websiden og tryk "Åbn skab" for at generere trafik.

### 1. Se TLS handshake live

```bash
sudo tshark -i any -f "tcp port 8883" -Y "tls.handshake"
```

Forventet output — TLS-forbindelsen etableres i tre trin:
```
1  0.000  ESP32-ip → 10.120.0.241  TLSv1.3  Client Hello
2  0.003  10.120.0.241 → ESP32-ip  TLSv1.3  Server Hello, Certificate, ...
3  0.008  ESP32-ip → 10.120.0.241  TLSv1.3  Finished
```

### 2. Vis at payload er krypteret (Application Data)

```bash
sudo tshark -i any -f "tcp port 8883" \
  -T fields \
  -e frame.number \
  -e ip.src \
  -e ip.dst \
  -e tls.record.content_type \
  -e tls.app_data
```

`content_type = 23` er "Application Data" — krypteret indhold. Der er ingen læsbare MQTT-felter (topic, payload) synlige.

### 3. Gem optagelse til pcap-fil

Nyttigt til at vise optagelsen offline eller i Wireshark GUI:

```bash
sudo tshark -i any -f "tcp port 8883" -w mqtts_capture.pcap
```

Afspil bagefter:

```bash
tshark -r mqtts_capture.pcap -Y "tls" -V | head -80
```

### 4. Bekræft at ukrypteret port 1883 ikke er åben

```bash
nc -zv 10.120.0.241 1883
# Forventet: Connection refused
```

### 5. Vis TLS-certifikatet der bruges

```bash
openssl s_client -connect 10.120.0.241:8883 -CAfile certs/ca.crt 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates
```

Forventet output:
```
subject=CN=locky-server
issuer=CN=Locky CA
notBefore=...
notAfter=...
```

`Verify return code: 0 (ok)` bekræfter at certifikatet er gyldigt og signeret af projektets CA.

---

## Sammenligning: hvad ville ses på port 1883 (ukrypteret)

Uden TLS ville tshark vise MQTT-feltere i klartekst:

```
mqtt.topic: locker/locker_nr01/open
mqtt.payload: open
mqtt.username: server
```

På port 8883 er disse felter ikke synlige — kun krypterede TLS Application Data-records.
