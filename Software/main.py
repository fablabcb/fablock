import config
import states
import api_commands
import threading
import tcp_server


def handle_lock():
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
    api_commands.listen()
except KeyboardInterrupt:
    print("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.stop()
