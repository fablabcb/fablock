import config
from states import *
import telegram_commands
import threading

globals().update(State.__members__)

config.setup()

# start telegram in a separate thread
open_event = threading.Event()
threading.Thread(target=telegram_commands.listen, args=(open_event,), daemon=True).start()

# enter initial state
enter_closing_halted()

try:
    while True:
        cases = {
            UNLOCKED: leave_unlocked,
            OPENING_HALTED: leave_opening_halted,
            OPENING: leave_opening,
            CLOSING_HALTED: leave_closing_halted,
            CLOSING: leave_closing,
            LOCKED: lambda:
                # clear the event if it was set from a previous iteration
                open_event.clear()
                # block until an open event occurs again
                open_event.wait()
                # after blocking, transition to the next state
                leave_locked()
        }[config.state]()
        config.sleep(.1)
except KeyboardInterrupt:
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.stop()
