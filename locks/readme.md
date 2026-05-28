Remember to set network ssid and password in [config.json](src/lock/config.json)

# Firmware
Find firmware and installation instructions at micropython.org, the [firmware for the esp32-C3](https://micropython.org/download/ESP32_GENERIC_C3/) is also used for the esp32-h2
To summarize:
## Install esptool
```bash
pip install esptool
```
## Erase the flash
```bash
esptool erase-flash
```
or if you want to define the port
```bash
esptool --port PORTNAME erase-flash
```
## Flashing
```bash
    esptool --baud 460800 write-flash 0 FIRMWARE-FILE_PATH
```

## Transfering module
When the ESP32's have the MicroPython firmware installed, you can transfer the python modules to the devices.
The files must be laid out as follows:
```
/
├── base/
│   ├── ble_constants.py
│   └── log.py
└── main.py
```


# Changelog
## Controller
- [x] Basic development boot file
- [x] Bluetooth connectivity
- [ ] Connection to remote server
- [ ] Status update

## lock
- [x] Basic development boot file
- [x] Bluetooth connectivity
- [ ] BLE mesh
- [ ] Open
- [ ] Close
- [ ] Battery status

# Config
Micropython v1.28.0+