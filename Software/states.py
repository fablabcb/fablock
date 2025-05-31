from enum import Enum
import time
import config
from api_commands import send_message
import logging
import threading

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

unlock_event = threading.Event()


class State(Enum):
    OPENING = 1
    OPENING_HALTED = 2
    OPENING_HALTED_TIMEOUT = 3
    UNLOCKED = 4
    CLOSING_HALTED = 5
    CLOSING_HALTED_TIMEOUT = 6
    CLOSING = 7
    # waiting for open command
    LOCKED = 8


class StateMachine:
    state: State = State.CLOSING_HALTED
    enter_time: float = 0.0

    def __init__(self):
        self.enter_closing_halted()

    def run(self):
        while True:
            match self.state:
                case State.UNLOCKED:
                    self.leave_unlocked()
                case State.OPENING_HALTED:
                    self.leave_opening_halted()
                case State.OPENING:
                    self.leave_opening()
                case State.CLOSING_HALTED:
                    self.leave_closing_halted()
                case State.CLOSING:
                    self.leave_closing()
                case State.LOCKED:
                    self.leave_locked()
            time.sleep(0.1)

    def enter_unlocked(self):
        logger.debug("entering unlocked")
        self.state = State.UNLOCKED
        self.enter_time = time.perf_counter()
        config.enable_motor(False)
        config.blink_LED(config.LED_MOVING, False)
        config.pi.write(config.LED_CLOSED, 0)
        config.pi.write(config.LED_OPEN, 1)
        send_message("\U0001f7e2 window open")

    def leave_unlocked(self):
        if (
            time.perf_counter() > self.enter_time + config.UNLOCKED_TIMEOUT
            or config.window_open()
        ):
            self.enter_closing_halted()

    def enter_opening(self):
        self.state = State.OPENING
        logger.debug("entering opening")
        config.set_direction(config.OPENING)
        config.enable_motor(True)
        config.pi.write(config.LED_CLOSED, 1)
        config.pi.write(config.LED_OPEN, 0)
        config.blink_LED(config.LED_MOVING)

    def leave_opening(self):
        if config.window_open():
            self.enter_opening_halted()
        elif config.endstop_unlocked_reached():
            self.enter_unlocked()

    def enter_opening_halted(self):
        logger.debug("entering opening_halted")
        self.enter_time = time.perf_counter()
        self.state = State.OPENING_HALTED
        config.enable_motor(False)
        config.pi.write(config.LED_OPEN, 0)
        config.pi.write(config.LED_CLOSED, 1)
        config.blink_LED(config.LED_MOVING, False)

    def leave_opening_halted(self):
        if time.perf_counter() > self.enter_time + config.MOVING_HALTED_TIMEOUT:
            self.enter_opening_halted_timeout()
        elif not config.window_open():
            self.enter_opening()

    def enter_opening_halted_timeout(self):
        logger.debug("entering opening_halted_timeout")
        msg = (
            "\U0001f479 Error: tried to open for more than "
            + str(config.MOVING_HALTED_TIMEOUT / 60)
            + "minutes!"
        )
        logger.warning(msg)
        send_message(msg)
        self.enter_opening_halted()

    def enter_closing_halted(self):
        logger.debug("entering closing_halted")
        self.enter_time = time.perf_counter()
        self.state = State.CLOSING_HALTED
        config.enable_motor(False)
        config.pi.write(config.LED_OPEN, 1)
        config.pi.write(config.LED_CLOSED, 0)
        config.blink_LED(config.LED_MOVING, False)

    def leave_closing_halted(self):
        if time.perf_counter() > self.enter_time + config.MOVING_HALTED_TIMEOUT:
            self.enter_closing_halted_timeout()
        elif not config.window_open():
            self.enter_closing()

    def enter_closing_halted_timeout(self):
        logger.debug("entering closing_halted_timeout")
        msg = (
            "\U0001f479 Error: tried to close for more than "
            + str(config.MOVING_HALTED_TIMEOUT / 60)
            + "minutes!"
        )
        logger.warning(msg)
        send_message(msg)
        self.enter_closing_halted()

    def enter_closing(self):
        self.state = State.CLOSING
        logger.debug("entering closing")
        config.set_direction(config.CLOSING)
        config.enable_motor(True)
        config.pi.write(config.LED_OPEN, 1)
        config.pi.write(config.LED_CLOSED, 0)
        config.blink_LED(config.LED_MOVING)

    def leave_closing(self):
        if config.window_open():
            self.enter_closing_halted()
        elif config.endstop_locked_reached():
            self.enter_locked()

    def enter_locked(self):
        logger.debug("entering locked")
        self.state = State.LOCKED
        config.enable_motor(False)
        config.blink_LED(config.LED_MOVING, False)
        config.pi.write(config.LED_OPEN, 0)
        config.pi.write(config.LED_CLOSED, 1)
        send_message("\U0001f512 window locked")
        unlock_event.clear()

    def leave_locked(self):
        unlock_event.wait()
        if self.state != State.LOCKED:
            raise ValueError("not in locked state")
        self.enter_opening_halted()


def unlock() -> bool:
    """
    Attempt to unlock and return success.

    If the window is already unlocked, returns `False`.
    """
    if unlock_event.is_set():
        return False
    else:
        unlock_event.set()
        return True
