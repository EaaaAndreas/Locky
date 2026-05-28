from builtins import callable
from umachine import Timer

__all__ = ["Task", "add_task", "remove_task", "set_timer_interval", "get_timer_interval_ms", "cycle_tasks", "run_main_loop"]


# * Set DEBUG = True to get verbose logging and raise errors.
# If you're playing around with the script or developing a solution with the module!, I encourage having `DEBUG=True`
# while developing.

DEBUG = False

# Set the maximum number of tasks the task manager can take at once
MAX_NUM_TASKS = 10


_tasks = [] # This list will contain all tasks
_timer = Timer(-1) # This timer controls the timing
_timer_interval_ms = 1


def _dbg_raise(msg:str, ex:type[Exception]=Exception):
    """
    A function to raise or print exeptions based on the state of DEBUG. This ensures that errors are not raised when
    running in a production environment.
    :param msg: str: The message to print or raise
    :param ex: type[Exception]: The exception to raise.
        Default: Exception
    :return: None
    """
    if DEBUG:
        raise ex(msg)
    print("[Task Manager]: \033[93m", ex.__name__, msg, "\033[0m")

def set_timer_interval(interval_ms:int):
    """
    Sets the timer interval, determining how long each tick of the clock will be. Thereby determining the
    time-resolution of the task manager.
        Want fast, precise timing: low timer interval
        Want slower, battery efficient timing: high timer interval
    :param interval_ms: The time in milliseconds between each tick of the clock in the task manager
    :return: None
    """
    global _timer_interval_ms
    _timer_interval_ms = interval_ms


def get_timer_interval_ms():
    """
    Returns the current timer interval in milliseconds.
    :return: int: the timer interval in milliseconds
    """
    return _timer_interval_ms


class Task:
    num: int
    def __init__(self, name:str, interval:int, callback):
        """
        A Task to be executed by the task manager. Every task the task manager excecutes must be an instance of the
        `Task` class. This class holds all the information that the task manager needs to run. You can modify or
        interrupt these tasks internally or from another Task.
        The `Task` class can be instantiated with the `add_task()` function and removed from the task manager cycle with
        the `remove_task()` function.

        When initialized, the `Task` object adds itself to the list of tasks to be executed.
        Each taks instance has it's own timer and interval. The interval determines how often the `Task` is executed,
        and the timer updates each time the task manager calls the

        Example:
            When using the task manager, you simply set up everything you'll need to execute the individual tasks
            (wifi, pins, PWM, etc.). Then use the `add_task()` function to add a callback to the execution list:
            ```
            import taskmanager as tm

            # Set up your wifi, pins, PWM, etc. here
            from machine import PIN

            board_led = Pin("LED", Pin.OUT, value=0)

            # Make your task callbacks
            def blink_led_task():
                board_led.toggle()

            def print_task():
                print("Hello, world!")

            # Add tasks to taskmanager
            tm.add_task("BLINK", 500, blink_led_task) # Toggles the board led every 0.5 seconds
            tm.add_task("PRINT", 5000, print_task) # Prints "Hello, World!" every 5 seconds

            # Run the task manager
            tm.run_main_loop()
            ```
            This example creates two callbacks. One, `blink_led_task`, that toggles the board LED. This is set to
            execute every 500ms or 0.5 seconds. The other `print_task`, that prints "Hello, World!" is set to execute
            every 5000ms or 5 seconds.

        :param name: str: The name of the task (used for debugging or removal). The name must be unique.
        :param interval: int: The interval, in milliseconds between each executon of the task.
        :param callback: Callable[[], None]: The callback function to call when the task is executed. The callback must
            not take any arguments and should return `None`, as the return value is not used or accessible anywhere.
        """
        self.name = name
        self.interval = interval
        if not callable(callback):
            _dbg_raise("Callback must be a callable function with no arguments and no return value")
        self.callback = callback
        self.timer = interval
        self.__add_task(self)

    def __run(self):
        """
        This function is called by the task manager main loop. This function runs the `Task.callback` if `Task.timer`
        has reached 0.
        :return: None
        """
        if self.timer <= 0:
            # Reset own timer
            self.reset_timer()
            # Run callback function
            self.callback()
            if DEBUG:
                print(f"Running task {self.name}")

    @staticmethod
    def __add_task(task) -> None:
        """
        Adds the task instance to the list of tasks to be executed by the task manager.
        :param task: Task instance
        :return: None
        """
        num_tasks = len(_tasks)
        if task.interval < _timer_interval_ms:
            _dbg_raise("Task not added. The interval is smaller than the task managers interval.")
            return
        if not task.callback:
            _dbg_raise(f"Task {task.name} not added. Missing callback")
            return
        if num_tasks < MAX_NUM_TASKS:
            _tasks.append(task)
            task.num = num_tasks
            if DEBUG:
                print(f"{task.name} added as task number {num_tasks}, with interval {task.interval}")
        else:
            _dbg_raise("Task not added due to max number of tasks")


    @staticmethod
    def __remove_task(task) -> None:
        """
        Removes the task from the list of tasks to be executed by the task manager.
        :param task: Task: The `Task` instance to be removed.
        :return: None
        """
        _tasks.remove(task)

    def reset_timer(self) -> None:
        """
        Resets the tasks timer to `Task.interval`
        :return: None
        """
        self.timer = self.interval

    def __del__(self) -> None:
        self.__remove_task(self)

def add_task(task_name:str, interval_ms:int, callback):
    return Task(task_name, interval_ms, callback)

def remove_task(task:Task=None, task_name:str=None, task_num:int=None):
    """
    Removes a task from the execution list.
    :param task: Task|None: The `Task` instance to be removed.
    :param task_name: str|None: The name of the `Task` instance to be removed.
    :param task_num: int|None : The enumeration of the task to be removed. (This can be accessed with `Task.num`)
    :return: None
    """
    if task_name:
        task = [t for t in _tasks if t.name == task_name][0]
        if not task:
            _dbg_raise(f"No task with name '{task_name}'")
            return
    elif task_num:
        task = [t for t in _tasks if t.num == task_num][0]
        if not task:
            _dbg_raise(f"No task with num '{task_num}'")
            return
    if task:
        task.__del__()

def __update_isr(*_):
    """
    This function is called by the timer, and updates the time on all tasks.
    """
    for i, task in enumerate(_tasks):
        if task.timer > 0:
            task.timer -= _timer_interval_ms

def cycle_tasks():
    """
    Runs the callback of each task, if the task timer has run out
    :return: None
    """
    for task in _tasks:
        task.__run()


def start_timer(period:int=None, mode:int=Timer.PERIODIC):
    """
    Sets the timer frequency and starts the timer.
    :param freq: int: The frequency [Hz] of the timer.
        Defaults to the interval of the timer * 1000
    :param mode: int: The mode of the timer. One of Timer.PERIODIC or Timer.ONESHOT.
        Default: Timer.PERIODIC
    :return: None
    """
    _timer.deinit()
    if period:
        global _timer_interval_ms
        _timer_interval_ms = period

    _timer.init(period=_timer_interval_ms, mode=mode, callback=__update_isr)


def run_main_loop(freq:int=1):
    """
    Starts the task manager main loop, which runs a timer, that updates the countdown on each task.
    Alongside this, a while loop is run, that runs the callbacks in the tasks.
    IMPORTANT: This function is blocking! So when this runs, nothing else will run!
    :param freq: int: The frequency [Hz] of the timer.
    :return: None
    """
    # TODO: Make a non-blocking option
    start_timer(freq)
    try:
        while True:
            cycle_tasks()
    finally:
        _timer.deinit()
