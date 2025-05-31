#!/bin/env bash

# exit as soon as there is any error
set -e

# make sure we are in the correct directory, especially because sudo
# will be used to run this file
cd /home/pi

apt -y install git pigpio python3
systemctl enable pigpiod.service

# create a venv in a folder named "venv"
python3 -m venv venv

# install the required python packages in the venv
venv/bin/pip3 install -r requirements.txt

systemctl enable /home/pi/fablock/RFID-companion/fablock-rfid.service

echo ""
echo "WHAT TO DO NOW:"
echo ""
echo "- edit the telegram secrets configuration file"
echo "    $EDITOR /home/pi/fablock/RFID-companion/telegram_bot/config.py"
echo ""
echo "- check the configuration to communicate with the main fablock, especially TCP_HOST and TCP_PORT"
echo "    $EDITOR /home/pi/fablock/RFID-companion/config.py"
echo ""
echo "- create TLS certificates and exchange with main fablock (see README.md section TLS setup)"
echo "    openssl req -new -newkey rsa:2048 -days 36500 -nodes -x509 -keyout tls.key -out tls.crt"
echo ""
echo "When you are done, start the fablock-rfid service:"
echo ""
echo "    sudo systemctl start fablock-rfid.service"
echo ""
