from telegram import Bot
import asyncio
import telegram_bot.config as config

bot = Bot(config.TELEGRAM_TOKEN)

def __await(fut):
    asyncio.get_event_loop().run_until_complete(fut)

# wrapper around telegram API that also makes it sync so calling it
# does not have to deal with async
def message(text, silent=None):
    __await(bot.send_message(chat_id=config.CHAT_ID, text=text, disable_notification=silent))

def set_typing():
    __await(bot.send_chat_action(chat_id=config.CHAT_ID, action='typing'))
