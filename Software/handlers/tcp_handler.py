from collections.abc import Callable
import config
import logging
import socket
import ssl
from . import Handler


logger = logging.getLogger("tcp")

# TCP level keepalive is used for keeping the connection up.
#
# All packets are one byte in length.
# The client can request opening by sending a zero byte.
RX_OPEN = 0x00
# The server will respond with a zero byte if this operation was successful.
TX_ACK = 0x00
# Otherwise the server will respond with a 0x01 byte.
TX_NAK = 0x01


class TcpHandler(Handler):
    def listen(self, request_open: Callable[[str], bool]):
        context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH, cafile=config.TLS_CLIENT_CERT_PATH
        )
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = (
            False  # checking the hostname on the self signed cert is not necessary
        )
        context.load_cert_chain(
            certfile=config.TLS_SERVER_CERT_PATH, keyfile=config.TLS_SERVER_KEY_PATH
        )

        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.bind((config.NETWORKING_HOST, config.NETWORKING_PORT))
            # only accept one connection at a time
            s.listen(0)

            while True:
                con, addr = s.accept()
                # enable and configure TCP keepalive
                con.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                con.setsockopt(
                    socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15
                )  # idle seconds (15s)
                con.setsockopt(
                    socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15
                )  # seconds between keepalive (15s)
                con.setsockopt(
                    socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4
                )  # maximum number of keepalive fails to be acceptable (4 * 15s = 1min)

                logger.info("connection from " + repr(addr))
                with context.wrap_socket(con, server_side=True) as con:
                    while True:
                        try:
                            # receive a packet (1 byte)
                            data = con.recv(1)
                        except Exception as e:
                            # some error during receiving, might have been a timeout
                            logger.error("error while receiving", exc_info=e)
                            break

                        if len(data) == 0:
                            logger.error("received empty data")
                            break

                        if data[0] == RX_OPEN:
                            logger.info("opening requested")
                            # TODO transmit and use actual name
                            if request_open("RFID"):
                                con.sendall(bytes([TX_ACK]))
                            else:
                                con.sendall(bytes([TX_NAK]))
                        else:
                            logger.warning(
                                "closing connection due to unrecognized message: ",
                                repr(data),
                            )
                            break
                logger.warning("connection lost")
