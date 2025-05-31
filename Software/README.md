# fablock bot

This is a Discourse bot that opens the fablock.

You can either trigger the opening by sending a Discourse chat message to it or by using the TCP interface.
The TCP interface is intended for the RFID-companion.

## TCP interface

When the program is started it will open a TCP listening socket on port 55555.
You can trigger the opening sequence by sending a `0x00` byte.
The reply will be a `0x00` byte if the request if the request was successful and the window is being opened; otherwise the reply will be a `0x01` byte.

The functionality uses TCP level keepalive and is intended to have one long-running connection.
Only one connection is possible at a time.

## Installation

Clone repository:

```sh
apt install git # not installed by default on raspbian
cd /home/pi
git clone https://github.com/fablabcb/fablock.git
```

The rest can be done using the install script, which must be run as root to be able to install more packages.
```sh
sudo ./install.sh
```

To complete the installation, you will need to do the following (the script will also remind you):

Before starting the fablock you have to input the configuration for Discourse in `Software/secret_config.py`.

You will also need to either create TLS certificates for the networking protocol or disable the networking protocol in `config.py` by setting `NETWORKING_ENABLED = False`.
For instructions on creating the certificates, see the instructions in `RFID-companion/README.md`.

When you are done, start the service:

```sh
sudo systemctl start fablock.service
```

You should see/hear some (short) movement for homing the mechanism to the closed position when starting.
