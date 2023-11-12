import config
import telegram_bot.commands
import rfid_listener
import threading
import queue
import time
import asyncio

config.setup()

rfid_command_queue = queue.SimpleQueue()

# start RFID management in a separate thread
threading.Thread(target=rfid_listener.listen, args=(rfid_command_queue,), daemon=True).start()

try:
    telegram_bot.commands.listen(rfid_command_queue)
except KeyboardInterrupt:
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_rfid(False)
    config.pi.stop()
