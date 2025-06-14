import config
import states
import telegram_commands
import threading
import tcp_server
import asyncio


def handle_lock():
    # separate thread needs separate event loop for sending
    # telegram messages
    asyncio.set_event_loop(asyncio.new_event_loop())

    # enter initial state
    state_machine = states.StateMachine()

    state_machine.run()


config.setup()

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
