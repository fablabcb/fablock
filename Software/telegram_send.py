from telegram import Bot
import asyncio
import secrets

bot = Bot(secrets.TELEGRAM_TOKEN)

# wrapper around telegram API that also makes it sync so calling it
# does not have to deal with async
def message(text, silent=None):
    asyncio.get_event_loop().run_until_complete(
        bot.send_message(chat_id=secrets.CHAT_ID, text=text, disable_notification=silent)
    )
