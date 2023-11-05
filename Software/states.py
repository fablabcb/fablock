from enum import Enum
import time
import config
import telegram_bot
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
    config.enableMotor(False)
    config.blinkLED(config.LED_MOVING, False)
    config.pi.write(config.LED_CLOSED, 0)
    config.pi.write(config.LED_OPEN, 1)

def leave_unlocked():
    if time.perf_counter() > config.enter_time + config.UNLOCKED_TIMEOUT or config.window_open(): 
        enter_closing_halted()

def enter_opening():
    config.state=OPENING
    logger.debug("entering opening")
    config.setDirection(config.OPENING)
    config.enableMotor(True)
    config.pi.write(config.LED_CLOSED, 1)
    config.pi.write(config.LED_OPEN, 0)
    config.blinkLED(config.LED_MOVING)

def leave_opening():
    if config.window_open():
       enter_opening_halted()
    elif config.endstop_unlocked_reached():
       enter_unlocked()

def enter_opening_halted():
    logger.debug("entering opening_halted")
    config.enter_time = time.perf_counter()
    config.state=OPENING_HALTED
    config.enableMotor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 1)
    config.blinkLED(config.LED_MOVING, False)

def leave_opening_halted():
    if time.perf_counter() > config.enter_time + config.MOVING_HALTED_TIMEOUT:
        enter_opening_halted_timeout()
    elif not config.window_open():
        enter_opening()

def enter_opening_halted_timeout():
    logger.debug("entering opening_halted_timeout")
    msg = "Error: tried to open for more than " + str(config.MOVING_HALTED_TIMEOUT/60) + "minutes!"
    logger.warning(msg)
    telegram_bot.message(msg)
    enter_opening_halted()

def enter_closing_halted():
    logger.debug("entering closing_halted")
    config.enter_time = time.perf_counter()
    config.state=CLOSING_HALTED
    config.enableMotor(False)
    config.pi.write(config.LED_OPEN, 1)
    config.pi.write(config.LED_CLOSED, 0)
    config.blinkLED(config.LED_MOVING, False)

def leave_closing_halted():
    if time.perf_counter() > config.enter_time + config.MOVING_HALTED_TIMEOUT:
        enter_closing_halted_timeout()
    elif not config.window_open():
        enter_closing()

def enter_closing_halted_timeout():
    logger.debug("entering closing_halted_timeout")
    msg = "Error: tried to close for more than " + str(config.MOVING_HALTED_TIMEOUT/60) + "minutes!"
    logger.warning(msg)
    telegram_bot.message(msg)
    enter_closing_halted()

def enter_closing():
    config.state=CLOSING
    logger.debug("entering closing")
    config.setDirection(config.CLOSING)
    config.enableMotor(True)
    config.pi.write(config.LED_OPEN, 1)
    config.pi.write(config.LED_CLOSED, 0)
    config.blinkLED(config.LED_MOVING)

def leave_closing():
    if config.window_open():
       enter_closing_halted()
    elif config.endstop_locked_reached():
       enter_locked()

def enter_locked():
    logger.debug("entering locked")
    config.state=LOCKED
    config.enableMotor(False)
    config.blinkLED(config.LED_MOVING, False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 1)
    telegram_bot.message("window locked")
    telegram_bot.update = None
    telegram_bot.context = None

