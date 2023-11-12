# -*- coding: utf8 -*-
#
#    Copyright 2014,2018 Mario Gomez <mario.gomez@teubi.co>
#
#    This file is part of MFRC522-Python
#    MFRC522-Python is a simple Python implementation for
#    the MFRC522 NFC Card Reader for the Raspberry Pi.
#
#    MFRC522-Python is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    MFRC522-Python is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with MFRC522-Python.  If not, see <http://www.gnu.org/licenses/>.
#
import spidev
import signal
import time
import logging
from functools import reduce
import operator

class MFRC522:
    MAX_LEN = 16

    # constants to signal errors
    MI_OK = 0
    MI_NOTAGERR = 1
    MI_ERR = 2

    # NXP MFRC522 commands as documented by the data sheet rev 3.9
    # unused commands are omitted
    PCD_IDLE       = 0x00 # 0b0000 no action, cancels current command execution
    PCD_CALCCRC    = 0x03 # 0b0011 activates the CRC coprocessor or performs a self test
    PCD_TRANSMIT   = 0x04 # 0b0100 transmits data from the FIFO buffer
    PCD_RECEIVE    = 0x08 # 0b1000 activates the receiver circuits
    PCD_TRANSCEIVE = 0x0C # 0b1100 transmits data from FIFO buffer to antenna and automatically activates the receiver after transmission
    PCD_AUTHENT    = 0x0E # 0b1110 performs the MIFARE standard authentication as a reader
    PCD_RESETPHASE = 0x0F # 0b1111 resets the MFRC522

    # NXP MFRC522 registers as documented by the data sheet rev 3.9
    # unused registers are omitted
    # page 0: command status
    CommandReg     = 0x01 # starts and stops command execution
    ComIEnReg      = 0x02 # enable and disable interrupt request control bits
    ComIrqReg      = 0x04 # interrupt request bits
    DivIrqReg      = 0x05 # interrupt request bits
    ErrorReg       = 0x06 # error bits showing the error status of the last command executed
    Status2Reg     = 0x08 # receiver and transmitter status bits
    FIFODataReg    = 0x09 # input and output of 64 byte FIFO buffer
    FIFOLevelReg   = 0x0A # number of bytes stored in the FIFO buffer
    ControlReg     = 0x0C # miscellaneous control registers
    BitFramingReg  = 0x0D # adjustments for bit-oriented frames
    # page 1: command
    ModeReg        = 0x11 # defines general modes for transmitting and receiving
    TxControlReg   = 0x14 # controls the logical behavior of the antenna driver pins TX1 and TX2
    TxASKReg       = 0x15 # controls the setting of the transmission modulation
    # page 2: configuration
    CRCResultRegM  = 0x21 # shows the MSB and LSB values of the CRC calculation
    CRCResultRegL  = 0x22 # ... continued
    RFCfgReg       = 0x26 # configures the receiver gain
    TModeReg       = 0x2A # defines settings for the internal timer
    TPrescalerReg  = 0x2B # defines settings for the internal timer
    TReloadRegH    = 0x2C # defines the 16-bit timer reload value
    TReloadRegL    = 0x2D # ... continued
    # page 3 (test registers) is not used here and omitted

    # PICC (proximity integrated circuit card) commands (ISO/IEC 14443-4)
    PICC_REQIDL    = 0x26 # PICCs in state IDLE should go to READY and prepare for anticollision detection
    PICC_READ      = 0x30 # MIFARE Classic: read 16 byte block from authenticated sector
    PICC_HALT      = 0x50 # PICCs in state ACTIVE should go to state HALT
    PICC_REQALL    = 0x52 # PICCs in state IDLE and HALT should go to READY and prepare for anticollission detection
    PICC_AUTHENT1A = 0x60 # MIFARE Classic: perform authentication with Key A
    PICC_AUTHENT1B = 0x61 # MIFARE Classic: perform authentication with Key B
    PICC_SELECTTAG = 0x93 # anticollision/select, cascade level 1 of 3
    PICC_WRITE     = 0xA0 # MIFARE Classic: write 16 byte block to authenticated sector
    PICC_TRANSFER  = 0xB0 # MIFARE Classic: write content of internal data register to a block
    PICC_DECREMENT = 0xC0 # MIFARE Classic: decrement a block and store result in internal data register
    PICC_INCREMENT = 0xC1 # MIFARE Classic: increment a block and store result in internal data register
    PICC_RESTORE   = 0xC2 # MIFARE Classic: read contents of a block into internal data register

    # from for MFRC522 datasheet: "speeds up to 10 Mbit/s"
    # just using 1 Mbit/s by default
    def __init__(self, bus=0, device=0, spd=1_000_000, debugLevel='WARNING'):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = spd

        self.logger = logging.getLogger('mfrc522Logger')
        self.logger.addHandler(logging.StreamHandler())
        level = logging.getLevelName(debugLevel)
        self.logger.setLevel(level)

        self.MFRC522_Init()

    # low level interaction methods for manipulating the MFRC522's registers

    # send the soft reset command to the chip
    def MFRC522_Reset(self):
        self.Write_MFRC522(self.CommandReg, self.PCD_RESETPHASE)

    # writes a byte to the given address on the chip
    def Write_MFRC522(self, addr, val):
        # address is constructed according to 8.1.2.3 from the data sheet
        # MSB = 1 for writing
        # 6 bits address
        # 1 bit constant 0
        self.spi.writebytes2([(addr << 1) & 0x7E, val])

    # reads a byte from the given address on the chip
    def Read_MFRC522(self, addr):
        # address is constructed according to 8.1.2.3 from the data sheet
        # MSB = 0 for reading
        # 6 bits address
        # 1 bit constant 0
        #
        # send address, then let the chip respond one byte
        val = self.spi.xfer2([((addr << 1) & 0x7E) | 0x80, 0])
        # during val[0] the command is sent so the chip won't respond
        return val[1]

    # terminates the connection to the chip
    def Close_MFRC522(self):
        self.spi.close()

    # changes the given address so the bits of the mask are set
    def SetBitMask(self, addr, mask):
        tmp = self.Read_MFRC522(addr)
        self.Write_MFRC522(addr, tmp | mask)

    # changes the given address so the bits of the mask are not set
    def ClearBitMask(self, addr, mask):
        tmp = self.Read_MFRC522(addr)
        self.Write_MFRC522(addr, tmp & (~mask))

    # medium level interactions manipulating the MFRC522

    # instructs the chip to enable the antenna
    def AntennaOn(self):
        self.SetBitMask(self.TxControlReg, 0x03)

    # instructs the chip to disable the antenna
    def AntennaOff(self):
        self.ClearBitMask(self.TxControlReg, 0x03)

    # communicate some data to the card under the given command
    # (can be used for normal command sending or authenticating)
    #
    # returns a tuple:
    # - status (MI_OK or MI_ERR)
    # - the received bytes
    # - the number of bits received (may not be a multiple of 8)
    def MFRC522_ToCard(self, command, sendData):
        irqEn = 0x00
        waitIRq = 0x00

        if command == self.PCD_AUTHENT:
            irqEn = 0x12 # set IdleIEn, ErrIEn
            waitIRq = 0x10 # IdleIRq (wait for command to finish)
        if command == self.PCD_TRANSCEIVE:
            irqEn = 0x77 # set TxlEn, RxlEn, IdleIEn, LoAlertIEn, ErrIEn, TimerIEn
            waitIRq = 0x30 # IdleIRQ & RxIRq (wait for command to finish and valid data stream to be detected)

        self.Write_MFRC522(self.ComIEnReg, irqEn | 0x80) # always set IRqInv bit
        self.ClearBitMask(self.ComIrqReg, 0x80) # clear interrupts
        self.SetBitMask(self.FIFOLevelReg, 0x80) # clear FIFO buffer

        self.Write_MFRC522(self.CommandReg, self.PCD_IDLE) # send chip to idle

        # write sendData to FIFO buffer
        for i in range(len(sendData)):
            self.Write_MFRC522(self.FIFODataReg, sendData[i])

        # send the respective command
        self.Write_MFRC522(self.CommandReg, command)

        if command == self.PCD_TRANSCEIVE:
            self.SetBitMask(self.BitFramingReg, 0x80) # set StartSend bit

        status = self.MI_ERR
        # wait for the transmission to finish, but at most 2000 iterations
        for i in range(2000):
            ComIrqReg = self.Read_MFRC522(self.ComIrqReg)
            # break if TimerIRq is set or the appropriate for this command
            if (ComIrqReg &  0x01) or (ComIrqReg & waitIRq):
                status = self.MI_OK
                break

        self.ClearBitMask(self.BitFramingReg, 0x80) # clear StartSend bit

        receivedData = []
        receivedBits = 0

        if status == self.MI_OK:
            # check that BufferOvfl, CollErr, ParityErr, ProtocolErr are not set
            if (self.Read_MFRC522(self.ErrorReg) & 0x1B) == 0x00:
                if command == self.PCD_TRANSCEIVE: # was there any data to be received?
                    FIFOLevel = self.Read_MFRC522(self.FIFOLevelReg)
                    FIFOLevel = min(FIFOLevel, self.MAX_LEN)

                    receivedBits = FIFOLevel * 8

                    # RxLastBits will be 0 if all bytes were valid,
                    # otherwise indicates the number of invalid bits
                    # in the last byte
                    RxLastBits = self.Read_MFRC522(self.ControlReg) & 0x07
                    if RxLastBits != 0:
                        receivedBits -= 8 - RxLastBits

                    # read all data from the FIFO buffer
                    for i in range(FIFOLevel):
                        receivedData.append(self.Read_MFRC522(self.FIFODataReg))
            else:
                status = self.MI_ERR

        return status, receivedData, receivedBits

    # calculate Cyclic Redundancy Check of data using the MFRC522 coprocessor
    #
    # returns an array of 2 bytes
    def CalculateCRC(self, pIndata):
        self.ClearBitMask(self.DivIrqReg, 0x04) # reset status indication for CRC completion
        self.SetBitMask(self.FIFOLevelReg, 0x80) # clear FIFO buffer

        # write data to FIFO buffer
        for i in range(len(pIndata)):
            self.Write_MFRC522(self.FIFODataReg, pIndata[i])

        self.Write_MFRC522(self.CommandReg, self.PCD_CALCCRC) # start CRC calculation
        # wait for CRC calculation to complete, i.e. until DivIrqReg[CRCIRq] bit is set
        # but at most 255 iterations
        for i in range(0xFF):
            CRCIRq = self.Read_MFRC522(self.DivIrqReg) & 0x04
            if CRCIRq:
                break

        # read CRC result from chip
        return [self.Read_MFRC522(self.CRCResultRegL), self.Read_MFRC522(self.CRCResultRegM)]

    # high level interactions with the card (PICC)

    # request something from the card
    #
    # returns a tuple:
    # - status (MI_OK or MI_ERR)
    # - number of bits received
    def MFRC522_Request(self, reqMode):
        # set RxAlign for bit oriented frames, here:
        #
        # LSB of the received bit is stored at bit position 7, the second
        # received bit is stored in the next byte that follows at bit
        # position 0
        self.Write_MFRC522(self.BitFramingReg, 0x07)

        status, _data, bits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, [reqMode])

        if status != self.MI_OK or bits != 0x10:
            status = self.MI_ERR

        return status, bits

    # activate any card and request the serial number from it ("anticollision loop")
    # checks the integrity of the serial number to see that there was only one card activated
    #
    # returns a tuple:
    # - status (MI_OK or MI_ERR)
    # - serial number (5 byte array)
    def MFRC522_Anticoll(self):
        # set BitFramingReg:
        # - clear StartSend (incidental)
        # - set RxAlign to 0 (all bits consecutive)
        # - all bits of the last byte should be transmitted
        self.Write_MFRC522(self.BitFramingReg, 0x00)

        status, serNum, bits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, [self.PICC_SELECTTAG, 0x20])

        if status == self.MI_OK:
            if bits == 5 * 8: # serial number is 5 bytes
                # check the integrity of the serial number
                # first four bytes XORed together must equal the last byte
                serNumCheck = reduce(operator.xor, serNum[:4], 0)
                if serNumCheck != serNum[4]:
                    status = self.MI_ERR
            else:
                status = self.MI_ERR

        return status, serNum

    # activate a specific card by its serial number
    #
    # returns a byte indicating the size of the card
    def MFRC522_SelectTag(self, serNum):
        buf = [self.PICC_SELECTTAG, 0x70]
        buf.extend(serNum[:5])
        # add CRC of buffer this far
        buf.extend(self.CalculateCRC(buf))

        # tell the card that it has been selected this will return the
        # ATS (Answer To Select) with information about the cardse
        status, ATS, bits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)

        if status == self.MI_OK and bits == 0x18:
            self.logger.debug("Size: " + str(ATS[0]))
            return ATS[0]
        else:
            return 0

    # Authenticate with MIFARE Classic
    # authMode: a MIFARE PICC command to select the authentication mode (PICC_AUTHENT1A or PICC_AUTHENT1B)
    # BlockAddr: address of the trailer block
    # Sectorkey: 6 byte array representing the key
    # serNum: serial number of the card
    def MFRC522_Auth(self, authMode, BlockAddr, Sectorkey, serNum):
        buf = [
            authMode,
            BlockAddr,
        ]
        buf.extend(Sectorkey)
        buf.extend(serNum[:4]) # the checksum of the serial number is not used

        # starting the authentication itself
        status, backData, backLen = self.MFRC522_ToCard(self.PCD_AUTHENT, buf)

        # Check if an error occurred
        if status != self.MI_OK:
            self.logger.error("AUTH ERROR!!")
        # check if MFCrypto1On bit is set
        if (self.Read_MFRC522(self.Status2Reg) & 0x08) == 0:
            self.logger.error("failed to activate MIFARE Crypto1 unit")

        return status

    # stops encrypted communication
    def MFRC522_StopCrypto1(self):
        # disable MIFARE Crypto1 unit
        self.ClearBitMask(self.Status2Reg, 0x08)

    # read a block from the card
    #
    # returns an array of 16 bytes if successful
    # otherwise returns None
    def MFRC522_Read(self, blockAddr):
        buf = [self.PICC_READ, blockAddr]
        buf.extend(self.CalculateCRC(buf))

        status, backData, bits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
        if status != self.MI_OK:
            self.logger.error("Error while reading!")

        if bits != 16 * 8:
            return None

        self.logger.debug("Sector " + str(blockAddr) + " " + str(backData))
        return backData

    # write a block to the card
    # blockAddr: address of the block to be written
    # writeData: an array of 16 bytes
    #
    # returns False if there was an error while writing the data
    # otherwise returns True
    def MFRC522_Write(self, blockAddr, writeData):
        assert len(writeData) == 16, "writeData must be 16 bytes"

        buf = [self.PICC_WRITE, blockAddr]
        buf.extend(self.CalculateCRC(buf))

        status, backData, bits = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
        # the card should return a nibble with the value 0xA
        if status != self.MI_OK or bits != 4 or (backData[0] & 0x0F) != 0x0A:
            status = self.MI_ERR
            return False

        if status == self.MI_OK:
            buf = writeData.copy()
            buf.extend(self.CalculateCRC(buf))

            status, backData, backLen = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
            # the card should return a nibble with the value 0xA
            if status != self.MI_OK or backLen != 4 or (backData[0] & 0x0F) != 0x0A:
                self.logger.error("Error while writing")
                return False
            else:
                self.logger.debug("Data written")
                return True


    # try to dump a MIFARE Classic 1K card to the logger
    def MFRC522_DumpClassic1K(self, key, uid):
        for i in range(64):
            status = self.MFRC522_Auth(self.PICC_AUTHENT1A, i, key, uid)
            # Check if authenticated
            if status == self.MI_OK:
                self.MFRC522_Read(i)
            else:
                self.logger.error("Authentication error")

    def MFRC522_Init(self):
        # perform soft reset on the chip
        self.MFRC522_Reset()
        # set TModeReg:
        # - set TAuto bit (automatically start timer after finishing transmission)
        # - set TGated to 0 (internal timer is running in gated mode)
        # - clear TAutoRestart bit (set TimerIRq instead of restarting)
        # - set TPrescaler_Hi
        self.Write_MFRC522(self.TModeReg, 0x8D)
        # set TPrescalerReg (setting TPrescaler_Lo)
        # TPrescaler = 0xD3E
        self.Write_MFRC522(self.TPrescalerReg, 0x3E)
        # set TReloadReg = 0x0030
        self.Write_MFRC522(self.TReloadRegL, 30)
        self.Write_MFRC522(self.TReloadRegH, 0)
        # set TxASKReg and sets Force100ASK bit:
        # forces a 100 % ASK modulation independent of the ModGsPReg register setting
        self.Write_MFRC522(self.TxASKReg, 0x40)
        # set ModeReg:
        # - clear MSBFirst bit (CRC coprocessor calcuates with LSB first)
        # - set TxWaitRf bit (transmitter can only be started if an RF field is generated)
        # - sets reserved bit 4?
        # - set PolMFin bit (polarity of pin MFIN is active HIGH)
        # - sets reserved bit 2?
        # - set CRCPreset to 01 (CRC preset = 0x6363)
        self.Write_MFRC522(self.ModeReg, 0x3D)
        # set RFCfgReg so RxGain is the maximum value (48 dB)
        self.Write_MFRC522(self.RFCfgReg, 0x70)

        self.AntennaOn()
