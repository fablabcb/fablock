from collections.abc import Callable
from enum import Enum
import time
import config
import hardware
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
    # waiting for Telegram open command
    LOCKED = 8


class StateMachine:
    state: State = State.CLOSING_HALTED
    enter_time: float = 0.0
    message: Callable[[str], None]

    def __init__(self, message):
        self.message = message
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
        hardware.enable_motor(False)
        hardware.show_status(hardware.LedStatus.OPEN)
        self.message("\U0001f7e2 window open")

    def leave_unlocked(self):
        if (
            time.perf_counter() > self.enter_time + config.UNLOCKED_TIMEOUT
            or hardware.window_open()
        ):
            self.enter_closing_halted()

    def enter_opening(self):
        self.state = State.OPENING
        logger.debug("entering opening")
        hardware.set_direction(config.OPENING)
        hardware.enable_motor(True)
        hardware.show_status(hardware.LedStatus.MOVING)

    def leave_opening(self):
        if hardware.window_open():
            self.enter_opening_halted()
        elif hardware.endstop_unlocked_reached():
            self.enter_unlocked()

    def enter_opening_halted(self):
        logger.debug("entering opening_halted")
        self.enter_time = time.perf_counter()
        self.state = State.OPENING_HALTED
        hardware.enable_motor(False)

    def leave_opening_halted(self):
        if time.perf_counter() > self.enter_time + config.MOVING_HALTED_TIMEOUT:
            self.enter_opening_halted_timeout()
        elif not hardware.window_open():
            self.enter_opening()

    def enter_opening_halted_timeout(self):
        logger.debug("entering opening_halted_timeout")
        msg = (
            "\U0001f479 Error: tried to open for more than "
            + str(config.MOVING_HALTED_TIMEOUT / 60)
            + "minutes!"
        )
        logger.warning(msg)
        self.message(msg)
        self.enter_opening_halted()

    def enter_closing_halted(self):
        logger.debug("entering closing_halted")
        self.enter_time = time.perf_counter()
        self.state = State.CLOSING_HALTED
        hardware.enable_motor(False)

    def leave_closing_halted(self):
        if time.perf_counter() > self.enter_time + config.MOVING_HALTED_TIMEOUT:
            self.enter_closing_halted_timeout()
        elif not hardware.window_open():
            self.enter_closing()

    def enter_closing_halted_timeout(self):
        logger.debug("entering closing_halted_timeout")
        msg = (
            "\U0001f479 Error: tried to close for more than "
            + str(config.MOVING_HALTED_TIMEOUT / 60)
            + "minutes!"
        )
        logger.warning(msg)
        self.message(msg)
        self.enter_closing_halted()

    def enter_closing(self):
        self.state = State.CLOSING
        logger.debug("entering closing")
        hardware.set_direction(config.CLOSING)
        hardware.enable_motor(True)
        hardware.show_status(hardware.LedStatus.MOVING)

    def leave_closing(self):
        if hardware.window_open():
            self.enter_closing_halted()
        elif hardware.endstop_locked_reached():
            self.enter_locked()

    def enter_locked(self):
        logger.debug("entering locked")
        self.state = State.LOCKED
        hardware.enable_motor(False)
        hardware.show_status(hardware.LedStatus.LOCKED)
        self.message("\U0001f512 window locked")
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
