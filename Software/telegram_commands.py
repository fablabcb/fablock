from datetime import datetime
from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram_send import message_async
import logging
import asyncio
import secrets
import states

application = None
OLD_MESSAGE_TIMEOUT = 30 # seconds

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("callback for /start")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(update.effective_chat.id))

async def open_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.debug("callback for /open")

    # get the current time in the same time zone as the server's sent date
    now = datetime.now(update.effective_message.date.tzinfo)
    if (now - update.effective_message.date).total_seconds() > OLD_MESSAGE_TIMEOUT:
        logging.warning("ignored outdated message")
        return

    if update.effective_chat.id == secrets.CHAT_ID:
        try:
            username = update.message.from_user.full_name
            await message_async(f"unlocking for {username}", critical=True)
        except RuntimeError:
            logging.error("unlocking failed because message could not be sent")
            return # don't unlock if this message could not be sent

        try:
            states.unlock()
        except ValueError:
            await message_async("already busy")
    else:
        logging.warning("not authorized: " + update.effective_chat.username)
        try:
            # not using message_async because this should not be sent to the configured group
            await context.bot.send_message(chat_id=update.effective_chat.id, text="not authorized")
        except:
            pass # don't care if this fails

def listen() -> None:
    global application

    application = ApplicationBuilder().token(secrets.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start_callback))
    application.add_handler(CommandHandler('open', open_callback))

    asyncio.get_event_loop().run_until_complete(application.bot.set_my_commands(
        [
            # /start is not documented because it is not intended to be used generally
            #BotCommand('start', 'retrieve chat ID'),
            BotCommand('open', 'open fablock'),
        ],
        BotCommandScopeChat(secrets.CHAT_ID)
    ))

    application.run_polling()
