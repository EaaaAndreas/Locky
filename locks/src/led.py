from umachine import Pin, Timer
from micropython import schedule

class Led(Pin):
    __n: int = 0
    __duration: int|None = None
    __period: int|None = None
    __running: bool = False
    __count: int = 0

    def __init__(self, *args, timer:Timer=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timer = timer or Timer(-1)

    def __reset(self, period:int=None, duration:int=None, n:int=0):
        self.__period = period
        self.__duration = duration
        self.__n = n

    @property
    def running(self) -> bool:
        return self.__running

    def stop(self) -> None:
        self.timer.deinit()
        self.__running = False
        self.__reset()

    def off(self) -> None:
        self.stop()
        super().off()

    def on(self) -> None:
        self.stop()
        super().on()

    def value(self, x:int=None) -> int|None:
        if x:
            self.stop()
        return super().value(x)

    def __blink(self, timer):
        v = super().value()
        self.__count += v
        if self.__n == 0:
            self.stop()
            print("Count:", self.__count)
        elif self.__n > 0:
            self.__n -= 1 - v
        period = self.__duration if self.__duration and not v else self.__period
        super().toggle()
        self.timer.init(period=period, mode=Timer.ONE_SHOT, callback= self.__blink)

    def _toggle(self, *_):
        #print("Toggle")
        super().toggle()

    def _init_timer(self, a):
        #print(a)
        self.timer.init(**a)#period=a[0], mode=a[1], callback=a[2])

    def blink(self, period:int, duration:int=None, n:int=0):
        self.off()
        if n == 0:
            n = -1
        self.__reset(period, duration, n)
        self.__running = True
        self.__count = 0

        if not duration and n <= 0:
            #print("Basic blink", period, duration, n)
            self.timer.init(period=period, mode=Timer.PERIODIC, callback=self._toggle)
        else:
            self.timer.init(period=period, mode=Timer.ONE_SHOT, callback=self.__blink)

    def __del__(self):
        self.stop()
        del self.timer