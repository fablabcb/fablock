# Code by Simon Monk https://github.com/simonmonk/

from . import MFRC522
import logging

DEFAULT_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# compute which sector the given block is in
# ever sector consists of 4 blocks
def sectorOf(block):
    return block // 4

# compute the block number of the sector trailer
# the trailer is always the last block in the sector, each sector consists of blocks 0 to 3
def trailerBlock(sector):
    return (sector * 4) + 3

class SimpleMFRC522:

    READER = None

    def __init__(self):
        self.READER = MFRC522.MFRC522()

    # interaction functions for MFRC522:
    #
    # There are generally two functions, one for normal use and one suffixed with `_no_block`.
    # The latter version will just return on error or may return partial data,
    # while the former will call the latter in a loop until successful.

    # read the serial number from a card
    # will block until a serial number is successfully read
    #
    # returns the serial number as an integer
    def read_id(self):
        uid = None
        while uid is None:
            uid = self.read_id_no_block()
        return self.uid_to_num(uid)

    # try to read the serial number from a card
    # returns None if there was any kind of error
    # if a successful result is returned, the card will be activated
    #
    # returns the serial number as an array of 5 bytes
    def read_id_no_block(self):
        # prepare cards in the field for anti-collision detection
        status, TagType = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        # actually run the anticollisison stuff to get the serial number
        # of the card this activates the card
        status, uid = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        return uid

    # read the given blocks with the given key for all sectors
    # will block until the blocks are successfully read
    # if no blocks are given, read data from sector 2 (default for historical reasons)
    # if no key is set, use the default key
    #
    # returns a tuple:
    # - serial number as integer
    # - data as an array of bytes
    def read(self, blocks = [8, 9, 10], key = DEFAULT_KEY):
        uid, data = None, []
        while uid is None or len(data) < len(blocks):
            uid, text = self.read_no_block(sector, key)
        return self.uid_to_num(uid), text

    # try to read the given blocks with the given key
    #
    # returns a tuple:
    # - serial number as array of 5 bytes
    # - data as an array of bytes
    #
    # retuns (None, None) if there was a fatal error
    # may return partial data if there was an error while reading
    def read_no_block(self, blocks = [8, 9, 10], key = DEFAULT_KEY):
        # activate a card in the field and get its uid
        uid = self.read_id_no_block()
        if uid is None:
            return None, None

        self.READER.MFRC522_SelectTag(uid) # TODO is this still necessary after running read_id_no_block?

        unlocked_sector = None
        data = []
        for block in blocks:
            sector = sectorOf(block)
            if unlocked_sector != sector:
                # sector we want to read is not unlocked, so unlock it
                self.READER.MFRC522_StopCrypto1()
                unlocked_sector = None
                status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, trailerBlock(sector), key, uid)
                if status == self.READER.MI_OK:
                    unlocked_sector = sector
                else:
                    logging.error(f"failed to unlock sector {sector}")
                    self.READER.MFRC522_StopCrypto1()
                    return None, None
            read_block = self.READER.MFRC522_Read(block)
            if read_block:
                data.extend(read_block)
            else:
                break

        self.READER.MFRC522_StopCrypto1()
        return uid, data

    # write the given data to the given blocks
    # if no blocks are specified, write to sector 2 (historical default)
    # if no key is specified, use the default key
    #
    # data: array of bytes (16 bytes per block)
    # blocks: array of block numbers
    # key: array of 6 bytes
    #
    # returns a tuple:
    # - serial number as integer
    # - data as array of bytes
    def write(self, data, blocks = [8, 9, 10], key = DEFAULT_KEY):
        uid, readback = None, None
        while uid is None or data != readback:
            uid, readback = self.write_no_block(data, blocks, key)
        return self.uid_to_num(uid), readback

    # try to write the given data to the given blocks
    # also read back the bytes that were just written
    #
    # returns a tuple:
    # - serial number as array of bytes
    # - data as array of bytes
    #
    # returns (None, None) if there was a fatal error
    # may return partial data if there was an error while writing or validation reading
    def write_no_block(self, data, blocks, key):
        assert len(blocks) * 16 == len(data)
        # activate a card in the field and get its uid
        uid = self.read_id_no_block()
        if uid is None:
            return None, None

        self.READER.MFRC522_SelectTag(uid) # TODO is this still necessary after running read_id_no_block?

        readback = []
        unlocked_sector = None
        for i, block in enumerate(blocks):
            sector = sectorOf(block)
            if unlocked_sector != sector:
                # sector we want to read is not unlocked, so unlock it
                self.READER.MFRC522_StopCrypto1()
                unlocked_sector = None
                status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, trailerBlock(sector), key, uid)
                if status == self.READER.MI_OK:
                    unlocked_sector = sector
                else:
                    logging.error(f"failed to unlock sector {sector}")
                    self.READER.MFRC522_StopCrypto1()
                    return None, None
            self.READER.MFRC522_Write(block, data[i * 16:(i + 1) * 16])

            read_block = self.READER.MFRC522_Read(block)
            if read_block:
                readback.extend(read_block)
            else:
                break

        self.READER.MFRC522_StopCrypto1()
        return uid, readback

    # transform array of bytes to an integer
    def uid_to_num(self, uid):
        n = 0
        for byte in uid:
            n = (n << 8) | byte
        return n
