from telegram import Bot
from telegram.error import TimedOut
import asyncio
import logging
import secrets
import time

bot = Bot(secrets.TELEGRAM_TOKEN)

def __await(fut):
    asyncio.get_event_loop().run_until_complete(fut)

# wrapper around telegram API that incorporates retries
# because in the past we have had problems with messages failing to send
# and the exceptions messing up everything
async def message_async(text, silent=None, critical=False):
    # (re)try up to 5 times if necessary
    for attempt in range(5):
        try:
            await bot.send_message(chat_id=secrets.CHAT_ID, text=text, disable_notification=silent)
            return
        except TimedOut:
            logging.warning(f"connection timeout, attempt={attempt}")
            time.sleep(1)

    logging.error(f"sending failed after retries, critical={critical}")
    if critical:
        raise RuntimeError("message sending timed out")

# wrapper around telegram API that also makes it sync so calling it
# does not have to deal with async
def message(text, silent=None, critical=False):
    __await(message_async(text, silent, critical))
