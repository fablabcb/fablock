from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import states
import config
import secrets

#globals().update(State.__members__)
update = None
context = None
updater = None

def telegram_callback(u, c):
    global update, context
    print("telegram callback")
    
    if u.effective_chat.id == secrets.CHAT_ID:
        if config.state==states.State.LOCKED:
            update = u
            context = c
            states.enter_opening_halted()
        else:
            message("lock is already busy")

    else:
        message("not authorized", u, c)
    
    

def message(text, u=None, c=None):
    # no u and c given: use the global ones
    if u == None:
        u = update
    if c == None:
        c = context
    
    # if global update and context are also None: cant send messages
    if u is None or c is None:
        return
    
    c.bot.send_message(chat_id=u.effective_chat.id, text=text)

def telegram_setup():
    global updater
    updater = Updater(token=secrets.TELEGRAM_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


    dispatcher.add_handler(CommandHandler('open', telegram_callback))

    updater.start_polling()

