# This file is not in the rfid/ subdirectory because it needs to import
# modules from the top level directory.
import asyncio
import queue
import time
import config
import rfid.cards_sqlite
from rfid.SimpleMFRC522 import SimpleMFRC522
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
        self.reader = SimpleMFRC522()

    def listen(self):
        # separate thread needs to have a separate event loop for telegram sending
        asyncio.set_event_loop(asyncio.new_event_loop())
        # only create cards here because sqlite3 is not happy being used across different threads
        self.cards = rfid.cards_sqlite.Cards(config.SQLITE_CARDS_PATH)

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
                tcp_client.broadcast(text)

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
            comment = comment or f"RFID card {id}"

            config.set_ready(False)

            if res == rfid.cards_sqlite.CardStatus.OK:
                self.reader_attempts = 0
                if tcp_client.request_open(comment):
                    config.set_ready(True)
                    config.blink_ready()
            elif res == rfid.cards_sqlite.CardStatus.INVALID:
                tcp_client.broadcast("RFID read card with unexpected data " + comment)
            elif res == rfid.cards_sqlite.CardStatus.UNKNOWN:
                tcp_client.broadcast("RFID read invalid card")
            elif res == rfid.cards_sqlite.CardStatus.EXPIRED:
                tcp_client.broadcast("RFID read expired card " + comment)

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
        tcp_client.broadcast("present card to RFID reader for creating")

        timeout = time.monotonic() + 60  # now + 60s
        uid = None
        while uid is None and timeout > time.monotonic():
            uid = self.reader.read_id_no_block()

        if uid is None:
            # must have run into the timeout
            tcp_client.broadcast("no card read, aborting...")
            # wait before trying to read again, maybe they just got to the reader
            # and this should not count as an invalid read
            time.sleep(5)
            return

        id = self.reader.read_id()
        data = self.cards.create_card(id, expires, comment)
        if data is None:
            tcp_client.broadcast("card not created: already exists")
            return

        written_id, _ = self.reader.write(data)
        if id == written_id:
            expires_txt = "never"
            if expires is not None:
                expires_txt = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(expires))
            tcp_client.broadcast(f"card {id} created: {comment}\nexpires {expires_txt}")
        else:
            self.cards.revoke_card(id)
            tcp_client.broadcast("card not created: error writing")

    def _command_list(self):
        cards_list = self.cards.cards()
        text = f"{len(cards_list)} RFID card(s)\n"
        for id, expired, expiry, comment in cards_list:
            text += f"{id}: {comment} ("
            if expired:
                text += f"has expired {expiry}"
            else:
                text += f"will expire {expiry}"
            text += ")\n"

        # use `strip` to remove final newline
        tcp_client.broadcast(text.strip())

    def _command_expiry(self, id: int, expires: float | None):
        if self.cards.set_card_expiry(id, expires):
            expires_txt = "never"
            if expires is not None:
                expires_txt = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(expires))
            comment = self.cards.get_card_comment(id)
            tcp_client.broadcast(f"card expiry changed: {comment}\nnew expiry: {expires_txt}")
        else:
            tcp_client.broadcast("unknown card")

    def _command_revoke(self, id):
        comment = self.cards.get_card_comment(id)
        if self.cards.revoke_card(id):
            tcp_client.broadcast(f"revoked card: {comment}")
        else:
            tcp_client.broadcast("unknown card")

    def _command_toggle(self):
        self.reader_disabled = not self.reader_disabled

        if self.reader_disabled:
            self.reader.READER.AntennaOff()
            config.set_ready(False)
            tcp_client.broadcast("reader disabled")
        else:
            self.reader.READER.AntennaOn()
            config.set_ready(True)
            self.reader_attempts = 0
            self.reader_timeout = None
            self.attempts_timeout = None
            tcp_client.broadcast("reader enabled and timeouts reset")
