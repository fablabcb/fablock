from enum import Enum
import time
import config
from telegram_send import message, set_typing
import logging

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)


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


# adds State class members to global variables
globals().update(State.__members__)



# entering states
def enter_unlocked():
    logger.debug("entering unlocked")
    config.state=UNLOCKED
    config.enter_time = time.perf_counter()
    config.enable_motor(False)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.write(config.LED_CLOSED, 0)
    config.pi.write(config.LED_OPEN, 1)
    message("\U0001F7E2 window open", silent=True)

def leave_unlocked():
    if time.perf_counter() > config.enter_time + config.UNLOCKED_TIMEOUT or config.window_open(): 
        enter_closing_halted()

def enter_opening():
    config.state=OPENING
    logger.debug("entering opening")
    config.set_direction(config.OPENING)
    config.enable_motor(True)
    config.pi.write(config.LED_CLOSED, 1)
    config.pi.write(config.LED_OPEN, 0)
    config.blink_LED(config.LED_MOVING)

def leave_opening():
    if config.window_open():
       enter_opening_halted()
    elif config.endstop_unlocked_reached():
       enter_unlocked()

def enter_opening_halted():
    logger.debug("entering opening_halted")
    config.enter_time = time.perf_counter()
    config.state=OPENING_HALTED
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 1)
    config.blink_LED(config.LED_MOVING, False)

def leave_opening_halted():
    if time.perf_counter() > config.enter_time + config.MOVING_HALTED_TIMEOUT:
        enter_opening_halted_timeout()
    elif not config.window_open():
        enter_opening()

def enter_opening_halted_timeout():
    logger.debug("entering opening_halted_timeout")
    msg = "\U0001F479 Error: tried to open for more than " + str(config.MOVING_HALTED_TIMEOUT/60) + "minutes!"
    logger.warning(msg)
    message(msg)
    enter_opening_halted()

def enter_closing_halted():
    logger.debug("entering closing_halted")
    config.enter_time = time.perf_counter()
    config.state=CLOSING_HALTED
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 1)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING, False)

def leave_closing_halted():
    if time.perf_counter() > config.enter_time + config.MOVING_HALTED_TIMEOUT:
        enter_closing_halted_timeout()
    elif not config.window_open():
        enter_closing()

def enter_closing_halted_timeout():
    logger.debug("entering closing_halted_timeout")
    msg = "\U0001F479 Error: tried to close for more than " + str(config.MOVING_HALTED_TIMEOUT/60) + "minutes!"
    logger.warning(msg)
    message(msg)
    enter_closing_halted()

def enter_closing():
    config.state=CLOSING
    logger.debug("entering closing")
    config.set_direction(config.CLOSING)
    config.enable_motor(True)
    config.pi.write(config.LED_OPEN, 1)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING)

def leave_closing():
    if config.window_open():
       enter_closing_halted()
    elif config.endstop_locked_reached():
       enter_locked()

def enter_locked():
    logger.debug("entering locked")
    config.state=LOCKED
    config.enable_motor(False)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 1)
    message("\U0001F512 window locked", silent=True)

def leave_locked():
    if config.state != LOCKED:
        raise ValueError("not in locked state")
    set_typing()
    enter_opening_halted()
