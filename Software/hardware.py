from enum import auto, Enum
import config
import pigpio  # http://abyz.me.uk/rpi/pigpio/


def endstop_unlocked_reached():
    return __pi.read(config.SW_MWO) == 0


def endstop_locked_reached():
    return __pi.read(config.SW_MWC) == 0


def window_open():
    return __pi.read(config.SW_WIN) == 0


# Connect to pigpiod daemon
__pi = pigpio.pi()


def setup():
    # Set up pins
    __pi.set_mode(config.DIR, pigpio.OUTPUT)
    __pi.set_mode(config.STEP, pigpio.OUTPUT)
    __pi.set_mode(config.SLEEP, pigpio.OUTPUT)
    __pi.set_mode(config.ENABLE, pigpio.OUTPUT)
    __pi.set_mode(config.LED_CLOSED, pigpio.OUTPUT)
    __pi.set_mode(config.LED_MOVING, pigpio.OUTPUT)
    __pi.set_mode(config.LED_OPEN, pigpio.OUTPUT)
    __pi.set_mode(config.SW_MWO, pigpio.INPUT)
    __pi.set_mode(config.SW_MWC, pigpio.INPUT)
    __pi.set_mode(config.SW_WIN, pigpio.INPUT)

    # Set up input switches
    __pi.set_pull_up_down(config.SW_MWO, pigpio.PUD_DOWN)
    __pi.set_pull_up_down(config.SW_MWC, pigpio.PUD_DOWN)
    __pi.set_pull_up_down(config.SW_WIN, pigpio.PUD_DOWN)


# enable Polulu driver (pass false, to disable)
def enable_motor(state: bool = True):
    __pi.write(config.SLEEP, state)
    __pi.write(config.ENABLE, not state)
    __pi.hardware_PWM(config.STEP, config.MOTOR_FREQ, config.MOTOR_DUTY if state else 0)


def set_direction(direction: bool):
    __pi.write(config.DIR, direction)


class LedStatus(Enum):
    LOCKED = auto()
    MOVING = auto()
    OPEN = auto()
    OFF = auto()


def show_status(status: LedStatus):
    # first turn everything off
    __pi.write(config.LED_OPEN, 0)
    __pi.write(config.LED_CLOSED, 0)
    __pi.set_PWM_dutycycle(config.LED_MOVING, 0)

    # then selectively turn back on
    match status:
        case LedStatus.LOCKED:
            __pi.write(config.LED_CLOSED, 1)
        case LedStatus.MOVING:
            __pi.set_PWM_frequency(config.LED_MOVING, 0)
            __pi.set_PWM_dutycycle(config.LED_MOVING, 64)
        case LedStatus.OPEN:
            __pi.write(config.LED_OPEN, 1)
        case LedStatus.OFF:
            pass


def stop():
    enable_motor(False)
    show_status(LedStatus.OFF)
    __pi.stop()
