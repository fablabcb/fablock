import config
from states import *
import telegram_commands
import threading
import time
import tcp_server
import asyncio

globals().update(State.__members__)

def handle_lock():
    # separate thread needs separate event loop for sending
    # telegram messages
    asyncio.set_event_loop(asyncio.new_event_loop())

    while True:
        cases = {
            UNLOCKED: leave_unlocked,
            OPENING_HALTED: leave_opening_halted,
            OPENING: leave_opening,
            CLOSING_HALTED: leave_closing_halted,
            CLOSING: leave_closing,
            LOCKED: lambda: time.sleep(1) # try to save some energy while locked
        }[config.state]()
        time.sleep(.1)

config.setup()

# enter initial state
enter_closing_halted()

# start hardware handler in a separate thread
threading.Thread(target=handle_lock, daemon=True).start()
# start TCP handler in a separate thread
if config.NETWORKING_ENABLED:
    threading.Thread(target=tcp_server.run, daemon=True).start()

try:
    # telegram must be handled in the main thread because of some I/O
    # operations that the library does
    telegram_commands.listen()
except KeyboardInterrupt:
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.stop()
