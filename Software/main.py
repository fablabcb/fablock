import config
import states
import telegram_commands
import threading
import time
import tcp_server
import asyncio


def handle_lock():
    # separate thread needs separate event loop for sending
    # telegram messages
    asyncio.set_event_loop(asyncio.new_event_loop())

    while True:
        match config.state:
            case states.State.UNLOCKED:
                states.leave_unlocked()
            case states.State.OPENING_HALTED:
                states.leave_opening_halted()
            case states.State.OPENING:
                states.leave_opening()
            case states.State.CLOSING_HALTED:
                states.leave_closing_halted()
            case states.State.CLOSING:
                states.leave_closing()
            case states.State.LOCKED:
                time.sleep(1)
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
    print("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.stop()
