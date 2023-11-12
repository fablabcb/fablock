from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import logging
import asyncio
import threading
import time
import telegram_bot.config as config
import queue

application = None
rfid_command_queue = None

async def update_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.id != config.CHAT_ID:
        logging.warn("not authorized: " + update.effective_chat.username)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="not authorized")
        return False
    else:
        return True

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(update.effective_chat.id))

async def create_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="usage: /create_card <YYYY-MM-DD> <name>")
        return

    expiry = None
    try:
        expiry = time.mktime(time.strptime(context.args[0], '%Y-%m-%d'))
    except ValueError:
        print(a)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="invalid date format, use YYYY-MM-DD")
        return

    rfid_command_queue.put('create')
    rfid_command_queue.put(expiry)
    rfid_command_queue.put(" ".join(context.args[1:]))

async def cards_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return

    rfid_command_queue.put('list')

def listen(_rfid_command_queue: queue.SimpleQueue) -> None:
    global application, rfid_command_queue

    # keep track of the queue to send back stuff to the main thread
    rfid_command_queue = _rfid_command_queue

    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start_callback))
    application.add_handler(CommandHandler('create_card', create_card_callback))
    application.add_handler(CommandHandler('manage_cards', cards_callback))

    asyncio.get_event_loop().run_until_complete(application.bot.set_my_commands(
        [
            # /start is not documented because it is not intended to be used generally
            #BotCommand('start', 'retrieve chat ID'),
            BotCommand('create_card', 'create/write new RFID card'),
            BotCommand('manage_cards', 'manage RFID cards')
        ],
        BotCommandScopeChat(config.CHAT_ID)
    ))

    application.run_polling()
