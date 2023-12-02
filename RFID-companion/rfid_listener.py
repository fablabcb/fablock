# This file is not in the rfid/ subdirectory because it needs to import
# modules from the top level directory.
import asyncio
import queue
import time
import config
import rfid.cards_sqlite
from rfid.SimpleMFRC522 import SimpleMFRC522
from telegram_bot.send import message

cards = None
reader = None

reader_disabled = False
# set by code whenever an invalid read is made
reader_attempts = 0
# set "automatically" by the reader handler
reader_timeout = None
# time at which `reader_attempts` should be reset to zero
attempts_timeout = None

def listen(command_queue):
    global cards, reader

    # separate thread needs to have a separate event loop for telegram sending
    asyncio.set_event_loop(asyncio.new_event_loop())

    cards = rfid.cards_sqlite.Cards(config.SQLITE_CARDS_PATH)
    reader = SimpleMFRC522()

    # main loop taking care of both the card reader itself
    # as well as any commands for managing the card database
    while True:
        handle_reader()
        handle_commands(command_queue)

        # check for any expired cards for which no notification has been sent yet
        text = ''
        for id, comment in cards.expired_cards():
            text += f'card {id} has expired: {comment}'
        if text != '':
            message(text, silent=True)

        time.sleep(.1)

def handle_reader():
    global attempts_timeout, reader_timeout, reader_attempts

    # first check whether we should not enable the reader
    # otherwise don't do anything else
    if reader_disabled:
        return
    if not reader_timeout is None:
        if reader_timeout > time.monotonic():
            # timeout has not passed yet
            return
        else:
            # timeout has ended
            reader.READER.AntennaOn()
            config.set_ready(True)
            reader_timeout = None
            attempts_timeout = time.monotonic() + 15 * 2 ** reader_attempts

    if not attempts_timeout is None and attempts_timeout <= time.monotonic():
        # attempts reset timeout has ended
        reader_attempts = 0
        attempts_timeout = None

    # try reading a card
    uid, data = reader.read_no_block()
    if not uid is None:
        id = reader.uid_to_num(uid)
        res, comment = cards.check_card(id, data)

        if res == cards.E_OK:
            message("read card: " + comment)
            # the open command is sent immediately because the opening
            # process takes some time so it will allow enough time for the
            # person to walk over to the other window
            message("/open", silent=True)
            reader_attempts = 0
        elif res == cards.E_UNKNOWN or res == cards.E_INVALID:
            message("read invalid card")
        elif res == cards.E_EXPIRED:
            message("read expired card " + comment)

        reader_attempts += 1
        reader_timeout = time.monotonic() + 15 * 2 ** reader_attempts
        reader.READER.AntennaOff()
        config.set_ready(False)

def handle_commands(command_queue):
    command = None
    try:
        # check for external commands
        command = command_queue.get_nowait()
    except queue.Empty:
        return

    if command == 'create':
        expires, comment = command_queue.get(), command_queue.get()
        command_create(expires, comment)
    elif command == 'list':
        command_list()
    elif command == 'expiry':
        id, expires = command_queue.get(), command_queue.get()
        command_expiry(id, expires)
    elif command == 'revoke':
        id = command_queue.get()
        command_revoke(id)
    elif command == 'toggle':
        command_toggle()

def command_create(expires, comment):
    global cards, reader

    message('present card to reader for creating', silent=True)

    timeout = time.monotonic() + 60 # now + 60s
    uid = None
    while uid is None and timeout > time.monotonic():
        uid = reader.read_id_no_block()

    if uid is None:
        # must have run into the timeout
        message('no card read, aborting...', silent=True)
        # wait before trying to read again, maybe they just got to the reader
        # and this should not count as an invalid read
        time.sleep(5)
        return

    id = reader.read_id()
    data = cards.create_card(id, expires, comment)
    if data is None:
        message('card not created: already exists', silent=True)
        return

    written_id, _ = reader.write(data)
    if id == written_id:
        expires_txt = 'never'
        if expires is not None:
            expires_txt = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(expires))
        message(f'card created: {comment}\nexpires {expires_txt}')
    else:
        cards.revoke_card(id)
        message('card not created: error writing', silent=True)

def command_list():
    global cards

    cards_list = cards.cards()
    text = f'{len(cards_list)} card(s)\n'
    for id, expired, expiry, comment in cards_list:
        text += f'{id}: {comment} ('
        if expired:
            text += f'has expired {expiry}'
        else:
            text += f'will expire {expiry}'
        text += ')\n'

    # use `strip` to remove final newline
    message(text.strip(), silent=True)

def command_expiry(id, expires):
    global cards
    if cards.set_card_expiry(id, expires):
        expires_txt = 'never'
        if expires is not None:
            expires_txt = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(expires))
        comment = cards.get_card_comment(id)
        message(f'card expiry changed: {comment}\nnew expiry: {expires_txt}')
    else:
        message('unknown card', silent=True)

def command_revoke(id):
    global cards
    comment = cards.get_card_comment(id)
    if cards.revoke_card(id):
        message(f'revoked card: {comment}')
    else:
        message('unknown card', silent=True)

def command_toggle():
    global reader_disableds
    reader_disabled = not reader_disabled

    if reader_disabled:
        reader.READER.AntennaOff()
        config.set_ready(False)
        message('reader disabled')
    else:
        reader.READER.AntennaOn()
        config.set_ready(True)
        reader_attempts = 0
        reader_timeout = None
        attempts_timeout = None
        message('reader enabled and timeouts reset')
