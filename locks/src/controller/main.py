import bluetooth as bt
import time
from base import ble_constants as bc, log
from machine import Pin
from neopixel import NeoPixel

log.write("Running main")

board_led = NeoPixel(Pin(10), 1)

def led_on(rgb):
    board_led.fill(rgb)
    board_led.write()

def led_off():
    led_on((0,0,0))

led_on((255, 255, 0))

log.write("Initialising BLE")
ble = bt.BLE()

ble.active(False)
time.sleep_ms(500)
ble.active(True)

devices = {}
target_device = None

conn_handle = None
value_handle = None


def bt_irq(event, data):
    global conn_handle, value_handle

    log.write(f"BLE IRQ: {bc.get_name("IRQ", event)}")

    if event == bc.IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data

        name = decode_name(adv_data)

        if name:
            devices[name] = (addr_type, bytes(addr))
            log.write(f"Discovered device: {name}, {addr_type}, {bytes(addr)}")

    elif event == bc.IRQ_SCAN_DONE:
        log.write(f"Scan complete")

    elif event == bc.IRQ_PERIPHERAL_CONNECT:
        conn_handle, addr_type, addr = data
        log.write("Connected", conn_handle, addr_type, addr)

        ble.gattc_discover_services(conn_handle)

    elif event == bc.IRQ_GATTC_SERVICE_RESULT:
        conn_handle, start_handle, end_handle, uuid = data
        log.write(f"Discovered service:", *data)

        if uuid == bc.SERVICE_UUID:
            ble.gattc_discover_characteristics(
                conn_handle,
                start_handle,
                end_handle,
            )
    elif event == bc.IRQ_GATTC_CHARACTERISTIC_RESULT:
        conn_handle, def_handle, value_h, properties, uuid = data

        if uuid == bc.COMMAND_UUID:
            value_handle = value_h
            log.write("Discovered characteristic:", *data)

    elif event == bc.IRQ_PERIPHERAL_DISCONNECT:
        log.write(f"Disconnected")

ble.irq(bt_irq)


def decode_name(payload):
    i = 0
    while i < len(payload):
        length = payload[i]

        if length == 0:
            break

        type_ = payload[i + 1]

        if type_ == 0x09:
            return bytes(payload[i + 2:i + 1 + length]).decode()

        i += 1 + length
    return None

def send_command(device_id, command):
    global conn_handle, value_handle

    name = "LOCK_%d" % device_id

    devices.clear()

    log.write(f"Scanning for '{name}'...")
    ble.gap_scan(3_000, 30_000, 30_000)

    timeout = time.ticks_ms() + 3_500

    while name not in devices:
        if time.ticks_ms() > timeout:
            log.write(f"Could not find device: '{name}'. Dropping command")
            return

    addr_type, addr = devices[name]
    log.write(f"Found device: '{name}'", addr_type, addr)
    value_handle = None

    log.write(f"Connecting to {name}...")
    ble.gap_connect(addr_type, addr)

    timeout = time.ticks_ms() + 5_000

    while value_handle is None:
        if time.ticks_ms() > timeout:
            log.write(f"Could not connect to '{name}'. Dropping command")
            return


    log.write(f"Sending command '{command}' to '{name}'")

    ble.gattc_write(
        conn_handle,
        value_handle,
        command.encode(),
    )

    time.sleep_ms(500)

    ble.gap_disconnect(conn_handle)

led_on((0,255,0))

send_command(101, "RED")