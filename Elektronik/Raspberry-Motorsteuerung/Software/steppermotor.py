from time import sleep
import pigpio

## TODO halting states, when f.e. closing, but window opened, should sleep motor

## Pin Numbering Scheme: BCM

# motor driver
DIR = 5 # Direction GPIO Pin
STEP = 12 # Step GPIO Pin
SLEEP = 13 # 0 for sleep
ENABLE = 19 # 0 for enable

# LEDs
LED_OPEN = 4
LED_MOVING = 14
LED_CLOSED = 15

# input switches
# push open type (low if pushed, normally closed NC)
# MWO/C ... Motor Window Open/Closed
SW_MWO = 27 # window handle in unlocked position (stop motor if low, if switch is pressed)
SW_MWC = 22 # window handle in locked position (stop motor if low, if switch is pressed)

# TODO determine whether key is retained in open or closed state
SW_KEY = 17 # key switch

# push type (high if pushed, normally open NO)d
SW_WIN = 26 # window open (stop motor if low, if switch is not pressed)

# future external signals
SESAME_OPEN    = 16
SESAME_OPENING = 21
SESAME_CLOSING = 20

# Connect to pigpiod daemon
pi = pigpio.pi()

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

# Set duty cycle and frequency
pi.set_PWM_dutycycle(STEP, 128)  # PWM 1/2 On 1/2 Off
pi.set_PWM_frequency(STEP, 600)  # 500 pulses per second (<= 1000 Hz is good for our slim stepper motor)

# enable Polulu driver (pass false, to disable)
def enableMotor(state=True):
  pi.write(SLEEP, state)
  pi.write(ENABLE, not state)

enableMotor()

try:
    while True:
        pi.write(DIR, pi.read(SW_WIN))  # Set direction
        sleep(.1)

except KeyboardInterrupt:
    enableMotor(False)
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    pi.set_PWM_dutycycle(STEP, 0)  # PWM off
    pi.stop()
