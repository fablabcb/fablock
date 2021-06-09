from time import sleep

# http://abyz.me.uk/rpi/pigpio/
import pigpio

enter_time = 0.0
state = 5
debug = True

## Pin Numbering Scheme: BCM

# motor driver
DIR = 5 # Direction GPIO Pin
STEP = 12 # Step GPIO Pin
SLEEP = 13 # 0 for sleep
ENABLE = 19 # 0 for enable
MOTOR_FREQ = 600 # 500 pulses per second (<= 1000 Hz is good for our slim stepper motor)
MOTOR_DUTY = 128 # 128 is 50% of 256 (50% off time)

OPENING = 1 # TODO check if direction is mechanically opening
CLOSING = 0 

UNLOCKED_TIMEOUT = 10 # TODO längeren Timeout einstellen
MOVING_HALTED_TIMEOUT = 10 # TODO

# LEDs
LED_OPEN = 4
LED_MOVING = 14
LED_CLOSED = 15

# input switches
# push open type (low if pushed, normally closed NC)
# MWO/C ... Motor Window Open/Closed
SW_MWO = 27 # window handle in unlocked position (stop motor if low, if switch is pressed)
SW_MWC = 22 # window handle in locked position (stop motor if low, if switch is pressed)

def endstop_unlocked_reached():
    return pi.read(SW_MWO) == 0
    
def endstop_locked_reached():
    return pi.read(SW_MWC) == 0
    
# TODO determine whether key is retained in open or closed state
SW_KEY = 17 # key switch

# push type (high if pushed, normally open NO)
SW_WIN = 26 # window open (stop motor if low, if switch is not pressed)
SW_WIN_OPEN = 0
SW_WIN_CLOSED = 1
def window_open():
    return pi.read(SW_WIN) == 0


# future external signals
SESAME_OPEN    = 16
SESAME_OPENING = 21
SESAME_CLOSING = 20

# Connect to pigpiod daemon
pi = pigpio.pi()

def setup():
    # Set up pins
    pi.set_mode(DIR, pigpio.OUTPUT)
    pi.set_mode(STEP, pigpio.OUTPUT)
    pi.set_mode(SLEEP, pigpio.OUTPUT)
    pi.set_mode(ENABLE, pigpio.OUTPUT)
    pi.set_mode(LED_CLOSED, pigpio.OUTPUT)
    pi.set_mode(LED_MOVING, pigpio.OUTPUT)
    pi.set_mode(LED_OPEN, pigpio.OUTPUT)
    pi.set_mode(SW_MWO, pigpio.INPUT)
    pi.set_mode(SW_MWC, pigpio.INPUT)
    pi.set_mode(SW_WIN, pigpio.INPUT)
    pi.set_mode(SW_KEY, pigpio.INPUT)
    pi.set_mode(SESAME_OPEN, pigpio.OUTPUT)
    pi.set_mode(SESAME_OPENING, pigpio.OUTPUT)
    pi.set_mode(SESAME_CLOSING, pigpio.OUTPUT)

    # Set up input switches
    pi.set_pull_up_down(SW_MWO, pigpio.PUD_DOWN)
    pi.set_pull_up_down(SW_MWC, pigpio.PUD_DOWN)
    pi.set_pull_up_down(SW_WIN, pigpio.PUD_DOWN)
    pi.set_pull_up_down(SW_KEY, pigpio.PUD_DOWN)


# enable Polulu driver (pass false, to disable)
def enableMotor(state=True):
  pi.write(SLEEP, state)
  pi.write(ENABLE, not state)
  pi.hardware_PWM(STEP, MOTOR_FREQ, MOTOR_DUTY if state else 0) 

def setDirection(direction):
    pi.write(DIR, direction)

def blinkLED(LED, on=True):
    if on:
        pi.set_PWM_frequency(LED, 0)
        pi.set_PWM_dutycycle(LED, 64)
    else:
        pi.set_PWM_dutycycle(LED, 0)
        
def noop():
    pass