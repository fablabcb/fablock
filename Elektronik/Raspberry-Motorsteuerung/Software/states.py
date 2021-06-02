from enum import Enum
import time
import config


def printD(message):
    if config.debug:
        print(message)


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
    printD("entering unlocked")
    config.state=UNLOCKED
    config.enter_time = time.perf_counter()
    config.enableMotor(False)
    config.blinkLED(config.LED_MOVING, False)
    config.pi.write(config.LED_CLOSED, 0)
    config.pi.write(config.LED_OPEN, 1)
    # TODO send telegram message

def leave_unlocked():
    if time.perf_counter() > config.enter_time + config.UNLOCKED_TIMEOUT or  config.pi.read(config.SW_WIN) == 0: 
        enter_closing_halted()
        
def enter_opening():
    config.state=OPENING
    printD("entering opening")
    config.setDirection(config.OPENING)
    config.enableMotor(True)
    config.pi.write(config.LED_CLOSED, 1)
    config.pi.write(config.LED_OPEN, 0)
    config.blinkLED(config.LED_MOVING)
    # TODO send Telegram message "opening"
    
def leave_opening():
    if config.pi.read(config.SW_WIN) == 0:
       enter_opening_halted()
    elif config.pi.read(config.SW_MWO) == 0:
       enter_unlocked()

def enter_opening_halted():
    printD("entering opening_halted")
    config.enter_time = time.perf_counter()
    config.state=OPENING_HALTED
    config.enableMotor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 1)
    config.blinkLED(config.LED_MOVING, False)
    
def leave_opening_halted():
    if time.perf_counter() > config.enter_time + config.MOVING_HALTED_TIMEOUT:
        enter_opening_halted_timeout()
    elif config.pi.read(config.SW_WIN) == 1:
        enter_opening()
    
def enter_opening_halted_timeout():
    printD("entering opening_halted_timeout")
    # TODO send Telegram error message
    enter_opening_halted()

def enter_closing_halted():
    printD("entering closing_halted")
    config.enter_time = time.perf_counter()
    config.state=CLOSING_HALTED
    config.enableMotor(False)
    config.pi.write(config.LED_OPEN, 1)
    config.pi.write(config.LED_CLOSED, 0)
    config.blinkLED(config.LED_MOVING, False)
    
def leave_closing_halted():
    if time.perf_counter() > config.enter_time + config.MOVING_HALTED_TIMEOUT:
        enter_closing_halted_timeout()
    elif config.pi.read(config.SW_WIN) == 1:
        enter_closing()

def enter_closing_halted_timeout():
    printD("entering closing_halted_timeout")
    # TODO send Telegram error message
    enter_closing_halted()
    
def enter_closing():
    config.state=CLOSING
    printD("entering closing")
    config.setDirection(config.CLOSING)
    config.enableMotor(True)
    config.pi.write(config.LED_OPEN, 1)
    config.pi.write(config.LED_CLOSED, 0)
    config.blinkLED(config.LED_MOVING)
    
def leave_closing():
    if config.pi.read(config.SW_WIN) == 0:
       enter_closing_halted()
    elif config.pi.read(config.SW_MWC) == 0:
       enter_locked()

def enter_locked():
    printD("entering locked")
    config.state=LOCKED
    config.enableMotor(False)
    config.blinkLED(config.LED_MOVING, False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 1)
    # TODO send telegram message

