#!/bin/env bash

set -e

# make sure we are in the correct diretory, especially because sudo
# will be used to run this file
cd /home/pi

# install external requirements
# -y to answer confirmation prompt with yes
apt -y install pigpio python3
systemctl enable pigpiod.service

# create a venv in a folder named "venv"
python3 -m venv venv

# install the required python packages in the venv
venv/bin/pip3 install telegram python-telegram-bot pigpio

systemctl enable /home/pi/fablock/Software/fablock.service

echo "WHAT TO DO NOW:"
echo ""
echo "- edit the secrets configuration file"
echo ""
echo "    $EDITOR /home/pi/fablock/Software/secrets.py"
echo ""
echo "- create TLS certificates or disable network integration by setting 'NETWORKING_ENABLED = False' in config.py"
echo ""
echo ""
echo "When you are done, start the fablock service:"
echo ""
echo "    sudo systemctl start fablock.service"
echo ""
