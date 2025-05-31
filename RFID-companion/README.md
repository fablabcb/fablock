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
Clone the repository
```sh
cd /home/pi
git clone https://github.com/fablabcb/fablock.git
```

For the SPI bus that was wired up above, you have to enable the SPI bus driver
with `raspi-config`.

The rest can be done using the install script, which must be run as root to be able to install more packages.
```sh
sudo ./install.sh
```

To complete the installation, you will need to do the following (the script will also remind you):
- Input the configuration for telegram in `RFID-companion/telegram-bot/config.py`
- Check the configuration for communication with the main fablock in `RFID-companion/config.py`, especially `TCP_HOST` and `TCP`_PORT`
- Prepare the TLS certificates (see section "TLS setup" below)

When you are done, start the service:
```sh
sudo systemctl start fablock-rfid.service
```

### TLS setup
The connection between the RFID-companion and the main fablock is secured using TLS. For this you will need to create certificates for both the fablock itself as well as the companion. This can be achieved with:
```sh
openssl req -new -newkey rsa:2048 -days 36500 -nodes -x509 -keyout tls.key -out tls.crt
```
You will probably be asked to input some values, you can input what you want or use the defaults, it does not matter for the purposes of this software.
The command must be run on each device separately, which will create two files on both devices:
- an RSA key (`tls.key`, this must be kept private) and
- a corresponding certificate (`tls.crt`).

Once the certificates are created, rename them appropriately to `server.key` and `client.key` and so on for each device. The RFID-companion is the client.
Copy the certificate (`.crt` file) to the other device, each device must have both certificates. The key files must not be copied as they contain secret data!
For example on the client (RFID-companion) you should have in total 3 files:
- `client.key`
- `client.crt`
- `server.crt`
