import config
import telegram_bot.commands
import rfid_listener
import threading
import queue
import tcp_client

config.setup()
tcp_client.connect()

rfid_command_queue = queue.SimpleQueue()

rfid = rfid_listener.RfidListener(rfid_command_queue)
telegram = telegram_bot.commands.TelegramListener(rfid_command_queue)

# start RFID management in a separate thread
threading.Thread(target=rfid.listen, daemon=True).start()

try:
    telegram.listen()
except KeyboardInterrupt:
    print("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    config.enable_rfid(False)
    config.pi.stop()
