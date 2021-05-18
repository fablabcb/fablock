from config import *
import states
import telegram

globals().update(states.State.__members__)


setup()



telegram_setup(telegram.telegram_callback)

closing_halted()

try:
    while True:
        cases = {
            LOCKED: lambda: pass
        }
        cases[state]()
        sleep(.1)




except KeyboardInterrupt:
    enableMotor(False)
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    pi.stop()
