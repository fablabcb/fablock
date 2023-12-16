from telegram import BotCommand, BotCommandScopeChatAdministrators, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import logging
import asyncio
import threading
import time
import telegram_bot.config as config
import queue

application = None
rfid_command_queue = None

# Returns `-1` on error or `None` if it should never expire.
# Otherwise, returns an integer representing the unix time.
def parse_expiry(text):
    if text == "never":
        return None
    else:
        try:
            return time.mktime(time.strptime(text, '%Y-%m-%d'))
        except ValueError:
            return -1

async def update_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.id != config.CHAT_ID:
        logging.warn("not authorized: " + update.effective_chat.username)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="not authorized")
        return False

    admins = await update.effective_chat.get_administrators()
    if not update.effective_user.id in [admin.user.id for admin in admins]:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="not authorized, admins only")
        return False

    return True

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(update.effective_chat.id))

async def create_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="usage: /rfid_create <YYYY-MM-DD> <name>")
        return

    expiry = parse_expiry(context.args[0])
    if expiry == -1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="invalid date format, use YYYY-MM-DD")
        return

    rfid_command_queue.put('create')
    rfid_command_queue.put(expiry)
    rfid_command_queue.put(" ".join(context.args[1:]))

async def cards_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return

    rfid_command_queue.put('list')

async def expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="usage: /rfid_expiry <id> <YYYY-MM-DD>")
        return

    # parse the card ID, it must be an integer
    id = None
    try:
        id = int(context.args[0], 10)
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="invalid id, must be an integer")
        return

    expiry = parse_expiry(context.args[1])
    if expiry == -1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="invalid date format, use YYYY-MM-DD")
        return

    rfid_command_queue.put('expiry')
    rfid_command_queue.put(id)
    rfid_command_queue.put(expiry)

async def revoke_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="usage: /rfid_revoke <id>")
        return

    # parse the card ID, it must be an integer
    id = None
    try:
        id = int(context.args[0], 10)
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="invalid id, must be an integer")
        return

    rfid_command_queue.put('revoke')
    rfid_command_queue.put(id)

async def toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await update_authorized(update, context):
        return

    rfid_command_queue.put('toggle')

def listen(_rfid_command_queue: queue.SimpleQueue) -> None:
    global application, rfid_command_queue

    # keep track of the queue to send back stuff to the main thread
    rfid_command_queue = _rfid_command_queue

    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start_callback))
    application.add_handler(CommandHandler('rfid_cards', cards_callback))
    application.add_handler(CommandHandler('rfid_create', create_card_callback))
    application.add_handler(CommandHandler('rfid_expiry', expiry_callback))
    application.add_handler(CommandHandler('rfid_revoke', revoke_callback))
    application.add_handler(CommandHandler('rfid_toggle', toggle_callback))

    asyncio.get_event_loop().run_until_complete(application.bot.set_my_commands(
        [
            # /start is not documented because it is not intended to be used generally
            #BotCommand('start', 'retrieve chat ID'),
            BotCommand('rfid_cards', 'list RFID cards'),
            BotCommand('rfid_create', 'create/write new RFID card'),
            BotCommand('rfid_expiry', 'set or remove expiry date of RFID card'),
            BotCommand('rfid_revoke', 'revoke and delete an existing RFID card'),
            BotCommand('rfid_toggle', 'enable/disable RFID reader')
        ],
        BotCommandScopeChatAdministrators(config.CHAT_ID)
    ))

    application.run_polling()
