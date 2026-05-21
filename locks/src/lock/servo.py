from umachine import PWM
from math import radians, degrees

class Servo:
    def __init__(self, pin, min_us:float=417, max_us:float=2593, min_deg:float=0, max_deg:float=180.0, freq:int=50):
        self.pwm = PWM(pin)
        self.pwm.freq(freq)
        self.current_us = 0.0
        self._slope = (min_us - max_us) / (radians(min_deg) - radians(max_deg))
        self._offset = min_us

    def write(self, deg:float):
        self.write_rad(radians(deg))

    def read(self):
        return degrees(self.read_rad())

    def write_rad(self, rad:float):
        self.write_us(int(rad * self._slope + self._offset))

    def read_rad(self):
        return (self.current_us - self._offset) / self._slope

    def write_us(self, us:int):
        self.current_us = us
        self.pwm.duty_ns(int(self.current_us * 1000))

    def read_us(self):
        return self.current_us

    def off(self):
        self.write_us(0)

