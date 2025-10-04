import asyncio
from collections.abc import Awaitable, Callable
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
    async def listen(self, request_open: Callable[[str], Awaitable[bool]]):
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

        lock = asyncio.Lock()

        def setup_connection(client_writer: asyncio.StreamWriter):
            # enable and configure TCP keepalive
            con: ssl.SSLSocket = client_writer.get_extra_info("socket")
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

            addr = con.getpeername()
            logger.info("connection from " + repr(addr))

        async def client_handler(
            client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
        ):
            if lock.locked():
                # only one concurrent connection is allowed
                return

            async with lock:
                setup_connection(client_writer)

                while True:
                    try:
                        # receive a packet (1 byte)
                        data = await client_reader.readexactly(1)
                    except Exception as e:
                        # some error during receiving, might have been a timeout
                        logger.error("error while receiving", exc_info=e)
                        break

                    assert len(data) == 1

                    if data[0] == RX_OPEN:
                        logger.info("opening requested")
                        # TODO transmit and use actual name
                        if await request_open("RFID"):
                            client_writer.write(bytes([TX_ACK]))
                        else:
                            client_writer.write(bytes([TX_NAK]))
                        await client_writer.drain()
                    else:
                        logger.warning(
                            "closing connection due to unrecognized message: ",
                            repr(data),
                        )
                        break
                logger.info("connection lost")

        await asyncio.start_server(
            client_handler,
            port=config.NETWORKING_PORT,
            limit=1,
            ssl=context,
        )
