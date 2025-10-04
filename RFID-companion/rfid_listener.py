# This file is not in the rfid/ subdirectory because it needs to import
# modules from the top level directory.
import asyncio
import queue
import time
import config
import rfid.cards_sqlite
from rfid.SimpleMFRC522 import SimpleMFRC522
from telegram_bot.send import message
import tcp_client


class RfidListener:
    command_queue: queue.SimpleQueue

    cards: rfid.cards_sqlite.Cards
    reader: SimpleMFRC522

    reader_disabled: bool = False
    # these variables should only be set to something other than 0/None by increment_timeout
    reader_attempts: int = 0
    reader_timeout: int | None = None
    # time at which `reader_attempts` should be reset to zero
    attempts_timeout: int | None = None

    def __init__(self, command_queue: queue.SimpleQueue) -> None:
        self.command_queue = command_queue
        self.cards = rfid.cards_sqlite.Cards(config.SQLITE_CARDS_PATH)
        self.reader = SimpleMFRC522()

    def listen(self):
        # separate thread needs to have a separate event loop for telegram sending
        asyncio.set_event_loop(asyncio.new_event_loop())

        # main loop taking care of both the card reader itself
        # as well as any commands for managing the card database
        while True:
            self._handle_reader()
            self._handle_commands()

            # check for any expired cards for which no notification has been sent yet
            text = ""
            for id, comment in self.cards.expired_cards():
                text += f"card {id} has expired: {comment}"
            if text != "":
                message(text, silent=True)

            time.sleep(0.1)

    def _increment_timeout(self):
        self.reader_attempts += 1
        self.reader_timeout = time.monotonic() + 15 * 2**self.reader_attempts
        self.reader.READER.AntennaOff()

    def _handle_reader(self):
        # first check whether we should not enable the reader
        # otherwise don't do anything else
        if self.reader_disabled:
            return
        if not self.reader_timeout is None:
            if self.reader_timeout > time.monotonic():
                # timeout has not passed yet
                return
            else:
                # timeout has ended
                self.reader.READER.AntennaOn()
                config.set_ready(True)
                self.reader_timeout = None
                self.attempts_timeout = time.monotonic() + 15 * 2**self.reader_attempts

        if (
            not self.attempts_timeout is None
            and self.attempts_timeout <= time.monotonic()
        ):
            # attempts reset timeout has ended
            self.reader_attempts = 0
            self.attempts_timeout = None

        # try reading a card
        uid, data = self.reader.read_no_block()
        if not uid is None:
            id = self.reader.uid_to_num(uid)
            res, comment = self.cards.check_card(id, data)
            comment = comment or ""

            config.set_ready(False)

            if res == rfid.cards_sqlite.CardStatus.OK:
                message("read card: " + comment)
                self.reader_attempts = 0
                if tcp_client.request_open():
                    config.set_ready(True)
                    config.blink_ready()
            elif res == rfid.cards_sqlite.CardStatus.INVALID:
                message("read card with unexpected data " + comment)
            elif res == rfid.cards_sqlite.CardStatus.UNKNOWN:
                message("read invalid card")
            elif res == rfid.cards_sqlite.CardStatus.EXPIRED:
                message("read expired card " + comment)

            self._increment_timeout()

    def _handle_commands(self):
        command = None
        try:
            # check for external commands
            command = self.command_queue.get_nowait()
        except queue.Empty:
            return

        if command == "create":
            expires, comment = self.command_queue.get(), self.command_queue.get()
            config.blink_ready()
            self._command_create(expires, comment)
            # after (trying) creating a card, disable the reader
            self._increment_timeout()
            config.set_ready(False)
        elif command == "list":
            self._command_list()
        elif command == "expiry":
            id, expires = self.command_queue.get(), self.command_queue.get()
            self._command_expiry(id, expires)
        elif command == "revoke":
            id = self.command_queue.get()
            self._command_revoke(id)
        elif command == "toggle":
            self._command_toggle()

    def _command_create(self, expires: float | None, comment: str | None):
        message("present card to reader for creating", silent=True)

        timeout = time.monotonic() + 60  # now + 60s
        uid = None
        while uid is None and timeout > time.monotonic():
            uid = self.reader.read_id_no_block()

        if uid is None:
            # must have run into the timeout
            message("no card read, aborting...", silent=True)
            # wait before trying to read again, maybe they just got to the reader
            # and this should not count as an invalid read
            time.sleep(5)
            return

        id = self.reader.read_id()
        data = self.cards.create_card(id, expires, comment)
        if data is None:
            message("card not created: already exists", silent=True)
            return

        written_id, _ = self.reader.write(data)
        if id == written_id:
            expires_txt = "never"
            if expires is not None:
                expires_txt = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(expires))
            message(f"card {id} created: {comment}\nexpires {expires_txt}")
        else:
            self.cards.revoke_card(id)
            message("card not created: error writing", silent=True)

    def _command_list(self):
        cards_list = self.cards.cards()
        text = f"{len(cards_list)} card(s)\n"
        for id, expired, expiry, comment in cards_list:
            text += f"{id}: {comment} ("
            if expired:
                text += f"has expired {expiry}"
            else:
                text += f"will expire {expiry}"
            text += ")\n"

        # use `strip` to remove final newline
        message(text.strip(), silent=True)

    def _command_expiry(self, id: int, expires: float | None):
        if self.cards.set_card_expiry(id, expires):
            expires_txt = "never"
            if expires is not None:
                expires_txt = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(expires))
            comment = self.cards.get_card_comment(id)
            message(f"card expiry changed: {comment}\nnew expiry: {expires_txt}")
        else:
            message("unknown card", silent=True)

    def _command_revoke(self, id):
        comment = self.cards.get_card_comment(id)
        if self.cards.revoke_card(id):
            message(f"revoked card: {comment}")
        else:
            message("unknown card", silent=True)

    def _command_toggle(self):
        self.reader_disabled = not self.reader_disabled

        if self.reader_disabled:
            self.reader.READER.AntennaOff()
            config.set_ready(False)
            message("reader disabled")
        else:
            self.reader.READER.AntennaOn()
            config.set_ready(True)
            self.reader_attempts = 0
            self.reader_timeout = None
            self.attempts_timeout = None
            message("reader enabled and timeouts reset")
