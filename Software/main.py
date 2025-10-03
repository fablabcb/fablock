import logging
import config
import states
import threading
import handlers.telegram_handler, handlers.tcp_handler

config.setup()

ingress_handlers: list[handlers.Handler] = [handlers.telegram_handler.TelegramHandler()]

if config.NETWORKING_ENABLED:
    ingress_handlers.append(handlers.tcp_handler.TcpHandler())


def request_open(name: str) -> bool:
    try:
        for handler in ingress_handlers:
            handler.broadcast(f"opening for {name}", critical=True)
    except RuntimeError:
        logging.error("unlocking failed because message could not be sent")
        return False  # don't unlock if this message could not be sent

    return states.unlock()


def broadcast(message: str):
    for handler in ingress_handlers:
        try:
            handler.broadcast(message)
        except:
            pass


for handler in ingress_handlers:
    threading.Thread(target=handler.listen, args=[request_open], daemon=True).start()

try:
    # enter initial state
    state_machine = states.StateMachine(broadcast)
    state_machine.run()
except KeyboardInterrupt:
    print("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_motor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 0)
    config.blink_LED(config.LED_MOVING, False)
    config.pi.stop()
