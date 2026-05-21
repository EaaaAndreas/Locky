> Remember to set network ssid and password in [config.json](src/lock/config.json)

This project is based on [Dynamic mesh network in MicroPython on ESP32 with ESP-NOW protocol ©Jindřich Šesták 2021/22](https://github.com/SestakJ/DP-Micropython-ESP32-Mesh)

# Getting started
To flash your ESP you need to install.
First, clone the ESP-IDF from GitHub:
```bash
git clone -b v4.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
```
_This may take a while_
> Windows
> ```PowerShell
> .\install.bat
> . .\export.sh
> ```

> Linux
> ```bash
> ./install.sh
> . ./export.sh
> ```



# Changelog
## Controller
- [x] Basic development boot file
- [ ] Bluetooth connectivity
- [ ] Connection to remote server
- [ ] Status update

## lock
- [x] Basic development boot file
- [ ] Bluetooth connectivity
- [ ] BLE mesh
- [ ] Open
- [ ] Close
- [ ] Battery status
- [ ] Remove use of WLAN

# Config
Micropython v1.28.0+