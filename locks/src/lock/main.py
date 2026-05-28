import time

import bluetooth as bt
import struct
from machine import Pin
from neopixel import NeoPixel
from base import log
from base import ble_constants as bc

log.write("Running main")

DEVICE_ID = 101

# ======================================== Methods ========================================
board_led = NeoPixel(Pin(10), 1)

def led_on(rgb=(255,255,255)):
    log.write(f"LED ON: {rgb}" if any(rgb) else "LED OFF")
    board_led.fill(rgb)
    board_led.write()

def led_off():
    led_on((0,0,0))

# ======================================== BLE Init ========================================


log.write("Initializing BLE")

ble = bt.BLE()
ble.active(False)
time.sleep_ms(500)
ble.active(True)

service = (
    bc.SERVICE_UUID,
    (
        (bc.COMMAND_UUID, bt.FLAG_WRITE),
    ),
)

((command_handle,),) = ble.gatts_register_services((service,))

log.write("BLE Services Registered", "Service UUID: %s" % bc.SERVICE_UUID, "Command UUID: %s" % bc.COMMAND_UUID, "command handle: %d" % command_handle)

state = "INIT"

def connection_timeout(t):
    log.write("Connection Timeout")
    if ble.active():
        ble.active(False)

def bt_irq(event, data):
    global state
    log.write(f"BT IRQ: {bc.get_name("IRQ", event)}")

    if event == bc.IRQ_CENTRAL_CONNECT:
        log.write("BLE Connected")

    elif event == bc.IRQ_CENTRAL_DISCONNECT:
        log.write("BLE Disconnected")

    elif event == bc.IRQ_GATTS_WRITE:
        conn_handle, attr_handle = data
        log.write(f"GATTS write", *data)
        if attr_handle == command_handle:
            value = ble.gatts_read(command_handle).decode().strip()

            log.write(f"BLE CMD: '{value}'")
            if not value == state:
                state = value
                if value == "RED":
                    led_on((255,0,0))
                elif value == "GREEN":
                    led_on((0,0,255))


ble.irq(bt_irq)

def advertising_payload():
    name = "LOCK_%d" % DEVICE_ID

    payload = bytearray()

    # Flags
    payload += struct.pack("BB", 2, 0x01)
    payload += b"\x06"

    # Complete name
    name_bytes = name.encode()
    payload += struct.pack("BB", len(name_bytes) + 1, 0x09)
    payload += name_bytes

    return payload

def start_advertising(interval_us=100_000):
    payload = advertising_payload()
    log.write(f"BLE Advertising: '{payload}'")

    ble.gap_advertise(
        interval_us,
        payload
    )


led_on((255,255,255))

start_advertising()