import logging

# set debug level for all modules
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING) # do not log every telegram polling request
# set debug level for states in states.py

NETWORKING_ENABLED = True
NETWORKING_PORT = 55555
TLS_SERVER_CERT_PATH = "/home/pi/server.crt"
TLS_SERVER_KEY_PATH = "/home/pi/server.key"
TLS_CLIENT_CERT_PATH = "/home/pi/client.crt"

OPENING = False
CLOSING = not OPENING

## Pin Numbering Scheme: BCM

# motor driver
DIR = 5 # Direction GPIO Pin
STEP = 12 # Step GPIO Pin
SLEEP = 13 # 0 for sleep
ENABLE = 19 # 0 for enable
MOTOR_FREQ = 500 # 500 pulses per second (<= 1000 Hz is good for our slim stepper motor)
MOTOR_DUTY = 128 # 128 is 50% of 256 (50% off time)

UNLOCKED_TIMEOUT = 12
MOVING_HALTED_TIMEOUT = 12

# LEDs
LED_OPEN = 4
LED_MOVING = 14
LED_CLOSED = 15

# input switches
# push open type (low if pushed, normally closed NC)
SW_LIMIT_OPEN = 27 # window handle in unlocked position (stop motor if low, if switch is pressed)
SW_LIMIT_CLOSED = 22 # window handle in locked position (stop motor if low, if switch is pressed)

# push type (high if pushed, normally open NO)
SW_WINDOW_OPEN = 26 # window open (stop motor if low, if switch is not pressed)
