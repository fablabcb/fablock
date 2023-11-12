import time
import sqlite3
import secrets
import marshal

class Cards:
    # constants used to signal the result of validating a card
    E_OK = 0
    E_UNKNOWN = 1
    E_EXPIRED = 2
    E_INVALID = 3

    con = None

    def __init__(self, cards_path):
        self.con = sqlite3.connect(cards_path)

        self.con.execute("""
            CREATE TABLE IF NOT EXISTS card (
                id INT,
                data BLOB NOT NULL,
                expires INT DEFAULT NULL,
                expire_notif INT NOT NULL DEFAULT 0,
                comment TEXT,
                PRIMARY KEY(id)
            );
	    """)
        self.con.commit()

    # Check whether a card is valid for entry.
    #
    # Returns a tuple:
    # - status
    # - comment of the card if known
    #
    # Returns status E_OK only if access should be granted.
    def check_card(self, id, data):
        data_ser = marshal.dumps(data)

        res = self.con.execute('SELECT expires, data, comment FROM card WHERE id = ?', [id]).fetchone()
        if res is None:
            return self.E_UNKNOWN, None
        elif res[1] != data_ser:
            return self.E_INVALID, res[2]
        elif res[0] is None:
            # this card never expires
            return self.E_OK, res[2]
        elif res[0] <= time.time():
            return self.E_EXPIRED, res[2]
        else:
            return self.E_OK, res[2]

    # Create a new card in the database.
    #
    # Returns the generated secret data for writing to the card.
    # Returns None if a card with that id already exists.
    def create_card(self, id, expires, comment):
        data = []
        for i in range(16 * 3):
            data.append(secrets.randbits(8))

        data_ser = marshal.dumps(data)

        try:
            self.con.execute('INSERT INTO card (id, data, expires, comment) VALUES (?, ?, ?, ?);', [id, data_ser, expires, comment])
            self.con.commit()
            return data
        except sqlite3.IntegrityError: # UNIQUE constraint on card.id violated
            return None

    # Revokes a card by removing it from the database.
    #
    # Returns true only if there was a matching card that could be revoked.
    def revoke_card(self, id):
        rowcount = self.con.execute('DELETE FROM card WHERE id = ?;', [id]).rowcount
        if rowcount == 1:
            self.con.commit()
            return True
        else:
            self.con.rollback()
            return False

    # Get the comment for a given card.
    #
    # Returns None if a card with that id is not known.
    def get_card_comment(self, id):
        card = self.con.execute('SELECT comment FROM card WHERE id = ?;', [id]).fetchone()
        if card is None:
            return None
        else:
            return card[0]

    # Replace the expiry date for a given card.
    #
    # Returns True if the card was successfully extended to the given date.
    def set_card_expiry(self, id, expires):
        rowcount = self.con.execute('UPDATE card SET expiry = ? WHERE id = ?;', [expiry, id]).rowcount
        return rowcount == 1

    # Get a list of all cards.
    #
    # Returns an array of tuples, where each tuple is:
    # - serial number of the card
    # - whether the card has expired
    # - expiry date ('never' or formatted as ISO 8601)
    # - comment for the card
    def cards(self):
        cards = self.con.execute('SELECT id, expires, comment FROM card;').fetchall()

        def map_cards(row):
            expiry_str = 'never'
            expired = False

            if row[1] is not None:
                time_str = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(row[1]))
                expired = row[1] <= time.time()

            return (row[0], expired, time_str, row[2])

        return [map_cards(row) for row in cards]

    # Get a list of all newly expired cards.
    # Updates the table to note that these cards have been notified of being expired.
    #
    # Returns an array of tuples, where each tuple is:
    # - serial number of the card
    # - comment for the card
    def expired_cards(self):
        cards = self.con.execute('SELECT id, comment, expires FROM card WHERE expire_notif = 0;').fetchall()

        def map_cards(row):
            expired = False

            if row[1] is not None:
                expired = row[1] <= time.time()

            return (row[0], expired, row[2])

        cards = [(row[0], row[1]) for row in cards if row[2] <= time.time()]

        for id, comment in cards:
            self.con.execute('UPDATE card SET expire_notif = 1 WHERE id = ?', [id])
        self.con.commit()

        return cards

