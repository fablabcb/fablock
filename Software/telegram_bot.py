from typing import Optional
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import logging
import asyncio
import states
import config
import secrets

application = None

async def open_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.debug("telegram callback")

    if update.effective_chat.id == secrets.CHAT_ID:
        if config.state==states.State.LOCKED:
            await message_async("window opening", update, context)
            states.enter_opening_halted()
        else:
            await message_async("lock is already busy", update, context)

    else:
        logging.warning("not authorized: " + update.effective_chat.username)
        await message_async("not authorized", update, context)

# sends a message. if either update or context are missing, sends to
# the configured channel by defaults
async def message_async(text: str, update: Optional[Update] = None, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
    if application is None:
        # application is not set up yet
        logging.error("tried to send message before telegram set up")
        return

    if update is None or context is None:
        # send this message in the configured channel
        await application.bot.send_message(chat_id=secrets.CHAT_ID, text=text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

# convenience wrapper to run the (async) message function in a sync environment
def message(text: str, u: Optional[Update] = None, c: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
    asyncio.get_event_loop().run_until_complete(message_async(text, u, c))

def telegram_setup() -> None:
    global application
    application = ApplicationBuilder().token(secrets.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('open', open_callback))

    application.run_polling()
