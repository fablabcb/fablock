import socket
import ssl
import logging
import config

logger = logging.getLogger("tcp")

# TCP level keepalive is used for keeping the connection up.
#
# The client can request one of these actions.
TX_OPEN = bytes([0x00])
TX_BROADCAST = bytes([0x01])
# Followed by a UTF-8 encoded string.
# The end of the string is delimited by a byte that cannot occur in valid UTF-8.
TX_STRING_DELIM = bytes([0xFF])
# The server will respond with a zero byte if this operation was successful.
RX_ACK = 0x00
# Otherwise the server will respond with a 0x01 byte.
RX_NAK = 0x01

CLIENT_CERT_PATH = "/home/pi/client.crt"
CLIENT_KEY_PATH = "/home/pi/client.key"
SERVER_CERT_PATH = "/home/pi/server.crt"


def check_socket_alive(sock: ssl.SSLSocket) -> bool:
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        sock.setblocking(False)
        data = sock.recv(1, socket.MSG_PEEK)
        if len(data) == 0:
            return False
    except BlockingIOError:
        sock.setblocking(True)
        return True  # socket is open and reading from it would block
    except ConnectionResetError:
        return False  # socket was closed for some other reason
    except Exception as e:
        logger.exception("unexpected exception when checking if a socket is closed")
        return False

    sock.setblocking(True)
    return True


con: ssl.SSLSocket | None = None


def connect() -> ssl.SSLSocket | None:
    """
    Tries to connect to the server.
    If the connection is established, returns True.
    If a connection is not possible within a timeout, returns False
    """
    global con

    if con is not None:
        if check_socket_alive(con):
            return con
        else:
            connection_lost()

    try:
        sock = socket.create_connection((config.TCP_HOST, config.TCP_PORT), timeout=10)
    except socket.timeout:
        con = None
        return None

    # set socket to blocking mode
    sock.setblocking(True)
    # enable and configure TCP keepalive
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15)  # idle seconds (15s)
    sock.setsockopt(
        socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15
    )  # seconds between keepalive (15s)
    sock.setsockopt(
        socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4
    )  # maximum number of keepalive fails to be acceptable (4 * 15s = 1min)

    context = ssl.create_default_context(
        ssl.Purpose.SERVER_AUTH, cafile=SERVER_CERT_PATH
    )
    context.load_cert_chain(certfile=CLIENT_CERT_PATH, keyfile=CLIENT_KEY_PATH)
    context.check_hostname = (
        False  # checking the hostname on the self signed cert is not necessary
    )

    con = context.wrap_socket(sock)

    return con


def connection_lost():
    global con
    con = None

    logger.warning("connection lost")
    # TODO: send telegram message?
    # TODO: set indicator light?


def request_open(name: str) -> bool:
    """
    Requests the other end to open.

    Returns True if the request was successful or False otherwise.
    """

    if (con := connect()) is None:
        return False

    try:
        name_bin = bytes(name, encoding="utf-8")
        con.sendall(TX_OPEN + name_bin + TX_STRING_DELIM)
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
