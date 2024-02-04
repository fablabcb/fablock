# fablock bot

This is a telegram bot that opens the fablock.

You can either trigger the opening by sending a Telegram command to it or by using the TCP interface.
The TCP interface is intended for the RFID-companion.

## TCP interface

When the program is started it will open a TCP listening socket on port 55555.
You can trigger the opening sequence by sending a `0x00` byte.
The reply will be a `0x00` byte if the request if the request was successful and the window is being opened; otherwise the reply will be a `0x01` byte.

The functionality uses TCP level keepalive and is intended to have one long-running connection.
Only one connection is possible at a time.

## Installation

Clone repository:

```
cd /home/pi
git clone --branch all-in-one-system  https://github.com/fablabcb/fablock.git 
```

Install python packages:

```
sudo apt install python3-pip
pip3 install telegram
pip3 install python-telegram-bot
```

Install and enable pigpio systemd daemon:

```
sudo apt install pigpio python3-pigpio
sudo systemctl enable pigpiod.service
```

Install fablock systemd file:

```
sudo ln -s /home/pi/fablock/Elektronik/Raspberry-Motorsteuerung/Software/fablock.service /etc/systemd/system/fablock.service

sudo systemctl daemon-reload
sudo systemctl enable fablock.service
```

To start the fablock:
```
sudo systemctl start fablock.service
```

or just reboot the pi.
