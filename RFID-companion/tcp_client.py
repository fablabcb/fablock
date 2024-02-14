import socket
import logging
import config

logger = logging.getLogger("tcp")

# TCP level keepalive is used for keeping the connection up.
#
# All packets are one byte in length.
# The client can request opening by sending a zero byte.
TX_OPEN = 0x00
# The server will respond with a zero byte if this operation was successful.
RX_ACK = 0x00
# Otherwise the server will respond with a 0x01 byte.
RX_NAK = 0x01


con = None

def connect():
    """
    Tries to connect to the server.
    If the connection is established, returns True.
    If a connection is not possible within a timeout, returns False
    """
    global con

    if con is not None:
        return True

    try:
        con = socket.create_connection((config.TCP_HOST, config.TCP_PORT), timeout = 10)
    except socket.timeout:
        con = None
        return False

    # set socket to blocking mode
    con.settimeout(None)
    # enable and configure TCP keepalive
    con.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    con.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15) # idle seconds (15s)
    con.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15) # seconds between keepalive (15s)
    con.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4) # maximum number of keepalive fails to be acceptable (4 * 15s = 1min)
    return True

def connection_lost():
    global con
    con = None

    logger.warning("connection lost")
    # TODO: send telegram message?
    # TODO: set indicator light?

def request_open():
    """
    Requests the other end to open.

    Returns True if the request was successful or False otherwise.
    """

    global con

    if not connect():
        return False

    try:
        con.sendall(bytes([TX_OPEN]))
        data = con.recv(1)
    except:
        connection_lost()
        return False

    if len(data) == 0:
        connection_lost()
        return False

    if data[0] == RX_ACK:
        return True
    elif data[0] == RX_NAK:
        return False
    else:
        logger.warning("unrecognized answer: " + repr(data))
        return False
