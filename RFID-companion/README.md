# RFID companion

This is an optional addition to the Fablock in case you want to be able to give
people access that cannot or do not want to use Telegram. This is done using a
second telegram bot that must be added to the same telegram group.

The hardware consists of a Raspberry Pi and the RFID reader. If the
surroundings allow for it, you could probably get away with running this
program on the same RPi. In our case however, the glass of our windows was too
thick for the reader to penetrate it, so we had to separate the RFID reader.

This bot can manage RFID tags through telegram commands and when a known and
valid tag is read, it will send the `/open` command to trigger the other bot.
It will also send an informational message of which card was read so it is
possible to audit who had access.

This implementation is written for a reader with the MFRC522 chip which is able
to read MIFARE 1K cards with Crypto1 implementation.

## Hardware setup
The MFRC522's you can usually get on breakout boards have the SPI bus wired.
The Raspberry Pi has hardware SPI pins.

The MFRC522 should be connected to the respective GPIO pins for SPI. The pins
on the breakout board should usually be labeled. For quick reference, here are
the physical pins on the Raspbery Pi that you will need to connect to:

|name on reader|physical RPi pin|BCM pin|
|---------------|---|---|
|VCC, 3v3       | 17|  -|
|MOSI, SIMO, SDO| 19| 10|
|GND            | 20|  -|
|MISO, SOMI, SDI| 21|  9|
|RST            | 22| 25|
|CLK, SCLK      | 23| 11|
|NSS, CSB       | 24|  8|

The breakout boards often also have a pin labeled "IRQ" or something similar,
this pin will stay unconnected.

There is an additional LED indicating the state of the RFID reader, so you
could label it something like "READY". The LED will go out while the reader is
inactive, which will happen whenever the RFID reader reads anything. This LED
is wired to a ground pin (suggested physical pin 14) and pyhsical pin 18, i.e.
BCM pin 24.

This LED is recommended but entirely optional. It will be on whenever the reader
is ready to read a card and will be off when the reader is currently disabled
due to a timeout.

## Software setup
For the SPI bus that was wired up above, you have to enable the SPI bus driver
with `raspi-config`.

For PiGpio to work you may also have to install a system package, e.g. on Raspbian:
```sh
sudo apt install pigpio
sudo systemctl enable pigpiod.service
sudo systemctl start pigpiod.service
```

On newer python versions, you will use a venv. You can create one in a new diretory `venv` (last parameter) with:
```sh
python -m venv venv
```
Please make sure these python packages are installed in the venv:
- `python-telegram-bot`
- `spidev`
- `pigpio`

E.g. on Raspbian:
```sh
venv/bin/pip install python-telegram-bot spidev pigpio
```

You can use the provided `fablock-rfid.service` systemd service file to run the RFID companion.
