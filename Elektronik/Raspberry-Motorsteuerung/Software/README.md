# fablock bot

This is a telegram bot that opens the fablock.

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
pip3 install --force-reinstall -v "python-telegram-bot==13.11"
```

NOTE: version 20.x of python-telegram-bot changed apis drastically, thats why we force the specific
version. 

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