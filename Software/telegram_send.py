from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import secrets

bot = Bot(secrets.TELEGRAM_TOKEN)

def __await(fut):
    asyncio.get_event_loop().run_until_complete(fut)

# wrapper around telegram API that also makes it sync so calling it
# does not have to deal with async
def message(text, silent=None):
    __await(bot.send_message(chat_id=secrets.CHAT_ID, text=text, disable_notification=silent, parse_mode=ParseMode.MARKDOWN_V2))
