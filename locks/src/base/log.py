import sys
import ntptime
import utime as time

_time_init = time.ticks_ms()
_time_synced = False



__logfile = open("log.txt", "a")

def write(*data:str, sep:str="\n\t"):
    if not data:
        return
    data = [str(bytes(s) if isinstance(s, memoryview) else s).strip() for s in data]
    if data:
        if _time_synced:
            timestamp = "%d-%d-%d %d:%d:%d" % time.gmtime()[:6]
        else:
            timestamp = str(time.ticks_diff(time.ticks_ms(), _time_init)) + "ms"
        line = f"[{timestamp}] {sep.join(data)}\n"
        __logfile.write(line)
        __logfile.flush()

        sys.stdout.write(line)
    else:
        flush()

def flush():
    __logfile.flush()

def sync_time():
    global _time_synced
    if _time_synced:
        return

    ntptime.host = "pool.ntp.org"

    for _ in range(5):
        try:
            ntptime.settime()
            _time_synced = True
            return
        except Exception as e:
            write("NTP failed:", str(e))
        time.sleep(1)

#sync_time()