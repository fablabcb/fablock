import states
import config

globals().update(states.State.__members__)

def telegram_callback():
    if config.state==LOCKED:
        enter_opening()

def telegram_setup(callback):
    pass
