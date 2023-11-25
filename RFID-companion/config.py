import pigpio # http://abyz.me.uk/rpi/pigpio/
import logging

# set debug level for all modules
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)
# set debug level for states in states.py

SQLITE_CARDS_PATH = "cards.db"

enter_time = 0.0
state = 5

## Pin Numbering Scheme: BCM

LED_READY = 24

# pins 8, 9, 10, 11 are used up by the hardware SPI bus
# an additional pin is needed to send reset to the MFRC522 chip
RFID_RST = 25

# Connect to pigpiod daemon
pi = pigpio.pi()

def setup():
    # Set up pins
    pi.set_mode(RFID_RST, pigpio.OUTPUT)
    pi.set_mode(LED_READY, pigpio.OUTPUT)

    enable_rfid()
    set_ready()

def enable_rfid(on=True):
    pi.write(RFID_RST, on)

def set_ready(on=True):
    pi.write(LED_READY, on)
