import config
from states import *
import telegram_bot

globals().update(State.__members__)


config.setup()



telegram_bot.telegram_setup()

enter_closing_halted()

try:
    while True:
        #printD(config.state)
        cases = {
            #LOCKED: lambda: pass,
            UNLOCKED: leave_unlocked,
            OPENING_HALTED: leave_opening_halted,
            OPENING: leave_opening,
            CLOSING_HALTED: leave_closing_halted,
            CLOSING: leave_closing,
            LOCKED: config.noop
                    
        }[config.state]()
        config.sleep(.1)




except KeyboardInterrupt:
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enableMotor(False)
    config.pi.write(config.LED_OPEN, 0)
    config.pi.write(config.LED_CLOSED, 0)    
    config.blinkLED(config.LED_MOVING, False)
    config.pi.stop()
    telegram_bot.updater.stop()
