from umachine import Pin, Timer, idle
from utime import sleep_ms
from network import WLAN, STAT_CONNECTING
import json
from led import Led
# sleep_ms(50)

board_led = Led("LED", Pin.OUT, value=0, timer=Timer(hard=True))
board_led.blink(200)

timeout = False
to_timer = Timer(-1)

def _timeout(*_):
    global timeout
    timeout = True

try:
    # Get config
    with open("config.json", "rb") as f:
        cfg = json.load(f)
    # Check for saved networks
    if "networks" in cfg.keys():
        # Connect to WLAN
        wlan = WLAN(WLAN.IF_STA)
        wlan.active(True)
        available_aps = [ap[0].decode() for ap in wlan.scan()]
        # Check for known saved networks
        for ssid in cfg["networks"].keys():
            if ssid in available_aps:
                # Connect
                wlan.connect(ssid, cfg["networks"][ssid])

                # Start timeout timer
                tout = cfg.get("networksettings", {}).get("connectiontimeout", 30)

                to_timer.init(period=timeout, mode=Timer.ONE_SHOT, callback=_timeout)

                # Wait for connection
                while not timeout or wlan.status() == STAT_CONNECTING or not wlan.isconnected():
                    idle()
                print(*wlan.ipconfig("addr4"), sep=" / ")
                break

        if not wlan.isconnected():
            wlan.active(False)
            wlan.deinit()
        elif "webrepl" in cfg.keys() and cfg["webrepl"].get("enabled", False):
            import webrepl
            webrepl.start(port=cfg["webrepl"].get("port", 8266), password=cfg["webrepl"].get("password", None))
            board_led.blink(1000, 5)
        else:
            board_led.blink(5000, 5)
except:
    board_led.on()
    pass


