from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import logging
import asyncio
import threading
import secrets

application = None
open_event = None

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(update.effective_chat.id))

async def open_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.debug("telegram callback")

    if update.effective_chat.id == secrets.CHAT_ID:
        open_event.set()
    else:
        logging.warning("not authorized: " + update.effective_chat.username)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="not authorized")

def listen(_open_event: threading.Event) -> None:
    global application, open_event

    # keep track of the queue to send back stuff to the main thread
    open_event = _open_event

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
