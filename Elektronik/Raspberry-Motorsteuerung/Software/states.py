from enum import Enum

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
    state = CLOSING_HALTED

# adds State class members to global variables
globals().update(State.__members__)


# entering states
def opening():
    # set state to OPENING
    # set direction to open
    # enable motor
    # send Telegram message "opening"
    # set LED_CLOSED low
    # set LED_MOVING high
    pass

def opening_halted():
    # disable motor
    # set LED_MOVING blinking
    pass
    
def opening_halted_timeout():
    # send Telegram error message
    pass

def unlocked():
    # set LED_OPEN high
    # set LED_MOVING low
    pass

def closing_halted():
    # disable motor
    # set LED_MOVING blinking
    pass

def closing_halted_timeout():
    # send Telegram error message
    pass
    
def closing():
    # set direction to closing
    # enable motor
    # set LED_MOVING high
    pass

def locked():
    pass
    # disable motor

